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
        "tools/crop_storyboard_sheet.py ..."
    ) from exc


def crop(source: Path, output: Path, crop_width: int, crop_height: int, row: int, col: int, *, inset: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    source_image = Image.open(source).convert("RGB")
    left = col * crop_width + inset
    top = row * crop_height + inset
    right = (col + 1) * crop_width - inset
    bottom = (row + 1) * crop_height - inset
    cell = source_image.crop((left, top, right, bottom))
    cleaned = ImageOps.fit(
        cell,
        (crop_width, crop_height),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )
    cleaned.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Crop a generated storyboard sheet into scene images.")
    parser.add_argument("--sheet", required=True, type=Path)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--start-page", required=True, type=int)
    parser.add_argument("--count", type=int, default=4)
    parser.add_argument("--cols", type=int, default=2)
    parser.add_argument("--rows", type=int, default=2)
    parser.add_argument("--inset", type=int, default=4, help="Pixels to trim from each grid-cell edge to remove separator lines.")
    parser.add_argument("--output-root", type=Path, default=Path("shared-content/assets/generated-draft/images/scenes"))
    args = parser.parse_args()

    with Image.open(args.sheet) as image:
        width, height = image.size
    crop_width = width // args.cols
    crop_height = height // args.rows
    cells: list[tuple[int, int]] = []
    for row in range(args.rows):
        for col in range(args.cols):
            cells.append((row, col))

    for index in range(args.count):
        page_number = args.start_page + index
        output = args.output_root / args.slug / f"page-{page_number:03d}.png"
        row, col = cells[index]
        crop(args.sheet, output, crop_width, crop_height, row, col, inset=args.inset)
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
