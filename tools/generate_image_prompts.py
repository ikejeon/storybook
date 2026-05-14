#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
OUTPUT = ROOT / "tools" / "output" / "image_prompts.md"
STYLE_BIBLE = CONTENT / "style" / "moonjar_style_bible.json"
LAYER_MANIFEST = CONTENT / "animation" / "layer_manifest.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_optional(path: Path) -> dict:
    if not path.exists():
        return {}
    return load(path)


def layer_lookup() -> dict[tuple[str, str], dict]:
    if not LAYER_MANIFEST.exists():
        return {}
    manifest = load(LAYER_MANIFEST)
    return {
        (entry.get("storyId"), entry.get("sceneId")): entry
        for entry in manifest.get("scenes", [])
        if isinstance(entry, dict)
    }


def main() -> None:
    catalog = load(CONTENT / "catalog.json")
    lines = [
        "# Moon Jar Stories Image Prompts",
        "",
        "Use these prompts with the global style bible and the per-book character bible listed under each title. Keep character designs consistent within each book.",
        "",
        f"Global style bible: `shared-content/{STYLE_BIBLE.relative_to(CONTENT)}`",
        ""
    ]
    layers_by_scene = layer_lookup()

    for entry in catalog["books"]:
        if entry["status"] != "complete":
            continue
        book = load(CONTENT / entry["bookPath"])
        character_bible = book.get("characterBible", "characters/launch_character_bible.json")
        book_bible = load_optional(CONTENT / character_bible)
        lines.append(f"## {book['title']['ko']} / {book['title']['en']}")
        lines.append("")
        lines.append(f"Character bible: `shared-content/{character_bible}`")
        if book_bible.get("masterArtStylePrompt"):
            lines.append("")
            lines.append(f"Master art style: {book_bible['masterArtStylePrompt']}")
        if book_bible.get("promptPrefix"):
            lines.append("")
            lines.append(f"Prompt prefix: {book_bible['promptPrefix']}")
        if book_bible.get("tigerEmotionalArc"):
            lines.append("")
            lines.append("Tiger emotional arc:")
            for arc in book_bible["tigerEmotionalArc"]:
                pages = ", ".join(str(page) for page in arc.get("pages", []))
                lines.append(f"- {arc.get('phase')}: pages {pages}. {arc.get('direction')}")
        anchor_plan = book_bible.get("anchorApprovalPlan")
        anchor_pages = set(anchor_plan.get("anchorPages", [])) if isinstance(anchor_plan, dict) else set()
        if anchor_plan:
            lines.append("")
            lines.append("Anchor approval gate:")
            lines.append(f"- Status: `{anchor_plan.get('status')}`")
            lines.append(f"- Instruction: {anchor_plan.get('instruction')}")
            lines.append(f"- Anchor pages: {', '.join(str(page) for page in anchor_plan.get('anchorPages', []))}")
        lines.append("")
        lines.append("")
        for page in book["pages"]:
            lines.append(f"### Page {page['pageNumber']:03d} - {page['id']}")
            lines.append("Required prompt packet:")
            lines.append(f"- Global style bible: `shared-content/{STYLE_BIBLE.relative_to(CONTENT)}`")
            if page.get("characterBible"):
                lines.append(f"- Book character bible: `shared-content/{page['characterBible']}`")
            if page["pageNumber"] in anchor_pages:
                lines.append("- Anchor approval page: generate and approve this design before any bulk Sun and Moon regeneration.")
            lines.append("- No text, letters, captions, watermarks, or signatures inside the image.")
            lines.append("- Child-safe ages 3-8; no graphic danger or frightening anatomy.")
            if book_bible.get("negativePrompt"):
                lines.append(f"- Negative prompt: {book_bible['negativePrompt']}")
            plan = layers_by_scene.get((book["id"], page["id"]))
            if plan:
                layers = ", ".join(f"{layer['role']}: {layer['description']}" for layer in plan.get("plannedLayers", []))
                lines.append(f"- Animation/layer plan: `{plan.get('animationType')}`; {layers}")
            lines.append("")
            lines.append(f"Scene prompt: {page['imagePrompt']}")
            lines.append("")
            lines.append(f"Target image asset: `{page.get('imageAsset', '')}`")
            lines.append(f"Image status: `{page.get('imageAssetStatus', 'placeholder')}`")
            lines.append("")
            layers = ", ".join(f"{layer['name']}: {layer['motion']}" for layer in page["animation"]["layers"])
            lines.append(f"Animation: {page['animation']['type']} ({layers})")
            lines.append("")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
