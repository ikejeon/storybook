#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "Pillow is required. In this Codex workspace, run with the bundled Python runtime: "
        "/Users/madmax/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 "
        "tools/normalize_generated_draft_images.py"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
IMAGE_ROOT = CONTENT / "assets" / "generated-draft" / "images"
TARGET_SIZE = (768, 512)
BLACK_THRESHOLD = 15


def non_black_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    rgb = image.convert("RGB")
    pixels = rgb.load()
    width, height = rgb.size
    min_x, min_y = width, height
    max_x, max_y = -1, -1

    for y in range(height):
        for x in range(width):
            if max(pixels[x, y]) > BLACK_THRESHOLD:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    if max_x < min_x or max_y < min_y:
        return None
    return (min_x, min_y, max_x + 1, max_y + 1)


def normalize_image(path: Path) -> bool:
    original = Image.open(path).convert("RGB")
    bbox = non_black_bbox(original)
    if bbox is None:
        return False

    width, height = original.size
    bbox_width = bbox[2] - bbox[0]
    bbox_height = bbox[3] - bbox[1]

    # Leave already-full images alone. The generated storyboard crops that hurt
    # the app are mostly black with the useful art squeezed into one edge.
    if bbox_width > width * 0.94 and bbox_height > height * 0.94:
        return False

    cropped = original.crop(bbox)
    cleaned = ImageOps.fit(
        cropped,
        TARGET_SIZE,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )
    cleaned.save(path)
    return True


def main() -> int:
    targets: list[Path] = []
    for folder in [
        IMAGE_ROOT / "scenes",
        IMAGE_ROOT / "covers",
        IMAGE_ROOT / "library",
    ]:
        if folder.exists():
            targets.extend(sorted(folder.rglob("*.png")))

    updated = 0
    for path in targets:
        if normalize_image(path):
            updated += 1

    print(f"Normalized generated-draft images: {updated}/{len(targets)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
