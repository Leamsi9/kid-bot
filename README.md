# AI Kid Bot

A real-time voice-chat robot for kids using Google Gemini API.

## Setup

1. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add it to `.env` file:
```bash
GEMINI_API_KEY=your_api_key_here
```

3. Install dependencies:
```bash
pip install -r requirements.txt
python models/download.py
```

## Run

```bash
python run.py
```

For low-resource systems, use tiny Whisper model:
```bash
python run.py --whisper tiny
```

Or with Docker:

```bash
docker run --gpus all --net=host -v $HOME/ai-kid-bot:/data ghcr.io/yourrepo/ai-kid-bot:latest
```

## iPad Connection

1. Start the bot on your laptop.
2. On iPad Safari, open http://chipbot.local
3. Talk to Chip the robot!

For Bluetooth: First pair 'ChipBot' in iPad Bluetooth settings.

For remote access: Use --tunnel flag and scan the QR code.
