# Smallest AI MCP Server

This project implements a full-featured ModelContextProtocol (MCP) server for the [Waves](https://waves.smallest.ai/) Text-to-Speech and Voice Cloning platform. It exposes all Waves features as MCP tools and resources, allowing any compatible LLM or agent to:

- List and preview all available voices
- Synthesize speech (sync and streaming)
- Clone voices (instant and professional)
- Manage cloned voices (list, delete)
- Use LiveKit, Plivo, Vonage integrations
- Access project info and best practices

## Features
- **Full Waves API coverage**: No placeholders, all endpoints are real
- **MCP Tools**: `ttsSync`, `ttsStream`, `listVoices`, `createClone`, `listClones`, `deleteClone`, integrations, and more
- **Resources**: `projects`, `bestPractices`, etc.
- **Prompts**: Prebuilt for common TTS and cloning tasks

## Usage
1. Clone this repo
2. Install dependencies: `pip install -r requirements.txt`
3. Set your Waves API key in `.env` as `WAVES_API_KEY=...`
4. Run the server: `python server.py`

## Tech Stack
- Python 3.11, FastAPI/Starlette, httpx, requests
- [modelcontextprotocol/mcp-sdk](https://github.com/modelcontextprotocol/mcp-sdk)

## Production & Deployment

- **Environment:** Copy `.env.example` to `.env` and add your real API key(s). Never commit `.env` to git.
- **Dependencies:** Install via `pip install -r requirements.txt` (Python 3.11+ recommended).
- **Docker:** Use the provided Dockerfile for easy containerization.
- **Testing:** (Add tests for your endpoints and tools as needed.)
- **Security:** Do not expose your API keys or sensitive data. The server checks for required env vars on startup.
- **License:** MIT (see LICENSE file).

## Docker Usage

To build and run this MCP server anywhere with Docker:

```sh
# Build the Docker image
# (from the project root)
docker build -t smallest-ai-mcp .

# Run the server (pass your API keys as env vars)
docker run -p 8000:8000 \
  -e WAVES_API_KEY=your_waves_api_key \
  smallest-ai-mcp
```

- The server will be available at `http://localhost:8000/`.
- Only set the env vars you need (optional integrations).
- You can now use this image on any machine or cloud provider with Docker.

---

## Portable MCP Config Example

To use this server with Cascade or any MCP client, add this to your `mcp_config.json`:

```json
{
  "mcpServers": {
    "waves": {
      "command": "docker",
      "args": [
        "run", "-p", "8000:8000",
        "-e", "WAVES_API_KEY=<YOUR_WAVES_API_KEY>",
        "smallest-ai-mcp"
      ]
    }
  }
}
```

---

## Notes
- The Docker image is fully portable and works on any OS with Docker installed.
- For production, use secrets management for API keys.
- You can publish this image to Docker Hub for even easier sharing.

## Contributing

Pull requests and issues are welcome! Please open an issue to discuss major changes.

## Maintainer
Akshay Sisodia

## License
MIT
