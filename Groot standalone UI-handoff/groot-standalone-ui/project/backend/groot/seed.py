"""Load the editable, fictional demo records from backend/data/*.json."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _load(name: str) -> Any:
    path = DATA_DIR / name
    try:
        with path.open("r", encoding="utf-8") as stream:
            return json.load(stream)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Required demo data file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Demo data file {path.name} is not valid JSON: {exc}") from exc


ORGANIZATION = _load("organization.json")
SOURCES = _load("sources.json")
SUPPLIERS = _load("suppliers.json")
SALES = _load("sales.json")
MANUFACTURERS = _load("manufacturers.json")
ROOM_SEGMENTS = _load("decision_room.json")
DEMO_SCENARIOS = _load("scenarios.json")
HISTORY = _load("history.json")


def _require_list(name: str, value: Any, minimum: int = 1) -> None:
    if not isinstance(value, list) or len(value) < minimum:
        raise RuntimeError(f"Demo data {name} must contain at least {minimum} records.")


for _name, _value, _minimum in (
    ("sources", SOURCES, 1),
    ("suppliers", SUPPLIERS, 2),
    ("sales", SALES, 1),
    ("manufacturers", MANUFACTURERS, 1),
    ("decision_room", ROOM_SEGMENTS, 1),
    ("scenarios", DEMO_SCENARIOS, 1),
):
    _require_list(_name, _value, _minimum)

if not isinstance(ORGANIZATION, dict) or not ORGANIZATION.get("name"):
    raise RuntimeError("organization.json must include the demo organization's name.")
if not isinstance(HISTORY.get("mission"), dict) or not isinstance(HISTORY.get("outcome"), dict) or not isinstance(HISTORY.get("memory_rule"), dict):
    raise RuntimeError("history.json must include one mission, one outcome, and one memory rule.")
