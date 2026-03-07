"""GrepDojo – entry point."""
import flet as ft

from ui.app import GrepDojoApp


def main(page: ft.Page) -> None:
    GrepDojoApp(page)


if __name__ == "__main__":
    ft.app(target=main)
