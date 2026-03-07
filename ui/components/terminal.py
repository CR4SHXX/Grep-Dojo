"""GrepDojo terminal component."""
import flet as ft

from ui.components.theme import (
    ACCENT_CYAN,
    ACCENT_GREEN,
    ACCENT_RED,
    ACCENT_YELLOW,
    BG_DARK,
    BG_INPUT,
    BORDER_COLOR,
    TEXT_MUTED,
    TEXT_PRIMARY,
    mono,
)


class TerminalPanel(ft.Column):
    """Left-panel simulated terminal with scrollable output and command input."""

    PROMPT = "grepdojo $ "

    def __init__(self, on_command, **kwargs):
        super().__init__(**kwargs)

        self._on_command = on_command
        self._history: list[str] = []
        self._history_pos: int = -1

        # Output area
        self._output = ft.ListView(
            expand=True,
            spacing=0,
            padding=ft.padding.all(8),
            auto_scroll=True,
        )

        # Loading ring
        self._loading = ft.ProgressRing(
            width=16,
            height=16,
            stroke_width=2,
            color=ACCENT_CYAN,
            visible=False,
        )

        # Command input
        self._input = ft.TextField(
            hint_text="Type a command...",
            hint_style=ft.TextStyle(color=TEXT_MUTED, font_family="monospace"),
            text_style=ft.TextStyle(color=ACCENT_GREEN, font_family="monospace", size=13),
            border=ft.InputBorder.NONE,
            expand=True,
            focused_border_color="transparent",
            cursor_color=ACCENT_GREEN,
            on_submit=self._handle_submit,
            on_change=self._handle_key,
        )

        # Build layout
        self.expand = True
        self.spacing = 0

        self.controls = [
            # Terminal output area
            ft.Container(
                content=self._output,
                expand=True,
                bgcolor=BG_DARK,
                border_radius=ft.border_radius.only(top_left=6, top_right=6),
            ),
            # Divider
            ft.Divider(height=1, color=BORDER_COLOR),
            # Input row
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(
                            self.PROMPT,
                            font_family="monospace",
                            color=ACCENT_GREEN,
                            size=13,
                        ),
                        self._input,
                        self._loading,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=BG_INPUT,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=ft.border_radius.only(bottom_left=6, bottom_right=6),
            ),
        ]

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def print_line(self, text: str, color: str = TEXT_PRIMARY, italic: bool = False) -> None:
        style = ft.TextStyle(
            font_family="monospace",
            italic=italic,
        )
        self._output.controls.append(
            ft.Text(
                text,
                color=color,
                size=13,
                style=style,
                selectable=True,
                no_wrap=False,
            )
        )
        self._output.update()

    def print_blank(self) -> None:
        self.print_line("")

    def print_command(self, cmd: str) -> None:
        self.print_line(f"{self.PROMPT}{cmd}", color=ACCENT_GREEN)

    def print_success(self, text: str) -> None:
        self.print_line(text, color=ACCENT_GREEN)

    def print_error(self, text: str) -> None:
        self.print_line(text, color=ACCENT_RED)

    def print_info(self, text: str) -> None:
        self.print_line(text, color=ACCENT_CYAN)

    def print_warning(self, text: str) -> None:
        self.print_line(text, color=ACCENT_YELLOW)

    def clear(self) -> None:
        self._output.controls.clear()
        self._output.update()

    def set_loading(self, loading: bool) -> None:
        self._loading.visible = loading
        self._input.disabled = loading
        self._loading.update()
        self._input.update()

    def focus_input(self) -> None:
        self._input.focus()

    def print_banner(self) -> None:
        self.print_line("╔══════════════════════════════════════════════════════╗", color=ACCENT_CYAN)
        self.print_line("║            GrepDojo  —  SOC grep trainer             ║", color=ACCENT_CYAN)
        self.print_line("╚══════════════════════════════════════════════════════╝", color=ACCENT_CYAN)
        self.print_blank()
        self.print_line("Type  help  for available commands.", color=TEXT_MUTED)
        self.print_line("Use the Mission Control panel to generate your first mission.", color=TEXT_MUTED)
        self.print_blank()

    def print_help(self) -> None:
        self.print_blank()
        self.print_line("─── Available commands ───────────────────────────────", color=ACCENT_CYAN)
        self.print_line("  grep <options> <pattern>  Run a grep command (main gameplay)", color=TEXT_PRIMARY)
        self.print_line("  help                      Show this help text", color=TEXT_PRIMARY)
        self.print_line("  clear                     Clear the terminal", color=TEXT_PRIMARY)
        self.print_line("  status                    Show XP, level, and missions completed", color=TEXT_PRIMARY)
        self.print_line("  mission                   Reprint current mission details", color=TEXT_PRIMARY)
        self.print_blank()
        self.print_line("─── Grep quick reference ─────────────────────────────", color=ACCENT_CYAN)
        self.print_line("  -i   Case-insensitive    -n   Show line numbers", color=TEXT_MUTED)
        self.print_line("  -c   Count matches       -v   Invert match", color=TEXT_MUTED)
        self.print_line("  -w   Whole word          -e   Multiple patterns", color=TEXT_MUTED)
        self.print_line("  -A N After context       -B N Before context   -C N Both", color=TEXT_MUTED)
        self.print_line("  -E   Extended regex      -F   Fixed strings", color=TEXT_MUTED)
        self.print_blank()
        self.print_line("RULES: Single grep command only. No pipes. No awk/sed.", color=ACCENT_YELLOW)
        self.print_blank()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _handle_submit(self, e: ft.ControlEvent) -> None:
        cmd = self._input.value.strip()
        if not cmd:
            return
        # Add to history
        if not self._history or self._history[-1] != cmd:
            self._history.append(cmd)
            if len(self._history) > 10:
                self._history.pop(0)
        self._history_pos = len(self._history)
        # Clear input
        self._input.value = ""
        self._input.update()
        # Dispatch
        self._on_command(cmd)

    def _handle_key(self, e: ft.ControlEvent) -> None:
        # Up/down arrow history is handled via keyboard event; this fires on every change.
        pass

    def handle_keyboard(self, e: ft.KeyboardEvent) -> None:
        """Call from page key_down handler to support command history."""
        if e.key == "Arrow Up":
            if self._history and self._history_pos > 0:
                self._history_pos -= 1
                self._input.value = self._history[self._history_pos]
                self._input.update()
        elif e.key == "Arrow Down":
            if self._history_pos < len(self._history) - 1:
                self._history_pos += 1
                self._input.value = self._history[self._history_pos]
                self._input.update()
            elif self._history_pos == len(self._history) - 1:
                self._history_pos = len(self._history)
                self._input.value = ""
                self._input.update()
