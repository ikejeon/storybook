from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class ProviderResult:
    output_file: Path
    status: str
    provider: str
    model: str | None
    generation_status: str
    seed: int | None = None
    duration: float | None = None
    normalization: dict | None = None
    metadata: dict = field(default_factory=dict)


class ImageProvider(Protocol):
    name: str

    def generate_image(self, prompt: str, output_file: Path, *, seed: int | None = None) -> ProviderResult:
        ...

    def upscale_image(self, source_file: Path, output_file: Path) -> ProviderResult:
        ...

    def extract_layers(self, source_file: Path, output_dir: Path, layer_plan: dict) -> ProviderResult:
        ...


class AudioProvider(Protocol):
    name: str

    def synthesize_korean(self, text: str, output_file: Path) -> ProviderResult:
        ...

    def synthesize_english(self, text: str, output_file: Path) -> ProviderResult:
        ...

    def normalize(self, source_file: Path, output_file: Path | None = None) -> ProviderResult:
        ...


class SoundEffectProvider(Protocol):
    name: str

    def generate_or_import(self, description: str, output_file: Path, *, source_file: Path | None = None) -> ProviderResult:
        ...
