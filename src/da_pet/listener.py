from __future__ import annotations

from collections.abc import Callable

from pynput import keyboard, mouse


class GlobalInputListener:
    def __init__(
        self,
        on_click: Callable[[int], None],
        on_key_press: Callable[[str | None], None],
    ) -> None:
        self._on_click = on_click
        self._on_key_press = on_key_press
        self._mouse_listener: mouse.Listener | None = None
        self._keyboard_listener: keyboard.Listener | None = None

    def _handle_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        del x, y, button
        if pressed:
            self._on_click(1)

    def _normalize_key(self, key: keyboard.Key | keyboard.KeyCode) -> str | None:
        if isinstance(key, keyboard.KeyCode) and key.char:
            return key.char.lower()

        special_keys = {
            keyboard.Key.space: "space",
            keyboard.Key.backspace: "backspace",
            keyboard.Key.enter: "enter",
            keyboard.Key.tab: "tab",
            keyboard.Key.alt: "alt",
            keyboard.Key.alt_l: "alt",
            keyboard.Key.alt_r: "alt",
            keyboard.Key.alt_gr: "alt",
            keyboard.Key.ctrl: "ctrl",
            keyboard.Key.ctrl_l: "ctrl",
            keyboard.Key.ctrl_r: "ctrl",
            keyboard.Key.up: "up",
            keyboard.Key.down: "down",
            keyboard.Key.left: "left",
            keyboard.Key.right: "right",
        }
        return special_keys.get(key)

    def _handle_key_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        self._on_key_press(self._normalize_key(key))

    def start(self) -> None:
        if self._mouse_listener is None:
            self._mouse_listener = mouse.Listener(on_click=self._handle_click)
            self._mouse_listener.daemon = True
            self._mouse_listener.start()

        if self._keyboard_listener is None:
            self._keyboard_listener = keyboard.Listener(on_press=self._handle_key_press)
            self._keyboard_listener.daemon = True
            self._keyboard_listener.start()

    def stop(self) -> None:
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None

        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
