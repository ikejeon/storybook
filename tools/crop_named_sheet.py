#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "Pillow is required. In this Codex workspace, run with the bundled Python runtime: "
        "/Users/madmax/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 "
        "tools/crop_named_sheet.py ..."
    ) from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Crop a generated grid sheet into named assets.")
    parser.add_argument("--sheet", required=True, type=Path)
    parser.add_argument("--cols", required=True, type=int)
    parser.add_argument("--rows", required=True, type=int)
    parser.add_argument("--inset", type=int, default=4, help="Pixels to trim from each grid-cell edge to remove separator lines.")
    parser.add_argument("--outputs", required=True, nargs="+", type=Path)
    args = parser.parse_args()

    source = Image.open(args.sheet).convert("RGB")
    width, height = source.size
    crop_width = width // args.cols
    crop_height = height // args.rows
    if len(args.outputs) > args.cols * args.rows:
        raise SystemExit("More outputs than grid cells.")

    for index, output in enumerate(args.outputs):
        row = index // args.cols
        col = index % args.cols
        output.parent.mkdir(parents=True, exist_ok=True)
        left = col * crop_width + args.inset
        top = row * crop_height + args.inset
        right = (col + 1) * crop_width - args.inset
        bottom = (row + 1) * crop_height - args.inset
        cell = source.crop((left, top, right, bottom))
        cleaned = ImageOps.fit(
            cell,
            (crop_width, crop_height),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        cleaned.save(output)
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
