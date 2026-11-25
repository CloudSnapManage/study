#!/usr/bin/env python3
"""Static policy audit for Cognito's zero-build frontend."""
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
TEXT_EXTENSIONS = {".html", ".css", ".js"}
BANNED = {
    "linear-gradient": "gradient",
    "radial-gradient": "gradient",
    "conic-gradient": "gradient",
    "backdrop-filter": "backdrop filter",
    "box-shadow": "drop shadow",
    "border-radius: 9999px": "pill radius",
    "#6366f1": "banned indigo",
    "#8b5cf6": "banned purple",
    "#a855f7": "banned purple",
    "#06b6d4": "banned neon cyan",
    "#0f172a": "banned dark-blue palette",
    "#1e293b": "banned dark-blue palette",
}
EXTERNAL_ASSET = re.compile(r"(?:src|href)=[\"']https?://|url\([\"']?https?://", re.I)
INLINE_HANDLER = re.compile(r"\son[a-z]+\s*=", re.I)
EMOJI = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF"
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "]"
)


def audit() -> list[str]:
    failures: list[str] = []
    for path in sorted(FRONTEND.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_EXTENSIONS:
            continue
        relative = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8", errors="ignore")
        lowered = text.lower()
        for token, label in BANNED.items():
            if token in lowered:
                failures.append(f"{relative}: contains {label} token {token!r}")
        if EXTERNAL_ASSET.search(text):
            failures.append(f"{relative}: loads an external runtime asset")
        if path.suffix == ".html" and INLINE_HANDLER.search(text):
            failures.append(f"{relative}: contains an inline event handler")
        if EMOJI.search(text):
            failures.append(f"{relative}: contains an emoji code point")
    return failures


def main() -> int:
    failures = audit()
    if failures:
        print("Frontend audit failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Frontend audit passed: no banned colors, gradients, shadows, backdrop filters, emojis, inline handlers, or external runtime assets.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
