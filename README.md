# AI Kid Bot

A real-time voice-chat AI robot for kids, featuring conversational AI, speech-to-text, and text-to-speech capabilities. Designed for educational and fun interactions, supporting multiple languages and customizable voices.

**Repository Description:** AI-powered conversational robot for children with real-time voice interaction, using STT/TTS and LLMs. Built with Python backend and web-based PWA frontend for cross-device compatibility.

## Features

- **Real-Time Voice Chat:** Continuous speech recognition and synthesis for natural conversations.
- **Educational Content:** Focuses on science, nature, space, dinosaurs, programming, and more.
- **Multi-Provider LLM Support:** Integrates with Groq, Ollama, and Gemini APIs.
- **Customizable Voices:** Supports various TTS voices via browser or server-side Piper.
- **Web-Based Interface:** Progressive Web App (PWA) for mobile and desktop.
- **Modular Architecture:** Separate STT, TTS, and LLM components for flexibility.
- **Low-Resource Mode:** Optimized for CPU-only systems with tiny models.

## Architecture

The application follows a client-server architecture:

- **Frontend (PWA):** HTML5 Canvas-based robot face, WebSocket client for real-time communication. Built with vanilla JavaScript, CSS, and PWA manifest for offline/installable experience.
- **Backend:** Python FastAPI server with WebSocket support.
  - **STT:** Whisper (OpenAI) for speech-to-text.
  - **TTS:** Web Speech API (browser) or Piper (server-side) for text-to-speech.
  - **LLM:** Groq API (default), Ollama for local models, or Gemini API.
  - **Audio Processing:** Real-time audio streaming via WebSockets.
- **Deployment:** Runs locally or in containers (Docker). Supports GPU acceleration where available.

High-level flow: User speaks → STT transcribes → LLM generates response → TTS synthesizes → Audio played back.

## Setup

### Prerequisites
- Python 3.10+
- API keys for LLM providers (Groq recommended for speed)
- Microphone and speakers

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-kid-bot.git
cd ai-kid-bot
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env-example .env
# Edit .env with your API keys (GROQ_API_KEY, GEMINI_API_KEY if needed)
```

5. Download models (optional, auto-downloads on first run):
```bash
python -c "import whisper; whisper.load_model('tiny')"
```

### Configuration

Edit `config.json` to customize:
- LLM provider and model
- STT/TTS providers
- Voice settings (rate, pitch, volume)

## Usage

### Running Locally

Start the server:
```bash
python run.py
```

Access at `http://localhost:8000` or `http://127.0.0.1:8000`.

For low-resource systems:
```bash
python run.py --whisper tiny --no-pull
```

### Mobile/Remote Access

- **PWA:** Install as app on mobile for fullscreen experience.
- **Remote:** Use `--tunnel` flag for ngrok tunneling and QR code access.
- **iPad:** Connect via `chipbot.local` (Bonjour) or Bluetooth pairing.

### Docker

Build and run:
```bash
docker build -t ai-kid-bot .
docker run --net=host -v $(pwd):/data ai-kid-bot
```

For GPU support:
```bash
docker run --gpus all --net=host -v $(pwd):/data ai-kid-bot
```

## Development

- **Backend:** `run.py` (FastAPI), `brain/` (LLM logic), `speech/` (TTS), `transport/` (WebSockets).
- **Frontend:** `avatar/` (HTML/JS/CSS).
- **Models:** Stored in `models/` (Whisper, Piper voices).

## Contributing

Contributions welcome! Please open issues for bugs or feature requests.

## License

MIT License - see LICENSE file.

