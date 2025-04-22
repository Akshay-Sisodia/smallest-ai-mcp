# Smallest AI MCP Server

This project implements a ModelContextProtocol (MCP) server for the [Waves](https://waves.smallest.ai/) Text-to-Speech and Voice Cloning platform. It exposes Waves features as MCP tools, allowing any compatible LLM or agent to:

- List and preview available voices
- Synthesize speech (WAV file output)
- Clone voices (instant and professional)
- Manage cloned voices (list, delete)

## Features
- **Waves API coverage**: No placeholders, all endpoints in code are real
- **MCP Tools**: `ttsToWav`, `listVoices`, `createClone`, `listClones`, `deleteClone`

## Usage
1. Clone this repo: `git clone https://github.com/Akshay-Sisodia/smallest-ai-mcp.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Set your Waves API key in `.env` as `WAVES_API_KEY=...`
4. Run the server: `python server.py`

## Tech Stack
- Python 3.11, Starlette, httpx, requests
- [modelcontextprotocol/mcp-sdk](https://github.com/modelcontextprotocol/mcp-sdk)

## Production & Deployment
- **Environment:** Copy `.env.example` to `.env` and add your real API key(s). Never commit `.env` to git.
- **Dependencies:** Install via `pip install -r requirements.txt` (Python 3.11+ recommended).
- **Docker:** Use the provided Dockerfile for easy containerization.
- **Testing:** (You may wish to add tests for your endpoints and tools.)
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

- For production, use secrets management for API keys.
- You can publish this image to Docker Hub for even easier sharing.

## Contributing
Pull requests and issues are welcome! Please open an issue to discuss major changes.

## Maintainer
Akshay Sisodia ([GitHub](https://github.com/Akshay-Sisodia))

## License
MIT
