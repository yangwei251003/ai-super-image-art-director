#!/usr/bin/env python3
"""Deterministic candidate retrieval for the art-director skill."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from catalog import load_styles

ROOT = Path(__file__).resolve().parents[1]

MATCH_FIELDS = (
    ("goal_tags", "goal_tags", 4, "传播目标"),
    ("industry", "industry_tags", 3, "行业"),
    ("audience_tags", "audience_tags", 3, "目标用户"),
    ("use_case", "use_cases", 3, "应用场景"),
    ("emotion_tags", "emotion_tags", 2, "情绪"),
    ("platform_tags", "platform_tags", 2, "平台"),
)


def values(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {value.strip().casefold()} if value.strip() else set()
    if isinstance(value, list):
        return {v.strip().casefold() for v in value if isinstance(v, str) and v.strip()}
    raise ValueError("Tags must be a string, list of strings, or null")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def brief_values(brief: dict[str, Any], field: str) -> set[str]:
    if field == "platform_tags":
        return values(brief.get("platform_tags") or brief.get("platform"))
    return values(brief.get(field))


def is_excluded(style: dict[str, Any], brief: dict[str, Any]) -> bool:
    if style["id"].casefold() in values(brief.get("avoid_style_ids")):
        return True
    if style["family"].casefold() in values(brief.get("avoid_families")):
        return True
    searchable = " ".join(
        [
            style["id"],
            style["name_zh"],
            style["name_en"],
            style["family"],
            *style.get("visual_traits", []),
        ]
    ).casefold()
    return any(term in searchable for term in values(brief.get("avoid_terms")))


def score_style(style: dict[str, Any], brief: dict[str, Any]) -> dict[str, Any]:
    breakdown: dict[str, int] = {}
    matched_tags: dict[str, list[str]] = {}
    for brief_key, style_key, weight, label in MATCH_FIELDS:
        overlap = brief_values(brief, brief_key) & values(style.get(style_key))
        breakdown[brief_key] = weight if overlap else 0
        if overlap:
            matched_tags[label] = sorted(overlap)
    total = sum(breakdown.values())
    return {
        "id": style["id"],
        "name_zh": style["name_zh"],
        "name_en": style["name_en"],
        "family": style["family"],
        "score": total,
        "score_breakdown": breakdown,
        "matched_tags": matched_tags,
        "philosophy": style["philosophy"],
        "reason": "匹配：" + "、".join(matched_tags) if matched_tags else "通用备选：暂无明确标签匹配",
    }


def match(brief: dict[str, Any], styles: list[dict[str, Any]], top_k: int = 3) -> dict[str, Any]:
    if not 3 <= top_k <= 6:
        raise ValueError("top_k must be between 3 and 6")
    candidates = [score_style(s, brief) for s in styles if not is_excluded(s, brief)]
    candidates.sort(key=lambda item: (-item["score"], -item["score_breakdown"]["use_case"], item["id"]))
    if len(candidates) < top_k:
        raise ValueError(f"Only {len(candidates)} styles remain after exclusions; need {top_k}")

    selected: list[dict[str, Any]] = []
    used_families: set[str] = set()
    for candidate in candidates:
        if candidate["family"] not in used_families:
            selected.append(candidate)
            used_families.add(candidate["family"])
        if len(selected) == top_k:
            break
    if len(selected) < top_k:
        chosen = {item["id"] for item in selected}
        selected.extend(item for item in candidates if item["id"] not in chosen)
        selected = selected[:top_k]

    return {
        "selected": selected,
        "ranked": candidates[: max(12, top_k)],
        "excluded_count": len(styles) - len(candidates),
        "weights": {brief_key: weight for brief_key, _, weight, _ in MATCH_FIELDS},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brief", required=True, type=Path, help="UTF-8 CreativeBrief JSON file")
    parser.add_argument("--styles", type=Path, help="Optional single catalog override; default loads both curated style files")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    brief = load_json(args.brief)
    styles = load_styles(args.styles)
    if not isinstance(brief, dict) or not isinstance(styles, list):
        raise SystemExit("Brief must be an object and styles must be an array")
    result = match(brief, styles, args.top_k)
    encoded = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
