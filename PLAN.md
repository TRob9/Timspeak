# Timspeak - AI-Powered Dictation Device
## Project Plan

### Overview
Timspeak is a cross-platform dictation system that captures voice input, cleans it using AI, and delivers the result to the user's clipboard. The system consists of three platform-specific proof-of-concepts (Mac, Windows, Raspberry Pi) with a swappable architecture for both speech-to-text engines and LLM providers.

---

## Architecture Philosophy: Hexagonal Design (Ports & Adapters)

We'll use a **semi-hexagonal architecture** to ensure maximum flexibility:

```
┌─────────────────────────────────────────────┐
│           Application Core                  │
│  (Platform-agnostic business logic)         │
│                                              │
│  - Audio capture management                 │
│  - Dictation workflow orchestration         │
│  - Text processing pipeline                 │
└─────────────────┬───────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
    ┌───▼────┐         ┌───▼────┐
    │ Ports  │         │ Ports  │
    │ (STT)  │         │ (LLM)  │
    └───┬────┘         └───┬────┘
        │                   │
  ┌─────┴──────┐      ┌────┴─────┐
  │  Adapters  │      │ Adapters │
  └────────────┘      └──────────┘
   - Whisper Local      - Claude API
   - Whisper Cloud      - OpenAI GPT
   - Google Cloud       - Ollama Local
                        - (via LiteLLM)
```

**Benefits:**
- Swap STT engines without changing core logic
- Swap LLM providers through unified interface
- Easy testing with mock adapters
- Platform-specific implementations isolated

---

## Technology Stack

### Shared Dependencies
- **LLM Abstraction:** LiteLLM (unified interface for 100+ LLM providers)
- **Speech-to-Text Options:**
  - OpenAI Whisper (local) via `whisper` Python package
  - OpenAI Whisper (cloud) via OpenAI API
  - Google Cloud Speech-to-Text API
- **Configuration:** YAML/JSON config files for API keys and preferences

### Platform-Specific Technologies

#### Mac
- **Language:** Python
- **Frontend:** Simple HTML/CSS/JS served via Flask
- **STT:** macOS Speech Framework (native) + Whisper + Google Cloud
- **Clipboard:** `pyperclip` or `subprocess` with `pbcopy`
- **Audio:** `sounddevice` + `numpy`

#### Windows
- **Language:** Python
- **Frontend:** Simple HTML/CSS/JS served via Flask
- **STT:** Windows Speech Recognition (native) + Whisper + Google Cloud
- **Clipboard:** `pyperclip` or `win32clipboard`
- **Audio:** `sounddevice` + `numpy`

#### Raspberry Pi
- **Language:** Python
- **Hardware:** 2 physical buttons via GPIO
- **GPIO Library:** `gpiozero` (modern, maintained, built-in debouncing)
- **STT:** Whisper (local/cloud) + Google Cloud
- **USB HID:** `adafruit-circuitpython-hid` or custom HID gadget mode
- **Audio:** `sounddevice` + `numpy` or `pyaudio`
- **Display (optional):** Small OLED for status feedback

---

## Project Structure

```
Timspeak/
├── PLAN.md                          # This file
├── README.md                        # User-facing documentation
├── .gitignore                       # Standard Python + secrets
├── shared/                          # Shared utilities (future refactor)
│   ├── llm_interface.py            # LiteLLM wrapper
│   └── stt_interface.py            # STT adapter interface
│
├── Mac/
│   ├── START_TIMSPEAK.command      # One-click launcher (double-click)
│   ├── requirements.txt            # Python dependencies
│   ├── config.yaml.example         # Configuration template
│   ├── main.py                     # Entry point
│   ├── core/
│   │   ├── audio_capture.py       # Audio recording logic
│   │   ├── stt_adapter.py         # STT port implementation
│   │   └── llm_adapter.py         # LLM port implementation
│   ├── adapters/
│   │   ├── stt/
│   │   │   ├── whisper_local.py    # openai-whisper
│   │   │   ├── whisper_fast.py     # faster-whisper
│   │   │   ├── whisper_cloud.py    # OpenAI API
│   │   │   ├── google_cloud.py
│   │   │   └── macos_speech.py     # Native macOS Speech Framework
│   │   └── llm/
│   │       └── litellm_adapter.py  # Unified LLM interface
│   └── web/
│       ├── app.py                  # Flask server
│       ├── templates/
│       │   └── index.html
│       └── static/
│           ├── style.css
│           └── script.js
│
├── Windows/
│   ├── START_TIMSPEAK.bat         # One-click launcher
│   ├── requirements.txt
│   ├── config.yaml.example
│   ├── main.py
│   ├── core/
│   │   ├── audio_capture.py
│   │   ├── stt_adapter.py
│   │   └── llm_adapter.py
│   ├── adapters/
│   │   ├── stt/
│   │   │   ├── whisper_local.py    # openai-whisper
│   │   │   ├── whisper_fast.py     # faster-whisper
│   │   │   ├── whisper_cloud.py    # OpenAI API
│   │   │   ├── google_cloud.py
│   │   │   └── windows_speech.py   # Native Windows Speech
│   │   └── llm/
│   │       └── litellm_adapter.py
│   └── web/
│       ├── app.py
│       ├── templates/
│       │   └── index.html
│       └── static/
│           ├── style.css
│           └── script.js
│
└── RaspberryPi/
    ├── requirements.txt
    ├── config.yaml.example
    ├── main.py                     # Entry point
    ├── timspeak.service            # Systemd service for auto-start
    ├── hardware/
    │   ├── buttons.py              # GPIO button handling (gpiozero)
    │   └── usb_hid.py              # USB HID keyboard emulation
    ├── core/
    │   ├── audio_capture.py
    │   ├── stt_adapter.py
    │   └── llm_adapter.py
    ├── adapters/
    │   ├── stt/
    │   │   ├── whisper_local.py    # openai-whisper
    │   │   ├── whisper_fast.py     # faster-whisper
    │   │   ├── whisper_cloud.py    # OpenAI API
    │   │   └── google_cloud.py
    │   └── llm/
    │       └── litellm_adapter.py
    └── setup/
        ├── install.sh              # Dependency installation + systemd setup
        └── usb_hid_setup.sh        # Configure Pi as USB HID device
```

---

## Feature Specifications

### Raspberry Pi Button Modes

#### Listen Button
Two toggleable modes:

1. **Hold-to-Record Mode (Default)**
   - Press and hold: Start recording
   - Release: Stop recording → Send to STT → Clean with LLM → Save to internal clipboard
   - LED indicator: Solid while recording

2. **Toggle Mode**
   - First press: Start recording (LED blinks)
   - Second press: Stop recording → Process → Save to clipboard
   - Useful for long dictations

**Mode Toggle:** Hold Listen button for 3 seconds to switch modes (LED blinks pattern to confirm)

#### Send Button
- Triggers USB HID keyboard emulation
- Types the cleaned text from internal clipboard into the connected computer
- Works regardless of which application has focus
- LED blinks during typing

### Mac/Windows Web Interface

**Localhost server (port 5000)** displays:

```
┌─────────────────────────────────────────┐
│         Timspeak Dashboard              │
├─────────────────────────────────────────┤
│                                         │
│  [●] Record    [○] Stop                 │
│                                         │
│  STT Engine:  [Whisper Local ▼]        │
│  LLM Provider: [Claude Sonnet ▼]       │
│                                         │
├─────────────────────────────────────────┤
│  Original Dictation:                    │
│  ┌───────────────────────────────────┐ │
│  │ um so i was thinking that we      │ │
│  │ should probably uh you know go    │ │
│  │ ahead and do that thing           │ │
│  └───────────────────────────────────┘ │
├─────────────────────────────────────────┤
│  Cleaned Output:                        │
│  ┌───────────────────────────────────┐ │
│  │ I was thinking that we should     │ │
│  │ go ahead and do that.             │ │
│  └───────────────────────────────────┘ │
│                                         │
│  [Copy to Clipboard]                    │
└─────────────────────────────────────────┘
```

**Features:**
- Real-time status updates (WebSocket or polling)
- Dropdown to select STT engine
- Dropdown to select LLM provider
- Side-by-side comparison of original vs. cleaned text
- Copy button for cleaned output
- Audio level visualization (optional stretch goal)

---

## Implementation Plan

### Phase 1: Windows Proof of Concept (BUILD FIRST)
**Deliverables:**
- [ ] Project scaffolding (folders, config structure)
- [ ] Audio capture using `sounddevice`
- [ ] All STT adapters (whisper local, faster-whisper, whisper cloud, Google Cloud, Windows Speech)
- [ ] LiteLLM adapter with multi-provider support
- [ ] Flask web interface with dropdowns
- [ ] Clipboard integration (pyperclip or win32clipboard)
- [ ] One-click `START_TIMSPEAK.bat` launcher
- [ ] Full workflow: Record → Transcribe → Clean → Display → Copy

### Phase 2: Mac Proof of Concept
**Deliverables:**
- [ ] Port Windows implementation to Mac
- [ ] macOS Speech Framework adapter
- [ ] macOS clipboard handling (pbcopy)
- [ ] One-click `START_TIMSPEAK.command` launcher
- [ ] Flask web interface (matching Windows)
- [ ] Full workflow testing on macOS

### Phase 3: Raspberry Pi Proof of Concept
**Deliverables:**
- [ ] GPIO button setup (gpiozero)
- [ ] Button mode logic (hold vs. toggle)
- [ ] Audio capture on Pi (test performance)
- [ ] USB HID gadget mode configuration
- [ ] Keyboard emulation implementation
- [ ] LED status indicators
- [ ] Systemd service for auto-start on boot
- [ ] Installation script (`setup/install.sh`)
- [ ] Full workflow: Button → Record → Process → HID Type

### Phase 4: Polish & Documentation
**Deliverables:**
- [ ] Comprehensive README with setup instructions
- [ ] API key configuration guide
- [ ] Raspberry Pi hardware assembly guide
- [ ] Troubleshooting section
- [ ] Example config files
- [ ] Cross-platform testing and bug fixes

---

## Configuration File Structure

**Example `config.yaml`:**

```yaml
# Timspeak Configuration

stt:
  default: whisper_fast
  providers:
    whisper_local:
      # Official openai-whisper (slower but original)
      model_size: base  # tiny, base, small, medium, large
      language: en
    whisper_fast:
      # faster-whisper (4x faster, less memory)
      model_size: base  # tiny, base, small, medium, large
      language: en
      device: cpu  # or cuda
      compute_type: int8  # int8, float16, float32
    whisper_cloud:
      # OpenAI API (cloud-based)
      api_key: ${OPENAI_API_KEY}
      model: whisper-1
    google_cloud:
      api_key: ${GOOGLE_CLOUD_API_KEY}
      language_code: en-US
    windows_speech:
      # Windows Speech Recognition (Windows only)
      enabled: true
    macos_speech:
      # macOS Speech Framework (Mac only)
      enabled: true

llm:
  default: claude
  providers:
    claude:
      model: claude-sonnet-4-5-20250929
      api_key: ${ANTHROPIC_API_KEY}
      max_tokens: 1000
    openai:
      model: gpt-4
      api_key: ${OPENAI_API_KEY}
    ollama:
      model: llama2
      base_url: http://localhost:11434

audio:
  sample_rate: 16000
  channels: 1
  chunk_size: 1024

# Raspberry Pi specific
raspberry_pi:
  listen_button_gpio: 17
  send_button_gpio: 27
  led_gpio: 22
  default_mode: hold_to_record  # or toggle
```

---

## LLM Cleaning Prompt

The LLM will receive this system prompt for cleaning dictation:

```
You are a dictation cleaning assistant. Your job is to:

1. Remove filler words (um, uh, like, you know)
2. Fix grammatical errors
3. Add appropriate punctuation
4. Preserve the original meaning and tone
5. Keep technical terms and proper nouns intact
6. Format as natural, readable text

Return ONLY the cleaned text without any explanations or commentary.

Example:
Input: "um so i was thinking that we should probably uh you know go ahead and do that thing"
Output: "I was thinking that we should go ahead and do that."
```

---

## Raspberry Pi USB HID Setup

The Pi will be configured as a USB HID gadget device using `dwc2` overlay:

1. Enable USB gadget mode in `/boot/config.txt`
2. Load HID kernel modules
3. Configure HID descriptor for keyboard
4. Python script emulates keyboard input

**Alternative:** Use CircuitPython HID library if simpler

---

## GPIO Library Decision Rationale

**Chosen:** `gpiozero`

**Critical Analysis:**

| Criteria | gpiozero | RPi.GPIO | pigpio |
|----------|----------|----------|--------|
| Maintenance | ✅ Active (Raspberry Pi Foundation) | ⚠️ Deprecated | ✅ Active (lgpio fork) |
| Ease of Use | ✅ High-level, intuitive | ⚠️ Medium | ❌ Complex (daemon) |
| Button Debouncing | ✅ Built-in | ❌ Manual | ✅ Built-in |
| Event Detection | ✅ Simple callbacks | ⚠️ Threading required | ✅ Callbacks |
| Our Use Case | ✅ Perfect fit | ⚠️ Overkill | ⚠️ Overkill |

**Conclusion:** gpiozero is the modern, maintained choice with exactly the features we need for simple button detection.

---

## Testing Strategy

### Unit Tests
- STT adapter mocking
- LLM adapter mocking
- Audio buffer handling

### Integration Tests
- Full workflow from audio → cleaned text
- Config file parsing
- Provider switching

### Manual Testing
- Button press timing (Pi)
- USB HID typing accuracy (Pi)
- Web interface responsiveness (Mac/Windows)
- Cross-platform clipboard behavior

---

## Security Considerations

1. **API Keys:** Never commit keys to git; use environment variables or `.env` files
2. **Local Network:** Mac/Windows apps only bind to `localhost` (no external access)
3. **Audio Privacy:** No audio sent to cloud unless user selects cloud STT
4. **Pi Physical Access:** No authentication needed (physical device security)

---

## Future Enhancements (Out of Scope for POC)

- [ ] Mobile app for remote triggering
- [ ] Multi-language support
- [ ] Custom vocabulary/training
- [ ] Voice commands for formatting (e.g., "new paragraph")
- [ ] Bluetooth connectivity for Pi
- [ ] Battery power for Pi
- [ ] Streaming transcription (live updates)
- [ ] Speaker diarization (multi-person dictation)

---

## Success Criteria

**Mac/Windows POC:**
✅ User can record audio via web interface
✅ Transcription appears in "Original" box
✅ Cleaned text appears in "Cleaned" box
✅ Text is copied to system clipboard
✅ User can switch STT and LLM providers via dropdowns

**Raspberry Pi POC:**
✅ Listen button records audio (both modes work)
✅ Send button types cleaned text via USB HID
✅ LED provides status feedback
✅ Works with any connected computer (no software install required)

---

## Timeline Estimate

- **Phase 1:** 1 day
- **Phase 2:** 2-3 days
- **Phase 3:** 1 day (port from Mac)
- **Phase 4:** 3-4 days (hardware complexity)
- **Phase 5:** 2 days
- **Phase 6:** 1 day

**Total:** ~10-12 days of development

---

## Final Design Decisions

### Critical Constraints
1. **Code Architecture:** Separate POCs - NO shared library. Each platform is fully independent.
2. **Target Hardware:** Raspberry Pi 4 (adequate performance for local Whisper)
3. **Whisper Modularity:** Support BOTH `openai-whisper` AND `faster-whisper` as toggleable options
4. **Scope:** Full implementation - all STT engines including native OS APIs
5. **Build Order:** Windows → Mac → Raspberry Pi
6. **Startup:**
   - Windows: One-click `.bat` executable
   - Mac: One-click `.command` or `.app` launcher
   - Raspberry Pi: Auto-start on boot via systemd service

### STT Engine Roster (All Platforms)
- **openai-whisper** (local) - Official implementation
- **faster-whisper** (local) - 4x faster variant
- **Whisper API** (cloud) - OpenAI hosted
- **Google Cloud Speech-to-Text** (cloud)
- **Windows Speech Recognition** (Windows only)
- **macOS Speech Framework** (Mac only)

### Modularity Philosophy
Each adapter is a standalone module with identical interface. User selects via config dropdown. NO HARDCODED DEPENDENCIES - if Whisper isn't installed, that option is grayed out in UI.

---

## Questions Resolved

1. **Repo Name:** Timspeak ✅
2. **STT Engine:** Toggleable between ALL variants (Whisper local/fast/cloud, Google Cloud, native) ✅
3. **GPIO Library:** gpiozero (critically evaluated) ✅
4. **Pi Clipboard:** USB HID device ✅
5. **LLM Framework:** LiteLLM (supports all major providers) ✅
6. **Code Sharing:** Separate POCs with independent codebases ✅
7. **Pi Model:** Raspberry Pi 4 ✅
8. **Build Order:** Windows first, then Mac, then Pi ✅

---

## Next Steps

1. Create GitHub repository under TRob9/Timspeak
2. Push initial structure and this PLAN.md
3. Begin Phase 1 implementation
4. Iterate with user feedback

---

**Author:** Claude (Sonnet 4.5)
**Date:** 2025-11-05
**Version:** 1.0
