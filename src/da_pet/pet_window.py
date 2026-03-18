from __future__ import annotations

import ctypes
from pathlib import Path
import tkinter as tk

from da_pet.state import PetState


TEXT_DARK = "#402a1d"
BAR_BG = "#ebd3a4"
BAR_FILL = "#ff9f1c"
TRANSPARENT_BG = "#010203"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
IMAGE_DIR = PROJECT_ROOT / "image"
FORM_IMAGES = {
    "Seed": "DA01.png",
    "Sprout": "DA02.png",
    "Blaze": "DA03.png",
    "Knight": "DA04.png",
    "Myth": "DA05.png",
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
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.width = 94
        self.height = 114
        self.status_height = 22
        self._image_cache: dict[str, tk.PhotoImage] = {}
        self._build_ui()
        self._position_bottom_right()

    def _build_ui(self) -> None:
        self.root.title("DA-pet")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.configure(bg=TRANSPARENT_BG)
        self.root.wm_attributes("-transparentcolor", TRANSPARENT_BG)

        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg=TRANSPARENT_BG,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack()

    def _position_bottom_right(self) -> None:
        self.root.update_idletasks()
        work_area = _get_windows_work_area()

        if work_area is None:
            right = self.root.winfo_screenwidth()
            bottom = self.root.winfo_screenheight()
        else:
            _, _, right, bottom = work_area

        x = right - self.width - 16
        y = bottom - self.height - 16
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def _image_for_form(self, form: str) -> tk.PhotoImage | None:
        file_name = FORM_IMAGES.get(form, FORM_IMAGES["Seed"])
        if file_name in self._image_cache:
            return self._image_cache[file_name]

        file_path = IMAGE_DIR / file_name
        if not file_path.exists():
            return None

        image = tk.PhotoImage(file=str(file_path))
        image = image.subsample(12, 12)
        self._image_cache[file_name] = image
        return image

    def refresh(self, state: PetState) -> None:
        self.canvas.delete("all")
        image = self._image_for_form(state.form)

        if image is not None:
            self.canvas.create_image(self.width / 2, 0, image=image, anchor="n")
        else:
            self.canvas.create_text(
                self.width / 2,
                40,
                text=f"Missing\n{state.form}",
                fill=TEXT_DARK,
                font=("Segoe UI", 10, "bold"),
            )

        self._draw_status(state)

    def _draw_status(self, state: PetState) -> None:
        top = self.height - self.status_height
        self.canvas.create_text(
            self.width / 2,
            top + 3,
            text=f"Lv{state.level}",
            fill=TEXT_DARK,
            font=("Segoe UI", 8, "bold"),
        )
        self.canvas.create_rectangle(10, self.height - 12, self.width - 10, self.height - 6, fill=BAR_BG, outline="")
        self.canvas.create_rectangle(
            10,
            self.height - 12,
            10 + ((self.width - 20) * state.progress_ratio),
            self.height - 6,
            fill=BAR_FILL,
            outline="",
        )
