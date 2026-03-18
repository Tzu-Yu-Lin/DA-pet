from __future__ import annotations

from collections.abc import Callable

from pynput import mouse


class GlobalClickListener:
    def __init__(self, on_click: Callable[[int], None]) -> None:
        self._on_click = on_click
        self._listener: mouse.Listener | None = None

    def _handle_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        del x, y, button
        if pressed:
            self._on_click(1)

    def start(self) -> None:
        if self._listener is not None:
            return

        self._listener = mouse.Listener(on_click=self._handle_click)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener is None:
            return

        self._listener.stop()
        self._listener = None
