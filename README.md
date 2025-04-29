<!-- PROJECT LOGO -->
<p align="center">
  <img src="https://waves.smallest.ai/favicon.ico" alt="Waves Logo" width="80" height="80">
</p>

<h1 align="center">Smallest AI MCP Server</h1>

<p align="center">
  <b>Production-grade ModelContextProtocol (MCP) server for the <a href="https://waves.smallest.ai/">Waves</a> Text-to-Speech and Voice Cloning platform.</b><br>
  <i>Fast, portable, and ready for real-world AI voice workflows.</i>
  <br><br>
  <a href="#features"><img src="https://img.shields.io/badge/Features-Fast%20%26%20Accurate-blue?style=flat-square"></a>
  <a href="#docker-usage"><img src="https://img.shields.io/badge/Docker-Ready-green?style=flat-square"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square"></a>
  <a href="https://github.com/Akshay-Sisodia/smallest-ai-mcp/stargazers"><img src="https://img.shields.io/github/stars/Akshay-Sisodia/smallest-ai-mcp?style=flat-square"></a>
</p>

---

## 🚀 Overview

Smallest AI MCP Server provides a seamless bridge between the powerful <a href="https://waves.smallest.ai/">Waves</a> TTS/Voice Cloning API and any MCP-compatible LLM or agent. It is designed for speed, security, and ease of deployment.

---

## ✨ Features

- 🎤 <b>List and preview voices</b> — Instantly fetch all available voices from Waves.
- 🗣️ <b>Synthesize speech</b> — Convert text to high-quality WAV audio files.
- 👤 <b>Clone voices</b> — Create instant/professional voice clones.
- 🗂️ <b>Manage clones</b> — List and delete your cloned voices.

All features are implemented as MCP tools, with no placeholders or stubs.

---

## ⚡ Quickstart

```bash
# 1. Clone the repo
$ git clone https://github.com/Akshay-Sisodia/smallest-ai-mcp.git
$ cd smallest-ai-mcp

# 2. Install dependencies
$ pip install -r requirements.txt

# 3. Configure your API key
$ cp .env.example .env
# Edit .env and add your real WAVES_API_KEY

# 4. Start the server
$ python server.py
```

---

## 🐳 Docker Usage

```bash
# Build the Docker image
$ docker build -t smallest-ai-mcp .

# Run the container
$ docker run -p 8000:8000 \
    -e WAVES_API_KEY=your_waves_api_key \
    smallest-ai-mcp
```

---

## 🛠️ Tech Stack

- <b>Python 3.11+</b>
- <b>Starlette</b>, <b>requests</b>, <b>httpx</b>
- <a href="https://github.com/modelcontextprotocol/mcp-sdk">modelcontextprotocol/mcp-sdk</a>

---

## 🏗️ Production & Deployment

- <b>Environment:</b> Copy <code>.env.example</code> to <code>.env</code> and add your API key. <b>Never</b> commit secrets to git.
- <b>Dependencies:</b> Install with <code>pip install -r requirements.txt</code> (Python 3.11+).
- <b>Docker:</b> Use the provided Dockerfile for containerization.
- <b>Security:</b> API keys are required at startup and never exposed.
- <b>License:</b> MIT (see <a href="LICENSE">LICENSE</a>).

---

## 🤝 Contributing

Pull requests and issues are welcome! Please open an issue to discuss major changes.

---

## 👤 Maintainer

- Akshay Sisodia ([GitHub](https://github.com/Akshay-Sisodia))

---

## 📄 License

MIT

# Groq MCP Client

A Streamlit application that connects to an MCP (Model Context Protocol) server and uses Groq's LLM API for chat conversations with tool execution capabilities.

## Features

- Connect to any MCP server using the official MCP SDK via SSE (Server-Sent Events)
- Asynchronous communication with the MCP server
- Chat interface with streaming responses from Groq
- Tool execution through the MCP server
- Clean and user-friendly UI

## Requirements

- Python 3.8+
- Groq API key
- An MCP server that supports SSE (running on HTTP)
- MCP SDK (automatically installed with requirements.txt)

## Installation

1. Clone this repository
2. Install the dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:

```bash
streamlit run groq_mcp_client.py
```

2. In the Streamlit UI:
   - Enter your Groq API key in the sidebar
   - Enter the URL of your MCP server (default: http://localhost:8000)
   - Click "Connect to MCP Server"
   - Start chatting!

## How it works

1. The application starts and connects to the MCP server using the official MCP SDK via SSE
2. The MCP server provides a list of available tools
3. When you send a message:
   - The message is sent to Groq's API
   - If Groq decides to use a tool, the tool call is executed through the MCP server
   - The tool results are sent back to Groq
   - Groq provides a final response

## Implementation Details

- Uses the official MCP SDK for communication with MCP servers
- Connects via SSE (Server-Sent Events) for HTTP-based servers
- Implements async/await pattern for efficient server communication
- Maintains compatibility with the Streamlit UI framework

## Customization

You can modify the following aspects of the application:

- Change the Groq model by modifying the `model` parameter in the `GroqClient.generate_stream` method
- Customize the UI by modifying the Streamlit components
- Add additional functionality to the MCP client

## License

MIT
