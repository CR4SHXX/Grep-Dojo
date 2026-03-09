"""GrepDojo main app controller."""
import json
import os
import threading
from typing import Optional

import flet as ft

from config.constants import (
    APP_TITLE,
    MAX_HINTS_PER_MISSION,
    XP_CORRECT_NO_HINTS,
    XP_CORRECT_ONE_HINT,
    XP_CORRECT_TWO_HINTS,
)
from config.settings import LOCAL_SETTINGS_FILE
from core.ai_service import AIService
from core.command_validator import (
    build_terminal_output,
    get_explanation,
    get_hint,
    validate_command,
)
from core.mission_generator import generate_mission
from core.progress_manager import add_xp, load_progress, save_progress
from models.types import MissionData, ProgressData
from ui.components.mission_panel import MissionPanel
from ui.components.terminal import TerminalPanel
from ui.components.theme import (
    ACCENT_CYAN,
    ACCENT_GREEN,
    ACCENT_RED,
    ACCENT_YELLOW,
    BG_DARK,
    BG_PANEL,
    BORDER_COLOR,
)
from utils.logger import get_logger

log = get_logger(__name__)


class GrepDojoApp:
    """Main application controller. Wires UI components and core logic."""

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self._configure_page()

        # State
        self._ai: Optional[AIService] = None
        self._progress: ProgressData = load_progress()
        self._mission: Optional[MissionData] = None
        self._hints_used: int = 0
        self._last_command: str = ""
        self._last_feedback: str = ""
        self._mission_solved: bool = False

        # Build UI
        self._terminal = TerminalPanel(on_command=self._handle_command)
        self._mission_panel = MissionPanel(
            on_new_mission=self._handle_new_mission,
            on_hint=self._handle_hint,
            on_explain=self._handle_explain,
            on_api_key_set=self._handle_api_key,
        )

        # Layout: 70/30 split
        self.page.add(
            ft.Row(
                controls=[
                    ft.Container(
                        content=self._terminal,
                        expand=7,
                        bgcolor=BG_DARK,
                        border_radius=6,
                        border=ft.border.all(1, BORDER_COLOR),
                        margin=ft.margin.only(right=6),
                    ),
                    ft.Container(
                        content=self._mission_panel,
                        expand=3,
                        bgcolor=BG_PANEL,
                        border_radius=6,
                        border=ft.border.all(1, BORDER_COLOR),
                    ),
                ],
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            )
        )

        # Keyboard handler
        self.page.on_keyboard_event = self._terminal.handle_keyboard

        # Init UI state
        self._terminal.print_banner()
        self._mission_panel.update_xp(
            self._progress["xp"],
            self._progress["level"],
            self._progress["missions_completed"],
        )

        # Try loading saved API key
        saved_key = self._load_saved_api_key()
        if saved_key:
            self._init_ai(saved_key)
        else:
            self._mission_panel.set_ai_ready(False)

    # ------------------------------------------------------------------
    # Page config
    # ------------------------------------------------------------------

    def _configure_page(self) -> None:
        self.page.title = APP_TITLE
        self.page.bgcolor = BG_DARK
        self.page.padding = 12
        self.page.window.width = 1200
        self.page.window.height = 780
        self.page.window.min_width = 900
        self.page.window.min_height = 600
        self.page.fonts = {"monospace": "Courier New"}
        self.page.theme = ft.Theme(font_family="monospace")

    # ------------------------------------------------------------------
    # API Key helpers
    # ------------------------------------------------------------------

    def _load_saved_api_key(self) -> Optional[str]:
        try:
            if os.path.exists(LOCAL_SETTINGS_FILE):
                with open(LOCAL_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("gemini_api_key", "")
        except Exception as exc:
            log.warning("Could not load saved API key: %s", exc)
        return None

    def _save_api_key(self, key: str) -> None:
        try:
            os.makedirs(os.path.dirname(LOCAL_SETTINGS_FILE), exist_ok=True)
            with open(LOCAL_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({"gemini_api_key": key}, f)
        except Exception as exc:
            log.warning("Could not save API key: %s", exc)

    def _init_ai(self, key: str) -> None:
        try:
            self._ai = AIService(key)
            self._save_api_key(key)
            self._mission_panel.set_ai_ready(True)
            self._terminal.print_info("✓ AI service initialised. Use 'New Mission' to start.")
            self._terminal.print_blank()
        except Exception as exc:
            self._ai = None
            self._mission_panel.set_ai_ready(False)
            self._terminal.print_error(f"✗ Failed to init AI: {exc}")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _handle_api_key(self, key: str) -> None:
        self._init_ai(key)

    def _handle_command(self, cmd: str) -> None:
        """Dispatch terminal command."""
        self._terminal.print_command(cmd)

        lower = cmd.strip().lower()
        if lower == "clear":
            self._terminal.clear()
            self._terminal.print_banner()
            return
        if lower == "help":
            self._terminal.print_help()
            return
        if lower == "status":
            self._print_status()
            return
        if lower == "mission":
            self._print_mission()
            return

        # Grep command
        if lower.startswith("grep"):
            self._handle_grep(cmd)
            return

        self._terminal.print_error(f"Unknown command: {cmd}. Type 'help' for usage.")
        self._terminal.print_blank()

    def _handle_grep(self, cmd: str) -> None:
        if not self._ai:
            self._terminal.print_error("✗ AI not initialised. Enter your Gemini API key first.")
            self._terminal.print_blank()
            return
        if not self._mission:
            self._terminal.print_error("✗ No active mission. Click 'New Mission' first.")
            self._terminal.print_blank()
            return
        if self._mission_solved:
            self._terminal.print_warning("Mission already solved. Generate a new mission!")
            self._terminal.print_blank()
            return

        self._last_command = cmd
        self._terminal.set_loading(True)
        self._mission_panel.set_buttons_loading(True)

        def _run():
            try:
                result = validate_command(self._ai, self._mission, cmd)
                output_lines = build_terminal_output(self._mission, result, cmd)

                # Display output
                if output_lines:
                    for line in output_lines:
                        self._terminal.print_line(line)
                else:
                    self._terminal.print_line("(no output)", color="#484f58")

                self._terminal.print_blank()

                if result["correct"]:
                    self._handle_correct(result)
                else:
                    self._last_feedback = result["feedback"]
                    self._terminal.print_error(f"✗  {result['feedback']}")
                    if result["missing_flags"]:
                        self._terminal.print_warning(
                            f"   Missing flags: {', '.join(result['missing_flags'])}"
                        )

                self._terminal.print_blank()
            except Exception as exc:
                log.exception("Grep validation error")
                self._terminal.print_error(f"✗ Error during validation: {exc}")
                self._terminal.print_blank()
            finally:
                self._terminal.set_loading(False)
                self._mission_panel.set_buttons_loading(False)
                self._mission_panel.set_mission_active(True)
                if self._hints_used >= MAX_HINTS_PER_MISSION:
                    self._mission_panel.set_hints_exhausted(True)

        threading.Thread(target=_run, daemon=True).start()

    def _handle_correct(self, result) -> None:
        self._mission_solved = True

        # XP
        if self._hints_used == 0:
            xp = XP_CORRECT_NO_HINTS
        elif self._hints_used == 1:
            xp = XP_CORRECT_ONE_HINT
        else:
            xp = XP_CORRECT_TWO_HINTS

        self._progress, leveled_up = add_xp(self._progress, xp)
        self._progress["missions_completed"] += 1
        save_progress(self._progress)

        self._terminal.print_success(f"✓  {result['feedback']}")
        self._terminal.print_success(f"   +{xp} XP  (hints used: {self._hints_used})")

        if leveled_up:
            self._terminal.print_info(
                f"   🎉 Level up! You are now Level {self._progress['level']}!"
            )

        self._mission_panel.update_xp(
            self._progress["xp"],
            self._progress["level"],
            self._progress["missions_completed"],
        )
        self._mission_panel.set_hints_exhausted(True)

    def _handle_new_mission(self) -> None:
        if not self._ai:
            self._terminal.print_error("✗ AI not initialised.")
            return

        self._terminal.set_loading(True)
        self._mission_panel.set_buttons_loading(True)

        def _run():
            try:
                mission, new_topic_idx = generate_mission(
                    self._ai,
                    self._progress["level"],
                    self._progress["last_topic_index"],
                )
                self._mission = mission
                self._hints_used = 0
                self._last_command = ""
                self._last_feedback = ""
                self._mission_solved = False

                self._progress["last_topic_index"] = new_topic_idx
                save_progress(self._progress)

                self._mission_panel.update_mission(mission)
                self._mission_panel.update_hint_counter(0, MAX_HINTS_PER_MISSION)
                self._mission_panel.set_mission_active(True)
                self._mission_panel.set_hints_exhausted(False)

                self._terminal.print_blank()
                self._terminal.print_info("══════════ NEW MISSION ══════════")
                self._print_mission()
            except Exception as exc:
                log.exception("Mission generation error")
                self._terminal.print_error(f"✗ Failed to generate mission: {exc}")
                self._terminal.print_blank()
            finally:
                self._terminal.set_loading(False)
                self._mission_panel.set_buttons_loading(False)

        threading.Thread(target=_run, daemon=True).start()

    def _handle_hint(self) -> None:
        if not self._ai or not self._mission:
            return
        if self._hints_used >= MAX_HINTS_PER_MISSION:
            self._terminal.print_warning("No more hints available for this mission.")
            return

        self._hints_used += 1
        self._mission_panel.update_hint_counter(self._hints_used, MAX_HINTS_PER_MISSION)
        if self._hints_used >= MAX_HINTS_PER_MISSION:
            self._mission_panel.set_hints_exhausted(True)

        self._terminal.set_loading(True)
        self._mission_panel.set_buttons_loading(True)

        def _run():
            try:
                hint = get_hint(self._ai, self._mission, self._last_command)
                self._terminal.print_blank()
                self._terminal.print_warning(f"💡 HINT ({self._hints_used}/{MAX_HINTS_PER_MISSION}):")
                for line in hint.split("\n"):
                    if line.strip():
                        self._terminal.print_warning(f"   {line}")
                self._terminal.print_blank()
            except Exception as exc:
                log.exception("Hint error")
                self._terminal.print_error(f"✗ Hint error: {exc}")
            finally:
                self._terminal.set_loading(False)
                self._mission_panel.set_buttons_loading(False)
                self._mission_panel.set_mission_active(True)
                if self._hints_used >= MAX_HINTS_PER_MISSION:
                    self._mission_panel.set_hints_exhausted(True)

        threading.Thread(target=_run, daemon=True).start()

    def _handle_explain(self) -> None:
        if not self._ai or not self._mission:
            return

        self._terminal.set_loading(True)
        self._mission_panel.set_buttons_loading(True)

        def _run():
            try:
                explanation = get_explanation(
                    self._ai,
                    self._mission,
                    self._last_command,
                    self._last_feedback,
                )
                self._terminal.print_blank()
                self._terminal.print_info("🔍 EXPLANATION:")
                for line in explanation.split("\n"):
                    if line.strip():
                        self._terminal.print_info(f"   {line}")
                self._terminal.print_blank()
            except Exception as exc:
                log.exception("Explain error")
                self._terminal.print_error(f"✗ Explain error: {exc}")
            finally:
                self._terminal.set_loading(False)
                self._mission_panel.set_buttons_loading(False)
                self._mission_panel.set_mission_active(True)
                if self._hints_used >= MAX_HINTS_PER_MISSION:
                    self._mission_panel.set_hints_exhausted(True)

        threading.Thread(target=_run, daemon=True).start()

    # ------------------------------------------------------------------
    # Terminal print helpers
    # ------------------------------------------------------------------

    def _print_status(self) -> None:
        p = self._progress
        self._terminal.print_blank()
        self._terminal.print_info("─── Status ──────────────────────────")
        self._terminal.print_line(f"  XP              : {p['xp']}", color=ACCENT_GREEN)
        self._terminal.print_line(f"  Level           : {p['level']}", color=ACCENT_CYAN)
        self._terminal.print_line(f"  Missions done   : {p['missions_completed']}")
        self._terminal.print_blank()

    def _print_mission(self) -> None:
        if not self._mission:
            self._terminal.print_warning("No active mission. Click 'New Mission'.")
            self._terminal.print_blank()
            return
        m = self._mission
        self._terminal.print_blank()
        self._terminal.print_info(f"  📋 {m['title']}")
        self._terminal.print_line(f"  Dataset : {m['dataset_name']} | {m['time_window']}")
        self._terminal.print_line(f"  Context : {m['case_context']}")
        self._terminal.print_blank()
        self._terminal.print_warning(f"  TASK: {m['task']}")
        reqs = m.get("requirements", {})
        if reqs.get("must_use_flags"):
            self._terminal.print_line(
                f"  Required flags : {' '.join(reqs['must_use_flags'])}"
            )
        if reqs.get("must_not_use"):
            self._terminal.print_line(
                f"  Forbidden      : {' '.join(reqs['must_not_use'])}"
            )
        self._terminal.print_blank()
        self._terminal.print_line("  LOG EXCERPT (for reference):", color="#484f58")
        excerpt = m.get("log_excerpt", [])
        for i, line in enumerate(excerpt, start=1):
            self._terminal.print_line(f"  {i:2d}: {line}", color="#484f58")
        self._terminal.print_blank()
