from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class KeyboardOutputStatus:
    enabled: bool
    available: bool
    last_output: str | None
    output_count: int
    error_message: str | None


class KeyboardOutput:
    """
    Simulate real keyboard input.

    This module is intentionally small:
    - The vision/audio system decides what key was confirmed.
    - This module only sends that key to the operating system.

    Notes:
    - On macOS, the app running this script may need Accessibility permission.
    - The simulated key goes to the currently focused application.
    """

    def __init__(
        self,
        enabled: bool = False,
        press_interval_seconds: float = 0.02,
        uppercase_letters: bool = False,
    ):
        self.enabled = enabled
        self.press_interval_seconds = press_interval_seconds
        self.uppercase_letters = uppercase_letters

        self.available = False
        self.error_message: str | None = None
        self.last_output: str | None = None
        self.output_count = 0

        self.keyboard = None
        self.Key = None

        self._setup_controller()

    def _setup_controller(self) -> None:
        try:
            from pynput.keyboard import Controller, Key

            self.keyboard = Controller()
            self.Key = Key
            self.available = True
            self.error_message = None

        except Exception as error:
            self.keyboard = None
            self.Key = None
            self.available = False
            self.error_message = str(error)

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def toggle_enabled(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled

    def type_label(self, label: str | None) -> bool:
        """
        Type one confirmed key label.

        Returns:
            True if output was sent
            False if output was skipped
        """
        if label is None:
            return False

        if not self.enabled:
            return False

        if not self.available or self.keyboard is None:
            return False

        normalized_label = str(label).strip()

        if not normalized_label:
            return False

        try:
            self._send_label(normalized_label)
            self.last_output = normalized_label
            self.output_count += 1

            if self.press_interval_seconds > 0:
                time.sleep(self.press_interval_seconds)

            return True

        except Exception as error:
            self.error_message = str(error)
            return False

    def _send_label(self, label: str) -> None:
        upper_label = label.upper()

        if len(label) == 1:
            if label.isalpha():
                text = label.upper() if self.uppercase_letters else label.lower()
                self.keyboard.type(text)
                return

            self.keyboard.type(label)
            return

        special_key = self._map_special_key(upper_label)

        if special_key is not None:
            self.keyboard.press(special_key)
            self.keyboard.release(special_key)
            return

        # Fallback: type the raw label as text.
        self.keyboard.type(label)

    def _map_special_key(self, label: str):
        if self.Key is None:
            return None

        mapping = {
            "SPACE": self.Key.space,
            "BACKSPACE": self.Key.backspace,
            "DELETE": self.Key.delete,
            "ENTER": self.Key.enter,
            "RETURN": self.Key.enter,
            "TAB": self.Key.tab,
            "ESC": self.Key.esc,
            "ESCAPE": self.Key.esc,
            "LEFT": self.Key.left,
            "RIGHT": self.Key.right,
            "UP": self.Key.up,
            "DOWN": self.Key.down,
        }

        return mapping.get(label)

    def get_status(self) -> KeyboardOutputStatus:
        return KeyboardOutputStatus(
            enabled=self.enabled,
            available=self.available,
            last_output=self.last_output,
            output_count=self.output_count,
            error_message=self.error_message,
        )