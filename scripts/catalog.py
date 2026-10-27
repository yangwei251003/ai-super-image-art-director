"""Read the curated base styles and reviewed gallery additions."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLE_FILES = (
    ROOT / "style_library" / "styles.json",
    ROOT / "style_library" / "gallery_additions.json",
)


def load_styles(override: Path | None = None) -> list[dict]:
    paths = (override,) if override else STYLE_FILES
    styles: list[dict] = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError(f"{path}: styles must be an array of objects")
        styles.extend(data)
    return styles
