#!/usr/bin/env python3
"""Validate a grounded QA report and choose the next bounded action."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_CHECKS = {
    "brief_alignment",
    "human_anatomy",
    "spatial",
    "lighting",
    "object_integrity",
    "text",
    "count",
    "scene_logic",
    "domain",
}
SOFT_AXES = {
    "communication",
    "hierarchy_composition",
    "style_brand_fit",
    "lighting_material",
    "legibility_export",
}
STRUCTURAL = {"brief_alignment", "spatial", "count", "scene_logic", "domain"}
STATUSES = {"pass", "fail", "uncertain", "not_applicable"}
SEVERITIES = {"critical", "major", "minor"}


def decide(report: dict[str, Any]) -> dict[str, Any]:
    attempt = report.get("attempt")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt not in (0, 1, 2):
        raise ValueError("attempt must be 0, 1, or 2")
    scope = report.get("issue_scope")
    if scope not in ("none", "local", "global"):
        raise ValueError("issue_scope must be none, local, or global")
    checks = report.get("hard_checks")
    if not isinstance(checks, list):
        raise ValueError("hard_checks must be an array")
    found: dict[str, dict[str, Any]] = {}
    for check in checks:
        if not isinstance(check, dict):
            raise ValueError("Each check must be an object")
        check_id = check.get("id")
        if check_id not in REQUIRED_CHECKS or check_id in found:
            raise ValueError(f"Unknown or duplicate hard check: {check_id}")
        if check.get("status") not in STATUSES:
            raise ValueError(f"Invalid status for {check_id}")
        if check.get("severity") not in SEVERITIES:
            raise ValueError(f"Invalid severity for {check_id}")
        if not isinstance(check.get("evidence"), str) or not check["evidence"].strip():
            raise ValueError(f"Grounded evidence is required for {check_id}")
        found[check_id] = check
    missing = REQUIRED_CHECKS - found.keys()
    if missing:
        raise ValueError(f"Missing hard checks: {sorted(missing)}")
    if found["brief_alignment"]["status"] == "not_applicable":
        raise ValueError("brief_alignment cannot be not_applicable")

    scores = report.get("soft_scores")
    if not isinstance(scores, dict) or set(scores) != SOFT_AXES:
        raise ValueError(f"soft_scores must have exactly: {sorted(SOFT_AXES)}")
    for axis, value in scores.items():
        if not isinstance(value, int) or isinstance(value, bool) or value not in (0, 1, 2):
            raise ValueError(f"Score for {axis} must be 0, 1, or 2")
    total = sum(scores.values())
    blocking = [check for check in found.values() if check["status"] in ("fail", "uncertain")]
    passed = not blocking and total >= 8 and all(value > 0 for value in scores.values())
    unresolved = [
        {"id": check["id"], "status": check["status"], "evidence": check["evidence"], "repair": check.get("repair", "")}
        for check in found.values()
        if check["status"] in ("fail", "uncertain")
    ]
    if passed:
        action = "pass"
    elif attempt == 2:
        action = "failed_preview"
    elif scope == "local" and not any(check["id"] in STRUCTURAL for check in blocking):
        action = "edit"
    else:
        action = "regenerate"
    return {
        "direction_id": report.get("direction_id"),
        "attempt": attempt,
        "passed": passed,
        "action": action,
        "score": total,
        "max_corrections": 2,
        "corrections_remaining": max(0, 2 - attempt),
        "blocking_check_ids": [check["id"] for check in blocking],
        "unresolved_issues": unresolved,
        "weak_axes": [axis for axis, value in scores.items() if value < 2],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    result = decide(report)
    encoded = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
