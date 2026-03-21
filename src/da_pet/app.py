from __future__ import annotations

import ctypes
from pathlib import Path
from queue import Empty, SimpleQueue
import tkinter as tk

from da_pet.listener import GlobalInputListener
from da_pet.pet_window import PetWindow
from da_pet.storage import load_state, save_state


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = PROJECT_ROOT / "data" / "pet_state.json"
QUEUE_POLL_MS = 100
HIDDEN_OBJECTS = (
    {"id": "ob01", "x_ratio": 0.14, "y_ratio": 0.22},
    {"id": "ob02", "x_ratio": 0.38, "y_ratio": 0.68},
    {"id": "ob03", "x_ratio": 0.68, "y_ratio": 0.26},
    {"id": "ob04", "x_ratio": 0.80, "y_ratio": 0.54},
    {"id": "ob05", "x_ratio": 0.26, "y_ratio": 0.82},
)
OBJECT_HIT_RADIUS = 36
SHOW_OBJECT_DEBUG_ZONES = False


def _enable_high_dpi_mode() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except OSError:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except OSError:
            pass


class DesktopPetApp:
    def __init__(self) -> None:
        _enable_high_dpi_mode()
        self.root = tk.Tk()
        self.state = load_state(STATE_FILE)
        self.event_queue: SimpleQueue[tuple[str, object]] = SimpleQueue()
        self.listener = GlobalInputListener(
            on_click=lambda x, y, count: self.event_queue.put_nowait(("click", (x, y, count))),
            on_key_press=lambda key_name: self.event_queue.put_nowait(("key", key_name)),
        )
        self._closed = False
        self.window = PetWindow(
            self.root,
            on_feed=self._handle_feed,
            hidden_objects=HIDDEN_OBJECTS,
            object_hit_radius=OBJECT_HIT_RADIUS,
            show_object_debug_zones=SHOW_OBJECT_DEBUG_ZONES,
        )
        self.window.refresh(self.state)

        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)
        self.root.bind("<Escape>", lambda event: self.shutdown())
        self.root.after(QUEUE_POLL_MS, self._process_events)

    def _process_events(self) -> None:
        if self._closed:
            return

        processed_clicks = 0
        processed_keys = 0
        found_objects: list[str] = []
        while True:
            try:
                event_type, payload = self.event_queue.get_nowait()
            except Empty:
                break
            else:
                if event_type == "click":
                    x, y, count = payload
                    processed_clicks += int(count)
                    object_id = self._object_at_click(int(x), int(y))
                    if object_id is not None and self.state.discover_object(object_id):
                        found_objects.append(object_id)
                elif event_type == "key":
                    processed_keys += 1
                    if isinstance(payload, str):
                        self.state.register_key(payload)

        if processed_clicks:
            self.state.total_clicks += processed_clicks

        if processed_keys:
            self.state.gain_exp(processed_keys)

        if processed_clicks:
            self.window.handle_food_rolls(processed_clicks)

        if found_objects:
            self.window.handle_object_finds(found_objects)

        if processed_clicks or processed_keys or found_objects:
            self._sync_state()

        self.root.after(QUEUE_POLL_MS, self._process_events)

    def _object_at_click(self, x: int, y: int) -> str | None:
        screen_width = max(1, self.root.winfo_screenwidth())
        screen_height = max(1, self.root.winfo_screenheight())
        radius_squared = OBJECT_HIT_RADIUS * OBJECT_HIT_RADIUS

        for hidden_object in HIDDEN_OBJECTS:
            target_x = int(screen_width * float(hidden_object["x_ratio"]))
            target_y = int(screen_height * float(hidden_object["y_ratio"]))
            dx = x - target_x
            dy = y - target_y
            if (dx * dx) + (dy * dy) <= radius_squared:
                return str(hidden_object["id"])

        return None

    def _handle_feed(self, exp_amount: int) -> None:
        self.state.gain_exp(exp_amount)
        self._sync_state()

    def _sync_state(self) -> None:
        save_state(STATE_FILE, self.state)
        self.window.refresh(self.state)

    def run(self) -> None:
        self.listener.start()
        try:
            self.root.mainloop()
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        if self._closed:
            return

        self._closed = True
        self.listener.stop()
        save_state(STATE_FILE, self.state)

        if self.root.winfo_exists():
            self.root.destroy()


def main() -> None:
    app = DesktopPetApp()
    app.run()
