#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageOps
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "Pillow is required. In this Codex workspace, run with the bundled Python runtime: "
        "/Users/madmax/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 "
        "tools/repair_generated_scene_crops.py"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
STORYBOARD_ROOT = ROOT / "shared-content" / "assets" / "generated-draft" / "images" / "storyboards"
SCENE_ROOT = ROOT / "shared-content" / "assets" / "generated-draft" / "images" / "scenes"
REPORT = ROOT / "tools" / "output" / "image_crop_alignment_report.md"


def crop_grid(sheet: Path, slug: str, start_page: int, count: int, cols: int, rows: int, inset: int = 4) -> list[Path]:
    source = Image.open(sheet).convert("RGB")
    width, height = source.size
    crop_width = width // cols
    crop_height = height // rows
    outputs: list[Path] = []

    for index in range(count):
        row = index // cols
        col = index % cols
        page_number = start_page + index
        output = SCENE_ROOT / slug / f"page-{page_number:03d}.png"
        output.parent.mkdir(parents=True, exist_ok=True)

        left = col * crop_width + inset
        top = row * crop_height + inset
        right = (col + 1) * crop_width - inset
        bottom = (row + 1) * crop_height - inset
        cell = source.crop((left, top, right, bottom))
        cleaned = ImageOps.fit(
            cell,
            (crop_width, crop_height),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        cleaned.save(output)
        outputs.append(output)

    return outputs


def make_contact_sheet(slug: str) -> Path:
    images = sorted((SCENE_ROOT / slug).glob("page-*.png"))
    thumb_width = 192
    thumb_height = 128
    cols = 5
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_width, rows * thumb_height), (242, 238, 224))
    draw = ImageDraw.Draw(sheet)

    for index, path in enumerate(images):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        x = (index % cols) * thumb_width + (thumb_width - image.width) // 2
        y = (index // cols) * thumb_height + (thumb_height - image.height) // 2
        sheet.paste(image, (x, y))
        label_box = [(index % cols) * thumb_width, (index // cols) * thumb_height, (index % cols) * thumb_width + 52, (index // cols) * thumb_height + 22]
        draw.rectangle(label_box, fill=(255, 255, 255))
        draw.text((label_box[0] + 5, label_box[1] + 4), path.stem, fill=(24, 31, 55))

    output = ROOT / "build" / "screenshots" / f"{slug}-crop-contact.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    return output


def main() -> int:
    repaired: list[Path] = []
    contact_sheets: list[Path] = []

    for slug_dir in sorted(STORYBOARD_ROOT.iterdir()):
        if not slug_dir.is_dir():
            continue
        slug = slug_dir.name

        if slug == "red-bean-porridge-grandma":
            repaired.extend(crop_grid(slug_dir / "sheet-01.png", slug, 1, 4, 2, 2))
            repaired.extend(crop_grid(slug_dir / "sheet-02.png", slug, 5, 4, 2, 2))
            repaired.extend(crop_grid(slug_dir / "sheet-03.png", slug, 9, 12, 3, 4))
        else:
            for sheet_index in range(1, 6):
                sheet = slug_dir / f"sheet-{sheet_index:02d}.png"
                if sheet.exists():
                    repaired.extend(crop_grid(sheet, slug, ((sheet_index - 1) * 4) + 1, 4, 2, 2))

        contact_sheets.append(make_contact_sheet(slug))

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Image Crop Alignment Report",
        "",
        "Generated-draft scene crops were repaired from storyboard sheets using deterministic top-left grid coordinates.",
        "A 4px inset is trimmed from each grid cell before resizing to remove white separator lines.",
        "",
        f"- Scene images repaired: {len(repaired)}",
        "",
        "## Contact Sheets",
        "",
    ]
    lines.extend(f"- `{path}`" for path in contact_sheets)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Repaired generated scene crops: {len(repaired)}")
    print(f"Wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
