"""GrepDojo constants."""

# AI Model
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_TEMPERATURE_MISSION = 0.6
GEMINI_TEMPERATURE_VALIDATE = 0.1
GEMINI_TEMPERATURE_HINT = 0.4
GEMINI_TEMPERATURE_EXPLAIN = 0.4
GEMINI_MAX_OUTPUT_TOKENS = 4096

# XP / Levels
XP_CORRECT_NO_HINTS = 100
XP_CORRECT_ONE_HINT = 50
XP_CORRECT_TWO_HINTS = 25

LEVEL_THRESHOLDS = [
    (1, 0, 299),
    (2, 300, 699),
    (3, 700, 1199),
    (4, 1200, 1999),
    (5, 2000, float("inf")),
]

MAX_HINTS_PER_MISSION = 2
MAX_COMMAND_HISTORY = 10

# Topics by level group
TOPICS_FUNDAMENTAL = [
    {"name": "Case-insensitive matching", "flags": ["-i"], "category": "fundamental"},
    {"name": "Line numbers", "flags": ["-n"], "category": "fundamental"},
    {"name": "Count matches", "flags": ["-c"], "category": "fundamental"},
    {"name": "Invert match", "flags": ["-v"], "category": "fundamental"},
    {"name": "Whole word match", "flags": ["-w"], "category": "fundamental"},
    {"name": "Multiple patterns", "flags": ["-e"], "category": "fundamental"},
    {"name": "Context lines", "flags": ["-A", "-B", "-C"], "category": "fundamental"},
]

TOPICS_ADVANCED = [
    {"name": "Extended regex", "flags": ["-E"], "category": "advanced"},
    {"name": "Anchors (^ and $)", "flags": ["-E"], "category": "advanced"},
    {"name": "Alternation (foo|bar)", "flags": ["-E"], "category": "advanced"},
    {"name": "Character classes", "flags": ["-E"], "category": "advanced"},
    {"name": "Noise reduction", "flags": ["-v", "-E"], "category": "advanced"},
]

# Difficulty mapping
DIFFICULTY_MAP = {
    1: "Easy",
    2: "Easy",
    3: "Medium",
    4: "Hard",
    5: "Expert",
}

# UI
APP_TITLE = "GrepDojo"
APP_WIDTH = 1200
APP_HEIGHT = 780
TERMINAL_FONT = "monospace"
