"""
Timspeak Raspberry Pi - Main Application

Physical dictation device with buttons and USB HID output.
"""

import yaml
import os
import sys
import signal
import time

from core.audio_capture import AudioCapture
from adapters.stt.whisper_local import WhisperLocalAdapter
from adapters.stt.whisper_fast import WhisperFastAdapter
from adapters.stt.whisper_cloud import WhisperCloudAdapter
from adapters.stt.google_cloud import GoogleCloudAdapter
from adapters.llm.litellm_adapter import LiteLLMAdapter
from hardware.buttons import ButtonHandler
from hardware.usb_hid import USBKeyboard


class TimspeakPi:
    """Main Timspeak Raspberry Pi application."""

    def __init__(self):
        self.config = None
        self.audio_capture = None
        self.stt_adapter = None
        self.llm_adapter = None
        self.button_handler = None
        self.usb_keyboard = None
        self.clipboard_text = ""  # Internal "clipboard" (last cleaned text)
        self.running = True

    def load_config(self):
        """Load configuration from config.yaml."""
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')

        if not os.path.exists(config_path):
            print("ERROR: config.yaml not found")
            print("Copy config.yaml.example to config.yaml and configure it")
            sys.exit(1)

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def init_adapters(self):
        """Initialize STT and LLM adapters."""
        stt_config = self.config.get('stt', {})
        llm_config = self.config.get('llm', {})
        audio_config = self.config.get('audio', {})
        cleaning_prompt = self.config.get('cleaning_prompt', '')

        # Initialize audio capture
        self.audio_capture = AudioCapture(
            sample_rate=audio_config.get('sample_rate', 16000),
            channels=audio_config.get('channels', 1),
            chunk_size=audio_config.get('chunk_size', 1024),
            device_index=audio_config.get('device_index')
        )
        print("✓ Audio capture initialized")

        # Initialize STT adapter
        stt_provider = stt_config.get('default', 'whisper_fast')
        stt_provider_config = stt_config.get('providers', {}).get(stt_provider, {})

        adapter_classes = {
            'whisper_local': WhisperLocalAdapter,
            'whisper_fast': WhisperFastAdapter,
            'whisper_cloud': WhisperCloudAdapter,
            'google_cloud': GoogleCloudAdapter,
        }

        if stt_provider in adapter_classes:
            adapter_class = adapter_classes[stt_provider]
            self.stt_adapter = adapter_class(stt_provider_config)

            if self.stt_adapter.is_available():
                print(f"✓ STT adapter loaded: {self.stt_adapter.get_name()}")
            else:
                print(f"✗ STT adapter '{stt_provider}' not available")
                sys.exit(1)
        else:
            print(f"✗ Unknown STT provider: {stt_provider}")
            sys.exit(1)

        # Initialize LLM adapter
        llm_provider = llm_config.get('default', 'claude')
        llm_provider_config = llm_config.get('providers', {}).get(llm_provider, {})

        self.llm_adapter = LiteLLMAdapter(llm_provider, llm_provider_config, cleaning_prompt)

        if self.llm_adapter.is_available():
            print(f"✓ LLM adapter loaded: {self.llm_adapter.get_name()}")
        else:
            print(f"✗ LLM adapter '{llm_provider}' not available")
            sys.exit(1)

    def init_hardware(self):
        """Initialize GPIO buttons and USB HID."""
        hardware_config = self.config.get('hardware', {})
        usb_hid_config = self.config.get('usb_hid', {})

        # Initialize button handler
        self.button_handler = ButtonHandler(hardware_config)
        self.button_handler.on_recording_start = self.on_recording_start
        self.button_handler.on_recording_stop = self.on_recording_stop
        self.button_handler.on_send = self.on_send
        self.button_handler.on_mode_change = self.on_mode_change
        print("✓ GPIO buttons initialized")

        # Initialize USB keyboard
        self.usb_keyboard = USBKeyboard(usb_hid_config)
        if self.usb_keyboard.is_available():
            print("✓ USB HID keyboard available")
        else:
            print("⚠ USB HID not available - Send button won't work")
            print("  Run setup/usb_hid_setup.sh to configure")

    def on_recording_start(self):
        """Callback when recording starts."""
        print("[APP] Starting audio recording...")
        self.audio_capture.start_recording()

    def on_recording_stop(self):
        """Callback when recording stops."""
        print("[APP] Stopping audio recording...")
        audio_data = self.audio_capture.stop_recording()

        if len(audio_data) == 0:
            print("[APP] No audio recorded")
            return

        print(f"[APP] Recorded {len(audio_data)} samples")

        # Process in background (blocking is OK for Pi use case)
        try:
            # Transcribe
            print(f"[APP] Transcribing with {self.stt_adapter.get_name()}...")
            original_text = self.stt_adapter.transcribe(audio_data, self.audio_capture.sample_rate)
            print(f"[APP] Transcription: {original_text}")

            # Clean with LLM
            print(f"[APP] Cleaning with {self.llm_adapter.get_name()}...")
            cleaned_text = self.llm_adapter.clean_text(original_text)
            print(f"[APP] Cleaned: {cleaned_text}")

            # Save to internal clipboard
            self.clipboard_text = cleaned_text
            print("[APP] Text ready to send!")

        except Exception as e:
            print(f"[ERROR] Processing failed: {e}")
            self.clipboard_text = ""

    def on_send(self):
        """Callback when Send button is pressed."""
        if not self.clipboard_text:
            print("[APP] No text to send")
            return

        if not self.usb_keyboard.is_available():
            print("[ERROR] USB HID not available")
            return

        print(f"[APP] Sending text via USB HID: {self.clipboard_text[:50]}...")

        try:
            self.usb_keyboard.type_text(self.clipboard_text)
            print("[APP] Text sent successfully!")
        except Exception as e:
            print(f"[ERROR] USB HID send failed: {e}")

    def on_mode_change(self, new_mode: str):
        """Callback when button mode changes."""
        print(f"[APP] Mode changed to: {new_mode}")

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(sig, frame):
            print("\n[APP] Shutting down...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def run(self):
        """Main application loop."""
        print("=" * 60)
        print("Timspeak Raspberry Pi - Physical Dictation Device")
        print("=" * 60)
        print()

        # Load configuration
        print("Loading configuration...")
        self.load_config()

        # Initialize components
        print("\nInitializing adapters...")
        self.init_adapters()

        print("\nInitializing hardware...")
        self.init_hardware()

        print()
        print("=" * 60)
        print("Timspeak is ready!")
        print(f"Button mode: {self.button_handler.current_mode}")
        print("Press Listen button to record, Send button to type")
        print("Hold Listen for 3 seconds to switch modes")
        print("Press Ctrl+C to exit")
        print("=" * 60)
        print()

        # Setup signal handlers
        self.setup_signal_handlers()

        # Main loop (just keep running, buttons handle everything)
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n[APP] Interrupted by user")

        # Cleanup
        print("[APP] Cleaning up...")
        if self.button_handler:
            self.button_handler.cleanup()
        if self.usb_keyboard:
            self.usb_keyboard.cleanup()
        if self.audio_capture:
            self.audio_capture.cleanup()

        print("[APP] Goodbye!")


if __name__ == '__main__':
    app = TimspeakPi()
    app.run()
