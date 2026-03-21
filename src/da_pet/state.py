from __future__ import annotations

from dataclasses import dataclass, field


LEVEL_BASE_EXP = 24
LEVEL_STEP_EXP = 12
BRANCH_UNLOCK_LEVEL = 15
ASPECT_UNLOCK_LEVEL = 30
WATER_KEYS = {"b", "q", "s", "u", "w"}
FIRE_KEYS = {"g", "j", "l", "o", "r"}
EARTH_KEYS = {"c", "d", "m", "x"}
DARK_KEYS = {"d", "a", "r", "k"}
LIGHT_KEYS = {"l", "i", "g", "h"}
BRANCH_NAMES = {"fire", "water", "earth"}
ASPECT_NAMES = {"dark", "light"}
EVOLUTION_STAGES = (
    (1, "Seed"),
    (5, "Sprout"),
    (10, "Blaze"),
)
OBJECT_IDS = ("ob01", "ob02", "ob03", "ob04", "ob05")


def exp_needed_for_level(level: int) -> int:
    return LEVEL_BASE_EXP + ((level - 1) * LEVEL_STEP_EXP)


def form_for_level(level: int) -> str:
    current_form = EVOLUTION_STAGES[0][1]
    for min_level, form_name in EVOLUTION_STAGES:
        if level >= min_level:
            current_form = form_name
    return current_form


def branch_for_scores(level: int, fire: int, water: int, earth: int) -> str:
    if level < BRANCH_UNLOCK_LEVEL:
        return "base"

    scores = {
        "fire": fire,
        "water": water,
        "earth": earth,
    }
    top_score = max(scores.values())
    if top_score <= 0:
        return "base"

    for branch_name in ("fire", "water", "earth"):
        if scores[branch_name] == top_score:
            return branch_name

    return "base"


def aspect_for_scores(level: int, dark: int, light: int) -> str:
    if level < ASPECT_UNLOCK_LEVEL:
        return "base"

    if dark <= 0 and light <= 0:
        return "base"

    if dark >= light:
        return "dark"
    return "light"


@dataclass
class PetState:
    total_clicks: int = 0
    total_exp: int = 0
    level: int = 1
    current_exp: int = 0
    next_level_exp: int = exp_needed_for_level(1)
    form: str = form_for_level(1)
    branch: str = "base"
    aspect: str = "base"
    fire_score: int = 0
    water_score: int = 0
    earth_score: int = 0
    dark_score: int = 0
    light_score: int = 0
    discovered_objects: list[str] = field(default_factory=list)
    fairy_achievement_shown: bool = False

    def _refresh_progression(self) -> None:
        self.form = form_for_level(self.level)
        if self.branch not in BRANCH_NAMES:
            self.branch = branch_for_scores(
                self.level,
                self.fire_score,
                self.water_score,
                self.earth_score,
            )
        if self.aspect not in ASPECT_NAMES:
            self.aspect = aspect_for_scores(
                self.level,
                self.dark_score,
                self.light_score,
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
        if key_name in WATER_KEYS:
            self.water_score += 1
        elif key_name in FIRE_KEYS:
            self.fire_score += 1
        elif key_name in EARTH_KEYS:
            self.earth_score += 1

        if self.level >= BRANCH_UNLOCK_LEVEL:
            if key_name in DARK_KEYS:
                self.dark_score += 1
            elif key_name in LIGHT_KEYS:
                self.light_score += 1

        self._refresh_progression()

    def register_click(self, count: int = 1, exp_per_click: int = 1) -> bool:
        if count <= 0 or exp_per_click <= 0:
            return False

        return self.gain_exp(count * exp_per_click, click_count=count)

    def has_object(self, object_id: str) -> bool:
        return object_id in self.discovered_objects

    def discover_object(self, object_id: str) -> bool:
        if object_id not in OBJECT_IDS or object_id in self.discovered_objects:
            return False

        self.discovered_objects.append(object_id)
        return True

    def all_objects_found(self) -> bool:
        return all(object_id in self.discovered_objects for object_id in OBJECT_IDS)

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
            "aspect": self.aspect,
            "fire_score": self.fire_score,
            "water_score": self.water_score,
            "earth_score": self.earth_score,
            "dark_score": self.dark_score,
            "light_score": self.light_score,
            "discovered_objects": [
                object_id
                for object_id in OBJECT_IDS
                if object_id in self.discovered_objects
            ],
            "fairy_achievement_shown": self.fairy_achievement_shown,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> "PetState":
        if not data:
            return cls()

        level = int(data.get("level", 1))
        current_exp = int(data.get("current_exp", 0))
        raw_discovered = data.get("discovered_objects", [])
        discovered_objects: list[str] = []
        if isinstance(raw_discovered, list):
            for object_id in OBJECT_IDS:
                if object_id in raw_discovered:
                    discovered_objects.append(object_id)

        state = cls(
            total_clicks=int(data.get("total_clicks", 0)),
            total_exp=int(data.get("total_exp", 0)),
            level=max(1, level),
            current_exp=max(0, current_exp),
            next_level_exp=exp_needed_for_level(max(1, level)),
            form=str(data.get("form", form_for_level(max(1, level)))),
            branch=str(data.get("branch", "base")),
            aspect=str(data.get("aspect", "base")),
            fire_score=max(0, int(data.get("fire_score", data.get("game_score", 0)))),
            water_score=max(0, int(data.get("water_score", data.get("engineer_score", 0)))),
            earth_score=max(
                0,
                int(
                    data.get(
                        "earth_score",
                        int(data.get("office_score", 0)) + int(data.get("rage_score", 0)),
                    )
                ),
            ),
            dark_score=max(0, int(data.get("dark_score", 0))),
            light_score=max(0, int(data.get("light_score", 0))),
            discovered_objects=discovered_objects,
            fairy_achievement_shown=bool(data.get("fairy_achievement_shown", False)),
        )
        state.next_level_exp = max(1, state.next_level_exp)
        state._refresh_progression()
        return state
