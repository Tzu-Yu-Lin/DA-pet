from __future__ import annotations

import ctypes
import math
from pathlib import Path
import random
import tkinter as tk
from collections.abc import Callable

from da_pet.state import OBJECT_IDS, PetState


TEXT_DARK = "#402a1d"
BAR_BG = "#ebd3a4"
BAR_FILL = "#ff9f1c"
SLOT_BG = "#fff4d8"
SLOT_BORDER = "#c28b48"
TRANSPARENT_BG = "#010203"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
IMAGE_DIR = PROJECT_ROOT / "image"
FORM_IMAGES = {
    "Seed": "DA01.png",
    "Sprout": "DA02.png",
    "Blaze": "DA03.png",
}
BRANCH_IMAGES = {
    "fire": ("DAf01.png", "DAf02.png", "DAf03.png"),
    "water": ("DAw01.png", "DAw02.png", "DAw03.png"),
    "earth": ("DAg01.png", "DAg02.png", "DAg03.png"),
}
ASPECT_IMAGES = {
    ("fire", "dark"): "DAfd01.png",
    ("fire", "light"): "DAfl01.png",
    ("water", "dark"): "DAwd01.png",
    ("water", "light"): "DAwl01.png",
    ("earth", "dark"): "DAgd01.png",
    ("earth", "light"): "DAgl01.png",
}
FOOD_IMAGE = "food01.png"
FOOD_EXP_VALUES = (6, 9, 12)
DROP_CHANCE = 0.05
DROP_STEP = 0.18
FLOAT_LIFE = 18
FOOD_SLOT_COUNT = 4
OBJECT_SLOT_COUNT = 5
ANIMATION_MS = 40
GWL_EXSTYLE = -20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TRANSPARENT = 0x00000020
IMM_CONTEXT_NONE = 0
QUESTION_COLOR = "#7b5635"
DEBUG_RING = "#63cdda"
DEBUG_TEXT = "#184e77"
FAIRY_IMAGE = "ang.png"
ACHIEVEMENT_LIFE = 90
ACHIEVEMENT_WIDTH = 300
CLOSED_PET_IMAGE_SHRINK = 11
OPEN_PET_IMAGE_SHRINK = 5
CLOSED_FAIRY_IMAGE_SHRINK = 40
OPEN_FAIRY_IMAGE_SHRINK = 16
WINDOW_RIGHT_MARGIN = 0
WINDOW_BOTTOM_MARGIN = 0
TASKBAR_CLOCK_OFFSET = 0
TASKBAR_OVERLAP = 18
UI_SCALE = 1.2


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
    def __init__(
        self,
        root: tk.Tk,
        on_feed: Callable[[int], None],
        hidden_objects: tuple[dict[str, float | str], ...] = (),
        object_hit_radius: int = 0,
        show_object_debug_zones: bool = False,
    ) -> None:
        self.root = root
        self.on_feed = on_feed
        self.hidden_objects = hidden_objects
        self.object_hit_radius = object_hit_radius
        self.show_object_debug_zones = show_object_debug_zones
        self.closed_width = self._scale(96)
        self.open_width = self._scale(530)
        self.width = self.closed_width
        self.height = self._scale(300)
        self.status_height = self._scale(26)
        self._image_cache: dict[tuple[str, int], tk.PhotoImage] = {}
        self._foods: list[dict[str, object] | None] = [None] * FOOD_SLOT_COUNT
        self._drop_effects: list[dict[str, object]] = []
        self._float_texts: list[dict[str, object]] = []
        self._dragging_food: dict[str, object] | None = None
        self._drag_origin: int | None = None
        self._drag_pos = (0, 0)
        self._current_state: PetState | None = None
        self._debug_window: tk.Toplevel | None = None
        self._debug_canvas: tk.Canvas | None = None
        self._fairy_phase = 0.0
        self._achievement_popup: dict[str, object] | None = None
        self.inventory_open = False
        self._build_ui()
        self._build_debug_overlay()
        self._position_bottom_right()
        self._make_click_through_focus()
        self._disable_ime()
        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.root.after(ANIMATION_MS, self._tick_effects)

    def _scale(self, value: float) -> int:
        return max(1, int(round(value * UI_SCALE)))

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

    def _build_debug_overlay(self) -> None:
        if not self.show_object_debug_zones or not self.hidden_objects or self.object_hit_radius <= 0:
            return

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        debug_window = tk.Toplevel(self.root)
        debug_window.overrideredirect(True)
        debug_window.attributes("-topmost", True)
        debug_window.configure(bg=TRANSPARENT_BG)
        debug_window.wm_attributes("-transparentcolor", TRANSPARENT_BG)
        debug_window.geometry(f"{screen_width}x{screen_height}+0+0")

        debug_canvas = tk.Canvas(
            debug_window,
            width=screen_width,
            height=screen_height,
            bg=TRANSPARENT_BG,
            highlightthickness=0,
            bd=0,
        )
        debug_canvas.pack()

        self._debug_window = debug_window
        self._debug_canvas = debug_canvas
        self._make_window_click_through(debug_window, transparent=True)
        self._draw_debug_overlay()

    def _position_bottom_right(self) -> None:
        self.root.update_idletasks()
        work_area = _get_windows_work_area()

        if work_area is None:
            right = self.root.winfo_screenwidth()
            bottom = self.root.winfo_screenheight()
        else:
            _, _, right, bottom = work_area

        x = right - self.width - WINDOW_RIGHT_MARGIN - self._scale(TASKBAR_CLOCK_OFFSET)
        y = bottom - self.height - WINDOW_BOTTOM_MARGIN + self._scale(TASKBAR_OVERLAP)
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def _make_click_through_focus(self) -> None:
        self._make_window_click_through(self.root, transparent=False)

    def _make_window_click_through(self, window: tk.Misc, transparent: bool) -> None:
        window.update_idletasks()
        hwnd = window.winfo_id()
        ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        extra_style = WS_EX_NOACTIVATE
        if transparent:
            extra_style |= WS_EX_TRANSPARENT
        ctypes.windll.user32.SetWindowLongW(
            hwnd,
            GWL_EXSTYLE,
            ex_style | extra_style,
        )

    def _disable_ime(self) -> None:
        self.root.update_idletasks()
        hwnd = self.root.winfo_id()
        ctypes.windll.imm32.ImmAssociateContext(hwnd, IMM_CONTEXT_NONE)

    def _draw_debug_overlay(self) -> None:
        if self._debug_canvas is None:
            return

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self._debug_canvas.delete("all")

        for hidden_object in self.hidden_objects:
            object_id = str(hidden_object["id"])
            center_x = int(screen_width * float(hidden_object["x_ratio"]))
            center_y = int(screen_height * float(hidden_object["y_ratio"]))
            radius = self.object_hit_radius
            self._debug_canvas.create_oval(
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
                outline=DEBUG_RING,
                width=3,
            )
            self._debug_canvas.create_text(
                center_x,
                center_y - radius - self._scale(12),
                text=object_id,
                fill=DEBUG_TEXT,
                font=("Segoe UI", self._scale(10), "bold"),
            )
            self._debug_canvas.create_text(
                center_x,
                center_y,
                text="+",
                fill=DEBUG_TEXT,
                font=("Segoe UI", self._scale(12), "bold"),
            )

    def _fairy_image(self) -> tk.PhotoImage | None:
        return self._cached_image(FAIRY_IMAGE, self._current_fairy_image_shrink())

    def _draw_fairy(self, state: PetState) -> None:
        if not state.all_objects_found():
            return

        pet_size = self._current_pet_size()
        pet_top = self._current_pet_top()
        center_x = self._pet_center_x() + (pet_size / 2) - self._scale(20) + (math.sin(self._fairy_phase) * self._scale(4))
        center_y_offset = self._scale(26)
        if not self.inventory_open:
            center_y_offset -= self._scale(10)
        center_y = pet_top + center_y_offset + (math.cos(self._fairy_phase * 1.4) * self._scale(3))
        fairy_image = self._fairy_image()
        if fairy_image is not None:
            self.canvas.create_image(center_x, center_y, image=fairy_image)
            return

        self.canvas.create_oval(
            center_x - self._scale(8),
            center_y - self._scale(8),
            center_x + self._scale(8),
            center_y + self._scale(8),
            fill="#b8f2e6",
            outline="",
        )

    def show_achievement(self, text: str) -> None:
        self._achievement_popup = {
            "text": text,
            "life": ACHIEVEMENT_LIFE,
        }
        self._redraw()

    def _draw_achievement(self) -> None:
        if self._achievement_popup is None:
            return

        x0 = self._scale(12)
        y0 = self._scale(12)
        x1 = self.width - self._scale(12)
        y1 = self._scale(40)
        self.canvas.create_rectangle(
            x0,
            y0,
            x1,
            y1,
            fill="#fff3bf",
            outline="#d4a017",
            width=2,
        )
        self.canvas.create_text(
            (x0 + x1) / 2,
            (y0 + y1) / 2,
            text=str(self._achievement_popup["text"]),
            fill="#6b3e00",
            font=("Segoe UI", self._scale(9), "bold"),
        )

    def _pet_center_x(self) -> float:
        if self.inventory_open:
            return self.width - self._scale(110)
        return self.width - self._scale(48)

    def _current_pet_size(self) -> int:
        if self.inventory_open:
            return self._scale(208)
        return self._scale(92)

    def _current_pet_top(self) -> int:
        if self.inventory_open:
            return self._scale(104)
        return self._scale(190)

    def _current_pet_image_shrink(self) -> int:
        if self.inventory_open:
            return OPEN_PET_IMAGE_SHRINK
        return CLOSED_PET_IMAGE_SHRINK

    def _current_fairy_image_shrink(self) -> int:
        if self.inventory_open:
            return OPEN_FAIRY_IMAGE_SHRINK
        return CLOSED_FAIRY_IMAGE_SHRINK

    def _pet_bounds(self) -> tuple[float, float, float, float]:
        center_x = self._pet_center_x()
        pet_size = self._current_pet_size()
        pet_top = self._current_pet_top()
        half = pet_size / 2
        return center_x - half, pet_top, center_x + half, pet_top + pet_size

    def _inventory_anchor_x(self) -> int:
        pet_left, _, _, _ = self._pet_bounds()
        return max(self._scale(12), int(pet_left) - self._scale(214))

    def _object_slots_top(self) -> int:
        _, pet_top, _, _ = self._pet_bounds()
        return max(self._scale(20), int(pet_top) + self._scale(18))

    def _food_slots_top(self) -> int:
        return self._object_slots_top() + self._scale(46)

    def _slot_rect(self, index: int) -> tuple[int, int, int, int]:
        x0 = self._inventory_anchor_x() + self._scale(20) + (index * self._scale(40))
        y0 = self._food_slots_top()
        return x0, y0, x0 + self._scale(34), y0 + self._scale(34)

    def _object_slot_rect(self, index: int) -> tuple[int, int, int, int]:
        x0 = self._inventory_anchor_x() + (index * self._scale(40))
        y0 = self._object_slots_top()
        return x0, y0, x0 + self._scale(34), y0 + self._scale(34)

    def _slot_center(self, index: int) -> tuple[float, float]:
        x0, y0, x1, y1 = self._slot_rect(index)
        return (x0 + x1) / 2, (y0 + y1) / 2

    def _object_slot_center(self, index: int) -> tuple[float, float]:
        x0, y0, x1, y1 = self._object_slot_rect(index)
        return (x0 + x1) / 2, (y0 + y1) / 2

    def _first_empty_slot(self) -> int | None:
        for index, food in enumerate(self._foods):
            if food is None:
                return index
        return None

    def _slot_at(self, x: float, y: float) -> int | None:
        if not self.inventory_open:
            return None

        for index in range(FOOD_SLOT_COUNT):
            x0, y0, x1, y1 = self._slot_rect(index)
            if x0 <= x <= x1 and y0 <= y <= y1:
                return index
        return None

    def _pet_hit(self, x: float, y: float) -> bool:
        left, top, right, bottom = self._pet_bounds()
        return left <= x <= right and top <= y <= bottom

    def _cached_image(self, file_name: str, shrink: int) -> tk.PhotoImage | None:
        cache_key = (file_name, shrink)
        if cache_key in self._image_cache:
            return self._image_cache[cache_key]

        file_path = IMAGE_DIR / file_name
        if not file_path.exists():
            return None

        image = tk.PhotoImage(file=str(file_path)).subsample(shrink, shrink)
        self._image_cache[cache_key] = image
        return image

    def _branch_image_name(self, state: PetState) -> str | None:
        image_names = BRANCH_IMAGES.get(state.branch)
        if image_names is None:
            return None

        if state.level >= 25:
            return image_names[2]
        if state.level >= 20:
            return image_names[1]
        return image_names[0]

    def _image_for_state(self, state: PetState) -> tk.PhotoImage | None:
        pet_shrink = self._current_pet_image_shrink()
        aspect_image = ASPECT_IMAGES.get((state.branch, state.aspect))
        if aspect_image is not None:
            return self._cached_image(aspect_image, pet_shrink)

        branch_image = self._branch_image_name(state)
        if branch_image is not None:
            return self._cached_image(branch_image, pet_shrink)

        return self._cached_image(FORM_IMAGES.get(state.form, FORM_IMAGES["Seed"]), pet_shrink)

    def _food_image(self) -> tk.PhotoImage | None:
        return self._cached_image(FOOD_IMAGE, 28)

    def _object_image(self, object_id: str) -> tk.PhotoImage | None:
        return self._cached_image(f"{object_id}.png", 28)

    def handle_food_rolls(self, count: int) -> None:
        spawned = False
        for _ in range(count):
            spawned = self._maybe_drop_food() or spawned

        if spawned:
            self._redraw()

    def handle_object_finds(self, object_ids: list[str], fairy_unlocked: bool = False) -> None:
        if not object_ids:
            return

        notice = "you find an item"
        self._add_float_text(notice, "#4caf50")
        if fairy_unlocked:
            self.show_achievement("Achievement unlocked: Fairy Companion!")
        self._redraw()

    def _maybe_drop_food(self) -> bool:
        slot_index = self._first_empty_slot()
        if slot_index is None or random.random() > DROP_CHANCE:
            return False

        food = {"exp": random.choice(FOOD_EXP_VALUES)}
        self._drop_effects.append({"food": food, "slot": slot_index, "progress": 0.0})
        return True

    def refresh(self, state: PetState) -> None:
        self._current_state = state
        self._redraw()

    def _set_width(self, width: int) -> None:
        if self.width == width:
            return

        self.width = width
        self.canvas.configure(width=self.width, height=self.height)
        self._position_bottom_right()

    def _redraw(self) -> None:
        if self._current_state is None:
            return

        desired_width = self.open_width if self.inventory_open else self.closed_width
        if self._achievement_popup is not None:
            desired_width = max(desired_width, ACHIEVEMENT_WIDTH)
        self._set_width(desired_width)
        self.canvas.delete("all")

        if self.inventory_open:
            self._draw_object_slots(self._current_state)
            self._draw_slots()

        self._draw_drop_effects()
        self._draw_pet(self._current_state)
        self._draw_fairy(self._current_state)
        self._draw_status(self._current_state)
        self._draw_float_texts()
        self._draw_achievement()

        if self._dragging_food is not None:
            self._draw_food(self._dragging_food, self._drag_pos[0], self._drag_pos[1], 13)

    def _draw_pet(self, state: PetState) -> None:
        image = self._image_for_state(state)
        pet_top = self._current_pet_top()
        if image is not None:
            self.canvas.create_image(self._pet_center_x(), pet_top, image=image, anchor="n")
        else:
            self.canvas.create_text(
                self._pet_center_x(),
                pet_top + 40,
                text=f"Missing\n{state.form}",
                fill=TEXT_DARK,
                font=("Segoe UI", self._scale(10), "bold"),
            )

    def _draw_object_slots(self, state: PetState) -> None:
        for index, object_id in enumerate(OBJECT_IDS[:OBJECT_SLOT_COUNT]):
            x0, y0, x1, y1 = self._object_slot_rect(index)
            self.canvas.create_rectangle(
                x0,
                y0,
                x1,
                y1,
                fill=SLOT_BG,
                outline=SLOT_BORDER,
                width=2,
            )
            if state.has_object(object_id):
                center_x, center_y = self._object_slot_center(index)
                self._draw_object(object_id, center_x, center_y)
            else:
                self.canvas.create_text(
                    (x0 + x1) / 2,
                    (y0 + y1) / 2,
                    text="?",
                    fill=QUESTION_COLOR,
                    font=("Segoe UI", self._scale(12), "bold"),
                )

    def _draw_slots(self) -> None:
        for index, food in enumerate(self._foods):
            x0, y0, x1, y1 = self._slot_rect(index)
            self.canvas.create_rectangle(
                x0,
                y0,
                x1,
                y1,
                fill=SLOT_BG,
                outline=SLOT_BORDER,
                width=2,
            )
            if food is not None:
                self._draw_food(food, (x0 + x1) / 2, (y0 + y1) / 2, 11)

    def _draw_object(self, object_id: str, center_x: float, center_y: float) -> None:
        image = self._object_image(object_id)
        if image is not None:
            self.canvas.create_image(center_x, center_y, image=image)
            return

        self.canvas.create_rectangle(
            center_x - self._scale(10),
            center_y - self._scale(10),
            center_x + self._scale(10),
            center_y + self._scale(10),
            fill="#8ecae6",
            outline="",
        )

    def _draw_food(
        self,
        food: dict[str, object],
        center_x: float,
        center_y: float,
        size: float,
    ) -> None:
        del food, size
        image = self._food_image()
        if image is not None:
            self.canvas.create_image(center_x, center_y, image=image)
        else:
            self.canvas.create_oval(
            center_x - self._scale(10),
            center_y - self._scale(10),
            center_x + self._scale(10),
            center_y + self._scale(10),
            fill="#f7b32b",
            outline="",
        )

    def _draw_drop_effects(self) -> None:
        for effect in self._drop_effects:
            center_x, target_y = self._slot_center(int(effect["slot"]))
            progress = float(effect["progress"])
            eased = progress * progress * (3 - (2 * progress))
            current_y = -18 + ((target_y + 18) * eased)
            wobble = 4 if progress < 0.7 else 0
            self._draw_food(dict(effect["food"]), center_x + wobble, current_y, 10 + progress)
            self.canvas.create_line(center_x - self._scale(10), current_y + self._scale(12), center_x - self._scale(4), current_y + self._scale(18), fill="#ffd166", width=self._scale(2))
            self.canvas.create_line(center_x + self._scale(10), current_y + self._scale(12), center_x + self._scale(4), current_y + self._scale(18), fill="#ffd166", width=self._scale(2))

    def _draw_float_texts(self) -> None:
        for text in self._float_texts:
            self.canvas.create_text(
                text["x"],
                text["y"],
                text=text["text"],
                fill=text["color"],
                font=("Segoe UI", self._scale(9), "bold"),
            )

    def _draw_status(self, state: PetState) -> None:
        center_x = self._pet_center_x()
        bar_width = self._scale(74)
        bar_top_offset = self._scale(13)
        bar_height = self._scale(4)
        _, pet_top, _, _ = self._pet_bounds()
        pet_size = self._current_pet_size()
        # The sprite PNGs have transparent padding, so anchor the status bar
        # slightly inside the pet area instead of below the full image bounds.
        top = min(self.height - self._scale(22), int(pet_top + (pet_size * 0.8)))
        if self.inventory_open:
            top -= self._scale(16)
        else:
            top -= self._scale(10)
        self.canvas.create_text(
            center_x,
            top + 4,
            text=f"Lv{state.level}",
            fill=TEXT_DARK,
            font=("Segoe UI", self._scale(7), "normal"),
        )
        self.canvas.create_rectangle(
            center_x - (bar_width / 2),
            top + bar_top_offset,
            center_x + (bar_width / 2),
            top + bar_top_offset + bar_height,
            fill=BAR_BG,
            outline="",
        )
        self.canvas.create_rectangle(
            center_x - (bar_width / 2),
            top + bar_top_offset,
            center_x - (bar_width / 2) + (bar_width * state.progress_ratio),
            top + bar_top_offset + bar_height,
            fill=BAR_FILL,
            outline="",
        )

    def _add_float_text(self, text: str, color: str = "#ff9f1c") -> None:
        self._float_texts.append(
            {
                "x": self._pet_center_x(),
                "y": self._scale(108),
                "text": text,
                "color": color,
                "life": FLOAT_LIFE,
            }
        )

    def _return_dragged_food(self, food: dict[str, object], target_slot: int | None) -> None:
        if target_slot is not None and self._foods[target_slot] is None:
            self._foods[target_slot] = food
            return

        if self._drag_origin is not None and self._foods[self._drag_origin] is None:
            self._foods[self._drag_origin] = food
            return

        empty_slot = self._first_empty_slot()
        if empty_slot is not None:
            self._foods[empty_slot] = food

    def _on_press(self, event: tk.Event) -> None:
        slot_index = self._slot_at(event.x, event.y)
        if slot_index is not None and self._foods[slot_index] is not None:
            self._dragging_food = self._foods[slot_index]
            self._foods[slot_index] = None
            self._drag_origin = slot_index
            self._drag_pos = (event.x, event.y)
            self._redraw()
            return

        if self._pet_hit(event.x, event.y):
            self.inventory_open = not self.inventory_open
            self._redraw()

    def _on_drag(self, event: tk.Event) -> None:
        if self._dragging_food is None:
            return

        self._drag_pos = (event.x, event.y)
        self._redraw()

    def _on_release(self, event: tk.Event) -> None:
        if self._dragging_food is None:
            return

        food = self._dragging_food
        target_slot = self._slot_at(event.x, event.y)
        self._dragging_food = None

        if self._pet_hit(event.x, event.y):
            exp_amount = int(food["exp"])
            self._drag_origin = None
            self._add_float_text(f"+{exp_amount} EXP")
            self.on_feed(exp_amount)
            self._redraw()
            return

        self._return_dragged_food(food, target_slot)
        self._drag_origin = None
        self._redraw()

    def _tick_effects(self) -> None:
        if not self.root.winfo_exists():
            return

        changed = False

        for effect in self._drop_effects[:]:
            effect["progress"] = float(effect["progress"]) + DROP_STEP
            if float(effect["progress"]) >= 1.0:
                slot_index = int(effect["slot"])
                if self._foods[slot_index] is None:
                    self._foods[slot_index] = dict(effect["food"])
                self._drop_effects.remove(effect)
            changed = True

        for text in self._float_texts[:]:
            text["y"] = float(text["y"]) - 2
            text["life"] = int(text["life"]) - 1
            if int(text["life"]) <= 0:
                self._float_texts.remove(text)
            changed = True

        if self._current_state is not None and self._current_state.all_objects_found():
            self._fairy_phase += 0.18
            changed = True

        if self._achievement_popup is not None:
            self._achievement_popup["life"] = int(self._achievement_popup["life"]) - 1
            if int(self._achievement_popup["life"]) <= 0:
                self._achievement_popup = None
            changed = True

        if changed:
            self._redraw()

        self.root.after(ANIMATION_MS, self._tick_effects)
