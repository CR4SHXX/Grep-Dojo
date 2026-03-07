"""GrepDojo TypedDict models."""
from typing import List, TypedDict


class MissionRequirements(TypedDict):
    must_use_flags: List[str]
    must_not_use: List[str]
    must_start_with: str


class MissionData(TypedDict):
    id: str
    title: str
    case_context: str
    dataset_name: str
    time_window: str
    task: str
    difficulty: str
    topic_category: str
    requirements: MissionRequirements
    log_excerpt: List[str]


class ValidationResult(TypedDict):
    correct: bool
    feedback: str
    detected_flags: List[str]
    missing_flags: List[str]
    matched_line_numbers: List[int]
    matched_lines: List[str]


class ProgressData(TypedDict):
    xp: int
    level: int
    last_topic_index: int
    missions_completed: int
