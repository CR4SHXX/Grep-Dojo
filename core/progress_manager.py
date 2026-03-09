"""GrepDojo progress manager – load/save XP and level data."""
import json
import os
from typing import Optional

from config.constants import LEVEL_THRESHOLDS
from config.settings import PROGRESS_FILE
from models.types import ProgressData
from utils.logger import get_logger

log = get_logger(__name__)

DEFAULT_PROGRESS: ProgressData = {
    "xp": 0,
    "level": 1,
    "last_topic_index": -1,
    "missions_completed": 0,
}


def load_progress() -> ProgressData:
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Ensure all keys present
            progress: ProgressData = {**DEFAULT_PROGRESS, **data}  # type: ignore[misc]
            log.info("Progress loaded: %s", progress)
            return progress
        except Exception as exc:
            log.warning("Failed to load progress: %s", exc)
    return dict(DEFAULT_PROGRESS)  # type: ignore[return-value]


def save_progress(progress: ProgressData) -> None:
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=2)
        log.info("Progress saved: %s", progress)
    except Exception as exc:
        log.error("Failed to save progress: %s", exc)


def compute_level(xp: int) -> int:
    for level, low, high in LEVEL_THRESHOLDS:
        if low <= xp <= high:
            return level
    return 5


def add_xp(progress: ProgressData, amount: int) -> tuple[ProgressData, bool]:
    """Add XP, recompute level. Returns (updated_progress, leveled_up)."""
    old_level = progress["level"]
    progress["xp"] += amount
    new_level = compute_level(progress["xp"])
    progress["level"] = new_level
    leveled_up = new_level > old_level
    save_progress(progress)
    return progress, leveled_up
