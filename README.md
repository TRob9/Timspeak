# Timspeak

AI-powered dictation device that captures your voice, cleans it with LLM, and delivers polished text to your clipboard.

## Overview

Timspeak is a cross-platform dictation system with three proof-of-concept implementations:

- **Mac:** Web interface for recording and viewing cleaned dictation
- **Windows:** Web interface for recording and viewing cleaned dictation
- **Raspberry Pi:** Physical button-based device that acts as a USB keyboard

## Features

- 🎤 **Multiple STT Engines:** Whisper (local/cloud) or Google Cloud Speech
- 🤖 **Swappable LLMs:** Claude, GPT-4, Ollama, or any provider via LiteLLM
- 🧹 **Smart Cleaning:** Removes filler words, fixes grammar, adds punctuation
- 📋 **Clipboard Ready:** Instantly paste cleaned text anywhere
- 🔌 **USB HID Mode (Pi):** Works with any computer, no software install required

## Project Structure

```
Timspeak/
├── Mac/              # macOS proof of concept
├── Windows/          # Windows proof of concept
├── RaspberryPi/      # Physical device implementation
└── PLAN.md           # Detailed architecture and implementation plan
```

## Quick Start

See `PLAN.md` for detailed architecture and setup instructions.

### Mac/Windows
```bash
cd Mac  # or Windows
pip install -r requirements.txt
cp config.yaml.example config.yaml
# Edit config.yaml with your API keys
python main.py
# Open http://localhost:5000
```

### Raspberry Pi
```bash
cd RaspberryPi
./setup/install.sh
cp config.yaml.example config.yaml
# Edit config.yaml with your API keys
python main.py
```

## Configuration

Copy `config.yaml.example` to `config.yaml` and add your API keys:

```yaml
stt:
  default: whisper_local

llm:
  default: claude
  providers:
    claude:
      api_key: your-key-here
```

## How It Works

1. **Record** your voice (button press on Pi, or web interface on Mac/Windows)
2. **Transcribe** using your chosen STT engine
3. **Clean** with AI to remove filler words and fix grammar
4. **Deliver** to clipboard (or type via USB HID on Pi)

## Raspberry Pi Button Modes

- **Listen Button:** Two modes (hold-to-record or toggle)
- **Send Button:** Types cleaned text via USB keyboard emulation
- **Mode Toggle:** Hold Listen for 3 seconds to switch modes

## Technology Stack

- **Python** for all implementations
- **LiteLLM** for unified LLM access
- **Flask** for Mac/Windows web interface
- **gpiozero** for Raspberry Pi GPIO
- **OpenAI Whisper** or **Google Cloud Speech** for transcription

## Development Status

🚧 **In Active Development** 🚧

See [PLAN.md](PLAN.md) for implementation roadmap.

## License

MIT

## Author

Tom (@TRob9)
Built with Claude Code
