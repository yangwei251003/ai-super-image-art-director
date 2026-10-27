#!/usr/bin/env python3
"""Validate the curated JSON catalog and report its coverage."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from catalog import load_styles

ROOT = Path(__file__).resolve().parents[1]
USE_CASES = {
    "technology", "corporate", "recruitment", "education", "product_ad", "festival",
    "luxury", "photography", "illustration", "three_d", "oriental", "international_graphic",
}
INDUSTRIES = {
    "technology", "automotive", "education", "healthcare", "finance", "fashion", "food",
    "real_estate", "tourism", "entertainment", "sports", "luxury", "gaming", "children",
    "government", "culture", "manufacturing", "aerospace", "ecommerce", "professional_services",
}
APPLICATIONS = {
    "corporate_poster", "recruitment_poster", "campus_event", "product_ad", "brand_visual",
    "festival_poster", "drone_promotion", "education_promotion",
}
GOALS = {"awareness", "trust", "conversion", "recruitment", "education", "celebration", "engagement", "prestige"}
AUDIENCES = {"students", "professionals", "families", "consumers", "premium_buyers", "children", "public", "business_buyers", "creators"}
EMOTIONS = {"confident", "energetic", "warm", "calm", "playful", "cinematic", "premium", "trustworthy", "innovative", "festive"}
PLATFORMS = {"poster", "social", "web", "ecommerce", "print", "slide"}
ORGANIZATIONS = {"Apple", "DJI", "Nike", "Tesla", "MUJI", "Google Material", "Pentagram", "IDEO", "Landor", "Interbrand"}
STYLE_FIELDS = {
    "id", "name_zh", "name_en", "family", "philosophy", "visual_traits", "use_cases",
    "industry_tags", "goal_tags", "audience_tags", "emotion_tags", "platform_tags",
    "color_palette", "composition", "lighting", "materials", "camera_viewpoint",
    "prompt_template", "negative_prompt", "contraindications", "source_urls",
}


def load(name: str) -> list[dict]:
    path = ROOT / name
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError(f"{name}: expected an array of objects")
    return data


def required(record: dict, fields: set[str], label: str) -> None:
    missing = fields - record.keys()
    if missing:
        raise ValueError(f"{label}: missing fields {sorted(missing)}")


def nonempty_text(record: dict, fields: set[str], label: str) -> None:
    for field in fields:
        if not isinstance(record.get(field), str) or not record[field].strip():
            raise ValueError(f"{label}: {field} must be nonempty text")


def list_of_text(record: dict, field: str, label: str, *, allow_empty: bool = False) -> list[str]:
    value = record.get(field)
    if not isinstance(value, list) or not all(isinstance(x, str) and x.strip() for x in value):
        raise ValueError(f"{label}: {field} must be an array of nonempty strings")
    if not allow_empty and not value:
        raise ValueError(f"{label}: {field} cannot be empty")
    return value


def check_urls(urls: list[str], label: str) -> None:
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError(f"{label}: expected a full HTTPS source URL: {url}")


def check_ids(rows: list[dict], label: str) -> None:
    ids = [row.get("id") for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{label}: duplicate IDs")
    if any(not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9_-]*", value) for value in ids):
        raise ValueError(f"{label}: IDs must be lowercase slugs")


def subset(record: dict, field: str, allowed: set[str], label: str) -> None:
    values = set(list_of_text(record, field, label))
    if values - allowed:
        raise ValueError(f"{label}: unknown {field} values {sorted(values - allowed)}")


def validate() -> dict:
    styles = load_styles()
    industry = load("knowledge/industry_profiles.json")
    applications = load("knowledge/use_cases.json")
    validators = load("knowledge/domain_validators.json")
    cases = load("knowledge/case_studies.json")
    trends = load("knowledge/trends.json")
    gallery = load("knowledge/gallery_patterns.json")

    if not 48 <= len(styles) <= 60:
        raise ValueError(f"Expected approximately 48 curated styles (48–60), got {len(styles)}")
    check_ids(styles, "styles")
    coverage: Counter[str] = Counter()
    for row in styles:
        label = f"style {row['id']}"
        required(row, STYLE_FIELDS, label)
        nonempty_text(row, {"name_zh", "name_en", "family", "philosophy", "prompt_template"}, label)
        for field in ("color_palette", "composition", "lighting", "materials", "camera_viewpoint"):
            value = row[field]
            if not (isinstance(value, str) and value.strip()) and not (
                isinstance(value, list) and value and all(isinstance(x, str) and x.strip() for x in value)
            ):
                raise ValueError(f"{label}: {field} needs text or a nonempty text array")
        for field in ("visual_traits", "negative_prompt", "source_urls"):
            list_of_text(row, field, label)
        list_of_text(row, "contraindications", label, allow_empty=True)
        for field, allowed in (
            ("use_cases", USE_CASES), ("industry_tags", INDUSTRIES), ("goal_tags", GOALS),
            ("audience_tags", AUDIENCES), ("emotion_tags", EMOTIONS), ("platform_tags", PLATFORMS),
        ):
            subset(row, field, allowed, label)
        if row["family"] not in USE_CASES:
            raise ValueError(f"{label}: unknown family {row['family']}")
        if "{subject}" not in row["prompt_template"] or "{environment}" not in row["prompt_template"]:
            raise ValueError(f"{label}: prompt_template needs subject and environment placeholders")
        check_urls(row["source_urls"], label)
        coverage.update(row["use_cases"])
    if set(coverage) != USE_CASES or min(coverage.values()) < 3:
        raise ValueError(f"Style coverage must include each of 12 use cases at least 3 times: {dict(coverage)}")

    if len(industry) != 20 or {row.get("id") for row in industry} != INDUSTRIES:
        raise ValueError("Expected exactly the 20 specified industry IDs")
    check_ids(industry, "industry profiles")
    for row in industry:
        label = f"industry {row['id']}"
        required(row, {"id", "name_zh", "core_goals", "audience_priorities", "visual_strategy", "avoid", "verification_questions", "source_urls"}, label)
        nonempty_text(row, {"name_zh"}, label)
        for field in ("core_goals", "audience_priorities", "visual_strategy", "avoid", "verification_questions", "source_urls"):
            list_of_text(row, field, label)
        check_urls(row["source_urls"], label)

    if len(applications) != 8 or {row.get("id") for row in applications} != APPLICATIONS:
        raise ValueError("Expected exactly the 8 priority application IDs")
    check_ids(applications, "application profiles")
    for row in applications:
        label = f"application {row['id']}"
        required(row, {"id", "name_zh", "goal_tags", "audience_tags", "platform_tags", "brief_questions", "style_guidance", "qa_focus"}, label)
        nonempty_text(row, {"name_zh"}, label)
        for field, allowed in (("goal_tags", GOALS), ("audience_tags", AUDIENCES), ("platform_tags", PLATFORMS)):
            subset(row, field, allowed, label)
        for field in ("brief_questions", "style_guidance", "qa_focus"):
            list_of_text(row, field, label)

    if len(validators) < 3:
        raise ValueError("Expected general and conditional domain validators")
    check_ids(validators, "domain validators")
    for row in validators:
        label = f"validator {row['id']}"
        required(row, {"id", "activates_when", "critical_checks", "caution", "source_urls"}, label)
        nonempty_text(row, {"activates_when", "caution"}, label)
        list_of_text(row, "critical_checks", label)
        check_urls(list_of_text(row, "source_urls", label), label)
    if not {"explicit_quadcopter_topology", "explicit_four_arm_fpv"} <= {row["id"] for row in validators}:
        raise ValueError("Conditional quadcopter and four-arm FPV validators are required")

    if len(cases) != 10 or {row.get("organization") for row in cases} != ORGANIZATIONS:
        raise ValueError("Expected exactly the 10 named organizations")
    check_ids(cases, "case studies")
    for row in cases:
        label = f"case {row['id']}"
        required(row, {"id", "organization", "case_title", "source_url", "source_date", "accessed_date",
                       "source_stated_facts", "design_observations", "communication_inferences",
                       "transfer_rules", "avoid_copying"}, label)
        nonempty_text(row, {"organization", "case_title", "source_url", "accessed_date"}, label)
        check_urls([row["source_url"]], label)
        date.fromisoformat(row["accessed_date"])
        if row["source_date"] is not None:
            date.fromisoformat(row["source_date"])
        for field in ("source_stated_facts", "design_observations", "communication_inferences", "transfer_rules", "avoid_copying"):
            list_of_text(row, field, label)

    if len(trends) < 5:
        raise ValueError("Expected at least five researched directions")
    check_ids(trends, "trends")
    for row in trends:
        label = f"trend {row['id']}"
        required(row, {"id", "name_zh", "source_urls", "source_dates", "observed_pattern", "transfer_rule", "limits"}, label)
        nonempty_text(row, {"name_zh"}, label)
        check_urls(list_of_text(row, "source_urls", label), label)
        if not isinstance(row["source_dates"], list):
            raise ValueError(f"{label}: source_dates must be an array")
        for field in ("observed_pattern", "transfer_rule", "limits"):
            if not isinstance(row[field], str) or not row[field].strip():
                raise ValueError(f"{label}: {field} must be nonempty text")

    if len(gallery) < 9:
        raise ValueError("Expected nine reviewed gallery patterns")
    check_ids(gallery, "gallery patterns")
    for row in gallery:
        label = f"gallery pattern {row['id']}"
        required(row, {"id", "case_reference", "source_url", "observed_prompt_structure",
                       "transfer_rule", "use_for", "limits", "evidence_scope"}, label)
        nonempty_text(row, {"case_reference", "source_url", "observed_prompt_structure",
                            "transfer_rule", "limits", "evidence_scope"}, label)
        list_of_text(row, "use_for", label)
        check_urls([row["source_url"]], label)

    return {
        "styles": len(styles),
        "style_coverage": dict(sorted(coverage.items())),
        "industries": len(industry),
        "priority_use_cases": len(applications),
        "domain_validators": len(validators),
        "case_studies": len(cases),
        "new_directions": len(trends),
        "gallery_patterns": len(gallery),
        "unique_style_source_urls": len({url for row in styles for url in row["source_urls"]}),
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, indent=2))
