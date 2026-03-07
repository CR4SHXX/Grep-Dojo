"""GrepDojo mission generator – builds SOC-realistic grep training missions."""
import json
import uuid
from typing import Optional

from config.constants import (
    DIFFICULTY_MAP,
    TOPICS_ADVANCED,
    TOPICS_FUNDAMENTAL,
)
from core.ai_service import AIService
from models.types import MissionData
from utils.logger import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a SOC incident response trainer creating grep command training missions.
You MUST output strict JSON only — no markdown, no explanation, no code fences.
The JSON must be a single object with these exact keys."""

USER_PROMPT_TEMPLATE = """Create a SOC-realistic grep training mission for Level {level} ({difficulty}).
Topic: {topic_name}
Required flags the student MUST use: {required_flags}

Output a JSON object with EXACTLY these keys:
{{
  "id": "<uuid string>",
  "title": "<short mission title>",
  "case_context": "<2-3 sentence SOC ticket description of the incident>",
  "dataset_name": "<filename like auth.log, access.log, syslog, edr.log, etc.>",
  "time_window": "<ISO time range like 2024-01-15T08:00:00Z - 2024-01-15T09:00:00Z>",
  "task": "<one sentence: what the analyst must find using grep>",
  "difficulty": "{difficulty}",
  "topic_category": "{topic_category}",
  "requirements": {{
    "must_use_flags": {must_use_flags_json},
    "must_not_use": [],
    "must_start_with": "grep"
  }},
  "log_excerpt": [
    "<line 1>",
    "<line 2>",
    ... (12 to 25 realistic log lines, mix of matching and non-matching)
  ]
}}

RULES:
- log_excerpt MUST contain 12 to 25 lines of plain text log entries (no JSON, no markdown).
- log_excerpt MUST contain at least 2 matching lines that the correct grep command would find.
- The task MUST be solvable with a single grep command using the required flags.
- Log lines should be realistic auth/web/edr/syslog style text entries.
- The dataset_name should match the log style.
- Do NOT include any text outside the JSON object.
"""


def _pick_topic(level: int, last_topic_index: int) -> tuple[dict, int]:
    """Pick next topic based on current level, cycling through pools."""
    if level <= 3:
        pool = TOPICS_FUNDAMENTAL
    else:
        pool = TOPICS_ADVANCED
    next_index = (last_topic_index + 1) % len(pool)
    return pool[next_index], next_index


def generate_mission(ai: AIService, level: int, last_topic_index: int) -> tuple[MissionData, int]:
    """Generate a new mission. Returns (mission, new_topic_index)."""
    topic, new_topic_index = _pick_topic(level, last_topic_index)
    difficulty = DIFFICULTY_MAP.get(level, "Easy")

    # Build required flags list — for context topics pick one
    required_flags = topic["flags"]
    if topic["name"] == "Context lines":
        required_flags = ["-C"]  # simplify to -C for the mission

    user_prompt = USER_PROMPT_TEMPLATE.format(
        level=level,
        difficulty=difficulty,
        topic_name=topic["name"],
        required_flags=", ".join(required_flags),
        topic_category=topic["category"],
        must_use_flags_json=json.dumps(required_flags),
    )

    log.info("Generating mission: level=%d topic=%s", level, topic["name"])
    raw = ai.generate_mission(SYSTEM_PROMPT, user_prompt)
    mission = _validate_and_fix(raw, level, topic, required_flags)
    return mission, new_topic_index


def _validate_and_fix(raw: dict, level: int, topic: dict, required_flags: list) -> MissionData:
    """Validate the AI response and fill in any missing required fields."""
    difficulty = DIFFICULTY_MAP.get(level, "Easy")

    # Ensure required top-level keys
    mission: MissionData = {
        "id": raw.get("id") or str(uuid.uuid4()),
        "title": raw.get("title") or f"SOC Mission – {topic['name']}",
        "case_context": raw.get("case_context") or "Investigate the log excerpt for suspicious activity.",
        "dataset_name": raw.get("dataset_name") or "auth.log",
        "time_window": raw.get("time_window") or "2024-01-15T08:00:00Z – 2024-01-15T09:00:00Z",
        "task": raw.get("task") or f"Use grep to find relevant entries using {', '.join(required_flags)}.",
        "difficulty": raw.get("difficulty") or difficulty,
        "topic_category": raw.get("topic_category") or topic["category"],
        "requirements": {
            "must_use_flags": required_flags,
            "must_not_use": raw.get("requirements", {}).get("must_not_use", []),
            "must_start_with": "grep",
        },
        "log_excerpt": raw.get("log_excerpt") or [],
    }

    # Validate log excerpt length
    excerpt = mission["log_excerpt"]
    if not isinstance(excerpt, list) or len(excerpt) < 12:
        log.warning("log_excerpt too short (%d lines), mission may be invalid", len(excerpt) if isinstance(excerpt, list) else 0)

    return mission
