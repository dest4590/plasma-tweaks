# SPDX-License-Identifier: GPL-2.0-or-later
"""Interactive patch selection for a terminal."""

import curses

from package_catalog import FEATURE_ORDER

DESCRIPTIONS = {
    "tray": "Compact system tray",
    "tray-hover": "Open the tray overflow on hover",
    "microphone": "Microphone indicators and mute controls",
    "launcher": "Icon-only favorites and Meta+number shortcuts",
}


def select_patches(state: dict, restart: bool) -> tuple[set[str], bool] | None:
    screen = None
    try:
        screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        screen.keypad(True)
        return _menu(screen, state, restart)
    except KeyboardInterrupt:
        return None
    except curses.error as error:
        raise ValueError(
            "Could not open the patch menu. Specify a command or use a compatible terminal."
        ) from error
    finally:
        if screen is not None:
            try:
                screen.keypad(False)
                curses.nocbreak()
                curses.echo()
            finally:
                curses.endwin()


def _menu(screen, state: dict, restart: bool) -> tuple[set[str], bool] | None:
    selected = set(state["desired"])
    active = set(state["active"])
    disabled = {
        feature
        for package in state["disabled"].values()
        for feature in package["features"]
    }
    cursor = 0

    while True:
        screen.erase()
        height, width = screen.getmaxyx()

        def draw(row: int, text: str) -> None:
            if row < height and width > 1:
                screen.addnstr(row, 0, text, width - 1)

        draw(0, "Plasma Tweaks")
        for index, name in enumerate(FEATURE_ORDER):
            mark = "x" if name in selected else " "
            status = (
                "disabled"
                if name in disabled
                else "active" if name in active else "inactive"
            )
            pointer = ">" if index == cursor else " "
            draw(
                index + 2,
                f"{pointer} [{mark}] {name:<11} {status:<8}  {DESCRIPTIONS[name]}",
            )

        footer = len(FEATURE_ORDER) + 3
        draw(footer, f"Restart Plasma after applying: {'yes' if restart else 'no'}")
        draw(
            footer + 1,
            "Up/Down Move   Space Toggle   Enter Apply   R Restart   Q Cancel",
        )
        screen.refresh()

        key = screen.getch()
        if key in (curses.KEY_UP, ord("k")):
            cursor = (cursor - 1) % len(FEATURE_ORDER)
        elif key in (curses.KEY_DOWN, ord("j")):
            cursor = (cursor + 1) % len(FEATURE_ORDER)
        elif key == ord(" "):
            selected.symmetric_difference_update((FEATURE_ORDER[cursor],))
        elif key in (10, 13, curses.KEY_ENTER):
            return selected, restart
        elif key in (ord("r"), ord("R")):
            restart = not restart
        elif key in (27, ord("q"), ord("Q")):
            return None
