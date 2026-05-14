#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import sys
import tempfile
import wave
from array import array
from pathlib import Path

from asset_pipeline_common import (
    AUDIO,
    AUDIO_STATUSES,
    CONTENT,
    complete_books,
    content_path,
    page_asset_name,
    utc_now,
    write_json,
)

AUDIO_MANIFEST = AUDIO / "manifests" / "audio_manifest.json"
NARRATION_DIR = AUDIO / "narration"
PROMPT_EXPORT = Path("tools/output/audio_prompts.md")


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise SystemExit(f"Required audio tool not found: {name}")
    return path


def wav_duration(path: Path) -> float | None:
    if not path.exists():
        return None
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / float(handle.getframerate())


def normalize_wav_peak(path: Path, target_peak_db: float) -> dict:
    with wave.open(str(path), "rb") as handle:
        params = handle.getparams()
        frames = handle.readframes(handle.getnframes())

    if params.sampwidth != 2:
        return {
            "applied": False,
            "reason": f"unsupported sample width {params.sampwidth}",
            "targetPeakDb": target_peak_db,
        }

    samples = array("h")
    samples.frombytes(frames)
    if sys.byteorder != "little":
        samples.byteswap()

    peak = max((abs(sample) for sample in samples), default=0)
    if peak == 0:
        return {"applied": False, "reason": "silent audio", "targetPeakDb": target_peak_db}

    target_peak = int(32767 * math.pow(10, target_peak_db / 20.0))
    scale = min(target_peak / peak, 6.0)
    if abs(scale - 1.0) < 0.01:
        return {
            "applied": False,
            "reason": "already near target peak",
            "sourcePeak": peak,
            "targetPeak": target_peak,
            "targetPeakDb": target_peak_db,
        }

    for index, sample in enumerate(samples):
        samples[index] = max(-32768, min(32767, int(sample * scale)))

    if sys.byteorder != "little":
        samples.byteswap()

    with wave.open(str(path), "wb") as handle:
        handle.setparams(params)
        handle.writeframes(samples.tobytes())

    return {
        "applied": True,
        "sourcePeak": peak,
        "targetPeak": target_peak,
        "scale": round(scale, 4),
        "targetPeakDb": target_peak_db,
    }


def synthesize_with_say(text: str, output: Path, voice: str, rate: int, target_peak_db: float) -> tuple[float, dict]:
    require_tool("say")
    require_tool("afconvert")
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="moonjar-tts-") as tmp:
        aiff = Path(tmp) / "speech.aiff"
        subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", str(aiff), text], check=True)
        subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16", str(aiff), str(output)], check=True)

    normalization = normalize_wav_peak(output, target_peak_db)
    duration = wav_duration(output)
    return duration or 0.0, normalization


def manifest_for_existing_sound(asset_type: str, relative_path: str, status: str = "placeholder") -> dict:
    path = content_path(relative_path)
    return {
        "assetType": asset_type,
        "outputFile": relative_path,
        "tool": "existing_placeholder",
        "model": None,
        "duration": round(wav_duration(path) or 0.0, 3) if path.exists() else None,
        "status": status,
        "generationStatus": "kept_existing_placeholder" if path.exists() else "missing",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate offline narration assets for Moon Jar Stories.")
    parser.add_argument("--voice", default="Grandma (Korean (South Korea))", help="macOS say voice for Korean narration.")
    parser.add_argument("--rate", default=155, type=int, help="macOS say speech rate.")
    parser.add_argument("--target-peak-db", default=-3.0, type=float, help="Peak normalization target in dBFS.")
    parser.add_argument("--dry-run", action="store_true", help="Write no audio and do not update book JSON.")
    args = parser.parse_args()

    generated_at = utc_now()
    narration_entries: list[dict] = []
    ambient_entries: list[dict] = []

    for _entry, book_path, book in complete_books():
        book["narrationAudioStatus"] = "synthetic_draft"
        seen_ambient: set[str] = set()
        for page in book["pages"]:
            output_relative = f"audio/narration/{book['slug']}/ko/{page_asset_name(page['pageNumber'], 'wav')}"
            output_path = content_path(output_relative)
            duration = 0.0
            normalization = {"applied": False, "reason": "dry run", "targetPeakDb": args.target_peak_db}
            generation_status = "dry_run"

            if not args.dry_run:
                duration, normalization = synthesize_with_say(
                    text=page["narrationScript"],
                    output=output_path,
                    voice=args.voice,
                    rate=args.rate,
                    target_peak_db=args.target_peak_db,
                )
                page["narrationAudio"] = output_relative
                page["narrationAudioStatus"] = "synthetic_draft"
                page["narrationVoice"] = args.voice
                page["audioGenerationTool"] = "macos_say"
                generation_status = "generated"

            narration_entries.append(
                {
                    "assetType": "korean_narration",
                    "storyId": book["id"],
                    "storySlug": book["slug"],
                    "sceneId": page["id"],
                    "pageNumber": page["pageNumber"],
                    "koreanNarrationText": page["narrationScript"],
                    "englishNarrationText": page["englishText"],
                    "outputFile": output_relative,
                    "voice": args.voice,
                    "tool": "macos_say",
                    "model": "macOS system speech voice",
                    "timestamp": generated_at,
                    "duration": round(duration, 3),
                    "normalization": normalization,
                    "status": "synthetic_draft",
                    "generationStatus": generation_status,
                }
            )

            ambient = page.get("ambientAudio")
            if ambient and ambient not in seen_ambient:
                seen_ambient.add(ambient)
                ambient_entries.append(manifest_for_existing_sound("ambient_loop", ambient))

        if not args.dry_run:
            write_json(book_path, book)

    ui_sound_entries = [
        manifest_for_existing_sound("page_flip_sound", "audio/ui/page-flip.wav"),
        manifest_for_existing_sound("button_tap_sound", "audio/ui/button-tap.wav"),
    ]

    manifest = {
        "schemaVersion": "1.0.0",
        "generatedAt": generated_at,
        "promptSource": str(PROMPT_EXPORT),
        "provider": "macos_say",
        "notes": [
            "No live TTS is performed inside the child app.",
            "This narration was generated offline/dev-time using local macOS Korean speech voices.",
            "Replace synthetic drafts with human_recorded_final narration before production release.",
        ],
        "statusVocabulary": sorted(AUDIO_STATUSES),
        "narrationEntries": narration_entries,
        "ambientEntries": ambient_entries,
        "uiSoundEntries": ui_sound_entries,
    }
    write_json(AUDIO_MANIFEST, manifest)

    generated = sum(1 for item in narration_entries if item["generationStatus"] == "generated")
    print(
        f"Audio manifest written: {AUDIO_MANIFEST.relative_to(CONTENT.parent)} "
        f"({len(narration_entries)} narration entries, generated {generated})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
