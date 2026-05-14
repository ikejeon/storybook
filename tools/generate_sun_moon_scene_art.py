#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import struct
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from asset_pipeline_common import CONTENT, ROOT, load_json, utc_now, write_json

BOOK_PATH = CONTENT / "books" / "sun_moon.json"
IMAGE_MANIFEST = CONTENT / "assets" / "manifests" / "image_manifest.json"
ANCHOR_PLAN = CONTENT / "assets" / "manifests" / "sun_moon_tiger_anchor_plan.json"
STYLE_BIBLE = CONTENT / "style" / "moonjar_style_bible.json"
CHARACTER_BIBLE = CONTENT / "characters" / "sun_moon.character_bible.json"
OUTPUT_DIR = CONTENT / "assets" / "generated-draft" / "images" / "scenes" / "sun-and-moon"
MANUAL_IMPORT_DIR = CONTENT / "assets" / "manual-import" / "images" / "sun-and-moon"
IOS_SHARED_CONTENT = (
    ROOT
    / "ios"
    / "MoonJarStoriesiOS"
    / "Sources"
    / "MoonJarStoriesiOS"
    / "Resources"
    / "shared-content"
)
JOB_EXPORT = ROOT / "tools" / "output" / "sun_moon_scene_regeneration_jobs.json"
STATUS_REPORT = ROOT / "tools" / "output" / "sun_moon_regeneration_status.md"
REJECTION_LIST = ROOT / "tools" / "output" / "sun_moon_regeneration_rejection_list.md"
CONTACT_SHEET_HTML = ROOT / "tools" / "output" / "sun_moon_32_scene_contact_sheet.html"
CONTACT_SHEET_PNG = ROOT / "build" / "screenshots" / "sun-moon-32-scene-contact-sheet.png"

OPENAI_IMAGE_ENDPOINT = "https://api.openai.com/v1/images/generations"
OPENAI_RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses"

APPROVED_ANCHORS = {
    "tiger": "assets/generated-draft/images/approval/sun-and-moon/tiger-character-sheet-v2.png",
    "children": "assets/generated-draft/images/approval/sun-and-moon/child-character-sheet.png",
    "forest": "assets/generated-draft/images/approval/sun-and-moon/forest-scene.png",
    "house": "assets/generated-draft/images/approval/sun-and-moon/house-night-scene.png",
    "chase": "assets/generated-draft/images/approval/sun-and-moon/chase-tension-scene.png",
    "hero": "assets/generated-draft/images/approval/sun-and-moon/app-hero-style.png",
}


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a PNG file: {path}")
    return struct.unpack(">II", header[16:24])


def page_filename(page_number: int) -> str:
    return f"page-{page_number:03d}.png"


def relative_to_content(path: Path) -> str:
    return str(path.relative_to(CONTENT))


def review_defaults(note: str) -> dict[str, Any]:
    return {
        "reviewer": None,
        "reviewDate": None,
        "rejectionReason": None,
        "notes": note,
        "culturalReviewStatus": "not_reviewed",
        "childSafetyReviewStatus": "not_reviewed",
        "productionApprovalStatus": "not_approved",
    }


def phase_for_page(page_number: int) -> str:
    if page_number <= 2:
        return "warmth_before_tiger"
    if page_number <= 6:
        return "phase_1_2_forest_watchful_deceptive"
    if page_number <= 10:
        return "phase_3_house_deception"
    if page_number <= 18:
        return "phase_4_chase_child_safe"
    if page_number <= 27:
        return "phase_5_resolved_defeated"
    return "mythic_sky_resolution"


def reference_paths_for_page(page_number: int) -> list[str]:
    refs = [APPROVED_ANCHORS["tiger"], APPROVED_ANCHORS["children"]]
    phase = phase_for_page(page_number)
    if "forest" in phase or "watchful" in phase:
        refs.append(APPROVED_ANCHORS["forest"])
    elif "house" in phase:
        refs.append(APPROVED_ANCHORS["house"])
    elif "chase" in phase:
        refs.append(APPROVED_ANCHORS["chase"])
    else:
        refs.append(APPROVED_ANCHORS["hero"])
    return [path for path in refs if (CONTENT / path).exists()]


def build_prompt(page: dict[str, Any], style: dict[str, Any], bible: dict[str, Any]) -> str:
    page_number = page["pageNumber"]
    story_beat = page.get("storyBeat", {})
    phase = phase_for_page(page_number)
    negative = bible.get("negativePrompt", "")
    phase_instruction = {
        "warmth_before_tiger": "Warm family setup; if the tiger is implied at all, keep him as a distant unseen forest presence.",
        "phase_1_2_forest_watchful_deceptive": "Tiger direction: mysterious, hungry, watchful, calculating. Lean mature tiger, narrowed amber eyes, shadowed brow, angular muzzle, controlled posture, adult antagonist presence.",
        "phase_3_house_deception": "Tiger direction: disguised/pretending at the house. He may look falsely gentle, but the eye, posture, shadow, paw, tail, or silhouette should feel wrong. Child-safe unease, no horror.",
        "phase_4_chase_child_safe": "Tiger direction: threatening chase tension from distance, eye line, shadow, and posture. No gore, no teeth/claw emphasis, no horror close-up.",
        "phase_5_resolved_defeated": "Tiger direction: defeated/resolved without graphic punishment or silly comedy. Keep dignity and child safety.",
        "mythic_sky_resolution": "Tiger is no longer the focus; emphasize reassuring mythic transformation, moon/sun light, Korean mountain sky, family safety.",
    }[phase]
    return (
        "Generate one production draft scene image for Moon Jar Stories / The Sun and the Moon. "
        "Use the approved anchor direction, especially tiger-character-sheet-v2.png for the antagonist tiger. "
        f"Global style: {style.get('globalStylePrompt') or style.get('masterArtStylePrompt', '')}. "
        f"Book style: {bible.get('masterArtStylePrompt', '')}. "
        f"Character continuity: {bible.get('promptPrefix', '')}. "
        f"Page {page_number} scene: {page.get('imagePrompt', '')}. "
        f"Story purpose: {story_beat.get('purpose', '')}; emotion: {story_beat.get('emotion', '')}. "
        f"{phase_instruction} "
        "Composition requirements: landscape 3:2 or 4:3 friendly, fit-safe for iPad two-page spread and mobile portrait reader, "
        "generous safe margins around all faces, ears, hands, and important props, no accidental cropping, no subject touching edges, "
        "clear thumbnail readability, no text or letters inside the image, no watermark/signature/logo. "
        "Style requirements: premium Korean watercolor, gouache, soft ink, hanji paper grain, warm lantern light, deep indigo, moon ivory, persimmon, jade, lotus pink, muted gold. "
        "Child-safety requirements: suspenseful folktale tension, but no blood, gore, graphic violence, dead/injured parent imagery, horror anatomy, jump scare, sharp teeth/claw emphasis. "
        f"Negative prompt: {negative}, plush toy tiger, mascot tiger, cute companion tiger, baby-faced tiger, oversized innocent tiger eyes, goofy grin, text, watermark, cropped faces, cut-off ears, cut-off hands."
    )


def build_jobs() -> list[dict[str, Any]]:
    book = load_json(BOOK_PATH)
    style = load_json(STYLE_BIBLE)
    bible = load_json(CHARACTER_BIBLE)
    jobs = []
    for page in book["pages"]:
        page_number = page["pageNumber"]
        output = OUTPUT_DIR / page_filename(page_number)
        jobs.append(
            {
                "storyId": book["id"],
                "storySlug": book["slug"],
                "sceneId": page["id"],
                "pageNumber": page_number,
                "phase": phase_for_page(page_number),
                "outputFile": relative_to_content(output),
                "prompt": build_prompt(page, style, bible),
                "referenceImages": reference_paths_for_page(page_number),
                "status": "pending_generation",
            }
        )
    return jobs


def encode_image_data_url(relative_path: str) -> str:
    path = CONTENT / relative_path
    mime = "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def find_image_base64(value: Any) -> str | None:
    if isinstance(value, dict):
        if value.get("type") == "image_generation_call" and isinstance(value.get("result"), str):
            return value["result"]
        for key in ("b64_json", "image_base64", "result"):
            if isinstance(value.get(key), str) and len(value[key]) > 1000:
                return value[key]
        for child in value.values():
            found = find_image_base64(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_image_base64(child)
            if found:
                return found
    return None


def openai_post(endpoint: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI image request failed: HTTP {exc.code}: {body}") from exc


def generate_with_openai_image_api(job: dict[str, Any], output: Path, *, model: str, size: str, quality: str, timeout: int) -> None:
    payload = {
        "model": model,
        "prompt": job["prompt"],
        "size": size,
        "quality": quality,
        "n": 1,
    }
    response = openai_post(OPENAI_IMAGE_ENDPOINT, payload, timeout)
    image_b64 = find_image_base64(response)
    if not image_b64:
        raise RuntimeError(f"OpenAI Images response did not include base64 image data for page {job['pageNumber']}.")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(base64.b64decode(image_b64))


def generate_with_openai_responses_api(job: dict[str, Any], output: Path, *, model: str, size: str, quality: str, timeout: int) -> None:
    content: list[dict[str, Any]] = [{"type": "input_text", "text": job["prompt"]}]
    for reference in job["referenceImages"][:3]:
        content.append({"type": "input_image", "image_url": encode_image_data_url(reference)})
    payload = {
        "model": model,
        "input": [{"role": "user", "content": content}],
        "tools": [{"type": "image_generation", "size": size, "quality": quality, "format": "png"}],
        "tool_choice": {"type": "image_generation"},
    }
    response = openai_post(OPENAI_RESPONSES_ENDPOINT, payload, timeout)
    image_b64 = find_image_base64(response)
    if not image_b64:
        raise RuntimeError(f"OpenAI Responses image tool did not include base64 image data for page {job['pageNumber']}.")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(base64.b64decode(image_b64))


def import_manual_images(jobs: list[dict[str, Any]], source_dir: Path) -> list[dict[str, Any]]:
    imported: list[dict[str, Any]] = []
    missing = []
    for job in jobs:
        filename = page_filename(job["pageNumber"])
        source = source_dir / filename
        if not source.exists():
            missing.append(str(source))
            continue
        png_dimensions(source)
        output = CONTENT / job["outputFile"]
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, output)
        job["status"] = "generated_draft"
        job["provider"] = "manual_import"
        job["generationModel"] = "externally_generated_scene_art"
        job["generationStatus"] = "imported"
        job["sourceFile"] = str(source)
        imported.append(job)
    if missing:
        raise RuntimeError("Manual import is missing required PNG files:\n" + "\n".join(missing[:40]))
    return imported


def generate_openai(jobs: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    generated: list[dict[str, Any]] = []
    for index, job in enumerate(jobs, start=1):
        output = CONTENT / job["outputFile"]
        print(f"[{index}/{len(jobs)}] generating {job['outputFile']}")
        if args.provider == "openai-image":
            generate_with_openai_image_api(
                job,
                output,
                model=args.image_model,
                size=args.size,
                quality=args.quality,
                timeout=args.timeout,
            )
            model = args.image_model
            generation_tool = "openai_image_api"
        else:
            generate_with_openai_responses_api(
                job,
                output,
                model=args.responses_model,
                size=args.size,
                quality=args.quality,
                timeout=args.timeout,
            )
            model = args.responses_model
            generation_tool = "openai_responses_image_generation"
        png_dimensions(output)
        job["status"] = "generated_draft"
        job["provider"] = generation_tool
        job["generationModel"] = model
        job["generationStatus"] = "generated"
        job["sourceFile"] = None
        generated.append(job)
        if args.delay_seconds:
            time.sleep(args.delay_seconds)
    return generated


def update_manifest(completed_jobs: list[dict[str, Any]], *, provider: str, blocked: bool = False, blocked_reason: str | None = None) -> None:
    manifest = load_json(IMAGE_MANIFEST)
    timestamp = utc_now()
    job_by_scene = {job["sceneId"]: job for job in completed_jobs}
    for entry in manifest.get("sceneEntries", []):
        if entry.get("storySlug") != "sun-and-moon":
            continue
        if blocked:
            entry["artDirectionStatus"] = "needs_tiger_anchor_regeneration"
            entry["anchorApprovalRequiredBeforeRegeneration"] = True
            entry["regenerationBlockedReason"] = blocked_reason
            continue
        job = job_by_scene.get(entry.get("sceneId"))
        if not job:
            continue
        output_file = job["outputFile"]
        width, height = png_dimensions(CONTENT / output_file)
        candidate = {
            "outputFile": output_file,
            "status": "generated_draft",
            "provider": job["provider"],
            "model": job["generationModel"],
            "generationStatus": job["generationStatus"],
            "timestamp": timestamp,
            "sourceFile": job.get("sourceFile"),
            "referenceImages": job.get("referenceImages", []),
            "dimensions": {"width": width, "height": height},
            "prompt": job["prompt"],
        }
        candidate.update(review_defaults("Regenerated Sun and Moon draft from approved anchor direction. Not reviewed and not final."))
        candidates = entry.setdefault("candidates", [])
        candidates[:] = [item for item in candidates if item.get("outputFile") != output_file]
        candidates.append(candidate)
        entry["prompt"] = job["prompt"]
        entry["rawPrompt"] = job["prompt"]
        entry["outputFile"] = output_file
        entry["status"] = "generated_draft"
        entry["generationTool"] = job["provider"]
        entry["generationModel"] = job["generationModel"]
        entry["generationStatus"] = job["generationStatus"]
        entry["timestamp"] = timestamp
        entry["dimensions"] = {"width": width, "height": height}
        entry["artDirectionStatus"] = "regenerated_from_approved_tiger_anchor_pending_review"
        entry["anchorApprovalRequiredBeforeRegeneration"] = False
        entry["regeneratedFromAnchorSet"] = [
            "tiger-character-sheet-v2.png",
            "child-character-sheet.png",
            "forest-scene.png",
            "house-night-scene.png",
            "chase-tension-scene.png",
        ]
        entry.pop("regenerationBlockedReason", None)
        entry.update(review_defaults("Generated draft only. Needs human creative, cultural, child-safety, and crop review."))

    manifest["generatedAt"] = timestamp
    manifest["sunMoonRegeneration"] = {
        "status": "blocked_no_image_provider_credentials" if blocked else "generated_draft_regeneration_complete_pending_review",
        "provider": provider,
        "expectedSceneCount": 32,
        "completedSceneCount": 0 if blocked else len(completed_jobs),
        "approvedAnchorReference": APPROVED_ANCHORS["tiger"],
        "manualImportDirectory": relative_to_content(MANUAL_IMPORT_DIR),
        "requiredFilenames": [page_filename(i) for i in range(1, 33)],
        "blockedReason": blocked_reason,
        "updatedAt": timestamp,
    }
    write_json(IMAGE_MANIFEST, manifest)


def write_job_export(jobs: list[dict[str, Any]]) -> None:
    payload = {
        "schemaVersion": "1.0.0",
        "generatedAt": utc_now(),
        "storyId": "book.sun_moon",
        "storySlug": "sun-and-moon",
        "purpose": "Ready-to-run Sun and Moon 32-scene generated-draft art regeneration queue.",
        "approvedAnchorReference": APPROVED_ANCHORS["tiger"],
        "manualImportDirectory": relative_to_content(MANUAL_IMPORT_DIR),
        "jobs": jobs,
    }
    write_json(JOB_EXPORT, payload)


def write_status_report(*, provider_available: bool, completed_jobs: list[dict[str, Any]], blocked_reason: str | None, commands: list[str]) -> None:
    lines = [
        "# Sun and Moon Scene Regeneration Status",
        "",
        f"Generated: {datetime.now(timezone.utc).replace(microsecond=0).isoformat()}",
        "",
        f"- Image provider credentials available: `{provider_available}`",
        f"- Scenes actually regenerated/imported this run: {len(completed_jobs)}",
        f"- Scene target count: 32",
        "- Status used for regenerated/imported art: `generated_draft`",
        "- Final promotion remains blocked until human creative, cultural, child-safety, and crop review.",
        "",
    ]
    if blocked_reason:
        lines.extend(
            [
                "## Blocker",
                "",
                blocked_reason,
                "",
            ]
        )
    lines.extend(
        [
            "## Ready Commands",
            "",
        ]
    )
    for command in commands:
        lines.append(f"```bash\n{command}\n```")
    lines.extend(
        [
            "## Output Paths",
            "",
            f"- Job queue: `{JOB_EXPORT.relative_to(ROOT)}`",
            f"- Manual import folder: `{MANUAL_IMPORT_DIR.relative_to(ROOT)}`",
            f"- Generated draft scenes: `{OUTPUT_DIR.relative_to(ROOT)}`",
            f"- Contact sheet HTML: `{CONTACT_SHEET_HTML.relative_to(ROOT)}`",
            f"- Contact sheet PNG, when Pillow is available: `{CONTACT_SHEET_PNG.relative_to(ROOT)}`",
            f"- Rejection/blocker list: `{REJECTION_LIST.relative_to(ROOT)}`",
            f"- Image manifest: `{IMAGE_MANIFEST.relative_to(ROOT)}`",
        ]
    )
    screenshot_paths = [
        ROOT / "build" / "screenshots" / "current-pass" / "ios-launched.png",
        ROOT / "build" / "screenshots" / "current-pass" / "ios-reader-real-book-page3.png",
    ]
    existing_screenshots = [path for path in screenshot_paths if path.exists()]
    if existing_screenshots:
        lines.extend(["", "## App Evidence Notes", ""])
        for path in existing_screenshots:
            lines.append(f"- Fresh iOS simulator screenshot: `{path.relative_to(ROOT)}`")
        lines.append("- Current visible Sun and Moon scene art is still pre-regeneration; use these screenshots as app-state evidence, not final art proof.")
    STATUS_REPORT.parent.mkdir(parents=True, exist_ok=True)
    STATUS_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_manual_import_readme() -> None:
    MANUAL_IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    required = "\n".join(f"- `{page_filename(i)}`" for i in range(1, 33))
    text = f"""# Sun and Moon Manual Scene Art Import

Place externally generated or commissioned PNG drafts for The Sun and the Moon here, using exact filenames:

{required}

Then run:

```bash
python3 tools/generate_sun_moon_scene_art.py --provider manual-import --manual-source-dir {MANUAL_IMPORT_DIR.relative_to(ROOT)}
```

The script copies files into `shared-content/assets/generated-draft/images/scenes/sun-and-moon/`, updates `image_manifest.json`, keeps status as `generated_draft`, and syncs the iOS Swift package resources.

Do not place final commissioned art here. Final art belongs in the `final/` asset tier only after complete review metadata exists.
"""
    (MANUAL_IMPORT_DIR / "README.md").write_text(text, encoding="utf-8")


def write_contact_sheet(jobs: list[dict[str, Any]]) -> None:
    CONTACT_SHEET_HTML.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for job in jobs:
        path = CONTENT / job["outputFile"]
        rel = Path(os.path.relpath(path, CONTACT_SHEET_HTML.parent))
        exists = path.exists()
        if exists:
            img_html = f'<img src="{rel.as_posix()}" alt="page {job["pageNumber"]}">'
        else:
            img_html = '<div class="empty">missing</div>'
        rows.append(
            f"<section class='card {'missing' if not exists else ''}'>"
            f"<div class='frame'>{img_html}</div>"
            f"<h2>Page {job['pageNumber']:03d}</h2><p>{job['phase']}</p></section>"
        )
    html = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>Sun and Moon 32 Scene Contact Sheet</title>
<style>
body { margin: 0; padding: 28px; background: #071426; color: #f8efd9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
h1 { margin: 0 0 18px; font-size: 24px; }
.grid { display: grid; grid-template-columns: repeat(4, minmax(180px, 1fr)); gap: 16px; }
.card { background: #101d32; border: 1px solid rgba(248,239,217,.22); border-radius: 12px; padding: 10px; }
.frame { aspect-ratio: 3 / 2; background: #efe3c4; border-radius: 8px; overflow: hidden; display: grid; place-items: center; }
img { width: 100%; height: 100%; object-fit: contain; display: block; }
h2 { margin: 8px 0 2px; font-size: 14px; color: #f2c779; }
p { margin: 0; font-size: 12px; color: #cfc3a9; }
.missing { border-color: #d95a34; }
.empty { color: #9d3b25; }
</style>
<h1>Sun and Moon 32 Scene Contact Sheet</h1>
<main class="grid">
""" + "\n".join(rows) + "\n</main>\n</html>\n"
    CONTACT_SHEET_HTML.write_text(html, encoding="utf-8")

    try:
        from PIL import Image, ImageDraw  # type: ignore
    except Exception:
        return

    thumbs: list[tuple[int, Path, str]] = [(job["pageNumber"], CONTENT / job["outputFile"], job["phase"]) for job in jobs]
    cols = 4
    thumb_w, thumb_h = 320, 214
    label_h = 40
    rows_count = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_w, rows_count * (thumb_h + label_h)), (7, 20, 38))
    draw = ImageDraw.Draw(sheet)
    for idx, (page_number, image_path, phase) in enumerate(thumbs):
        x = (idx % cols) * thumb_w
        y = (idx // cols) * (thumb_h + label_h)
        if image_path.exists():
            image = Image.open(image_path).convert("RGB")
            image.thumbnail((thumb_w - 12, thumb_h - 12))
            px = x + (thumb_w - image.width) // 2
            py = y + (thumb_h - image.height) // 2
            sheet.paste(image, (px, py))
        draw.text((x + 10, y + thumb_h + 8), f"Page {page_number:03d} - {phase}", fill=(242, 199, 121))
    CONTACT_SHEET_PNG.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET_PNG)


def sync_ios_resources(completed_jobs: list[dict[str, Any]]) -> None:
    if not IOS_SHARED_CONTENT.exists():
        return
    target_manifest = IOS_SHARED_CONTENT / "assets" / "manifests" / "image_manifest.json"
    target_manifest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(IMAGE_MANIFEST, target_manifest)
    for job in completed_jobs:
        source = CONTENT / job["outputFile"]
        target = IOS_SHARED_CONTENT / job["outputFile"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def write_blocked_outputs(jobs: list[dict[str, Any]], reason: str) -> None:
    write_job_export(jobs)
    update_manifest([], provider="none", blocked=True, blocked_reason=reason)
    sync_ios_resources([])
    write_manual_import_readme()
    write_contact_sheet(jobs)
    write_status_report(
        provider_available=False,
        completed_jobs=[],
        blocked_reason=reason,
        commands=[
            "OPENAI_API_KEY=... python3 tools/generate_sun_moon_scene_art.py --provider openai-responses",
            "python3 tools/generate_sun_moon_scene_art.py --provider manual-import --manual-source-dir shared-content/assets/manual-import/images/sun-and-moon",
        ],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate or import The Sun and the Moon 32 scene images as generated_draft assets.")
    parser.add_argument("--provider", choices=["auto", "openai-responses", "openai-image", "manual-import"], default="auto")
    parser.add_argument("--manual-source-dir", type=Path, default=MANUAL_IMPORT_DIR)
    parser.add_argument("--size", default=os.environ.get("MOONJAR_OPENAI_IMAGE_SIZE", "1536x1024"))
    parser.add_argument("--quality", default=os.environ.get("MOONJAR_OPENAI_IMAGE_QUALITY", "high"))
    parser.add_argument("--image-model", default=os.environ.get("MOONJAR_OPENAI_IMAGE_MODEL", "gpt-image-1"))
    parser.add_argument("--responses-model", default=os.environ.get("MOONJAR_OPENAI_RESPONSES_MODEL", "gpt-5"))
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--delay-seconds", type=float, default=0.0)
    parser.add_argument("--no-ios-sync", action="store_true")
    args = parser.parse_args()

    jobs = build_jobs()
    write_job_export(jobs)
    write_manual_import_readme()

    provider = args.provider
    if provider == "auto":
        provider = "openai-responses" if os.environ.get("OPENAI_API_KEY") else "manual-import"

    completed: list[dict[str, Any]]
    try:
        if provider == "manual-import":
            source_dir = args.manual_source_dir
            if not source_dir.exists() or not any(source_dir.glob("page-*.png")):
                reason = (
                    "Real image generation is blocked because no image-generation provider/API/MCP is configured in this environment, "
                    f"and no manual PNG import set exists at `{source_dir}`. Add `OPENAI_API_KEY` or place exact `page-001.png` through `page-032.png` files in the manual import folder."
                )
                write_blocked_outputs(jobs, reason)
                print(reason, file=sys.stderr)
                return 2
            completed = import_manual_images(jobs, source_dir)
            provider_name = "manual_import"
        elif provider in {"openai-responses", "openai-image"}:
            if not os.environ.get("OPENAI_API_KEY"):
                reason = "Real image generation is blocked because `OPENAI_API_KEY` is not configured."
                write_blocked_outputs(jobs, reason)
                print(reason, file=sys.stderr)
                return 2
            args.provider = provider
            completed = generate_openai(jobs, args)
            provider_name = provider
        else:
            raise RuntimeError(f"Unsupported provider: {provider}")
    except Exception as exc:
        reason = f"Sun and Moon scene regeneration failed before completion: {exc}"
        write_blocked_outputs(jobs, reason)
        print(reason, file=sys.stderr)
        return 1

    update_manifest(completed, provider=provider_name)
    write_contact_sheet(completed)
    if not args.no_ios_sync:
        sync_ios_resources(completed)
    write_status_report(
        provider_available=provider != "manual-import",
        completed_jobs=completed,
        blocked_reason=None,
        commands=[
            "python3 tools/generate_asset_status_report.py",
            "python3 tools/validate_assets.py",
            "python3 tools/validate_production_readiness.py --level generated-draft",
        ],
    )
    print(f"Sun and Moon generated_draft scene assets ready: {len(completed)}/32")
    print(f"Contact sheet: {CONTACT_SHEET_HTML.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
