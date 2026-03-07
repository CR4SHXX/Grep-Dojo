# GrepDojo 🔍

A **desktop training app** that teaches SOC analysts to master the `grep` command through AI-generated, SOC-realistic missions. Built with **Python + Flet** and powered by **Google Gemini**.

---

## Features

- 🎯 **AI-generated SOC missions** – each mission is a realistic incident-response ticket with a log excerpt
- 🤖 **Strict AI grading** – Gemini validates your grep command and checks evidence against the log excerpt deterministically
- 💡 **Hints and explanations** – up to 2 hints per mission; detailed explanation on demand
- 📈 **XP and levels** – earn XP for correct answers, level up through 5 tiers
- 🖥️ **Split terminal UI** – simulated terminal on the left, Mission Control panel on the right

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/CR4SHXX/Grep-Dojo.git
cd Grep-Dojo

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Get a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create a project and generate an API key
3. Paste it into the **API Key** field in the app (right panel)

The key is saved to `config/local_settings.json` (git-ignored) so you only need to enter it once.

## Run

```bash
python main.py
```

## Gameplay Commands

| Command | Description |
|---------|-------------|
| `grep <options> <pattern>` | Submit your grep answer |
| `help` | Show available commands and grep tips |
| `clear` | Clear the terminal |
| `status` | Show your XP, level, and missions completed |
| `mission` | Reprint the current mission details |

**Up/Down arrows** cycle through command history (last 10 commands).

## Strict Mode Rules

- Commands **must start with `grep`**
- **No pipes** allowed (`|` outside of regex patterns)
- **No other tools** (awk, sed, cut, etc.)
- Required flags listed in the mission **must** be present
- The AI verifies that matched lines are real lines from the log excerpt

## XP & Levels

| XP Earned | Condition |
|-----------|-----------|
| 100 XP | Correct on first try (0 hints) |
| 50 XP | Correct with 1 hint |
| 25 XP | Correct with 2 hints |

| Level | XP Range |
|-------|----------|
| 1 | 0–299 |
| 2 | 300–699 |
| 3 | 700–1199 |
| 4 | 1200–1999 |
| 5 | 2000+ |

## Project Structure

```
GrepDojo/
  main.py                    # Entry point
  requirements.txt
  README.md
  .gitignore
  config/
    constants.py             # XP thresholds, topics, AI model settings
    settings.py              # File paths
  core/
    ai_service.py            # Gemini API wrapper
    mission_generator.py     # Mission generation
    command_validator.py     # Validation + deterministic evidence check
    progress_manager.py      # Load/save XP progress
  models/
    types.py                 # TypedDicts
  ui/
    app.py                   # GrepDojoApp controller
    components/
      terminal.py            # Terminal panel
      mission_panel.py       # Mission Control panel
      theme.py               # Colors and styles
  utils/
    logger.py                # Logging setup
```
