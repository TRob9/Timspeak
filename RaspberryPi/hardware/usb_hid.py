"""
USB HID Keyboard Emulation

Emulates a USB keyboard to type cleaned dictation text.
Requires Raspberry Pi to be configured in USB gadget mode.
"""

import time


class USBKeyboard:
    """USB HID keyboard emulator."""

    def __init__(self, config: dict):
        """
        Initialize USB keyboard.

        Args:
            config: USB HID configuration dict
        """
        self.config = config
        self.typing_delay = config.get('typing_delay', 0.01)
        self.device_path = '/dev/hidg0'  # Default HID gadget device
        self.device = None

    def _open_device(self):
        """Open the HID device file."""
        if self.device is None:
            try:
                self.device = open(self.device_path, 'rb+')
            except FileNotFoundError:
                raise RuntimeError(
                    f"USB HID device not found at {self.device_path}. "
                    "Make sure USB gadget mode is configured. "
                    "Run setup/usb_hid_setup.sh"
                )
            except PermissionError:
                raise RuntimeError(
                    f"Permission denied for {self.device_path}. "
                    "Run: sudo chmod 666 /dev/hidg0"
                )

    def _write_report(self, report: bytes):
        """
        Write HID report to device.

        Args:
            report: 8-byte HID report
        """
        self._open_device()
        self.device.write(report)
        self.device.flush()

    def _press_key(self, keycode: int, modifier: int = 0):
        """
        Press a key.

        Args:
            keycode: HID keycode
            modifier: Modifier keys (shift, ctrl, etc.)
        """
        # HID report format: [modifier, reserved, key1, key2, key3, key4, key5, key6]
        report = bytes([modifier, 0, keycode, 0, 0, 0, 0, 0])
        self._write_report(report)

    def _release_keys(self):
        """Release all keys."""
        report = bytes([0, 0, 0, 0, 0, 0, 0, 0])
        self._write_report(report)

    def type_text(self, text: str):
        """
        Type a string of text.

        Args:
            text: Text to type
        """
        print(f"[USB HID] Typing {len(text)} characters...")

        for char in text:
            keycode, modifier = self._char_to_keycode(char)
            if keycode is not None:
                self._press_key(keycode, modifier)
                time.sleep(self.typing_delay)
                self._release_keys()
                time.sleep(self.typing_delay)

        print("[USB HID] Typing complete")

    def _char_to_keycode(self, char: str) -> tuple:
        """
        Convert a character to HID keycode and modifier.

        Args:
            char: Single character

        Returns:
            Tuple of (keycode, modifier)
        """
        # Modifier keys
        MOD_NONE = 0x00
        MOD_SHIFT = 0x02

        # HID keycodes (US keyboard layout)
        keycodes = {
            'a': (0x04, MOD_NONE), 'A': (0x04, MOD_SHIFT),
            'b': (0x05, MOD_NONE), 'B': (0x05, MOD_SHIFT),
            'c': (0x06, MOD_NONE), 'C': (0x06, MOD_SHIFT),
            'd': (0x07, MOD_NONE), 'D': (0x07, MOD_SHIFT),
            'e': (0x08, MOD_NONE), 'E': (0x08, MOD_SHIFT),
            'f': (0x09, MOD_NONE), 'F': (0x09, MOD_SHIFT),
            'g': (0x0A, MOD_NONE), 'G': (0x0A, MOD_SHIFT),
            'h': (0x0B, MOD_NONE), 'H': (0x0B, MOD_SHIFT),
            'i': (0x0C, MOD_NONE), 'I': (0x0C, MOD_SHIFT),
            'j': (0x0D, MOD_NONE), 'J': (0x0D, MOD_SHIFT),
            'k': (0x0E, MOD_NONE), 'K': (0x0E, MOD_SHIFT),
            'l': (0x0F, MOD_NONE), 'L': (0x0F, MOD_SHIFT),
            'm': (0x10, MOD_NONE), 'M': (0x10, MOD_SHIFT),
            'n': (0x11, MOD_NONE), 'N': (0x11, MOD_SHIFT),
            'o': (0x12, MOD_NONE), 'O': (0x12, MOD_SHIFT),
            'p': (0x13, MOD_NONE), 'P': (0x13, MOD_SHIFT),
            'q': (0x14, MOD_NONE), 'Q': (0x14, MOD_SHIFT),
            'r': (0x15, MOD_NONE), 'R': (0x15, MOD_SHIFT),
            's': (0x16, MOD_NONE), 'S': (0x16, MOD_SHIFT),
            't': (0x17, MOD_NONE), 'T': (0x17, MOD_SHIFT),
            'u': (0x18, MOD_NONE), 'U': (0x18, MOD_SHIFT),
            'v': (0x19, MOD_NONE), 'V': (0x19, MOD_SHIFT),
            'w': (0x1A, MOD_NONE), 'W': (0x1A, MOD_SHIFT),
            'x': (0x1B, MOD_NONE), 'X': (0x1B, MOD_SHIFT),
            'y': (0x1C, MOD_NONE), 'Y': (0x1C, MOD_SHIFT),
            'z': (0x1D, MOD_NONE), 'Z': (0x1D, MOD_SHIFT),
            '1': (0x1E, MOD_NONE), '!': (0x1E, MOD_SHIFT),
            '2': (0x1F, MOD_NONE), '@': (0x1F, MOD_SHIFT),
            '3': (0x20, MOD_NONE), '#': (0x20, MOD_SHIFT),
            '4': (0x21, MOD_NONE), '$': (0x21, MOD_SHIFT),
            '5': (0x22, MOD_NONE), '%': (0x22, MOD_SHIFT),
            '6': (0x23, MOD_NONE), '^': (0x23, MOD_SHIFT),
            '7': (0x24, MOD_NONE), '&': (0x24, MOD_SHIFT),
            '8': (0x25, MOD_NONE), '*': (0x25, MOD_SHIFT),
            '9': (0x26, MOD_NONE), '(': (0x26, MOD_SHIFT),
            '0': (0x27, MOD_NONE), ')': (0x27, MOD_SHIFT),
            '\n': (0x28, MOD_NONE),  # Enter
            ' ': (0x2C, MOD_NONE),   # Space
            '-': (0x2D, MOD_NONE), '_': (0x2D, MOD_SHIFT),
            '=': (0x2E, MOD_NONE), '+': (0x2E, MOD_SHIFT),
            '[': (0x2F, MOD_NONE), '{': (0x2F, MOD_SHIFT),
            ']': (0x30, MOD_NONE), '}': (0x30, MOD_SHIFT),
            '\\': (0x31, MOD_NONE), '|': (0x31, MOD_SHIFT),
            ';': (0x33, MOD_NONE), ':': (0x33, MOD_SHIFT),
            "'": (0x34, MOD_NONE), '"': (0x34, MOD_SHIFT),
            '`': (0x35, MOD_NONE), '~': (0x35, MOD_SHIFT),
            ',': (0x36, MOD_NONE), '<': (0x36, MOD_SHIFT),
            '.': (0x37, MOD_NONE), '>': (0x37, MOD_SHIFT),
            '/': (0x38, MOD_NONE), '?': (0x38, MOD_SHIFT),
        }

        return keycodes.get(char, (None, None))

    def is_available(self) -> bool:
        """Check if USB HID device is available."""
        try:
            self._open_device()
            return True
        except:
            return False

    def cleanup(self):
        """Clean up resources."""
        if self.device:
            self.device.close()
            self.device = None
