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
