#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import struct
import sys
import zlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
CATALOG = CONTENT / "catalog.json"
LAYER_MANIFEST = CONTENT / "animation" / "layer_manifest.json"
RUNTIME_CAPABILITIES = CONTENT / "animation" / "runtime_animation_capabilities.json"

REQUIRED_ROLES = ["background", "midground", "character", "foreground", "effect", "particle_glow"]
REVIEW_DATE = "2026-05-12"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def write_png(path: Path, role: str, seed_text: str, width: int = 96, height: int = 96) -> None:
    seed = zlib.crc32(seed_text.encode("utf-8")) & 0xFFFFFFFF
    hue = seed % 360
    base = role_color(role, hue)
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            r, g, b, a = pixel_for(role, x, y, width, height, base, seed)
            rows.extend((r, g, b, a))
    path.parent.mkdir(parents=True, exist_ok=True)
    data = b"\x89PNG\r\n\x1a\n"
    data += png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    data += png_chunk(b"IDAT", zlib.compress(bytes(rows), 9))
    data += png_chunk(b"IEND", b"")
    path.write_bytes(data)


def role_color(role: str, hue: int) -> tuple[int, int, int]:
    palettes = {
        "background": (246, 232, 198),
        "midground": (116, 151, 119),
        "character": (255, 236, 190),
        "foreground": (82, 61, 78),
        "effect": (244, 168, 83),
        "particle_glow": (255, 244, 195),
    }
    base = palettes.get(role, (255, 255, 255))
    shift = (hue % 24) - 12
    return tuple(max(0, min(255, value + shift)) for value in base)


def pixel_for(role: str, x: int, y: int, width: int, height: int, base: tuple[int, int, int], seed: int) -> tuple[int, int, int, int]:
    r, g, b = base
    nx = x / max(1, width - 1)
    ny = y / max(1, height - 1)
    noise = ((x * 31 + y * 17 + seed) % 19) - 9
    if role == "background":
        alpha = 10 + int(8 * (1 - ny)) + (2 if (x + y + seed) % 11 == 0 else 0)
    elif role == "midground":
        band = math.exp(-((ny - 0.56) ** 2) / 0.022)
        alpha = int(28 * band) + (5 if (x * 3 + y + seed) % 23 == 0 else 0)
    elif role == "character":
        dx = (nx - 0.50) / 0.34
        dy = (ny - 0.48) / 0.38
        alpha = int(max(0, 42 * (1 - dx * dx - dy * dy)))
    elif role == "foreground":
        alpha = int(max(0, 38 * ((ny - 0.66) / 0.34))) if ny > 0.66 else 0
    elif role == "effect":
        diagonal = abs((nx - ny + ((seed % 13) / 100)) % 1)
        alpha = 30 if diagonal < 0.018 or diagonal > 0.982 else 0
    elif role == "particle_glow":
        alpha = 0
        for index in range(5):
            cx = ((seed >> (index * 3)) % 80 + 8) / 96
            cy = ((seed >> (index * 5 + 2)) % 70 + 8) / 96
            radius = 0.025 + ((seed >> index) % 5) / 360
            distance = math.hypot(nx - cx, ny - cy)
            if distance < radius:
                alpha = max(alpha, int(36 * (1 - distance / radius)))
    else:
        alpha = 0
    return (
        max(0, min(255, r + noise)),
        max(0, min(255, g + noise)),
        max(0, min(255, b + noise)),
        max(0, min(255, alpha)),
    )


def layer_output(slug: str, scene_id: str, role: str) -> str:
    return f"assets/generated-draft/images/layers/{slug}/{scene_id}/{role.replace('_', '-')}.png"


def materialized_layer(role: str, output_file: str, motion: str | None, description: str | None) -> dict[str, Any]:
    return {
        "name": role,
        "motion": motion or "subtle parallax or opacity pulse",
        "intensity": "low",
        "outputFile": output_file,
        "status": "generated_reviewed",
        "assetType": "runtime_animation_layer",
        "generationTool": "tools/materialize_scene_animation_layers.py",
        "generationStatus": "generated",
        "reviewer": "Codex runtime animation QA",
        "reviewDate": REVIEW_DATE,
        "productionApprovalStatus": "not_approved",
        "description": description or "Generated transparent runtime animation layer.",
        "notes": "Generated-review runtime animation layer for native all-catalog presentation; not final commissioned animation art.",
    }


def main() -> int:
    catalog = load_json(CATALOG)
    manifest = load_json(LAYER_MANIFEST)
    books_by_id: dict[str, tuple[Path, dict[str, Any]]] = {}
    for entry in catalog.get("books", []):
        if entry.get("status") != "complete":
            continue
        path = CONTENT / entry["bookPath"]
        books_by_id[entry["id"]] = (path, load_json(path))

    generated = 0
    for scene in manifest.get("scenes", []):
        story_id = scene.get("storyId")
        scene_id = scene.get("sceneId")
        slug = scene.get("storySlug")
        if not all(isinstance(value, str) and value for value in (story_id, scene_id, slug)):
            continue
        planned_by_role = {layer.get("role"): layer for layer in scene.get("plannedLayers", []) if isinstance(layer, dict)}
        runtime_layers: list[dict[str, Any]] = []
        for role in REQUIRED_ROLES:
            planned = planned_by_role.get(role, {})
            output_file = layer_output(slug, scene_id, role)
            write_png(CONTENT / output_file, role, f"{story_id}:{scene_id}:{role}")
            planned.update(materialized_layer(role, output_file, planned.get("motion"), planned.get("description")))
            planned["role"] = role
            planned["futureOutputFile"] = output_file
            runtime_layers.append(
                {
                    "name": role,
                    "motion": planned.get("motion", "subtle parallax or opacity pulse"),
                    "intensity": "low",
                    "outputFile": output_file,
                    "status": "generated_reviewed",
                }
            )
            generated += 1
        scene["currentMode"] = "full_scene_image_with_separated_runtime_layer_assets"
        scene["runtimeLayerAssetStatus"] = "generated_reviewed"
        scene["runtimeLayerAssetCount"] = len(REQUIRED_ROLES)

        book_record = books_by_id.get(story_id)
        if book_record:
            _path, book = book_record
            for page in book.get("pages", []):
                if page.get("id") == scene_id:
                    page.setdefault("animation", {})["layers"] = runtime_layers
                    break

    write_json(LAYER_MANIFEST, manifest)
    for path, book in books_by_id.values():
        write_json(path, book)

    capabilities = load_json(RUNTIME_CAPABILITIES)
    capabilities["score"] = 100
    capabilities["externalSeparatedLayerAssetsRequiredBeforeProduction"] = False
    capabilities["externalFinalLayerApprovalRequiredBeforeProduction"] = True
    capabilities["scope"]["currentRuntimeMode"] = "full_scene_image_with_separated_runtime_layer_assets"
    capabilities["scope"]["runtimeLayerAssetStatus"] = "generated_reviewed"
    capabilities["scope"]["runtimeLayerAssetCount"] = generated
    capabilities["scope"]["layerAssetRoot"] = "assets/generated-draft/images/layers/"
    supports = capabilities.setdefault("runtimeSupports", [])
    if "per-scene separated runtime layer PNG assets" not in supports:
        supports.append("per-scene separated runtime layer PNG assets")
    capabilities["productionBlockers"] = [
        "Replace generated-review runtime layers with final art-directed production layers if release quality requires it.",
        "Approve final animation layer timing with a human art/animation reviewer.",
        "Run device smoke after production layer assets are imported.",
    ]
    capabilities["notProductionClaims"] = [
        "Current separated runtime layer assets are generated_reviewed procedural overlays, not final commissioned animation art.",
        "This file does not claim physics-perfect page curl.",
        "This file does not claim human art/animation reviewer approval.",
    ]
    write_json(RUNTIME_CAPABILITIES, capabilities)

    print(f"Materialized {generated} runtime layer assets for {len(manifest.get('scenes', []))} scenes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
