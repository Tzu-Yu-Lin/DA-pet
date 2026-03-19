from __future__ import annotations

from pathlib import Path
from queue import Empty, SimpleQueue
import tkinter as tk

from da_pet.listener import GlobalInputListener
from da_pet.pet_window import PetWindow
from da_pet.storage import load_state, save_state


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = PROJECT_ROOT / "data" / "pet_state.json"
QUEUE_POLL_MS = 100


class DesktopPetApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.state = load_state(STATE_FILE)
        self.event_queue: SimpleQueue[tuple[str, object]] = SimpleQueue()
        self.listener = GlobalInputListener(
            on_click=lambda count: self.event_queue.put_nowait(("click", count)),
            on_key_press=lambda key_name: self.event_queue.put_nowait(("key", key_name)),
        )
        self._closed = False
        self.window = PetWindow(self.root, on_feed=self._handle_feed)
        self.window.refresh(self.state)

        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)
        self.root.bind("<Escape>", lambda event: self.shutdown())
        self.root.after(QUEUE_POLL_MS, self._process_events)

    def _process_events(self) -> None:
        if self._closed:
            return

        processed_clicks = 0
        processed_keys = 0
        while True:
            try:
                event_type, payload = self.event_queue.get_nowait()
            except Empty:
                break
            else:
                if event_type == "click":
                    processed_clicks += int(payload)
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

        if processed_clicks or processed_keys:
            self._sync_state()

        self.root.after(QUEUE_POLL_MS, self._process_events)

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
