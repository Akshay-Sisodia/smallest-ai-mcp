import os
import base64
import requests
import json
import logging
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, StreamingResponse
import httpx
import uuid
import wave
import datetime
import tempfile

load_dotenv()

# --- Configuration ---
# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API Configuration
WAVES_API_BASE_URL = "https://waves-api.smallest.ai"
WAVES_API_KEY = os.getenv("WAVES_API_KEY")
if not WAVES_API_KEY:
    # Log error before raising
    logger.critical("WAVES_API_KEY environment variable is not set. Server cannot start.")
    raise RuntimeError("WAVES_API_KEY env variable required")

# Model Endpoints (using f-strings for clarity if base URL might change)
ENDPOINT_LIGHTNING_GET_SPEECH = f"{WAVES_API_BASE_URL}/api/v1/lightning/get_speech"
ENDPOINT_LIGHTNING_LARGE_GET_SPEECH = f"{WAVES_API_BASE_URL}/api/v1/lightning-large/get_speech"
ENDPOINT_GET_VOICES = f"{WAVES_API_BASE_URL}/api/v1/lightning/get_voices" # Assuming lightning for general voices
ENDPOINT_MODEL_ADD_VOICE = f"{WAVES_API_BASE_URL}/api/v1/{{model}}/add_voice" # Placeholder for model
ENDPOINT_MODEL_GET_CLONES = f"{WAVES_API_BASE_URL}/api/v1/{{model}}/get_cloned_voices" # Placeholder for model
ENDPOINT_MODEL_DELETE = f"{WAVES_API_BASE_URL}/api/v1/{{model}}" # Placeholder for model

# Output Configuration
MCP_BASE_PATH = os.getenv("MCP_BASE_PATH", "/tmp")
logger.info(f"Using MCP_BASE_PATH: {MCP_BASE_PATH}")

# Custom Exception for Waves API errors
class WavesApiError(Exception):
    def __init__(self, message, status_code=None, reason=None, text=None):
        super().__init__(message)
        self.status_code = status_code
        self.reason = reason
        self.text = text

    def __str__(self):
        # Log the full error when it's created/raised might be better than just in __str__
        full_error_details = f"Status: {self.status_code}, Reason: {self.reason}, Text: {self.text}"
        # Shorten the string representation for general display
        return f"WavesApiError: {super().__str__()} (Status: {self.status_code})"

# Create a single httpx client for reuse
http_client = httpx.AsyncClient()

# Wrapper for Waves API calls - now asynchronous
async def waves_api(path, method="GET", headers=None, json_payload=None, data=None, files=None):
    """
    Asynchronous wrapper for all Waves API calls.
    Uses defined constants for base URL and Authorization header.
    """
    headers = headers.copy() if headers else {}
    headers['Authorization'] = f'Bearer {WAVES_API_KEY}'
    # Use path directly as it should now contain the full URL from constants
    url = path # Assuming path is now a full URL like ENDPOINT_GET_VOICES
    logger.debug(f"Calling Waves API: {method} {url}")
    try:
        resp = await http_client.request(method, url, headers=headers, json=json_payload, data=data, files=files)
        logger.debug(f"Received response: {resp.status_code}")

        if not resp.is_success:
            try:
                error_text = await resp.aread()
                error_text = error_text.decode('utf-8', errors='replace')
            except Exception as decode_err:
                error_text = f"[Could not decode error body: {decode_err}]"
            # Log the detailed error before raising
            logger.error(f"Waves API Error: Status={resp.status_code}, Reason={resp.reason_phrase}, URL={url}, Response Text={error_text}")
            raise WavesApiError(
                f"Waves API request failed to {url}",
                status_code=resp.status_code,
                reason=resp.reason_phrase,
                text=error_text
            )
        return resp
    except httpx.RequestError as exc:
        logger.error(f"HTTPX RequestError while calling {url}: {exc}")
        raise WavesApiError(f"Network error calling Waves API at {url}: {exc}") from exc
    except Exception as exc:
        # Catch unexpected errors during the request process
        logger.exception(f"Unexpected error during Waves API call to {url}: {exc}")
        raise WavesApiError(f"Unexpected error during API call to {url}") from exc

mcp = FastMCP("smallest-ai-waves")

@mcp.tool()
async def createClone(
    model: str = "lightning-large",
    displayName: str = "",
    file: dict = None  # Changed to accept a dictionary with file data
) -> dict:
    """
    Creates a new voice clone on the Waves API using the provided audio file.

    Args:
        model: The model to use for cloning (e.g., "lightning-large").
        displayName: The desired display name for the new clone.
        file: A dictionary containing the file information, including 'content' (base64 encoded audio),
              'name' (optional), and 'type' (optional). Expected content type is audio/wav.

    Returns:
        A dictionary in MCP format containing the API response or an error message.
    """
    logger.info(f"Starting createClone with model={model}, displayName={displayName}")
    logger.info(f"Received file data type: {type(file)}")

    try:
        if not file or not isinstance(file, dict):
            error_msg = f"Invalid file data: {type(file)}"
            logger.error(error_msg)
            return {
                "content": [{"type": "error", "message": error_msg}]
            }

        if 'content' not in file:
            error_msg = "No file content provided"
            logger.error(error_msg)
            return {
                "content": [{"type": "error", "message": error_msg}]
            }

        logger.info(f"File info - name: {file.get('name', 'N/A')}, type: {file.get('type', 'N/A')}")

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file_path = temp_file.name # Store path for logging/cleanup
            try:
                if isinstance(file['content'], str):
                    logger.info("Decoding base64 content")
                    try:
                        wav_bytes = base64.b64decode(file['content'])
                        logger.info(f"Successfully decoded base64 content, size: {len(wav_bytes)} bytes")
                    except Exception as decode_err:
                        error_msg = f"Invalid base64 content: {str(decode_err)}"
                        logger.error(error_msg)
                        return {"content": [{"type": "error", "message": error_msg}]}
                else:
                    # This case might not be expected anymore if client always sends base64
                    logger.warning("Received raw bytes content directly, expected base64 string.")
                    wav_bytes = file['content']

                logger.info(f"Writing {len(wav_bytes)} bytes to temporary file: {temp_file_path}")
                temp_file.write(wav_bytes)
                temp_file.flush()

                logger.info("Preparing multipart form data")
                # Ensure file is opened in binary read mode for httpx
                with open(temp_file_path, 'rb') as f_for_upload:
                    files = {'file': ('voice.wav', f_for_upload, 'audio/wav')}
                    data = {'displayName': displayName}

                    endpoint_url = ENDPOINT_MODEL_ADD_VOICE.format(model=model)
                    logger.info(f"Making API request to: {endpoint_url}")

                    try:
                        resp = await waves_api(endpoint_url, method="POST", files=files, data=data)
                        logger.info(f"API response status: {resp.status_code}")
                        # Handle successful but potentially error-containing JSON responses if necessary
                        # Example: if resp.status_code == 200 and 'error' in resp.json(): ...
                        resp_json = resp.json()
                        logger.info(f"API response: {resp_json}")

                        return {
                            "content": [{
                                "type": "resource",
                                "resource": {
                                    "uri": "waves://create-clone",
                                    "text": json.dumps(resp_json),
                                    "mimeType": "application/json"
                                }
                            }]
                        }
                    # Catch WavesApiError specifically to extract details
                    except WavesApiError as api_err:
                        # Format detailed error message
                        error_msg = f"API Request Failed: Status={api_err.status_code}, Reason={api_err.reason}, Details={api_err.text}"
                        logger.error(error_msg, exc_info=False) # Log concise error message
                        return {"content": [{"type": "error", "message": error_msg}]}
                    except Exception as api_err: # Catch other potential request errors
                        error_msg = f"API request failed unexpectedly: {str(api_err)}"
                        logger.error(error_msg, exc_info=True)
                        return {"content": [{"type": "error", "message": error_msg}]}

            except Exception as e:
                error_msg = f"Error processing file: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return {"content": [{"type": "error", "message": error_msg}]}
            finally:
                try:
                    logger.info(f"Cleaning up temporary file: {temp_file_path}")
                    os.unlink(temp_file_path)
                except Exception as unlink_err:
                    logger.warning(f"Failed to delete temporary file {temp_file_path}: {unlink_err}")

    except Exception as e:
        # Check if it's a WavesApiError bubbled up
        if isinstance(e, WavesApiError):
             error_msg = f"Failed to create clone: Status={e.status_code}, Reason={e.reason}, Details={e.text}"
        else:
            error_msg = f"Failed to create voice clone (unexpected): {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"content": [{"type": "error", "message": error_msg}]}

@mcp.tool()
async def listClones(
    model: str = "lightning-large"
) -> dict:
    """
    Lists the available voice clones for a specified model from the Waves API.

    Args:
        model: The model for which to list clones (e.g., "lightning-large").

    Returns:
        A dictionary in MCP format containing the list of clones or an error message.
    """
    endpoint_url = ENDPOINT_MODEL_GET_CLONES.format(model=model)
    logger.info(f"Listing clones for model: {model} via {endpoint_url}")
    try:
        resp = await waves_api(endpoint_url)
        resp_json = resp.json()
        logger.info(f"Successfully retrieved clones for model {model}")
        return {
            "content": [{
                "type": "resource",
                "resource": {
                    "uri": "waves://clones",
                    "text": json.dumps(resp_json),
                    "mimeType": "application/json"
                }
            }]
        }
    except WavesApiError as e:
        error_msg = f"Failed to list clones: Status={e.status_code}, Reason={e.reason}, Details={e.text}"
        logger.error(error_msg)
        return {"content": [{"type": "error", "message": error_msg}]}
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse listClones response: {e}"
        logger.error(error_msg)
        return {"content": [{"type": "error", "message": error_msg}]}
    except Exception as e:
        error_msg = f"Unexpected error listing clones for model {model}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"content": [{"type": "error", "message": error_msg}]}

@mcp.tool()
async def deleteClone(
    model: str = "lightning-large",
    voiceId: str = ""
) -> dict:
    """
    Deletes a specific voice clone from the Waves API.

    Args:
        model: The model the clone belongs to (e.g., "lightning-large").
        voiceId: The unique identifier of the voice clone to delete.

    Returns:
        A dictionary in MCP format containing the API response or an error message.
    """
    if not voiceId:
        error_msg = "voiceId is required to delete a clone."
        logger.error(error_msg)
        return {"content": [{"type": "error", "message": error_msg}]}

    endpoint_url = ENDPOINT_MODEL_DELETE.format(model=model)
    logger.info(f"Attempting to delete clone {voiceId} for model {model} via {endpoint_url}")
    try:
        resp = await waves_api(
            endpoint_url,
            method="DELETE",
            headers={"Content-Type": "application/json"},
            json_payload={"voiceId": voiceId}
        )
        resp_json = resp.json()
        logger.info(f"Successfully requested deletion for clone {voiceId}")
        return {
            "content": [{
                "type": "resource",
                "resource": {
                    "uri": "waves://delete-clone",
                    "text": json.dumps(resp_json),
                    "mimeType": "application/json"
                }
            }]
        }
    except WavesApiError as e:
        error_msg = f"Failed to delete clone {voiceId}: Status={e.status_code}, Reason={e.reason}, Details={e.text}"
        logger.error(error_msg)
        return {"content": [{"type": "error", "message": error_msg}]}
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse deleteClone response for {voiceId}: {e}"
        logger.error(error_msg)
        return {"content": [{"type": "error", "message": error_msg}]}
    except Exception as e:
        error_msg = f"Unexpected error deleting clone {voiceId} for model {model}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"content": [{"type": "error", "message": error_msg}]}

@mcp.tool()
async def listVoices() -> dict:
    """
    Lists all available pre-set voices from the Waves API.

    Returns:
        A dictionary in MCP format containing the list of voices or an error message.
    """
    logger.info(f"Listing available voices via {ENDPOINT_GET_VOICES}")
    try:
        resp = await waves_api(ENDPOINT_GET_VOICES)
        data = resp.json()
        logger.info("Successfully retrieved available voices.")
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
    except WavesApiError as e:
        error_msg = f"Failed to list voices: Status={e.status_code}, Reason={e.reason}, Details={e.text}"
        logger.error(error_msg)
        return {"content": [{"type": "error", "message": error_msg}]}
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse listVoices response: {e}"
        logger.error(error_msg)
        return {"content": [{"type": "error", "message": error_msg}]}
    except Exception as e:
        error_msg = f"Unexpected error listing voices: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"content": [{"type": "error", "message": error_msg}]}

@mcp.tool()
async def ttsToWav(
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
    Generate TTS audio and save it as a WAV file in a configurable output directory,
    returning the file URI for LLM playback. Follows MCP resource conventions.
    Adds duration, timestamp, and file size to metadata.

    If output_dir is provided, saves the file there; otherwise, uses a temp directory
    in the project folder (./tmp) or MCP_BASE_PATH.

    Args:
        text: The text to synthesize.
        voiceId: The ID of the voice to use.
        model: The TTS model to use ("lightning" or "lightning-large").
        language: Language code (required for lightning-large).
        outputFormat: The desired output format (e.g., "wav").
        add_wav_header: Whether to add a WAV header to the output.
        sample_rate: The sample rate for the audio.
        speed: Playback speed factor.
        consistency: Voice consistency level.
        similarity: Voice similarity level.
        enhancement: Enhancement level.
        output_dir: Optional directory to save the output file.

    Returns:
        A dictionary in MCP format containing the audio resource details or an error message.
    """
    # import uuid - Already imported globally
    # import tempfile # tempfile not used
    # import os - Already imported globally

    logger.info(f"Starting ttsToWav for voiceId: {voiceId}, model: {model}")
    try:
        # Refactored payload creation
        base_payload = {
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

        # Select endpoint based on model
        if model == "lightning":
            endpoint_url = ENDPOINT_LIGHTNING_GET_SPEECH
            payload = base_payload
        elif model == "lightning-large":
            endpoint_url = ENDPOINT_LIGHTNING_LARGE_GET_SPEECH
            payload = base_payload.copy()
            payload["language"] = language
            if not language:
                error_msg = "Language parameter is required for the lightning-large model."
                logger.error(error_msg)
                return {"content": [{"type": "error", "message": error_msg}]}
        else:
            # Use logger, return MCP error format instead of raising RuntimeError directly in tool
            error_msg = f"Unsupported model requested in ttsToWav: {model}"
            logger.error(error_msg)
            return {"content": [{"type": "error", "message": error_msg}]}

        logger.debug(f"TTS Payload: {payload}")
        resp = await waves_api(
            endpoint_url,
            method="POST",
            headers={"Content-Type": "application/json"},
            json_payload=payload
        )

        # No need to check resp.is_success here, waves_api raises WavesApiError on failure

        # Determine output directory
        if output_dir:
            save_dir = output_dir
        else:
            # Use ./tmp in the project folder by default
            save_dir = MCP_BASE_PATH if MCP_BASE_PATH != "/tmp" else os.path.abspath(os.path.join(os.path.dirname(__file__), "tmp"))

        # Ensure directory exists (handle potential race conditions if needed, though unlikely here)
        try:
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
                logger.info(f"Created output directory: {save_dir}")
        except OSError as e:
            error_msg = f"Failed to create output directory {save_dir}: {e}"
            logger.error(error_msg)
            return {"content": [{"type": "error", "message": error_msg}]}

        filename = f"tts_{uuid.uuid4().hex}.wav"
        file_path = os.path.join(save_dir, filename)

        # Get audio bytes (waves_api ensures success or raises error)
        audio_bytes = await resp.aread() # Read bytes async

        logger.info(f"Writing {len(audio_bytes)} bytes to {file_path}")
        try:
            with open(file_path, "wb") as f:
                f.write(audio_bytes)
        except IOError as e:
            # Use logger, return MCP error format
            error_msg = f"Failed to write audio file {file_path}: {e}"
            logger.error(error_msg)
            return {"content": [{"type": "error", "message": error_msg}]}

        # Validate file was written
        if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
             # Use logger, return MCP error format
            error_msg = f"Failed to write audio file or file is empty: {file_path}"
            logger.error(error_msg)
            # Attempt cleanup even if write failed
            try:
                if os.path.exists(file_path): os.unlink(file_path)
            except OSError: pass # Ignore cleanup error
            return {"content": [{"type": "error", "message": error_msg}]}


        # Validate WAV header (RIFF) - crucial check
        try:
            with open(file_path, "rb") as f:
                header = f.read(4)
            if header != b'RIFF':
                 # Use logger, return MCP error format
                error_msg = f"Invalid WAV file written (missing RIFF header): {file_path}"
                logger.error(error_msg)
                try: os.unlink(file_path) # Cleanup invalid file
                except OSError: pass
                return {"content": [{"type": "error", "message": error_msg}]}
        except IOError as e:
            error_msg = f"Could not read back WAV file for validation: {file_path}, Error: {e}"
            logger.error(error_msg)
            # File might exist but be unreadable, attempt cleanup
            try:
                if os.path.exists(file_path): os.unlink(file_path)
            except OSError: pass
            return {"content": [{"type": "error", "message": error_msg}]}


        # Get duration (if WAV)
        duration = None
        try:
            with wave.open(file_path, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0: # Avoid division by zero
                    duration = frames / float(rate)
                else:
                    logger.warning(f"Invalid frame rate (0) in WAV file: {file_path}")
        except wave.Error as e:
            # Log warning but proceed, duration is optional metadata
            logger.warning(f"Could not read WAV duration from {file_path}: {e}")
        except Exception as e:
            # Catch other potential errors during wave processing
            logger.warning(f"Unexpected error getting WAV duration from {file_path}: {e}")


        file_stat = os.stat(file_path)
        logger.info(f"Successfully generated TTS file: {file_path}, Size: {file_stat.st_size}, Duration: {duration}")
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
    except WavesApiError as e:
        error_msg = f"TTS generation failed (API Error): Status={e.status_code}, Reason={e.reason}, Details={e.text}"
        logger.error(error_msg)
        return {"content": [{"type": "error", "message": error_msg}]}
    except Exception as e:
        # Catch any other unexpected errors during the process
        error_msg = f"Unexpected error during ttsToWav execution: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"content": [{"type": "error", "message": error_msg}]}


# NOTE: The playWavFile tool is deprecated and will be removed. For MCP-compliance and client-side playback, only return file resources (URIs) via ttsToWav. Clients/LLMs are responsible for playback. - REMOVED

# Create the SSE app from FastMCP
app = mcp.sse_app()

# Optional: Add a status endpoint for "/"
@app.route("/")
async def homepage(request):
    logger.info("Homepage '/' accessed.")
    return PlainTextResponse("MCP SSE server running. Use /sse for protocol.")

# Ensure the HTTP client is closed gracefully on shutdown
# Starlette provides lifespan events for this
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down HTTP client...")
    await http_client.aclose()

if __name__ == "__main__":
    print("Starting MCP server with SSE transport on port 8000...")
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, log_level="info")
