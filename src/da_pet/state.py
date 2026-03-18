from __future__ import annotations

from dataclasses import dataclass


LEVEL_BASE_EXP = 10
LEVEL_STEP_EXP = 5
EVOLUTION_STAGES = (
    (1, "Seed"),
    (5, "Sprout"),
    (10, "Blaze"),
    (15, "Knight"),
    (20, "Myth"),
)


def exp_needed_for_level(level: int) -> int:
    return LEVEL_BASE_EXP + ((level - 1) * LEVEL_STEP_EXP)


def form_for_level(level: int) -> str:
    current_form = EVOLUTION_STAGES[0][1]
    for min_level, form_name in EVOLUTION_STAGES:
        if level >= min_level:
            current_form = form_name
    return current_form


@dataclass
class PetState:
    total_clicks: int = 0
    total_exp: int = 0
    level: int = 1
    current_exp: int = 0
    next_level_exp: int = exp_needed_for_level(1)
    form: str = form_for_level(1)

    def register_click(self, count: int = 1, exp_per_click: int = 1) -> bool:
        if count <= 0 or exp_per_click <= 0:
            return False

        gained_exp = count * exp_per_click
        self.total_clicks += count
        self.total_exp += gained_exp
        self.current_exp += gained_exp

        leveled_up = False
        while self.current_exp >= self.next_level_exp:
            self.current_exp -= self.next_level_exp
            self.level += 1
            self.next_level_exp = exp_needed_for_level(self.level)
            leveled_up = True

        self.form = form_for_level(self.level)
        return leveled_up

    @property
    def progress_ratio(self) -> float:
        if self.next_level_exp <= 0:
            return 0.0
        return min(1.0, self.current_exp / self.next_level_exp)

    def to_dict(self) -> dict:
        return {
            "total_clicks": self.total_clicks,
            "total_exp": self.total_exp,
            "level": self.level,
            "current_exp": self.current_exp,
            "next_level_exp": self.next_level_exp,
            "form": self.form,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> "PetState":
        if not data:
            return cls()

        level = int(data.get("level", 1))
        current_exp = int(data.get("current_exp", 0))

        state = cls(
            total_clicks=int(data.get("total_clicks", 0)),
            total_exp=int(data.get("total_exp", 0)),
            level=max(1, level),
            current_exp=max(0, current_exp),
            next_level_exp=int(data.get("next_level_exp", exp_needed_for_level(max(1, level)))),
            form=str(data.get("form", form_for_level(max(1, level)))),
        )
        state.next_level_exp = max(1, state.next_level_exp)
        state.form = form_for_level(state.level)
        return state
