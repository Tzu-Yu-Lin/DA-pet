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
        self.width = 220
        self.height = 240
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
            bd=2,
            relief="solid",
            highlightbackground="#d5b27a",
            highlightcolor="#d5b27a",
            highlightthickness=0,
            padx=10,
            pady=8,
        )
        self.container.pack(fill="both", expand=True)

        header = tk.Frame(self.container, bg=CARD_BG)
        header.pack(fill="x")

        self.title_label = tk.Label(
            header,
            text="DA-pet",
            font=("Microsoft JhengHei UI", 11, "bold"),
            bg=CARD_BG,
            fg=TEXT_DARK,
        )
        self.title_label.pack(side="left")

        self.close_button = tk.Button(
            header,
            text="X",
            command=self.on_close,
            font=("Segoe UI", 8, "bold"),
            bg="#f7d9d0",
            fg=TEXT_DARK,
            bd=0,
            padx=6,
            pady=2,
            activebackground="#efc6ba",
            activeforeground=TEXT_DARK,
            cursor="hand2",
        )
        self.close_button.pack(side="right")

        self.canvas = tk.Canvas(
            self.container,
            width=190,
            height=110,
            bg=CARD_BG,
            highlightthickness=0,
        )
        self.canvas.pack(pady=(6, 4))

        self.level_label = tk.Label(
            self.container,
            text="Lv.1  Seed",
            font=("Microsoft JhengHei UI", 12, "bold"),
            bg=CARD_BG,
            fg=TEXT_DARK,
        )
        self.level_label.pack(anchor="w")

        self.exp_label = tk.Label(
            self.container,
            text="EXP 0 / 10",
            font=("Segoe UI", 10),
            bg=CARD_BG,
            fg=TEXT_SOFT,
        )
        self.exp_label.pack(anchor="w", pady=(2, 4))

        self.progress_canvas = tk.Canvas(
            self.container,
            width=190,
            height=16,
            bg=CARD_BG,
            highlightthickness=0,
        )
        self.progress_canvas.pack()

        self.stats_label = tk.Label(
            self.container,
            text="Clicks: 0  Total EXP: 0",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg=TEXT_SOFT,
        )
        self.stats_label.pack(anchor="w", pady=(6, 0))

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
        self.level_label.config(text=f"Lv.{state.level}  {state.form}")
        self.exp_label.config(text=f"EXP {state.current_exp} / {state.next_level_exp}")
        self.stats_label.config(
            text=f"Clicks: {state.total_clicks}  Total EXP: {state.total_exp}"
        )
        self._draw_progress_bar(state.progress_ratio)
        self._draw_pet(state)

    def _draw_progress_bar(self, progress_ratio: float) -> None:
        self.progress_canvas.delete("all")
        self.progress_canvas.create_rectangle(
            0,
            2,
            190,
            14,
            fill=BAR_BG,
            outline="",
        )
        self.progress_canvas.create_rectangle(
            0,
            2,
            190 * progress_ratio,
            14,
            fill=BAR_FILL,
            outline="",
        )

    def _draw_pet(self, state: PetState) -> None:
        style = FORM_STYLES.get(state.form, FORM_STYLES["Seed"])
        self.canvas.delete("all")

        self.canvas.create_oval(42, 78, 150, 102, fill="#ead2a2", outline="")
        self.canvas.create_oval(
            48,
            18,
            144,
            96,
            fill=style["body"],
            outline=style["outline"],
            width=3,
        )

        if state.form == "Seed":
            self.canvas.create_polygon(
                92,
                10,
                78,
                34,
                106,
                30,
                fill=style["accent"],
                outline=style["outline"],
                width=2,
            )
        elif state.form == "Bud":
            self.canvas.create_oval(
                78,
                4,
                112,
                34,
                fill=style["accent"],
                outline=style["outline"],
                width=2,
            )
            self.canvas.create_line(95, 34, 95, 22, fill=style["outline"], width=2)
        else:
            self.canvas.create_oval(
                70,
                2,
                92,
                26,
                fill=style["accent"],
                outline=style["outline"],
                width=2,
            )
            self.canvas.create_oval(
                98,
                2,
                120,
                26,
                fill=style["accent"],
                outline=style["outline"],
                width=2,
            )
            self.canvas.create_oval(
                84,
                10,
                106,
                32,
                fill=style["accent"],
                outline=style["outline"],
                width=2,
            )

        self.canvas.create_oval(74, 48, 82, 56, fill=style["outline"], outline="")
        self.canvas.create_oval(108, 48, 116, 56, fill=style["outline"], outline="")
        self.canvas.create_oval(62, 58, 72, 68, fill=style["cheek"], outline="")
        self.canvas.create_oval(118, 58, 128, 68, fill=style["cheek"], outline="")
        self.canvas.create_arc(
            82,
            58,
            108,
            74,
            start=200,
            extent=140,
            style="arc",
            width=2,
            outline=style["outline"],
        )

        self.canvas.create_text(
            158,
            18,
            text="+1 EXP",
            fill=TEXT_DARK,
            font=("Segoe UI", 10, "bold"),
        )
