from __future__ import annotations

import json
from pathlib import Path

from da_pet.state import PetState


def load_state(file_path: Path) -> PetState:
    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return PetState()
    except json.JSONDecodeError:
        return PetState()

    return PetState.from_dict(data)


def save_state(file_path: Path, state: PetState) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as file:
        json.dump(state.to_dict(), file, ensure_ascii=False, indent=2)
