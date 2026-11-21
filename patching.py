# SPDX-License-Identifier: GPL-2.0-or-later
"""Apply ordered feature overlays to an extracted applet in staging."""

from pathlib import Path
import re
import shutil

from qml_validation import load_jsonc

PATCH_OPS = {
    "replace": lambda _, added: added,
    "insert_after": lambda match, added: match + added,
    "insert_before": lambda match, added: added + match,
}


def patch_text(value: object, field: str, context: str) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(line, str) for line in value):
        return "\n".join(value)
    raise ValueError(f"{context}: {field!r} must be a string or an array of strings")


def apply_operation(text: str, op: dict, context: str) -> str:
    kind = op.get("op")
    if kind not in PATCH_OPS:
        raise ValueError(f"{context}: unknown operation {kind!r}")
    context += f" ({kind})"
    anchor_field = "old" if kind == "replace" else "anchor"
    anchor = patch_text(op.get(anchor_field), anchor_field, context)
    if not anchor:
        raise ValueError(f"{context}: {anchor_field!r} cannot be empty")

    if kind != "replace" and "lines" in op:
        lines = op["lines"]
        if (
            "text" in op
            or not isinstance(lines, list)
            or not lines
            or any(
                not isinstance(line, str) or "\n" in line or "\r" in line
                for line in lines
            )
        ):
            raise ValueError(
                f"{context}: use 'lines' alone with a nonempty array of single lines"
            )
        pattern = re.compile(r"^" + re.escape(anchor) + r"$", re.MULTILINE)
        separator = "\n"
        added = separator.join(lines)
        added = separator + added if kind == "insert_after" else added + separator
    else:
        pattern = re.compile(re.escape(anchor))
        added_field = "new" if kind == "replace" else "text"
        added = patch_text(op.get(added_field), added_field, context)

    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        preview = anchor.split("\n", 1)[0]
        locations = ", ".join(
            str(text.count("\n", 0, match.start()) + 1) for match in matches[:5]
        )
        detail = f" at lines {locations}" if locations else ""
        raise ValueError(
            f"{context}: expected 1 match for {preview!r}, found {len(matches)}{detail}"
        )
    match = matches[0]
    return (
        text[: match.start()]
        + PATCH_OPS[kind](match.group(), added)
        + text[match.end() :]
    )


def package_path(pkg_dir: Path, relative: str) -> Path:
    path = Path(relative)
    if not path.parts or path.is_absolute() or ".." in path.parts:
        raise ValueError(
            f"Expected a file path relative to the applet package: {relative!r}"
        )
    return pkg_dir / path


def apply_feature_patches(
    pkg_dir: Path, feature_dir: Path, feature_name: str
) -> list[str]:
    spec_path = feature_dir / "patches.jsonc"
    if not spec_path.is_file():
        spec_path = feature_dir / "patches.json"
    if not spec_path.is_file():
        raise ValueError(f"[{feature_name}] Missing patch specification: {spec_path}")
    spec = load_jsonc(spec_path)
    changed_files: set[str] = set()

    for item in spec.get("copy_from", []):
        src = package_path(pkg_dir, item["src"])
        dst = package_path(pkg_dir, item["dst"])
        if not src.is_file():
            raise ValueError(
                f"[{feature_name}] Missing source file for copy_from: {item['src']}"
            )
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        changed_files.add(item["dst"])

    files_dir = feature_dir / "files"
    if files_dir.is_dir():
        for src in sorted(files_dir.rglob("*")):
            if src.is_file():
                rel = src.relative_to(files_dir).as_posix()
                dst = pkg_dir / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                changed_files.add(rel)

    for rel, ops in spec.get("patches", {}).items():
        target = package_path(pkg_dir, rel)
        if not target.is_file():
            raise ValueError(
                f"[{feature_name}] Target file missing in extracted KDE resources: {rel}"
            )
        text = target.read_text()
        for idx, op in enumerate(ops, start=1):
            text = apply_operation(text, op, f"[{feature_name}] {rel} operation #{idx}")
        target.write_text(text)
        changed_files.add(rel)

    return sorted(changed_files)
