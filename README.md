# Timspeak

AI-powered dictation system that captures your voice, cleans it with LLM, and delivers polished text.

[![GitHub](https://img.shields.io/badge/GitHub-TRob9%2FTimspeak-blue)](https://github.com/TRob9/Timspeak)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Overview

Timspeak is a cross-platform dictation system with **three complete proof-of-concept implementations**:

- **Windows:** Web interface with one-click launcher
- **Mac:** Web interface with native macOS support
- **Raspberry Pi:** Physical button-based device with USB HID keyboard emulation

## Features

### 🎤 Multiple STT Engines (Swappable)
- **OpenAI Whisper (local)** - Official implementation, runs offline
- **Faster Whisper (local)** - 4x faster, recommended for Pi 4
- **OpenAI Whisper API (cloud)** - Hosted Whisper via API
- **Google Cloud Speech (cloud)** - High accuracy cloud STT
- **Windows Speech Recognition** (Windows only)
- **macOS Speech Framework** (macOS only)

### 🤖 Swappable LLMs via LiteLLM
- **Claude (Anthropic)** - Sonnet 4.5
- **OpenAI GPT** - GPT-4 or GPT-3.5
- **Ollama (local)** - Run Llama 2, Mistral, etc. locally
- **100+ providers** supported through LiteLLM

### 🧹 Smart Text Cleaning
- Removes filler words (um, uh, like, you know)
- Fixes grammatical errors
- Adds appropriate punctuation
- Preserves meaning and tone
- Keeps technical terms intact

### Platform-Specific Features

**Windows/Mac:**
- Beautiful web UI at `http://localhost:5000`
- Real-time provider selection dropdowns
- Side-by-side original vs. cleaned text view
- Automatic clipboard copy
- One-click executable launchers

**Raspberry Pi:**
- **Physical buttons** - Listen + Send
- **Dual recording modes** - Hold-to-record or toggle
- **LED status indicator** - Visual feedback
- **USB HID keyboard** - Types text into any computer (no software install!)
- **Auto-start on boot** - Systemd service
- **Mode switching** - Hold Listen button for 3 seconds

## Quick Start

### Windows

1. **Download** or clone the repository
2. **Double-click** `Windows/START_TIMSPEAK.bat`
3. **Configure** your API keys in `config.yaml` (auto-opens)
4. **Access** the web interface at http://localhost:5000

The launcher automatically:
- Creates a Python virtual environment
- Installs all dependencies
- Launches the Flask server

### macOS

1. **Download** or clone the repository
2. **Double-click** `Mac/START_TIMSPEAK.command`
3. **Configure** your API keys in `config.yaml` (auto-opens in TextEdit)
4. **Access** the web interface at http://localhost:5000

First-time setup:
```bash
chmod +x Mac/START_TIMSPEAK.command
```

### Raspberry Pi

**Requirements:**
- Raspberry Pi 4 (recommended) or Pi Zero
- 2 buttons + 1 LED (see wiring below)
- Microphone (USB or HAT)
- MicroSD card with Raspberry Pi OS

**Installation:**
```bash
cd RaspberryPi
bash setup/install.sh
```

The installer will:
1. Install system dependencies
2. Create Python virtual environment
3. Install Python packages
4. Optionally configure USB HID gadget mode
5. Optionally install systemd service for auto-start

**Configuration:**
```bash
nano config.yaml  # Add your API keys
```

**Hardware Wiring (BCM pin numbers):**
```
Listen Button: GPIO 17 → GND
Send Button:   GPIO 27 → GND
LED:           GPIO 22 → 220Ω resistor → LED → GND
```

**Usage:**

*Manual start:*
```bash
python3 main.py
```

*Auto-start (if installed as service):*
```bash
sudo systemctl start timspeak
sudo systemctl enable timspeak  # Start on boot
```

## How It Works

### Windows/Mac Workflow

1. Click **Record** button in web interface
2. Speak into your microphone
3. Click **Stop** when finished
4. **Original** transcription appears in left box
5. **Cleaned** text appears in right box (automatically)
6. Text is **copied to clipboard** automatically
7. Paste anywhere!

### Raspberry Pi Workflow

1. Press **Listen** button (hold or toggle mode)
2. Speak into microphone
3. Release button (hold mode) or press again (toggle mode)
4. LED blinks while processing
5. Press **Send** button when ready
6. Cleaned text **types automatically** into connected computer!

#### Button Modes

**Hold-to-Record (default):**
- Press and hold Listen → Recording (LED solid)
- Release → Processing → Ready
- Simple, intuitive

**Toggle Mode:**
- First press → Start recording (LED blinking)
- Second press → Stop recording → Processing → Ready
- Better for long dictations

**Switch modes:** Hold Listen button for 3 seconds (LED blinks 3x to confirm)

## LLM Setup (Required)

Timspeak **requires an LLM** to clean your dictation. By default, it uses **Ollama** (local, no API key needed).

### Option 1: Ollama (Recommended for Getting Started)

**Runs locally on your computer - no API keys, no internet, no cost!**

#### Windows
```bash
# Download and install from https://ollama.ai/download
# Or use winget:
winget install Ollama.Ollama

# Open a terminal and run:
ollama pull llama2
ollama serve
```

#### macOS
```bash
# Download from https://ollama.ai/download
# Or use Homebrew:
brew install ollama

# Then run:
ollama pull llama2
ollama serve
```

#### Raspberry Pi
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama2
ollama serve
```

**Note:** Ollama runs in the background. Keep it running while using Timspeak!

#### Recommended Models
- **llama2** (default) - Good balance of speed and quality
- **mistral** - Faster, good quality
- **llama2:13b** - Better quality, slower
- **codellama** - Good for technical dictation

To use a different model:
```bash
ollama pull mistral
# Then update config.yaml: model: mistral
```

### Option 2: Cloud LLMs (Better Quality)

For better results, use cloud LLMs:

#### Anthropic Claude (Recommended)
1. Get API key: https://console.anthropic.com
2. Edit `config.yaml`:
```yaml
llm:
  default: claude  # Change from ollama
  providers:
    claude:
      enabled: true
      api_key: YOUR_API_KEY_HERE
```

#### OpenAI GPT
1. Get API key: https://platform.openai.com
2. Edit `config.yaml`:
```yaml
llm:
  default: openai
  providers:
    openai:
      enabled: true
      api_key: YOUR_API_KEY_HERE
```

**Cost Comparison:**
- **Ollama:** Free, runs locally
- **Claude:** ~$0.003 per dictation (high quality)
- **GPT-4:** ~$0.01 per dictation (highest quality)

### Startup Behavior

When you start Timspeak:
- **If Ollama is running:** Everything works automatically!
- **If no LLM available:** You'll see helpful setup instructions
- Timspeak will guide you through the setup process

## Configuration

All platforms use a `config.yaml` file (copy from `config.yaml.example`):

```yaml
# Speech-to-Text
stt:
  default: whisper_fast  # Recommended
  providers:
    whisper_fast:
      enabled: true
      model_size: base    # tiny, base, small, medium, large
      device: cpu
      compute_type: int8  # Best for Pi

    whisper_cloud:
      enabled: false
      api_key: YOUR_OPENAI_API_KEY

    google_cloud:
      enabled: false
      api_key: YOUR_GOOGLE_CLOUD_API_KEY

# LLM for text cleaning (Default: ollama - no API key needed!)
llm:
  default: ollama  # Change to 'claude' or 'openai' after adding API keys
  providers:
    ollama:
      enabled: true
      model: llama2
      base_url: http://localhost:11434

    claude:
      enabled: false
      model: claude-sonnet-4-5-20250929
      api_key: YOUR_ANTHROPIC_API_KEY

    openai:
      enabled: false
      model: gpt-4
      api_key: YOUR_OPENAI_API_KEY

# Raspberry Pi hardware (Pi only)
hardware:
  listen_button_gpio: 17
  send_button_gpio: 27
  led_gpio: 22
  default_mode: hold_to_record
```

## Architecture

### Hexagonal Design (Ports & Adapters)

Each platform implements a **modular architecture** with swappable adapters:

```
Application Core
├── Audio Capture
├── Workflow Orchestration
└── Text Processing

Adapters (Swappable)
├── STT Ports → Whisper, Google Cloud, etc.
└── LLM Ports → Claude, GPT, Ollama, etc.
```

**Benefits:**
- Easy to swap STT/LLM providers
- Add new providers without changing core logic
- Test with mock adapters
- Platform-specific implementations isolated

### Project Structure

```
Timspeak/
├── Windows/
│   ├── START_TIMSPEAK.bat         # One-click launcher
│   ├── core/                      # Core modules
│   ├── adapters/stt/              # STT adapters
│   ├── adapters/llm/              # LLM adapters
│   ├── web/                       # Flask web app
│   ├── requirements.txt
│   └── config.yaml.example
│
├── Mac/
│   ├── START_TIMSPEAK.command     # One-click launcher
│   ├── [Same structure as Windows]
│   └── adapters/stt/macos_speech.py  # macOS-specific
│
├── RaspberryPi/
│   ├── hardware/                  # GPIO + USB HID
│   │   ├── buttons.py            # Button/LED handler
│   │   └── usb_hid.py            # USB keyboard emulation
│   ├── core/                      # Core modules
│   ├── adapters/                  # STT/LLM adapters
│   ├── setup/                     # Installation scripts
│   │   ├── install.sh
│   │   └── usb_hid_setup.sh
│   ├── timspeak.service           # Systemd service
│   ├── main.py
│   └── config.yaml.example
│
├── PLAN.md                        # Detailed architecture
└── README.md                      # This file
```

## Technology Stack

- **Python 3.8+** - All platforms
- **Flask** - Web interface (Windows/Mac)
- **LiteLLM** - Unified LLM access
- **openai-whisper** - Official Whisper
- **faster-whisper** - Optimized Whisper (4x faster)
- **google-cloud-speech** - Google Cloud STT
- **gpiozero** - Raspberry Pi GPIO
- **sounddevice** - Audio capture
- **pyperclip** - Clipboard integration (Windows/Mac)

## Dependencies

### Windows/Mac
```
flask, pyyaml, numpy, scipy, sounddevice, pyperclip
litellm, openai-whisper, faster-whisper, google-cloud-speech
```

### Raspberry Pi
Same as above, plus:
```
gpiozero, lgpio (GPIO backend)
```

System dependencies (Pi):
```bash
sudo apt-get install python3-venv portaudio19-dev
```

## USB HID Setup (Raspberry Pi)

The Pi can act as a **USB keyboard** to type cleaned text into any computer:

1. Run the setup script:
   ```bash
   bash setup/usb_hid_setup.sh
   ```

2. Reboot the Pi

3. Connect Pi to computer via **USB data port**:
   - **Pi 4:** USB-C port
   - **Pi Zero:** Micro USB port (labeled "USB", not "PWR")

4. Pi appears as a USB keyboard (no drivers needed!)

5. Press Send button → Text types automatically

**Testing:**
```bash
echo 'test' | sudo tee /dev/hidg0  # Should type "test"
```

## Performance Notes

### Whisper Model Sizes

| Model  | Speed     | Accuracy | RAM    | Recommended For      |
|--------|-----------|----------|--------|----------------------|
| tiny   | Fastest   | Basic    | ~400MB | Pi Zero, quick tests |
| base   | Fast      | Good     | ~500MB | Pi 4, general use    |
| small  | Moderate  | Better   | ~1GB   | Desktop, high accuracy |
| medium | Slow      | Great    | ~2GB   | Desktop only         |
| large  | Very slow | Best     | ~4GB   | Desktop only         |

**Recommendation:**
- **Pi 4:** Use `faster-whisper` with `base` model
- **Windows/Mac:** Use `faster-whisper` with `small` or `medium` model
- **Cloud option:** OpenAI Whisper API for best speed/accuracy

## Troubleshooting

### Windows/Mac

**"No adapters available"**
- Install dependencies: `pip install -r requirements.txt`
- Check config.yaml for enabled adapters
- Verify API keys are correct

**"Audio device not found"**
- Check microphone is connected
- Run `python -c "import sounddevice; print(sounddevice.query_devices())"`
- Set `device_index` in config.yaml if needed

### Raspberry Pi

**"USB HID device not found"**
- Run `bash setup/usb_hid_setup.sh`
- Reboot after setup
- Check `/dev/hidg0` exists
- Verify USB cable is data-capable (not power-only)

**"GPIO permission denied"**
- Add user to gpio group: `sudo usermod -a -G gpio $USER`
- Reboot

**"Whisper too slow"**
- Use `faster-whisper` instead of `openai-whisper`
- Use `tiny` or `base` model
- Consider cloud STT (Whisper API or Google Cloud)

**Service not starting:**
```bash
sudo journalctl -u timspeak -f  # View logs
sudo systemctl status timspeak  # Check status
```

## Development Status

✅ **Complete** - All three POCs fully implemented and tested

See [PLAN.md](PLAN.md) for detailed architecture and design decisions.

## Future Enhancements

- [ ] Mobile app for remote triggering
- [ ] Multi-language support
- [ ] Custom vocabulary/training
- [ ] Voice commands for formatting
- [ ] Bluetooth connectivity for Pi
- [ ] Battery power for Pi
- [ ] Streaming transcription
- [ ] Speaker diarization

## Contributing

This is a personal proof-of-concept project, but feedback and suggestions are welcome!

## License

MIT License - See LICENSE file

## Author

**Tom** (@TRob9)

Built with [Claude Code](https://claude.com/claude-code)

## Acknowledgments

- OpenAI for Whisper
- Anthropic for Claude
- The faster-whisper team for CTranslate2 optimization
- Raspberry Pi Foundation for gpiozero

---

**Questions?** Check [PLAN.md](PLAN.md) for detailed architecture and implementation notes.
