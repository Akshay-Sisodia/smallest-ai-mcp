import os
import base64
import requests
import json
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, StreamingResponse
import httpx
import tempfile
import uuid
import wave
import datetime

load_dotenv()
WAVES_API_KEY = os.getenv("WAVES_API_KEY")
if not WAVES_API_KEY:
    raise RuntimeError("WAVES_API_KEY env variable required")

# Utility: Get output directory for generated files
MCP_BASE_PATH = os.getenv("MCP_BASE_PATH", "/tmp")

def waves_api(path, method="GET", headers=None, json=None, data=None, files=None):
    """
    Wrapper for all Waves API calls.
    Always includes the Bearer token in the Authorization header as per docs:
    https://waves-docs.smallest.ai/v3.0.1/content/api-references/authentication
    """
    headers = headers.copy() if headers else {}
    # Always set Authorization header as required by docs
    headers['Authorization'] = f'Bearer {os.getenv("WAVES_API_KEY")}'
    url = path if path.startswith("http") else f"https://waves-api.smallest.ai{path}"
    resp = requests.request(method, url, headers=headers, json=json, data=data, files=files)
    return resp

mcp = FastMCP("smallest-ai-waves")

@mcp.tool()
def createClone(
    model: str = "lightning-large",
    displayName: str = "",
    file: str = ""
) -> dict:
    wav_bytes = base64.b64decode(file)
    files = {'file': ('voice.wav', wav_bytes, 'audio/wav')}
    data = {'displayName': displayName}
    resp = waves_api(f'/api/v1/{model}/add_voice', method="POST", files=files, data=data)
    if not resp.ok:
        raise RuntimeError(f"Failed to create clone: {resp.status_code} {resp.text}")
    return {
        "content": [{
            "type": "resource",
            "resource": {
                "uri": "waves://create-clone",
                "text": json.dumps(resp.json()),
                "mimeType": "application/json"
            }
        }]
    }

@mcp.tool()
def listClones(
    model: str = "lightning-large"
) -> dict:
    resp = waves_api(f'/api/v1/{model}/get_cloned_voices')
    if not resp.ok:
        raise RuntimeError(f"Failed to list clones: {resp.status_code} {resp.text}")
    return {
        "content": [{
            "type": "resource",
            "resource": {
                "uri": "waves://clones",
                "text": json.dumps(resp.json()),
                "mimeType": "application/json"
            }
        }]
    }

@mcp.tool()
def deleteClone(
    model: str = "lightning-large",
    voiceId: str = ""
) -> dict:
    resp = waves_api(
        f'/api/v1/{model}',
        method="DELETE",
        headers={"Content-Type": "application/json"},
        json={"voiceId": voiceId}
    )
    if not resp.ok:
        raise RuntimeError(f"Failed to delete clone: {resp.status_code} {resp.text}")
    return {
        "content": [{
            "type": "resource",
            "resource": {
                "uri": "waves://delete-clone",
                "text": json.dumps(resp.json()),
                "mimeType": "application/json"
            }
        }]
    }

@mcp.tool()
def listVoices() -> dict:
    resp = waves_api('/api/v1/lightning/get_voices')
    if not resp.ok:
        raise RuntimeError(f"Failed to fetch voices: {resp.status_code} {resp.text}")
    data = resp.json()
    return {
        "content": [{
            "type": "resource",
            "resource": {
                "uri": "waves://voices",
                "text": json.dumps(data),
                "mimeType": "application/json"
            }
        }]
    }

@mcp.tool()
def ttsToWav(
    text: str,
    voiceId: str,
    model: str = "lightning",
    language: str = None,
    outputFormat: str = "wav",
    add_wav_header: bool = False,
    sample_rate: int = 24000,
    speed: float = 1.0,
    consistency: float = 0.5,
    similarity: float = 0.0,
    enhancement: float = 1.0,
    output_dir: str = None
) -> dict:
    """
    Generate TTS audio and save it as a WAV file in a configurable output directory, returning the file URI for LLM playback. Follows MCP resource conventions. Adds duration, timestamp, and file size to metadata.
    If output_dir is provided, saves the file there; otherwise, uses a temp directory in the project folder (./tmp) or MCP_BASE_PATH.
    """
    import uuid
    import tempfile
    import os
    # Prepare payload as in ttsSync
    if model == "lightning":
        endpoint = "/api/v1/lightning/get_speech"
        payload = {
            "text": text,
            "voice_id": voiceId,
            "add_wav_header": add_wav_header,
            "sample_rate": sample_rate,
            "speed": speed,
            "consistency": consistency,
            "similarity": similarity,
            "enhancement": enhancement,
            "output_format": outputFormat,
        }
    elif model == "lightning-large":
        endpoint = "/api/v1/lightning-large/get_speech"
        payload = {
            "text": text,
            "voice_id": voiceId,
            "language": language,
            "add_wav_header": add_wav_header,
            "sample_rate": sample_rate,
            "speed": speed,
            "consistency": consistency,
            "similarity": similarity,
            "enhancement": enhancement,
            "output_format": outputFormat,
        }
    else:
        raise RuntimeError(f"Unsupported model: {model}")
    resp = waves_api(
        endpoint,
        method="POST",
        headers={"Content-Type": "application/json"},
        json=payload
    )
    if not resp.ok:
        raise RuntimeError(f"TTS failed: {resp.status_code} {resp.text}")
    # Determine output directory
    if output_dir:
        save_dir = output_dir
    else:
        # Use ./tmp in the project folder by default
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "tmp"))
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    filename = f"tts_{uuid.uuid4().hex}.wav"
    file_path = os.path.join(save_dir, filename)
    # ElevenLabs: ensure correct binary data is written
    audio_bytes = resp.content
    # If the API sometimes returns base64-encoded audio, decode it (uncomment if needed)
    # import base64
    # audio_bytes = base64.b64decode(resp.json().get('audio', ''))
    with open(file_path, "wb") as f:
        f.write(audio_bytes)
        f.flush()
        os.fsync(f.fileno())
    # Validate WAV header (RIFF)
    with open(file_path, "rb") as f:
        header = f.read(4)
        if header != b'RIFF':
            raise RuntimeError(f"Invalid WAV file written (missing RIFF header): {file_path}")
    if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
        raise RuntimeError(f"Failed to write audio file: {file_path}")
    # Get duration (if WAV)
    duration = None
    try:
        with wave.open(file_path, 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)
    except Exception:
        pass
    file_stat = os.stat(file_path)
    return {
        "content": [{
            "type": "resource",
            "resource": {
                "uri": f"file://{file_path}",
                "filename": filename,
                "mimeType": "audio/wav",
                "size": file_stat.st_size,
                "duration": duration,
                "created_at": datetime.datetime.fromtimestamp(file_stat.st_ctime).isoformat()
            }
        }],
        "meta": {
            "output_dir": save_dir
        }
    }

@mcp.tool()
def cleanupGeneratedAudio(
    older_than_minutes: int = 60
) -> dict:
    """
    Remove generated audio files in the MCP_BASE_PATH older than a given number of minutes. Returns count and list of deleted files.
    """
    import os
    import time
    now = time.time()
    deleted = []
    cutoff = now - older_than_minutes * 60
    for fname in os.listdir(MCP_BASE_PATH):
        if fname.startswith("tts_") and fname.endswith(".wav"):
            fpath = os.path.join(MCP_BASE_PATH, fname)
            try:
                if os.path.isfile(fpath) and os.path.getctime(fpath) < cutoff:
                    os.remove(fpath)
                    deleted.append(fname)
            except Exception:
                pass
    return {"deleted": deleted, "count": len(deleted)}

# NOTE: The playWavFile tool is deprecated and will be removed. For MCP-compliance and client-side playback, only return file resources (URIs) via ttsToWav. Clients/LLMs are responsible for playback.

# Create the SSE app from FastMCP
app = mcp.sse_app()

# Optional: Add a status endpoint for "/"
@app.route("/")
async def homepage(request):
    return PlainTextResponse("MCP SSE server running. Use /sse for protocol.")

if __name__ == "__main__":
    print("Starting MCP server with SSE transport on port 8000...")
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, log_level="info")
