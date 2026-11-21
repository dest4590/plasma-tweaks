#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""QML/JS syntax validation helpers for staged plasma-tweaks packages."""
from pathlib import Path
import tempfile
import shutil
import subprocess
import json


def strip_jsonc(text: str) -> str:
    """Remove JSONC comments and trailing commas while preserving string contents."""
    out: list[str] = []
    i = 0
    quote: str | None = None
    escape = False

    while i < len(text):
        ch = text[i]
        if quote is not None:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch in ('"', "'"):
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < len(text) and text[i + 1] == "/":
            i += 2
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue
        if ch == "/" and i + 1 < len(text) and text[i + 1] == "*":
            i += 2
            while i + 1 < len(text) and text[i:i + 2] != "*/":
                if text[i] in "\r\n":
                    out.append(text[i])
                i += 1
            if i + 1 >= len(text):
                raise ValueError("Unclosed block comment")
            i += 2
            continue
        out.append(ch)
        i += 1

    stripped = "".join(out)
    # Remove commas that precede a closing brace or bracket.
    out = []
    for i, ch in enumerate(stripped):
        if ch == ",":
            j = i + 1
            while j < len(stripped) and stripped[j].isspace():
                j += 1
            if j < len(stripped) and stripped[j] in "}]":
                continue
        out.append(ch)
    return "".join(out)


def load_jsonc(path: Path) -> dict:
    try:
        value = json.loads(strip_jsonc(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid JSONC file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSONC root must be an object: {path}")
    return value


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
    warnings: list[str] = []
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

    probe = (
        "pragma ComponentBehavior: Bound\n"
        "import QtQuick\n"
        "Item {\n"
        "    required property int idNum\n"
        "    property var maybeObj\n"
        "    property string t: maybeObj?.text ?? \"\"\n"
        "}\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".qml", delete=False, encoding="utf-8") as tf:
        tf.write(probe)
        probe_path = Path(tf.name)
    try:
        probe_res = subprocess.run(
            [qmlformat, str(probe_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    finally:
        probe_path.unlink(missing_ok=True)
    if probe_res.returncode != 0:
        return [
            "qmlformat parser is too old for modern Plasma QML syntax; "
            "ran delimiter-only validation (not full QML syntax)."
        ]

    for path in files:
        rel = path.relative_to(pkg_dir).as_posix()
        if path.suffix != ".qml":
            continue
        cmd = [qmlformat, "--ignore-settings", str(path)]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0 and "Unknown option 'ignore-settings'" in (res.stderr or ""):
            cmd = [qmlformat, str(path)]
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            err = res.stderr.strip()
            if err:
                raise ValueError(f"[{pkg_name}] QML syntax check failed for {rel}: {err}")
            warnings.append(
                f"qmlformat returned {res.returncode} without diagnostics for {rel}; "
                "kept delimiter-only validation for this file."
            )
    return warnings
