#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""QML/JS syntax validation helpers for staged plasma-tweaks packages."""
from pathlib import Path
import shutil
import subprocess


def find_qmlformat() -> str | None:
    for name in ("qmlformat6", "qmlformat-qt6", "qmlformat"):
        found = shutil.which(name)
        if found:
            return found
    for candidate in ("/usr/lib/qt6/bin/qmlformat", "/usr/lib64/qt6/bin/qmlformat"):
        if Path(candidate).is_file():
            return candidate
    return None


def check_balanced_delimiters(text: str, rel_path: str, pkg_name: str) -> None:
    pairs = {"{": "}", "(": ")", "[": "]"}
    closing = {v: k for k, v in pairs.items()}
    stack: list[tuple[str, int]] = []
    i = 0
    n = len(text)
    line = 1

    while i < n:
        ch = text[i]
        if ch == "\n":
            line += 1
            i += 1
            continue
        if ch == "/" and i + 1 < n:
            nxt = text[i + 1]
            if nxt == "/":
                nl = text.find("\n", i + 2)
                if nl == -1:
                    break
                i = nl
                continue
            if nxt == "*":
                end = text.find("*/", i + 2)
                if end == -1:
                    raise ValueError(f"[{pkg_name}] Unclosed block comment in {rel_path} (line {line})")
                line += text[i:end + 2].count("\n")
                i = end + 2
                continue
        if ch in ('"', "'", "`"):
            quote = ch
            start_line = line
            i += 1
            while i < n:
                c = text[i]
                if c == "\\":
                    if i + 1 < n and text[i + 1] == "\n":
                        line += 1
                    i += 2
                    continue
                if c == "\n":
                    line += 1
                if c == quote:
                    i += 1
                    break
                i += 1
            else:
                raise ValueError(f"[{pkg_name}] Unclosed string literal in {rel_path} (line {start_line})")
            continue
        if ch in pairs:
            stack.append((ch, line))
        elif ch in closing:
            if not stack or stack[-1][0] != closing[ch]:
                raise ValueError(f"[{pkg_name}] Unbalanced delimiters in {rel_path} at line {line}")
            stack.pop()
        i += 1

    if stack:
        open_ch, open_line = stack[-1]
        raise ValueError(f"[{pkg_name}] Unbalanced delimiters in {rel_path}: unclosed '{open_ch}' from line {open_line}")


def validate_qml_directory(pkg_dir: Path, pkg_name: str) -> list[str]:
    files = sorted(
        p for p in pkg_dir.rglob("*")
        if p.is_file() and p.suffix in (".qml", ".js", ".mjs")
    )
    for path in files:
        rel = path.relative_to(pkg_dir).as_posix()
        check_balanced_delimiters(path.read_text(encoding="utf-8"), rel, pkg_name)

    qmlformat = find_qmlformat()
    if not qmlformat:
        return ["qmlformat not found; ran basic delimiter check only (not full QML syntax)."]

    for path in files:
        rel = path.relative_to(pkg_dir).as_posix()
        res = subprocess.run(
            [qmlformat, "--ignore-settings", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        if res.returncode != 0:
            err = res.stderr.strip() or f"qmlformat exited with {res.returncode}"
            raise ValueError(f"[{pkg_name}] QML syntax check failed for {rel}: {err}")
    return []
