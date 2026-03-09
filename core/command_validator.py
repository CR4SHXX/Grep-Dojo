"""GrepDojo command validator – strict AI-based grading with deterministic verification."""
import json
from typing import Optional, Tuple

from core.ai_service import AIService
from models.types import MissionData, ValidationResult
from utils.logger import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a strict SOC mentor and grep exam proctor.
You MUST output strict JSON only — no markdown, no explanation, no code fences.
Your job is to grade a student's grep command against a mission."""

USER_PROMPT_TEMPLATE = """Grade the following grep command against the mission.

MISSION:
{mission_json}

USER COMMAND: {command}

LOG EXCERPT (1-indexed, this is ground truth):
{indexed_excerpt}

OUTPUT a JSON object with EXACTLY these keys:
{{
  "correct": <true or false>,
  "feedback": "<concise feedback sentence>",
  "detected_flags": ["<flags found in command>"],
  "missing_flags": ["<required flags not in command>"],
  "matched_line_numbers": [<1-based line numbers that the command matches in the excerpt>],
  "matched_lines": ["<exact text of those lines from the excerpt>"]
}}

STRICT RULES:
1. If the command contains a pipe character `|` (except inside a regex pattern in -e/-E): mark correct=false, feedback="Pipes are not allowed. Use a single grep command."
2. If the command does not start with "grep": mark correct=false, feedback="Command must start with grep."
3. If the command uses tools other than grep (awk, sed, cut, etc.): mark correct=false.
4. Check that all flags in requirements.must_use_flags are present in the command.
5. matched_line_numbers and matched_lines MUST correspond to actual lines from the log_excerpt.
   - matched_line_numbers are 1-based indices into the log_excerpt array.
   - matched_lines[i] MUST equal log_excerpt[matched_line_numbers[i] - 1] EXACTLY.
6. If the command would produce zero matches but matches are expected: mark correct=false.
7. If correct=true but a minor improvement exists (e.g., could use -F for fixed-string), you MAY note it in feedback.
8. Do NOT invent lines. Only reference lines that actually exist in the log_excerpt.
"""


def _build_indexed_excerpt(log_excerpt: list) -> str:
    lines = []
    for i, line in enumerate(log_excerpt, start=1):
        lines.append(f"{i:3d}: {line}")
    return "\n".join(lines)


def _has_pipe_outside_pattern(command: str) -> bool:
    """Detect pipe character outside of quoted/pattern context (simplified check)."""
    # Check for unquoted pipe: look for | not inside single or double quotes
    in_single = False
    in_double = False
    i = 0
    while i < len(command):
        c = command[i]
        if c == "'" and not in_double:
            in_single = not in_single
        elif c == '"' and not in_single:
            in_double = not in_double
        elif c == "|" and not in_single and not in_double:
            return True
        i += 1
    return False


def verify_validation_evidence(
    mission: MissionData, result: ValidationResult
) -> Tuple[bool, str]:
    """
    Deterministically verify that AI's matched_lines match excerpt at stated positions.
    Returns (ok, reason).
    """
    excerpt = mission.get("log_excerpt", [])
    numbers = result.get("matched_line_numbers", [])
    lines = result.get("matched_lines", [])

    if len(numbers) != len(lines):
        return False, f"matched_line_numbers length ({len(numbers)}) != matched_lines length ({len(lines)})"

    for i, (num, line) in enumerate(zip(numbers, lines)):
        if not isinstance(num, int) or num < 1 or num > len(excerpt):
            return False, f"matched_line_numbers[{i}]={num} is out of range 1..{len(excerpt)}"
        expected = excerpt[num - 1]
        if line != expected:
            return (
                False,
                f"matched_lines[{i}] does not match excerpt line {num}.\n"
                f"  Expected: {expected!r}\n"
                f"  Got:      {line!r}",
            )
    return True, ""


def validate_command(
    ai: AIService,
    mission: MissionData,
    command: str,
) -> ValidationResult:
    """
    Validate user command against mission.
    Performs deterministic evidence verification with one AI retry if needed.
    """
    # Fast-path checks
    stripped = command.strip()

    if not stripped.startswith("grep"):
        return _make_result(
            correct=False,
            feedback="Command must start with 'grep'.",
            detected_flags=[],
            missing_flags=mission["requirements"]["must_use_flags"],
        )

    if _has_pipe_outside_pattern(stripped):
        return _make_result(
            correct=False,
            feedback="Pipes are not allowed. Use a single grep command only.",
            detected_flags=[],
            missing_flags=mission["requirements"]["must_use_flags"],
        )

    # Build prompts
    indexed_excerpt = _build_indexed_excerpt(mission["log_excerpt"])
    mission_json = json.dumps(
        {
            "title": mission["title"],
            "task": mission["task"],
            "requirements": mission["requirements"],
        },
        indent=2,
    )
    user_prompt = USER_PROMPT_TEMPLATE.format(
        mission_json=mission_json,
        command=stripped,
        indexed_excerpt=indexed_excerpt,
    )

    log.info("Validating command: %s", stripped)

    # First AI call
    raw = ai.validate_command(SYSTEM_PROMPT, user_prompt)
    result = _parse_validation_result(raw)

    # Deterministic verification
    ok, reason = verify_validation_evidence(mission, result)
    if not ok:
        log.warning("Evidence verification failed: %s — retrying AI", reason)
        correction = (
            "Your matched_lines must be exact lines from the log_excerpt provided. "
            "You invented lines that do not exist. Correct your response. "
            "Only reference lines that appear verbatim in the log_excerpt.\n"
            f"Verification failure: {reason}"
        )
        raw2 = ai.validate_command_retry(SYSTEM_PROMPT, user_prompt, correction)
        result = _parse_validation_result(raw2)
        ok2, reason2 = verify_validation_evidence(mission, result)
        if not ok2:
            log.error("Evidence verification failed on retry: %s — treating as invalid", reason2)
            result["correct"] = False
            result["feedback"] = (
                f"Validation could not be completed reliably. {result.get('feedback', '')} "
                "(Evidence mismatch detected — please try again.)"
            )
            result["matched_line_numbers"] = []
            result["matched_lines"] = []

    return result


def _parse_validation_result(raw: dict) -> ValidationResult:
    return {
        "correct": bool(raw.get("correct", False)),
        "feedback": str(raw.get("feedback", "No feedback provided.")),
        "detected_flags": list(raw.get("detected_flags", [])),
        "missing_flags": list(raw.get("missing_flags", [])),
        "matched_line_numbers": [int(n) for n in raw.get("matched_line_numbers", [])],
        "matched_lines": [str(l) for l in raw.get("matched_lines", [])],
    }


def _make_result(
    correct: bool,
    feedback: str,
    detected_flags: list,
    missing_flags: list,
) -> ValidationResult:
    return {
        "correct": correct,
        "feedback": feedback,
        "detected_flags": detected_flags,
        "missing_flags": missing_flags,
        "matched_line_numbers": [],
        "matched_lines": [],
    }


def build_terminal_output(mission: MissionData, result: ValidationResult, command: str) -> list[str]:
    """
    Build terminal output lines from verified matched lines.
    If -n flag is in the command, prefix with line number.
    """
    show_line_numbers = "-n" in command.split()
    output = []
    for num, line in zip(result["matched_line_numbers"], result["matched_lines"]):
        if show_line_numbers:
            output.append(f"{num}:{line}")
        else:
            output.append(line)
    return output


# ---------------------------------------------------------------------------
# Hint and Explain prompts
# ---------------------------------------------------------------------------

HINT_SYSTEM = "You are a SOC training mentor providing one targeted hint for a grep exercise."
HINT_USER_TEMPLATE = """Mission: {mission_title}
Task: {task}
Required flags: {required_flags}
Student command so far: {command}

Provide ONE concise hint about which flag or approach to use next.
Do NOT give the complete final command. Just hint at the next step."""

EXPLAIN_SYSTEM = "You are a SOC training mentor explaining a grep command mistake and providing the correct solution."
EXPLAIN_USER_TEMPLATE = """Mission: {mission_title}
Task: {task}
Required flags: {required_flags}
Student command: {command}
Validation feedback: {feedback}

Explain in 2-3 sentences what is wrong or missing.
Then show the corrected grep command on its own line starting with 'Corrected command:'"""


def get_hint(ai: AIService, mission: MissionData, command: str) -> str:
    user_prompt = HINT_USER_TEMPLATE.format(
        mission_title=mission["title"],
        task=mission["task"],
        required_flags=", ".join(mission["requirements"]["must_use_flags"]),
        command=command or "(nothing entered yet)",
    )
    return ai.get_hint(HINT_SYSTEM, user_prompt)


def get_explanation(ai: AIService, mission: MissionData, command: str, feedback: str) -> str:
    user_prompt = EXPLAIN_USER_TEMPLATE.format(
        mission_title=mission["title"],
        task=mission["task"],
        required_flags=", ".join(mission["requirements"]["must_use_flags"]),
        command=command or "(nothing entered yet)",
        feedback=feedback or "No previous feedback.",
    )
    return ai.get_explanation(EXPLAIN_SYSTEM, user_prompt)
