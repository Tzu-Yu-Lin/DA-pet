from __future__ import annotations

from pathlib import Path
from queue import Empty, SimpleQueue
import tkinter as tk

from da_pet.listener import GlobalClickListener
from da_pet.pet_window import PetWindow
from da_pet.storage import load_state, save_state


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = PROJECT_ROOT / "data" / "pet_state.json"
QUEUE_POLL_MS = 100


class DesktopPetApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.state = load_state(STATE_FILE)
        self.event_queue: SimpleQueue[int] = SimpleQueue()
        self.listener = GlobalClickListener(self.event_queue.put_nowait)
        self._closed = False
        self.window = PetWindow(self.root)
        self.window.refresh(self.state)

        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)
        self.root.bind("<Escape>", lambda event: self.shutdown())
        self.root.after(QUEUE_POLL_MS, self._process_events)

    def _process_events(self) -> None:
        if self._closed:
            return

        processed_clicks = 0
        while True:
            try:
                processed_clicks += self.event_queue.get_nowait()
            except Empty:
                break

        if processed_clicks:
            self.state.register_click(count=processed_clicks)
            save_state(STATE_FILE, self.state)
            self.window.refresh(self.state)

        self.root.after(QUEUE_POLL_MS, self._process_events)

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
