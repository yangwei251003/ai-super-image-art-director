"""Focused behavioral checks for catalog retrieval, prompts, QA, and export."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_prompt import build_package  # noqa: E402
from catalog import load_styles  # noqa: E402
from export_image import render  # noqa: E402
from match_styles import match  # noqa: E402
from qa_state import REQUIRED_CHECKS, decide  # noqa: E402
from validate_catalog import validate  # noqa: E402


def read_fixture(name: str) -> dict:
    return json.loads((ROOT / "tests" / "fixtures" / name).read_text(encoding="utf-8"))


def good_report() -> dict:
    return {
        "direction_id": "test_direction",
        "attempt": 0,
        "issue_scope": "none",
        "hard_checks": [
            {"id": check_id, "status": "pass", "severity": "critical", "evidence": f"Observed {check_id}", "repair": ""}
            for check_id in sorted(REQUIRED_CHECKS)
        ],
        "soft_scores": {
            "communication": 2,
            "hierarchy_composition": 2,
            "style_brand_fit": 2,
            "lighting_material": 1,
            "legibility_export": 2,
        },
    }


class CatalogAndMatcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.styles = load_styles()

    def test_catalog_is_complete_and_traceable(self) -> None:
        summary = validate()
        self.assertEqual(summary["styles"], 53)
        self.assertEqual(summary["gallery_patterns"], 9)
        self.assertEqual(summary["case_studies"], 10)
        self.assertEqual(summary["industries"], 20)
        self.assertGreaterEqual(min(summary["style_coverage"].values()), 3)

    def test_recruitment_retrieval_has_distinct_families(self) -> None:
        result = match(read_fixture("recruitment_brief.json"), self.styles, 3)
        selected = result["selected"]
        self.assertEqual(len(selected), 3)
        self.assertEqual(len({item["family"] for item in selected}), 3)
        self.assertTrue(any("recruitment" in item["matched_tags"].get("应用场景", []) for item in selected))
        self.assertGreater(selected[0]["score"], 0)

    def test_explicit_exclusion_is_hard(self) -> None:
        brief = read_fixture("recruitment_brief.json")
        brief["avoid_families"] = ["recruitment"]
        brief["avoid_style_ids"] = ["windowlight_portrait"]
        result = match(brief, self.styles, 3)
        self.assertTrue(all(item["family"] != "recruitment" for item in result["ranked"]))
        self.assertTrue(all(item["id"] != "windowlight_portrait" for item in result["ranked"]))

    def test_cross_industry_retrieval_keeps_context_and_variety(self) -> None:
        briefs = [
            {"industry": "food", "use_case": "product_ad", "goal_tags": ["conversion"],
             "audience_tags": ["consumers"], "emotion_tags": ["warm"], "platform_tags": ["ecommerce"]},
            {"industry": "education", "use_case": "education", "goal_tags": ["education"],
             "audience_tags": ["children"], "emotion_tags": ["playful"], "platform_tags": ["poster"]},
            {"industry": "culture", "use_case": "festival", "goal_tags": ["celebration"],
             "audience_tags": ["public"], "emotion_tags": ["festive"], "platform_tags": ["print"]},
        ]
        for brief in briefs:
            with self.subTest(industry=brief["industry"]):
                selected = match(brief, self.styles, 3)["selected"]
                self.assertEqual(len({item["family"] for item in selected}), 3)
                self.assertGreaterEqual(selected[0]["score"], 10)
                self.assertEqual(selected[0]["score_breakdown"]["use_case"], 3)


class PromptAndQATests(unittest.TestCase):
    def test_exact_copy_and_facts_survive_prompt_building(self) -> None:
        brief = read_fixture("drone_brief.json")
        styles = load_styles()
        style = next(item for item in styles if item["id"] == "data_constellation")
        package = build_package(brief, style)
        self.assertIn("无人机社团招新", package["compiled_prompt"])
        self.assertIn("恰好四个机臂", package["compiled_prompt"])
        self.assertIn("恰好四个电机", package["compiled_prompt"])
        self.assertIn("避免：", package["compiled_prompt"])
        self.assertEqual(package["exact_text"], ["无人机社团招新"])

    def test_qa_pass_edit_regenerate_and_limit(self) -> None:
        report = good_report()
        self.assertEqual(decide(report)["action"], "pass")
        text_check = next(c for c in report["hard_checks"] if c["id"] == "text")
        text_check.update(status="fail", evidence="One title character is wrong", repair="Correct that glyph")
        report["issue_scope"] = "local"
        self.assertEqual(decide(report)["action"], "edit")
        count_check = next(c for c in report["hard_checks"] if c["id"] == "count")
        count_check.update(status="fail", evidence="Five motors are visible", repair="Regenerate four")
        self.assertEqual(decide(report)["action"], "regenerate")
        report["attempt"] = 2
        self.assertEqual(decide(report)["action"], "failed_preview")

    def test_uncertain_even_minor_cannot_pass(self) -> None:
        report = good_report()
        check = next(c for c in report["hard_checks"] if c["id"] == "lighting")
        check.update(status="uncertain", severity="minor", evidence="Shadow is obscured")
        self.assertFalse(decide(report)["passed"])

    def test_failed_minor_check_cannot_pass(self) -> None:
        report = good_report()
        check = next(c for c in report["hard_checks"] if c["id"] == "lighting")
        check.update(status="fail", severity="minor", evidence="Visible isolated reflection mismatch")
        report["issue_scope"] = "local"
        self.assertEqual(decide(report)["action"], "edit")


class ExportTests(unittest.TestCase):
    def test_contain_preserves_full_source_and_exact_pixels(self) -> None:
        source = Image.new("RGB", (4, 2), "#ff0000")
        result, metadata = render(source, 8, 8, background="#000000")
        self.assertEqual(result.size, (8, 8))
        self.assertEqual(metadata["padding"], {"left": 0, "top": 2, "right": 0, "bottom": 2})
        self.assertEqual(result.getpixel((0, 0)), (0, 0, 0))
        self.assertEqual(result.getpixel((0, 2)), (255, 0, 0))
        self.assertEqual(result.getpixel((7, 5)), (255, 0, 0))

    def test_export_can_write_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "preview.png"
            image, _ = render(Image.new("RGB", (30, 20), "#336699"), 60, 60)
            image.save(output)
            with Image.open(output) as reread:
                self.assertEqual(reread.size, (60, 60))


if __name__ == "__main__":
    unittest.main()
