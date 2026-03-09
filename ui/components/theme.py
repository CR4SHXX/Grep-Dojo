"""GrepDojo theme colours and text styles."""
import flet as ft

# Colors
BG_DARK = "#0d1117"
BG_PANEL = "#161b22"
BG_INPUT = "#21262d"
ACCENT_GREEN = "#39d353"
ACCENT_CYAN = "#58a6ff"
ACCENT_RED = "#f85149"
ACCENT_YELLOW = "#e3b341"
ACCENT_ORANGE = "#f0883e"
TEXT_PRIMARY = "#c9d1d9"
TEXT_MUTED = "#8b949e"
TEXT_DIM = "#484f58"
BORDER_COLOR = "#30363d"

# Typography helpers
def mono(text: str, color: str = TEXT_PRIMARY, size: int = 13, **kwargs) -> ft.Text:
    return ft.Text(text, font_family="monospace", color=color, size=size, **kwargs)


def label(text: str, color: str = TEXT_MUTED, size: int = 12, **kwargs) -> ft.Text:
    return ft.Text(text, color=color, size=size, **kwargs)


def heading(text: str, color: str = ACCENT_CYAN, size: int = 16, **kwargs) -> ft.Text:
    return ft.Text(text, color=color, size=size, weight=ft.FontWeight.BOLD, **kwargs)
