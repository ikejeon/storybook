#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
OUTPUT = ROOT / "tools" / "output" / "audio_prompts.md"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    catalog = load(CONTENT / "catalog.json")
    lines = [
        "# Moon Jar Stories Audio Prompts",
        "",
        "Default direction: English-first narration for the demo app, with optional Korean narration available from the language toggle. Use a warm, premium child-safe storyteller voice, gentle bedtime-safe pacing, and no startling effects.",
        ""
    ]

    for entry in catalog["books"]:
        if entry["status"] != "complete":
            continue
        book = load(CONTENT / entry["bookPath"])
        lines.append(f"## {book['title']['ko']} / {book['title']['en']}")
        lines.append("")
        for page in book["pages"]:
            lines.append(f"### Page {page['pageNumber']:03d} - {page['id']}")
            lines.append(f"English narration: {page['englishText']}")
            lines.append(f"Optional Korean narration: {page['narrationScript']}")
            lines.append("")
            lines.append(f"Direction: {page['audioPrompt']}")
            lines.append("")
            lines.append(f"Target English narration asset: `audio/synthetic-draft/narration/{book['slug']}/en/page-{page['pageNumber']:03d}.wav`")
            lines.append(f"Optional Korean narration asset: `{page.get('narrationAudio', '')}`")
            lines.append(f"Audio status: `{page.get('narrationAudioStatus', 'placeholder')}`")
            lines.append("")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
