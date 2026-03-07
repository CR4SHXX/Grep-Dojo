"""GrepDojo mission control panel (right side)."""
import flet as ft

from ui.components.theme import (
    ACCENT_CYAN,
    ACCENT_GREEN,
    ACCENT_ORANGE,
    ACCENT_RED,
    ACCENT_YELLOW,
    BG_INPUT,
    BG_PANEL,
    BORDER_COLOR,
    TEXT_MUTED,
    TEXT_PRIMARY,
)


class MissionPanel(ft.Column):
    """Right panel: XP/Level, mission info, action buttons."""

    def __init__(
        self,
        on_new_mission,
        on_hint,
        on_explain,
        on_api_key_set,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._on_new_mission = on_new_mission
        self._on_hint = on_hint
        self._on_explain = on_explain
        self._on_api_key_set = on_api_key_set

        # --- XP bar ---
        self._xp_text = ft.Text("XP: 0", color=ACCENT_GREEN, size=13, weight=ft.FontWeight.BOLD)
        self._level_text = ft.Text("Level 1", color=ACCENT_CYAN, size=13, weight=ft.FontWeight.BOLD)
        self._missions_text = ft.Text("Missions: 0", color=TEXT_MUTED, size=12)

        # --- API Key section ---
        self._api_key_field = ft.TextField(
            label="Gemini API Key",
            password=True,
            can_reveal_password=True,
            hint_text="Paste your API key here",
            text_style=ft.TextStyle(color=TEXT_PRIMARY, size=12),
            label_style=ft.TextStyle(color=TEXT_MUTED, size=11),
            border_color=BORDER_COLOR,
            focused_border_color=ACCENT_CYAN,
            bgcolor=BG_INPUT,
        )
        self._api_key_btn = ft.ElevatedButton(
            "Set API Key",
            on_click=self._handle_api_key,
            bgcolor=ACCENT_CYAN,
            color="#000000",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)),
        )
        self._api_status = ft.Text("⚠ API key not set", color=ACCENT_YELLOW, size=11)
        self._api_section = ft.Column(
            [
                self._api_status,
                self._api_key_field,
                self._api_key_btn,
            ],
            spacing=6,
            visible=True,
        )

        # --- Mission info ---
        self._mission_title = ft.Text(
            "No mission loaded", color=ACCENT_CYAN, size=14, weight=ft.FontWeight.BOLD, selectable=True
        )
        self._mission_difficulty = ft.Text("", color=TEXT_MUTED, size=11)
        self._mission_context = ft.Text(
            "Generate a mission to begin.", color=TEXT_PRIMARY, size=12, selectable=True
        )
        self._mission_dataset = ft.Text("", color=TEXT_MUTED, size=11, selectable=True)
        self._mission_time = ft.Text("", color=TEXT_MUTED, size=11, selectable=True)
        self._mission_task = ft.Text("", color=ACCENT_YELLOW, size=12, weight=ft.FontWeight.W_500, selectable=True)

        # Required flags chips
        self._flags_row = ft.Row(wrap=True, spacing=4)

        # Hint counter
        self._hint_counter = ft.Text("Hints used: 0 / 2", color=TEXT_MUTED, size=11)

        # --- Buttons ---
        self._btn_new_mission = ft.ElevatedButton(
            "⚡  New Mission",
            on_click=lambda _: self._on_new_mission(),
            bgcolor=ACCENT_GREEN,
            color="#000000",
            expand=True,
            disabled=True,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)),
        )
        self._btn_hint = ft.OutlinedButton(
            "💡  Hint",
            on_click=lambda _: self._on_hint(),
            expand=True,
            disabled=True,
            style=ft.ButtonStyle(
                side=ft.BorderSide(1, ACCENT_YELLOW),
                color=ACCENT_YELLOW,
                shape=ft.RoundedRectangleBorder(radius=4),
            ),
        )
        self._btn_explain = ft.OutlinedButton(
            "🔍  Explain",
            on_click=lambda _: self._on_explain(),
            expand=True,
            disabled=True,
            style=ft.ButtonStyle(
                side=ft.BorderSide(1, ACCENT_ORANGE),
                color=ACCENT_ORANGE,
                shape=ft.RoundedRectangleBorder(radius=4),
            ),
        )

        # Build layout
        self.expand = True
        self.spacing = 0
        self.scroll = ft.ScrollMode.AUTO

        self.controls = [
            # XP / Level
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [self._xp_text, ft.Text("•", color=TEXT_MUTED), self._level_text],
                            spacing=8,
                        ),
                        self._missions_text,
                    ],
                    spacing=4,
                ),
                bgcolor=BG_PANEL,
                padding=ft.padding.all(12),
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
            ),
            # API Key
            ft.Container(
                content=self._api_section,
                bgcolor=BG_PANEL,
                padding=ft.padding.all(12),
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
            ),
            # Mission info
            ft.Container(
                content=ft.Column(
                    [
                        self._mission_title,
                        ft.Row([self._mission_difficulty], spacing=4),
                        ft.Divider(height=1, color=BORDER_COLOR),
                        ft.Text("CONTEXT", color=TEXT_MUTED, size=10, weight=ft.FontWeight.BOLD),
                        self._mission_context,
                        ft.Text("DATASET", color=TEXT_MUTED, size=10, weight=ft.FontWeight.BOLD),
                        self._mission_dataset,
                        ft.Text("TIME WINDOW", color=TEXT_MUTED, size=10, weight=ft.FontWeight.BOLD),
                        self._mission_time,
                        ft.Divider(height=1, color=BORDER_COLOR),
                        ft.Text("TASK", color=TEXT_MUTED, size=10, weight=ft.FontWeight.BOLD),
                        self._mission_task,
                        ft.Divider(height=1, color=BORDER_COLOR),
                        ft.Text("REQUIRED FLAGS", color=TEXT_MUTED, size=10, weight=ft.FontWeight.BOLD),
                        self._flags_row,
                        self._hint_counter,
                    ],
                    spacing=6,
                ),
                bgcolor=BG_PANEL,
                padding=ft.padding.all(12),
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
                expand=True,
            ),
            # Buttons
            ft.Container(
                content=ft.Column(
                    [
                        self._btn_new_mission,
                        ft.Row([self._btn_hint, self._btn_explain], spacing=8),
                    ],
                    spacing=8,
                ),
                bgcolor=BG_PANEL,
                padding=ft.padding.all(12),
            ),
        ]

    # ------------------------------------------------------------------
    # Public update methods
    # ------------------------------------------------------------------

    def update_xp(self, xp: int, level: int, missions: int) -> None:
        self._xp_text.value = f"XP: {xp}"
        self._level_text.value = f"Level {level}"
        self._missions_text.value = f"Missions: {missions}"
        self._xp_text.update()
        self._level_text.update()
        self._missions_text.update()

    def update_mission(self, mission: dict) -> None:
        self._mission_title.value = mission.get("title", "")
        diff = mission.get("difficulty", "")
        topic = mission.get("topic_category", "")
        self._mission_difficulty.value = f"{diff}  •  {topic}"
        self._mission_context.value = mission.get("case_context", "")
        self._mission_dataset.value = f"📁  {mission.get('dataset_name', '')}"
        self._mission_time.value = f"🕐  {mission.get('time_window', '')}"
        self._mission_task.value = mission.get("task", "")

        # Flags
        self._flags_row.controls.clear()
        reqs = mission.get("requirements", {})
        for flag in reqs.get("must_use_flags", []):
            self._flags_row.controls.append(
                ft.Container(
                    content=ft.Text(flag, color="#000000", size=11, font_family="monospace"),
                    bgcolor=ACCENT_CYAN,
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    border_radius=4,
                )
            )
        for flag in reqs.get("must_not_use", []):
            self._flags_row.controls.append(
                ft.Container(
                    content=ft.Text(f"✗ {flag}", color="#000000", size=11, font_family="monospace"),
                    bgcolor=ACCENT_RED,
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    border_radius=4,
                )
            )

        self._mission_title.update()
        self._mission_difficulty.update()
        self._mission_context.update()
        self._mission_dataset.update()
        self._mission_time.update()
        self._mission_task.update()
        self._flags_row.update()

    def update_hint_counter(self, hints_used: int, max_hints: int) -> None:
        self._hint_counter.value = f"Hints used: {hints_used} / {max_hints}"
        self._hint_counter.update()

    def set_ai_ready(self, ready: bool) -> None:
        if ready:
            self._api_status.value = "✓ AI ready"
            self._api_status.color = ACCENT_GREEN
            self._api_section.visible = False
            self._btn_new_mission.disabled = False
        else:
            self._api_status.value = "⚠ API key not set"
            self._api_status.color = ACCENT_YELLOW
            self._api_section.visible = True
            self._btn_new_mission.disabled = True
        self._api_status.update()
        self._api_section.update()
        self._btn_new_mission.update()

    def set_mission_active(self, active: bool) -> None:
        self._btn_hint.disabled = not active
        self._btn_explain.disabled = not active
        self._btn_hint.update()
        self._btn_explain.update()

    def set_hints_exhausted(self, exhausted: bool) -> None:
        self._btn_hint.disabled = exhausted
        self._btn_hint.update()

    def set_buttons_loading(self, loading: bool) -> None:
        self._btn_new_mission.disabled = loading
        self._btn_hint.disabled = loading
        self._btn_explain.disabled = loading
        self._btn_new_mission.update()
        self._btn_hint.update()
        self._btn_explain.update()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _handle_api_key(self, e: ft.ControlEvent) -> None:
        key = self._api_key_field.value.strip()
        if key:
            self._on_api_key_set(key)
