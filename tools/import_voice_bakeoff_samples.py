#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import wave
from pathlib import Path

from asset_pipeline_common import AUDIO, CONTENT, utc_now, write_json

MANIFEST = AUDIO / "manifests" / "voice_bakeoff_manifest.json"

SAMPLE_LINES = {
    "en_calm_opening": "Long ago, in a quiet mountain village, two children waited for their mother to come home.",
    "en_suspense": "Outside the door, a soft voice called again, but the children knew something was wrong.",
    "en_bedtime_closing": "High in the sky, the children shone gently, watching over the village until morning.",
    "ko_calm_opening": "옛날 깊은 산골 마을에, 어머니를 기다리는 오누이가 살았어요.",
    "ko_suspense": "문밖에서 다시 부드러운 목소리가 들렸지만, 오누이는 어딘가 이상하다는 걸 알았어요.",
    "ko_bedtime_closing": "하늘 높이 올라간 오누이는 아침까지 마을을 포근하게 비추었답니다.",
}


def wav_duration(path: Path) -> float | None:
    if path.suffix.lower() != ".wav":
        return None
    try:
        with wave.open(str(path), "rb") as handle:
            return handle.getnframes() / float(handle.getframerate())
    except wave.Error:
        return None


def output_dir_for_status(status: str) -> Path:
    if status.startswith("human_recorded"):
        return AUDIO / "human-recorded-final" / "voice-bakeoff"
    if status.endswith("_reviewed"):
        return AUDIO / "reviewed" / "voice-bakeoff"
    return AUDIO / "synthetic-draft" / "voice-bakeoff"


def main() -> int:
    parser = argparse.ArgumentParser(description="Import short provider voice-bakeoff samples.")
    parser.add_argument("--provider", required=True, choices=["openai_tts", "elevenlabs_tts", "naver_clova_voice", "google_cloud_tts", "azure_speech", "human_narrator"])
    parser.add_argument("--sample-id", required=True, choices=sorted(SAMPLE_LINES))
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--status", default="synthetic_draft", choices=["synthetic_draft", "synthetic_reviewed", "human_recorded_draft", "human_recorded_reviewed", "human_recorded_final"])
    parser.add_argument("--voice", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"Source audio file missing: {args.source}")

    extension = args.source.suffix.lower()
    if extension not in {".wav", ".mp3", ".m4a", ".aac"}:
        raise SystemExit("Voice bakeoff import accepts .wav, .mp3, .m4a, or .aac files.")

    output = output_dir_for_status(args.status) / args.provider / f"{args.sample_id}{extension}"
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.source, output)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {
        "schemaVersion": "1.0.0",
        "generatedAt": utc_now(),
        "purpose": "Short voice-provider bakeoff samples before full narration generation.",
        "sampleLines": SAMPLE_LINES,
        "entries": [],
    }
    manifest["entries"] = [
        entry for entry in manifest.get("entries", [])
        if not (entry.get("provider") == args.provider and entry.get("sampleId") == args.sample_id)
    ]
    manifest["entries"].append(
        {
            "provider": args.provider,
            "sampleId": args.sample_id,
            "language": "ko" if args.sample_id.startswith("ko_") else "en",
            "text": SAMPLE_LINES[args.sample_id],
            "outputFile": str(output.relative_to(CONTENT)),
            "status": args.status,
            "voice": args.voice,
            "model": args.model,
            "timestamp": utc_now(),
            "duration": round(wav_duration(output) or 0.0, 3) if extension == ".wav" else None,
            "notes": args.notes,
            "reviewer": None,
            "reviewDate": None,
            "warmthReview": "not_reviewed",
            "pronunciationReview": "not_reviewed",
            "pacingReview": "not_reviewed",
            "childFriendlinessReview": "not_reviewed",
            "licensingReview": "not_reviewed",
        }
    )
    manifest["generatedAt"] = utc_now()
    write_json(MANIFEST, manifest)
    print(f"Imported voice bakeoff sample: {output.relative_to(CONTENT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
