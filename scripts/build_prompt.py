#!/usr/bin/env python3
"""Build a labeled prompt package and one image-tool-ready prompt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from catalog import load_styles

ROOT = Path(__file__).resolve().parents[1]


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return [item for item in value if item.strip()]
    raise ValueError("Expected text or list of text")


def joined(value: Any) -> str:
    return "；".join(as_list(value))


def build_package(brief: dict[str, Any], style: dict[str, Any]) -> dict[str, Any]:
    subject = brief.get("subject", "").strip()
    if not subject:
        raise ValueError("CreativeBrief.subject is required")
    environment = brief.get("environment", "").strip() or "适合传播目标且符合事实的环境"
    template = style["prompt_template"]
    if "{subject}" not in template or "{environment}" not in template:
        raise ValueError(f"Style {style['id']} template needs subject and environment placeholders")
    positive = template.replace("{subject}", subject).replace("{environment}", environment)
    composition = joined(style["composition"])
    lighting = joined(style["lighting"])
    material = joined(style["materials"])
    camera = joined(style["camera_viewpoint"])
    negatives = list(dict.fromkeys(as_list(style["negative_prompt"]) + as_list(brief.get("avoid_terms"))))
    exact_text = as_list(brief.get("exact_text"))
    must_have = as_list(brief.get("must_have"))
    brand = as_list(brief.get("brand_constraints"))
    references = brief.get("reference_images") or []
    if not isinstance(references, list):
        raise ValueError("reference_images must be a list")

    lines = [
        f"作品用途：{joined(brief.get('platform_tags') or brief.get('platform')) or '用户指定的图像用途'}。",
        f"主体：{subject}。",
        f"环境：{environment}。",
        f"视觉方向：{style['name_zh']}。核心理念：{style['philosophy']}。",
        f"正向画面：{positive}。",
        f"构图：{composition}。",
        f"镜头或视角：{camera}。",
        f"光影：{lighting}。",
        f"材质和表面细节：{material}。",
        "真实细节：主体结构、接触、透视、光源、阴影和数量须与用户要求一致；若明确为幻想场景，则保持设定内部一致。",
    ]
    if must_have:
        lines.append(f"必须满足的可核查事实：{joined(must_have)}。")
    if brand:
        lines.append(f"品牌约束：{joined(brand)}。不自行创造未提供的徽标、产品参数或宣传事实。")
    if exact_text:
        quoted = "；".join(f"「{item}」" for item in exact_text)
        lines.append(f"图中必须逐字、清晰地呈现且仅呈现这些文字：{quoted}。除此之外，墙面、屏幕、纸张、书脊、衣服及背景均不得出现任何可读文字、伪文字或品牌标识。不得增删或错写指定文案。")
    else:
        lines.append("不要添加未要求的品牌名、日期、联系人或伪文字。")
    if brief.get("width") and brief.get("height"):
        lines.append(f"目标画幅：{int(brief['width'])} × {int(brief['height'])} 像素的比例；保留安全边距，主体和文字不得贴边。")
    if references:
        roles = []
        for index, ref in enumerate(references, start=1):
            if not isinstance(ref, dict) or not ref.get("role"):
                raise ValueError("Each reference image needs a role")
            roles.append(f"参考图{index}用于{ref['role']}")
        lines.append("参考图角色：" + "；".join(roles) + "。")
    if negatives:
        lines.append(f"避免：{joined(negatives)}。")

    return {
        "style_id": style["id"],
        "style_name": style["name_zh"],
        "positive_prompt": positive,
        "negative_prompt": negatives,
        "composition_prompt": composition,
        "lighting_prompt": lighting,
        "material_prompt": material,
        "camera_or_viewpoint_prompt": camera,
        "exact_text": exact_text,
        "compiled_prompt": "\n".join(lines),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brief", required=True, type=Path)
    parser.add_argument("--style-id", required=True)
    parser.add_argument("--styles", type=Path, help="Optional single catalog override; default loads both curated style files")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    brief = json.loads(args.brief.read_text(encoding="utf-8"))
    styles = load_styles(args.styles)
    style = next((item for item in styles if item["id"] == args.style_id), None)
    if style is None:
        raise SystemExit(f"Unknown style ID: {args.style_id}")
    result = build_package(brief, style)
    encoded = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
