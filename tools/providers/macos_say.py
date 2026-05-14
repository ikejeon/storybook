from __future__ import annotations

import math
import shutil
import subprocess
import sys
import tempfile
import wave
from array import array
from pathlib import Path

from .base import ProviderResult


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"Required tool not found: {name}")
    return path


def wav_duration(path: Path) -> float | None:
    if not path.exists():
        return None
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / float(handle.getframerate())


def normalize_wav_peak(path: Path, target_peak_db: float = -3.0) -> dict:
    with wave.open(str(path), "rb") as handle:
        params = handle.getparams()
        frames = handle.readframes(handle.getnframes())

    if params.sampwidth != 2:
        return {"applied": False, "reason": f"unsupported sample width {params.sampwidth}", "targetPeakDb": target_peak_db}

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


class MacOSSayAudioProvider:
    name = "macos_say"

    def __init__(
        self,
        korean_voice: str = "Grandma (Korean (South Korea))",
        english_voice: str = "Samantha",
        rate: int = 155,
        target_peak_db: float = -3.0,
    ):
        self.korean_voice = korean_voice
        self.english_voice = english_voice
        self.rate = rate
        self.target_peak_db = target_peak_db

    def synthesize_korean(self, text: str, output_file: Path) -> ProviderResult:
        return self._synthesize(text, output_file, voice=self.korean_voice, status="synthetic_draft")

    def synthesize_english(self, text: str, output_file: Path) -> ProviderResult:
        return self._synthesize(text, output_file, voice=self.english_voice, status="synthetic_draft")

    def normalize(self, source_file: Path, output_file: Path | None = None) -> ProviderResult:
        target = output_file or source_file
        if output_file is not None and output_file.resolve() != source_file.resolve():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target)
        normalization = normalize_wav_peak(target, self.target_peak_db)
        return ProviderResult(
            output_file=target,
            status="synthetic_draft",
            provider=self.name,
            model="macOS system speech voice",
            generation_status="normalized",
            duration=wav_duration(target),
            normalization=normalization,
        )

    def _synthesize(self, text: str, output_file: Path, *, voice: str, status: str) -> ProviderResult:
        require_tool("say")
        require_tool("afconvert")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="moonjar-tts-") as tmp:
            aiff = Path(tmp) / "speech.aiff"
            subprocess.run(["say", "-v", voice, "-r", str(self.rate), "-o", str(aiff), text], check=True)
            subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16", str(aiff), str(output_file)], check=True)

        normalization = normalize_wav_peak(output_file, self.target_peak_db)
        return ProviderResult(
            output_file=output_file,
            status=status,
            provider=self.name,
            model="macOS system speech voice",
            generation_status="generated",
            duration=wav_duration(output_file),
            normalization=normalization,
            metadata={"voice": voice, "rate": self.rate},
        )
