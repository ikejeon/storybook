#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from providers.macos_say import normalize_wav_peak, wav_duration


def iter_wavs(paths: list[Path]) -> list[Path]:
    result: list[Path] = []
    for path in paths:
        if path.is_dir():
            result.extend(sorted(path.rglob("*.wav")))
        elif path.suffix.lower() == ".wav":
            result.append(path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize Moon Jar WAV assets to a target peak.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--target-peak-db", type=float, default=-3.0)
    args = parser.parse_args()

    wavs = iter_wavs(args.paths)
    if not wavs:
        raise SystemExit("No WAV files found.")

    for wav in wavs:
        info = normalize_wav_peak(wav, args.target_peak_db)
        duration = wav_duration(wav)
        print(f"{wav}: duration={duration:.3f}s normalization={info}" if duration else f"{wav}: normalization={info}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
