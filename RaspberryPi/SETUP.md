# Timspeak Raspberry Pi Setup Guide

The Pi version runs as a **systemd service on boot** (headless), so it requires manual configuration before enabling the service.

## Prerequisites

- Raspberry Pi 4 (recommended)
- Raspbian/Raspberry Pi OS
- Python 3.8+
- Microphone connected
- Internet connection (for initial setup)

## Initial Setup

### 1. Install System Dependencies

```bash
cd ~/Projects/Timspeak/RaspberryPi

# Install audio dependencies
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-pyaudio

# Install GPIO dependencies (if not already installed)
sudo apt-get install -y python3-gpiozero
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Settings

```bash
# Copy example config
cp config.yaml.example config.yaml

# Edit configuration
nano config.yaml
```

**Important Configuration Notes:**

- **STT (Speech-to-Text):** Pi has NO interactive setup. Choose ONE:
  - `faster-whisper` (recommended for Pi - uncomment in requirements.txt and install)
  - OpenAI Whisper API (requires API key)
  - Google Cloud Speech (requires API key)

- **LLM (Language Model):** Pi has NO interactive setup. Choose ONE:
  - **Cloud LLM** (recommended - faster): Add API key for Claude or OpenAI
  - **Local Ollama** (slower on Pi): Install Ollama and run `ollama pull llama3.2`

Example `config.yaml` for Pi:

```yaml
stt:
  default: whisper_fast
  providers:
    whisper_fast:
      enabled: true
      model_size: base
      language: en
      device: cpu
      compute_type: int8

llm:
  default: claude  # Or openai, or ollama
  providers:
    claude:
      enabled: true
      model: claude-sonnet-4-5-20250929
      api_key: YOUR_API_KEY_HERE
      max_tokens: 1000
      temperature: 0.3
```

### 5. Test Manually

**IMPORTANT:** Test the configuration manually BEFORE enabling the service:

```bash
# Make sure venv is activated
source venv/bin/activate

# Run manually
python main.py
```

If you see errors:
- **"No STT adapters available"** → Check STT config and dependencies
- **"No LLM adapters available"** → Check LLM config and API keys
- **GPIO errors** → Run with `sudo` or add user to `gpio` group

### 6. Configure USB HID (Keyboard Emulation)

```bash
# Run the USB HID setup script
sudo ./setup/usb_hid_setup.sh
```

This enables the Pi to act as a USB keyboard.

### 7. Install Systemd Service

Only after successful manual testing:

```bash
# Copy service file
sudo cp timspeak.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service (starts on boot)
sudo systemctl enable timspeak

# Start service now
sudo systemctl start timspeak

# Check status
sudo systemctl status timspeak
```

### 8. View Logs

```bash
# Real-time logs
sudo journalctl -u timspeak -f

# Recent logs
sudo journalctl -u timspeak -n 50
```

## Troubleshooting

### Service Won't Start

1. Check logs: `sudo journalctl -u timspeak -n 100`
2. Common issues:
   - Missing API keys in config.yaml
   - STT/LLM adapters disabled or misconfigured
   - Python dependencies not installed
   - GPIO permission issues

### Fix: Test manually first!

```bash
# Stop service
sudo systemctl stop timspeak

# Test manually
cd ~/Projects/Timspeak/RaspberryPi
source venv/bin/activate
python main.py
```

### Audio Issues

```bash
# List audio devices
arecord -l

# Test microphone
arecord -d 5 test.wav
aplay test.wav
```

### GPIO Permission Issues

```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Reboot for changes to take effect
sudo reboot
```

## Hardware Setup

### Button Wiring (BCM numbering)

- **Listen Button:** GPIO 17
- **Send Button:** GPIO 27
- **LED:** GPIO 22

See `config.yaml` to change pin assignments.

### Button Modes

1. **Hold-to-Record (default):**
   - Hold Listen button to record
   - Release to process and clean
   - Press Send to type via USB HID

2. **Toggle Mode:**
   - Press Listen to start recording (LED blinks)
   - Press Listen again to stop
   - LED blinks fast while typing

**Switch modes:** Hold Listen button for 3 seconds

## Updating

```bash
# Stop service
sudo systemctl stop timspeak

# Pull latest changes
cd ~/Projects/Timspeak
git pull

# Update dependencies (if needed)
cd RaspberryPi
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl start timspeak
```

## Key Differences from Windows/Mac

| Feature | Windows/Mac | Pi |
|---------|-------------|-----|
| **Setup** | Interactive prompts | Manual config required |
| **Interface** | Web browser | Physical buttons + LED |
| **Output** | Clipboard | USB HID keyboard |
| **Service** | Run manually | Systemd auto-start |
| **LLM Speed** | Fast (local Ollama works well) | Cloud LLM recommended |

## Recommended Configuration for Pi

**For best performance on Pi 4:**

```yaml
stt:
  default: whisper_fast  # faster-whisper is optimized for CPU
  providers:
    whisper_fast:
      enabled: true
      model_size: base     # Good balance of speed/quality
      compute_type: int8   # CPU-optimized

llm:
  default: claude          # Cloud LLM is much faster than local
  providers:
    claude:
      enabled: true
      model: claude-sonnet-4-5-20250929
```

**If you must use local Ollama on Pi:**
- Use smallest model: `llama3.2:latest` (2GB)
- Expect 10-30 second processing time
- Consider Pi 5 for better performance

## Support

For issues, check:
1. Service logs: `sudo journalctl -u timspeak -f`
2. Manual test: `python main.py`
3. GitHub issues: https://github.com/TRob9/Timspeak/issues
