from __future__ import annotations

from dataclasses import dataclass


LEVEL_BASE_EXP = 9
LEVEL_STEP_EXP = 4
BRANCH_UNLOCK_LEVEL = 20
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


def branch_for_scores(level: int, game: int, engineer: int, office: int, rage: int) -> str:
    if level < BRANCH_UNLOCK_LEVEL:
        return "base"

    scores = {
        "game": game,
        "engineer": engineer,
        "office": office,
        "rage": rage,
    }
    top_score = max(scores.values())
    if top_score <= 0:
        return "base"

    # Hidden branch: only trigger when Backspace usage is clearly dominant.
    if rage > max(game, engineer, office):
        return "rage"

    for branch_name in ("game", "engineer", "office"):
        if scores[branch_name] == top_score:
            return branch_name

    return "base"


@dataclass
class PetState:
    total_clicks: int = 0
    total_exp: int = 0
    level: int = 1
    current_exp: int = 0
    next_level_exp: int = exp_needed_for_level(1)
    form: str = form_for_level(1)
    branch: str = "base"
    game_score: int = 0
    engineer_score: int = 0
    office_score: int = 0
    rage_score: int = 0

    def _refresh_progression(self) -> None:
        self.form = form_for_level(self.level)
        self.branch = branch_for_scores(
            self.level,
            self.game_score,
            self.engineer_score,
            self.office_score,
            self.rage_score,
        )

    def gain_exp(self, amount: int, click_count: int = 0) -> bool:
        if amount <= 0:
            return False

        if click_count > 0:
            self.total_clicks += click_count

        self.total_exp += amount
        self.current_exp += amount

        leveled_up = False
        while self.current_exp >= self.next_level_exp:
            self.current_exp -= self.next_level_exp
            self.level += 1
            self.next_level_exp = exp_needed_for_level(self.level)
            leveled_up = True

        self._refresh_progression()
        return leveled_up

    def register_key(self, key_name: str) -> None:
        if key_name == "backspace":
            self.rage_score += 1
        elif key_name in {"w", "a", "s", "d"} or key_name.isdigit():
            self.game_score += 1
        elif key_name in {"{", "}", "(", ")", "[", "]", ";", "/", "\\", "=", "_"}:
            self.engineer_score += 1
        elif key_name in {"tab", "alt", "ctrl", "enter", "up", "down", "left", "right"}:
            self.office_score += 1

        self._refresh_progression()

    def register_click(self, count: int = 1, exp_per_click: int = 1) -> bool:
        if count <= 0 or exp_per_click <= 0:
            return False

        return self.gain_exp(count * exp_per_click, click_count=count)

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
            "branch": self.branch,
            "game_score": self.game_score,
            "engineer_score": self.engineer_score,
            "office_score": self.office_score,
            "rage_score": self.rage_score,
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
            branch=str(data.get("branch", "base")),
            game_score=max(0, int(data.get("game_score", 0))),
            engineer_score=max(0, int(data.get("engineer_score", 0))),
            office_score=max(0, int(data.get("office_score", 0))),
            rage_score=max(0, int(data.get("rage_score", 0))),
        )
        state.next_level_exp = max(1, state.next_level_exp)
        state._refresh_progression()
        return state
