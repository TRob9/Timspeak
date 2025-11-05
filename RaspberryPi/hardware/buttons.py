"""
Raspberry Pi GPIO Button Handler

Handles the Listen and Send buttons with gpiozero.
Supports two modes: hold-to-record and toggle.
"""

from gpiozero import Button, LED
import threading
import time


class ButtonHandler:
    """Manages GPIO buttons and LED for Timspeak."""

    MODE_HOLD = "hold_to_record"
    MODE_TOGGLE = "toggle"

    def __init__(self, config: dict):
        """
        Initialize button handler.

        Args:
            config: Hardware configuration dict from config.yaml
        """
        self.config = config

        # GPIO pins
        listen_pin = config.get('listen_button_gpio', 17)
        send_pin = config.get('send_button_gpio', 27)
        led_pin = config.get('led_gpio', 22)

        # Initialize GPIO
        self.listen_button = Button(listen_pin, bounce_time=config.get('debounce_time', 0.05))
        self.send_button = Button(send_pin, bounce_time=config.get('debounce_time', 0.05))
        self.led = LED(led_pin)

        # Mode settings
        self.current_mode = config.get('default_mode', self.MODE_HOLD)
        self.mode_switch_hold_time = config.get('mode_switch_hold_time', 3.0)

        # LED blink settings
        self.led_blink_recording = config.get('led_blink_recording', 0.5)
        self.led_blink_sending = config.get('led_blink_sending', 0.1)

        # State
        self.is_recording = False
        self.mode_switch_timer = None
        self.led_blink_thread = None
        self.stop_blink = False

        # Callbacks (to be set by main application)
        self.on_recording_start = None
        self.on_recording_stop = None
        self.on_send = None
        self.on_mode_change = None

        # Setup button handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup button event handlers."""
        # Listen button
        self.listen_button.when_pressed = self._on_listen_pressed
        self.listen_button.when_released = self._on_listen_released
        self.listen_button.when_held = self._on_listen_held

        # Send button
        self.send_button.when_pressed = self._on_send_pressed

    def _on_listen_pressed(self):
        """Handle Listen button press."""
        print(f"[BUTTON] Listen pressed (mode: {self.current_mode})")

        if self.current_mode == self.MODE_HOLD:
            # Hold-to-record mode: Start recording immediately
            self._start_recording()

            # Start timer for mode switch (if held for 3 seconds)
            self.mode_switch_timer = threading.Timer(
                self.mode_switch_hold_time,
                self._switch_mode
            )
            self.mode_switch_timer.start()

        elif self.current_mode == self.MODE_TOGGLE:
            if not self.is_recording:
                # Toggle mode: First press starts recording
                self._start_recording()
            else:
                # Toggle mode: Second press stops recording
                self._stop_recording()

    def _on_listen_released(self):
        """Handle Listen button release."""
        print("[BUTTON] Listen released")

        # Cancel mode switch timer if released early
        if self.mode_switch_timer:
            self.mode_switch_timer.cancel()
            self.mode_switch_timer = None

        if self.current_mode == self.MODE_HOLD and self.is_recording:
            # Hold-to-record mode: Stop recording on release
            self._stop_recording()

    def _on_listen_held(self):
        """Handle Listen button held (for 3+ seconds)."""
        print("[BUTTON] Listen held - switching mode")
        # Mode switch is handled by timer

    def _on_send_pressed(self):
        """Handle Send button press."""
        print("[BUTTON] Send pressed")

        # Blink LED rapidly while sending
        self._start_led_blink(self.led_blink_sending)

        # Trigger send callback
        if self.on_send:
            try:
                self.on_send()
            except Exception as e:
                print(f"[ERROR] Send callback failed: {e}")

        # Stop LED blink
        self._stop_led_blink()
        self.led.off()

    def _start_recording(self):
        """Start recording."""
        if self.is_recording:
            return

        self.is_recording = True
        print("[STATUS] Recording started")

        # LED indication based on mode
        if self.current_mode == self.MODE_HOLD:
            # Solid LED for hold mode
            self.led.on()
        elif self.current_mode == self.MODE_TOGGLE:
            # Blinking LED for toggle mode
            self._start_led_blink(self.led_blink_recording)

        # Trigger callback
        if self.on_recording_start:
            try:
                self.on_recording_start()
            except Exception as e:
                print(f"[ERROR] Recording start callback failed: {e}")

    def _stop_recording(self):
        """Stop recording."""
        if not self.is_recording:
            return

        self.is_recording = False
        print("[STATUS] Recording stopped")

        # Stop LED
        self._stop_led_blink()
        self.led.off()

        # Trigger callback
        if self.on_recording_stop:
            try:
                self.on_recording_stop()
            except Exception as e:
                print(f"[ERROR] Recording stop callback failed: {e}")

    def _switch_mode(self):
        """Switch between hold and toggle modes."""
        if self.current_mode == self.MODE_HOLD:
            self.current_mode = self.MODE_TOGGLE
        else:
            self.current_mode = self.MODE_HOLD

        print(f"[MODE] Switched to: {self.current_mode}")

        # Blink LED 3 times to confirm mode switch
        self._blink_confirm()

        # Trigger callback
        if self.on_mode_change:
            try:
                self.on_mode_change(self.current_mode)
            except Exception as e:
                print(f"[ERROR] Mode change callback failed: {e}")

    def _start_led_blink(self, interval: float):
        """Start LED blinking in a background thread."""
        self._stop_led_blink()  # Stop any existing blink

        self.stop_blink = False

        def blink():
            while not self.stop_blink:
                self.led.toggle()
                time.sleep(interval)

        self.led_blink_thread = threading.Thread(target=blink, daemon=True)
        self.led_blink_thread.start()

    def _stop_led_blink(self):
        """Stop LED blinking."""
        self.stop_blink = True
        if self.led_blink_thread:
            self.led_blink_thread.join(timeout=1.0)
            self.led_blink_thread = None

    def _blink_confirm(self):
        """Blink LED 3 times quickly to confirm action."""
        for _ in range(3):
            self.led.on()
            time.sleep(0.15)
            self.led.off()
            time.sleep(0.15)

    def cleanup(self):
        """Clean up GPIO resources."""
        self._stop_led_blink()
        self.led.off()
        self.listen_button.close()
        self.send_button.close()
        self.led.close()
