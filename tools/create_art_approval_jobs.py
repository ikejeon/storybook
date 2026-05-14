#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from asset_pipeline_common import CONTENT, load_json, utc_now, write_json
from providers.vendor_specs import PROVIDER_SPECS

OUTPUT_DIR = Path("tools/output")
APPROVAL_JOBS = CONTENT / "assets/manifests/art_approval_jobs.json"
STYLE_BIBLE = CONTENT / "style/moonjar_style_bible.json"
SUN_MOON_BIBLE = CONTENT / "characters/sun_moon.character_bible.json"
SUN_MOON_BOOK = CONTENT / "books/sun_moon.json"
ART_CHECKLIST = OUTPUT_DIR / "art_review_checklist.md"
BAKEOFF_REPORT = OUTPUT_DIR / "art_generation_bakeoff_report.md"


def provider_rows() -> list[dict]:
    rows: list[dict] = []
    for spec in PROVIDER_SPECS:
        if spec.capability == "image_generation":
            pass
        elif spec.name != "manual_commissioned_art":
            continue
        rows.append(
            {
                "provider": spec.name,
                "capability": spec.capability,
                "configured": spec.configured,
                "missingEnv": list(spec.missing_env),
                "defaultModel": spec.default_model,
                "docs": spec.docs_url,
                "productionNotes": spec.production_notes,
            }
        )
    return rows


def build_prompt(job_name: str, scene: str, *, extra: str = "") -> str:
    style = load_json(STYLE_BIBLE)
    bible = load_json(SUN_MOON_BIBLE)
    style_prompt = style.get("globalStylePrompt") or style.get("masterArtStylePrompt", "")
    master_style = bible.get("masterArtStylePrompt", "")
    negative = bible.get("negativePrompt", "")
    continuity = bible.get("promptPrefix", "")
    return (
        f"Global Moon Jar Stories style bible: {style_prompt} {master_style} "
        f"Book character bible: {continuity} "
        f"Approval asset: {job_name}. Scene direction: {scene}. {extra} "
        "Requirements: premium Korean watercolor, gouache, soft ink, hanji texture, warm lantern light, "
        "deep indigo and moon ivory atmosphere, child-safe ages 3-8, no text or letters in image, "
        "no watermark, generous safe margins around faces and full bodies, subject not cropped, "
        "review-ready composition. "
        f"Negative prompt: {negative}, text in image, watermark, logo, cropped face, cut-off hands, cut-off ears, "
        "overly cute plush tiger, goofy tiger, friendly companion tiger, horror, gore, blood, jump scare."
    )


def approval_jobs() -> list[dict]:
    book = load_json(SUN_MOON_BOOK)
    pages = {page["pageNumber"]: page for page in book["pages"]}
    timestamp = utc_now()
    previous_jobs = {}
    if APPROVAL_JOBS.exists():
        try:
            previous_jobs = {
                job["jobId"]: job
                for job in load_json(APPROVAL_JOBS).get("jobs", [])
                if job.get("jobId")
            }
        except (json.JSONDecodeError, OSError):
            previous_jobs = {}
    base = {
        "storyId": "book.sun_moon",
        "storySlug": "sun-and-moon",
        "styleBible": "style/moonjar_style_bible.json",
        "characterBible": "characters/sun_moon.character_bible.json",
        "status": "not_generated",
        "provider": "openai_image",
        "generationStatus": "blocked_no_provider_credentials",
        "timestamp": timestamp,
        "reviewer": None,
        "reviewDate": None,
        "reviewerNotes": "",
        "culturalReviewStatus": "not_reviewed",
        "childSafetyReviewStatus": "not_reviewed",
        "productionApprovalStatus": "not_approved",
    }
    specs = [
        (
            "app_hero_style",
            None,
            "A cinematic app hero/banner style image for Moon Jar Stories, moon jar, Korean mountain night, warm cottage window, subtle story magic, no characters cropped.",
            "assets/generated-draft/images/approval/sun-and-moon/app-hero-style.png",
            "Validate overall product mood before any bulk scene work.",
        ),
        (
            "cover_concept",
            None,
            "A cover concept for The Sun and the Moon: siblings protected by moon/sun imagery, tiger presence in forest shadow, suspenseful but child-safe, no title text.",
            "assets/generated-draft/images/approval/sun-and-moon/cover-concept.png",
            "Reject if the tiger dominates like horror art or if faces/subjects are cropped.",
        ),
        (
            "tiger_character_sheet",
            3,
            "Tiger character sheet: cunning, hungry, watchful antagonist; less baby-like face; alert eyes; lean strong posture; consistent stripe pattern; child-safe tension.",
            "assets/generated-draft/images/approval/sun-and-moon/tiger-character-sheet.png",
            "Primary approval gate for tiger tone and continuity.",
        ),
        (
            "child_character_sheet",
            1,
            "Child character sheet for the older and younger siblings: Korean children in simple hanbok, brave/protective and curious, consistent proportions, outfits, and colors.",
            "assets/generated-draft/images/approval/sun-and-moon/child-character-sheet.png",
            "Approve before scenes with children are regenerated.",
        ),
        (
            "forest_scene",
            3,
            pages[3]["imagePrompt"],
            "assets/generated-draft/images/approval/sun-and-moon/forest-scene.png",
            "Mysterious forest presence with mature watchful tiger tone.",
        ),
        (
            "house_night_scene",
            7,
            pages[7]["imagePrompt"],
            "assets/generated-draft/images/approval/sun-and-moon/house-night-scene.png",
            "Unsettling disguised-at-door moment, child-safe.",
        ),
        (
            "chase_tension_scene",
            11,
            pages[11]["imagePrompt"],
            "assets/generated-draft/images/approval/sun-and-moon/chase-tension-scene.png",
            "Threatening chase posture without gore or horror framing.",
        ),
    ]
    jobs: list[dict] = []
    for job_name, page_number, scene, output_file, notes in specs:
        job = dict(base)
        job_id = f"sun_moon_{job_name}"
        job.update(
            {
                "jobId": job_id,
                "pageNumber": page_number,
                "sceneId": pages[page_number]["id"] if page_number else None,
                "assetType": "approval_anchor",
                "prompt": build_prompt(job_name, scene, extra=notes),
                "outputFile": output_file,
                "reviewFocus": notes,
                "bulkGenerationGate": "Do not bulk-generate remaining scenes until this approval set is accepted.",
            }
        )
        previous = previous_jobs.get(job_id, {})
        if (CONTENT / output_file).exists():
            job["status"] = previous.get("status") if previous.get("status") != "not_generated" else "generated_draft"
            job["status"] = job["status"] or "generated_draft"
            job["provider"] = previous.get("provider") or "manual_import"
            job["generationStatus"] = previous.get("generationStatus") or "generated"
            job["generationModel"] = previous.get("generationModel") or previous.get("model") or "unknown"
            job["timestamp"] = previous.get("timestamp") or timestamp
            job["reviewer"] = previous.get("reviewer")
            job["reviewDate"] = previous.get("reviewDate")
            job["reviewerNotes"] = previous.get("reviewerNotes", "")
            job["culturalReviewStatus"] = previous.get("culturalReviewStatus", "not_reviewed")
            job["childSafetyReviewStatus"] = previous.get("childSafetyReviewStatus", "not_reviewed")
            job["productionApprovalStatus"] = previous.get("productionApprovalStatus", "not_approved")
        jobs.append(job)
    return jobs


def write_checklist() -> None:
    text = """# Moon Jar Stories Art Review Checklist

Use this checklist before approving generated art for additional scene generation or production import.

## Composition And Cropping
- Faces, ears, hands, important props, and story action are inside safe margins.
- No accidental crop on cover, thumbnail, reader, or two-page spread.
- 3:2 scene/covers remain usable with `.scaledToFit`/`ContentScale.Fit`.
- No critical subject sits within the outer 8% edge safety zone.

## Image Integrity
- No text, letters, signatures, logos, UI, or watermarks inside the image.
- No duplicated or near-identical scene posing unless intentionally storyboarded.
- No distorted hands, faces, eyes, limbs, or hanbok details.
- Image matches the requested scene, not a generic Korean fantasy background.

## Korean Cultural Fit
- Hanbok, cottage, food, mountain village, household objects, and lighting feel Korean and respectful.
- No random pan-Asian mashups, temple clichés, or modern props unless scripted.
- Moon jar identity remains elegant and not over-literal in every scene.

## The Sun And The Moon Tiger
- Tiger is cunning, hungry, watchful, and dangerous through eyes, posture, shadow, framing, and lighting.
- Tiger reads as cunning, hungry, watchful, mature, and dangerous through posture, eyes, shadow, and framing.
- Tiger is never graphic, bloody, horror-like, or anatomically frightening.
- Emotional arc is visible: forest presence, deceptive watchfulness, unsettling disguise, chase tension, resolved defeat.

## Child Safety
- Children are never shown injured, trapped in graphic danger, or traumatized.
- Tension is suspenseful folktale tension, not horror.
- No blood, gore, exposed teeth emphasis, dead-body imagery, or graphic punishment.

## Review Metadata Required
- reviewer
- reviewDate
- culturalReviewStatus
- childSafetyReviewStatus
- productionApprovalStatus
- notes or rejectionReason

Generated drafts may become `generated_reviewed` only after review. Nothing becomes `commissioned_final` without human/commissioned provenance plus complete approvals.
"""
    ART_CHECKLIST.parent.mkdir(parents=True, exist_ok=True)
    ART_CHECKLIST.write_text(text, encoding="utf-8")


def write_bakeoff_report(jobs: list[dict], providers: list[dict]) -> None:
    lines = [
        "# Moon Jar Stories Art Generation Bakeoff Report",
        "",
        f"Generated: {utc_now()}",
        "",
        "## Tool Availability",
        "",
        "No MCP image-generation server was discovered in this environment. No OpenAI or Adobe Firefly API credentials were present in environment variables, so no provider API generation was executed by this script.",
        "",
        "| Provider | Capability | Configured | Missing Env | Default Model | Status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for provider in providers:
        status = "ready" if provider["configured"] else "blocked"
        missing = ", ".join(provider["missingEnv"]) if provider["missingEnv"] else "-"
        lines.append(
            f"| {provider['provider']} | {provider['capability']} | {provider['configured']} | {missing} | {provider['defaultModel'] or '-'} | {status} |"
        )
    lines.extend(
        [
            "",
            "## Approval-First Jobs",
            "",
            "These jobs are the required approval set. Bulk regeneration of the full catalog-derived scene set should stay blocked until the anchor set is reviewed. The first approved bulk pass should remain a single-book calibration pass before all-catalog production use.",
            "",
            "| Job | Provider | Output | Status | Review Focus |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for job in jobs:
        lines.append(
            f"| {job['jobId']} | {job['provider']} | `{job['outputFile']}` | {job['status']} | {job['reviewFocus']} |"
        )
    lines.extend(
        [
            "",
            "## Current Recommendation",
            "",
            "- Use OpenAI GPT Image models first for the seven anchor images and edit loops because they fit character-sheet, scene-draft, and cover-concept workflows.",
            "- Evaluate Adobe Firefly as the commercial-safety-oriented comparison provider once credentials are available.",
            "- Do not mix providers inside the same book unless the approved style packet is locked and prompts reference the same character bible.",
            "- Commissioned/manual import remains the final production path for assets marked `commissioned_final`.",
        ]
    )
    BAKEOFF_REPORT.parent.mkdir(parents=True, exist_ok=True)
    BAKEOFF_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    jobs = approval_jobs()
    providers = provider_rows()
    manifest = {
        "schemaVersion": "1.0.0",
        "generatedAt": utc_now(),
        "purpose": "Approval-first art generation jobs before any bulk scene regeneration.",
        "bulkGenerationAllowed": False,
        "providers": providers,
        "jobs": jobs,
    }
    write_json(APPROVAL_JOBS, manifest)
    write_checklist()
    write_bakeoff_report(jobs, providers)
    print(f"Wrote {APPROVAL_JOBS.relative_to(CONTENT.parent)}")
    print(f"Wrote {ART_CHECKLIST}")
    print(f"Wrote {BAKEOFF_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
