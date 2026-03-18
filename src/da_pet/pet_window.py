from __future__ import annotations

import ctypes
import tkinter as tk
from collections.abc import Callable

from da_pet.state import PetState


CARD_BG = "#fff6dd"
TEXT_DARK = "#402a1d"
TEXT_SOFT = "#8b5e3c"
BAR_BG = "#ebd3a4"
BAR_FILL = "#ff9f1c"

FORM_STYLES = {
    "Seed": {
        "body": "#8bd17c",
        "outline": "#326b32",
        "accent": "#4f9d69",
        "cheek": "#f6b8a8",
    },
    "Bud": {
        "body": "#80cfa9",
        "outline": "#2d6a4f",
        "accent": "#f4a4c0",
        "cheek": "#ffd0c2",
    },
    "Bloom": {
        "body": "#ffd166",
        "outline": "#9c4f00",
        "accent": "#ff7f51",
        "cheek": "#ffcab1",
    },
}


class _Rect(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


def _get_windows_work_area() -> tuple[int, int, int, int] | None:
    rect = _Rect()
    if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
        return rect.left, rect.top, rect.right, rect.bottom
    return None


class PetWindow:
    def __init__(self, root: tk.Tk, on_close: Callable[[], None]) -> None:
        self.root = root
        self.on_close = on_close
        self.width = 80
        self.height = 60
        self.canvas_width = 76
        self.canvas_height = 56
        self._build_ui()
        self._position_bottom_right()

    def _build_ui(self) -> None:
        self.root.title("DA-pet")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.configure(bg=CARD_BG)

        self.container = tk.Frame(
            self.root,
            bg=CARD_BG,
            bd=1,
            relief="solid",
            highlightbackground="#d5b27a",
            highlightcolor="#d5b27a",
            highlightthickness=0,
            padx=1,
            pady=1,
        )
        self.container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            self.container,
            width=self.canvas_width,
            height=self.canvas_height,
            bg=CARD_BG,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

    def _position_bottom_right(self) -> None:
        self.root.update_idletasks()

        work_area = _get_windows_work_area()
        if work_area is None:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            right = screen_width
            bottom = screen_height
        else:
            _, _, right, bottom = work_area

        x = right - self.width - 16
        y = bottom - self.height - 16
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def refresh(self, state: PetState) -> None:
        self._draw_pet(state)

    def _draw_pet(self, state: PetState) -> None:
        style = FORM_STYLES.get(state.form, FORM_STYLES["Seed"])
        self.canvas.delete("all")
        scale_x = self.canvas_width / 190
        scale_y = self.canvas_height / 110

        def sx(value: float) -> float:
            return value * scale_x

        def sy(value: float) -> float:
            return value * scale_y

        self.canvas.create_oval(sx(42), sy(78), sx(150), sy(102), fill="#ead2a2", outline="")
        self.canvas.create_oval(
            sx(48),
            sy(18),
            sx(144),
            sy(96),
            fill=style["body"],
            outline=style["outline"],
            width=2,
        )

        if state.form == "Seed":
            self.canvas.create_polygon(
                sx(92),
                sy(10),
                sx(78),
                sy(34),
                sx(106),
                sy(30),
                fill=style["accent"],
                outline=style["outline"],
                width=1,
            )
        elif state.form == "Bud":
            self.canvas.create_oval(
                sx(78),
                sy(4),
                sx(112),
                sy(34),
                fill=style["accent"],
                outline=style["outline"],
                width=1,
            )
            self.canvas.create_line(
                sx(95), sy(34), sx(95), sy(22), fill=style["outline"], width=1
            )
        else:
            self.canvas.create_oval(
                sx(70),
                sy(2),
                sx(92),
                sy(26),
                fill=style["accent"],
                outline=style["outline"],
                width=1,
            )
            self.canvas.create_oval(
                sx(98),
                sy(2),
                sx(120),
                sy(26),
                fill=style["accent"],
                outline=style["outline"],
                width=1,
            )
            self.canvas.create_oval(
                sx(84),
                sy(10),
                sx(106),
                sy(32),
                fill=style["accent"],
                outline=style["outline"],
                width=1,
            )

        self.canvas.create_oval(sx(74), sy(48), sx(82), sy(56), fill=style["outline"], outline="")
        self.canvas.create_oval(sx(108), sy(48), sx(116), sy(56), fill=style["outline"], outline="")
        self.canvas.create_oval(sx(62), sy(58), sx(72), sy(68), fill=style["cheek"], outline="")
        self.canvas.create_oval(sx(118), sy(58), sx(128), sy(68), fill=style["cheek"], outline="")
        self.canvas.create_arc(
            sx(82),
            sy(58),
            sx(108),
            sy(74),
            start=200,
            extent=140,
            style="arc",
            width=1,
            outline=style["outline"],
        )

        self.canvas.create_rectangle(
            sx(2),
            sy(2),
            sx(30),
            sy(14),
            fill="#fff8e8",
            outline="",
        )
        self.canvas.create_text(
            sx(16),
            sy(8),
            text=f"Lv{state.level}",
            fill=TEXT_DARK,
            font=("Segoe UI", 7, "bold"),
        )
        self.canvas.create_rectangle(
            sx(4),
            sy(96),
            sx(186),
            sy(102),
            fill=BAR_BG,
            outline="",
        )
        self.canvas.create_rectangle(
            sx(4),
            sy(96),
            sx(4 + (182 * state.progress_ratio)),
            sy(102),
            fill=BAR_FILL,
            outline="",
        )
