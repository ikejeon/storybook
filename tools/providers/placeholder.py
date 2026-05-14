from __future__ import annotations

import shutil
from pathlib import Path

from .base import ProviderResult


class PlaceholderImageProvider:
    name = "placeholder"

    def __init__(self, source_file: Path | None = None):
        self.source_file = source_file

    def generate_image(self, prompt: str, output_file: Path, *, seed: int | None = None) -> ProviderResult:
        if self.source_file is None or not self.source_file.exists():
            raise FileNotFoundError("Placeholder image generation requires an existing source file.")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        if self.source_file.resolve() != output_file.resolve():
            shutil.copy2(self.source_file, output_file)
        return ProviderResult(
            output_file=output_file,
            status="placeholder",
            provider=self.name,
            model="local_placeholder_copy",
            generation_status="copied_placeholder",
            seed=seed,
        )

    def upscale_image(self, source_file: Path, output_file: Path) -> ProviderResult:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, output_file)
        return ProviderResult(
            output_file=output_file,
            status="placeholder",
            provider=self.name,
            model="no_upscale_placeholder_copy",
            generation_status="copied_without_upscale",
        )

    def extract_layers(self, source_file: Path, output_dir: Path, layer_plan: dict) -> ProviderResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / source_file.name
        shutil.copy2(source_file, output_file)
        return ProviderResult(
            output_file=output_file,
            status="placeholder",
            provider=self.name,
            model="single_scene_layer_placeholder",
            generation_status="kept_single_scene_image",
            metadata={"layerPlan": layer_plan},
        )


class PlaceholderSoundProvider:
    name = "placeholder"

    def generate_or_import(self, description: str, output_file: Path, *, source_file: Path | None = None) -> ProviderResult:
        if source_file is None or not source_file.exists():
            raise FileNotFoundError("Placeholder sound import requires an existing source file.")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        if source_file.resolve() != output_file.resolve():
            shutil.copy2(source_file, output_file)
        return ProviderResult(
            output_file=output_file,
            status="placeholder",
            provider=self.name,
            model="local_placeholder_copy",
            generation_status="copied_placeholder",
        )
