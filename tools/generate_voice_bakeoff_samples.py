#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
import wave
from pathlib import Path

from asset_pipeline_common import AUDIO, CONTENT, utc_now, write_json
from import_voice_bakeoff_samples import SAMPLE_LINES

MANIFEST = AUDIO / "manifests" / "voice_bakeoff_manifest.json"

LOCAL_VOICES = {
    "macos_grandma_en": ("Grandma (English (US))", ["en_calm_opening", "en_suspense", "en_bedtime_closing"]),
    "macos_samantha_en": ("Samantha", ["en_calm_opening", "en_suspense", "en_bedtime_closing"]),
    "macos_yuna_ko": ("Yuna", ["ko_calm_opening", "ko_suspense", "ko_bedtime_closing"]),
    "macos_grandma_ko": ("Grandma (Korean (South Korea))", ["ko_calm_opening", "ko_suspense", "ko_bedtime_closing"]),
}


def duration(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / float(handle.getframerate())


def synthesize(voice: str, text: str, output: Path, rate: int = 145) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="moonjar-voice-bakeoff-") as tmp:
        aiff = Path(tmp) / "sample.aiff"
        subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", str(aiff), text], check=True)
        subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16", str(aiff), str(output)], check=True)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {
        "schemaVersion": "1.0.0",
        "generatedAt": utc_now(),
        "purpose": "Short voice-provider bakeoff samples before full narration generation.",
        "sampleLines": SAMPLE_LINES,
        "entries": [],
    }

    existing = [
        entry for entry in manifest.get("entries", [])
        if not str(entry.get("provider", "")).startswith("macos_")
    ]
    generated = 0

    for provider, (voice, sample_ids) in LOCAL_VOICES.items():
        for sample_id in sample_ids:
            text = SAMPLE_LINES[sample_id]
            output = AUDIO / "synthetic-draft" / "voice-bakeoff" / provider / f"{sample_id}.wav"
            synthesize(voice, text, output)
            existing.append(
                {
                    "provider": provider,
                    "sampleId": sample_id,
                    "language": "ko" if sample_id.startswith("ko_") else "en",
                    "text": text,
                    "outputFile": str(output.relative_to(CONTENT)),
                    "status": "synthetic_draft",
                    "voice": voice,
                    "model": "macOS system speech",
                    "timestamp": utc_now(),
                    "duration": round(duration(output), 3),
                    "notes": "Local baseline sample only. Useful for functional comparison, not production-quality narration.",
                    "reviewer": None,
                    "reviewDate": None,
                    "warmthReview": "not_reviewed",
                    "pronunciationReview": "not_reviewed",
                    "pacingReview": "not_reviewed",
                    "childFriendlinessReview": "not_reviewed",
                    "licensingReview": "not_reviewed",
                }
            )
            generated += 1

    manifest["entries"] = existing
    manifest["generatedAt"] = utc_now()
    write_json(MANIFEST, manifest)
    print(f"Generated {generated} macOS voice bakeoff samples.")
    print(f"Manifest: {MANIFEST.relative_to(CONTENT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
