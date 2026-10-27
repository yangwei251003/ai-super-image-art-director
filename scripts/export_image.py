#!/usr/bin/env python3
"""Export an image to exact PNG dimensions with safe padding by default."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from statistics import median
from tempfile import NamedTemporaryFile

from PIL import Image


def color_from_corners(image: Image.Image) -> tuple[int, int, int]:
    rgb = image.convert("RGB")
    w, h = rgb.size
    points = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    pixels = [rgb.getpixel(point) for point in points]
    return tuple(int(median(pixel[channel] for pixel in pixels)) for channel in range(3))


def parse_color(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    if len(value) != 6:
        raise ValueError("Background color must be #RRGGBB")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def render(
    source: Image.Image,
    width: int,
    height: int,
    mode: str = "contain",
    background: str | None = None,
    anchor_x: float = 0.5,
    anchor_y: float = 0.5,
) -> tuple[Image.Image, dict]:
    if width <= 0 or height <= 0 or width > 10000 or height > 10000 or width * height > 30_000_000:
        raise ValueError("Target dimensions must be positive and at most 30 million pixels")
    if mode not in ("contain", "cover"):
        raise ValueError("mode must be contain or cover")
    if not 0 <= anchor_x <= 1 or not 0 <= anchor_y <= 1:
        raise ValueError("anchors must be in [0, 1]")
    src_w, src_h = source.size
    scale = min(width / src_w, height / src_h) if mode == "contain" else max(width / src_w, height / src_h)
    new_w = max(1, round(src_w * scale))
    new_h = max(1, round(src_h * scale))
    resized = source.resize((new_w, new_h), Image.Resampling.LANCZOS)

    if mode == "contain":
        alpha = "A" in source.getbands()
        canvas = Image.new("RGBA" if alpha else "RGB", (width, height),
                           (0, 0, 0, 0) if alpha else (parse_color(background) if background else color_from_corners(source)))
        left = round((width - new_w) * anchor_x)
        top = round((height - new_h) * anchor_y)
        if alpha:
            canvas.alpha_composite(resized.convert("RGBA"), (left, top))
        else:
            canvas.paste(resized.convert("RGB"), (left, top))
        details = {"padding": {"left": left, "top": top, "right": width - new_w - left, "bottom": height - new_h - top}}
    else:
        left = round((new_w - width) * anchor_x)
        top = round((new_h - height) * anchor_y)
        canvas = resized.crop((left, top, left + width, top + height))
        details = {"crop": {"left": left, "top": top, "right": new_w - width - left, "bottom": new_h - height - top}}
    return canvas, {"source_size": [src_w, src_h], "target_size": [width, height], "mode": mode, "scale": scale, **details}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--width", required=True, type=int)
    parser.add_argument("--height", required=True, type=int)
    parser.add_argument("--mode", choices=("contain", "cover"), default="contain")
    parser.add_argument("--crop-approved", action="store_true", help="Required when mode=cover after inspecting a safe crop")
    parser.add_argument("--background", help="Optional #RRGGBB for opaque padding")
    parser.add_argument("--anchor-x", type=float, default=0.5)
    parser.add_argument("--anchor-y", type=float, default=0.5)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    source_path, output_path = args.input.resolve(), args.output.resolve()
    if source_path == output_path:
        parser.error("Input and output must differ")
    if output_path.exists() and not args.overwrite:
        parser.error("Output exists; pass --overwrite to replace it")
    if args.mode == "cover" and not args.crop_approved:
        parser.error("Cover mode requires --crop-approved after visual inspection")
    if not source_path.is_file():
        parser.error(f"Input not found: {source_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source_path) as source:
        image, details = render(source, args.width, args.height, args.mode, args.background, args.anchor_x, args.anchor_y)
    with NamedTemporaryFile(prefix=".export-", suffix=".png", dir=output_path.parent, delete=False) as tmp:
        temp_path = Path(tmp.name)
    try:
        image.save(temp_path, format="PNG")
        os.replace(temp_path, output_path)
    finally:
        temp_path.unlink(missing_ok=True)
    print(json.dumps({"output": str(output_path), **details}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
