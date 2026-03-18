from __future__ import annotations

from collections.abc import Callable

from pynput import keyboard, mouse


class GlobalInputListener:
    def __init__(
        self,
        on_click: Callable[[int], None],
        on_key_press: Callable[[], None],
    ) -> None:
        self._on_click = on_click
        self._on_key_press = on_key_press
        self._mouse_listener: mouse.Listener | None = None
        self._keyboard_listener: keyboard.Listener | None = None

    def _handle_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        del x, y, button
        if pressed:
            self._on_click(1)

    def _handle_key_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        del key
        self._on_key_press()

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
