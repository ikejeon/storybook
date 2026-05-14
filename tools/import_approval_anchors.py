#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import struct
from pathlib import Path

from asset_pipeline_common import ASSETS, CONTENT, IMAGE_STATUSES, load_json, utc_now, write_json

ART_JOBS = ASSETS / "manifests" / "art_approval_jobs.json"
IMAGE_MANIFEST = ASSETS / "manifests" / "image_manifest.json"


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"Not a valid PNG: {path}")
    return struct.unpack(">II", header[16:24])


def review_defaults(job: dict | None = None) -> dict:
    job = job or {}
    metadata = {
        "reviewer": job.get("reviewer"),
        "reviewDate": job.get("reviewDate"),
        "rejectionReason": job.get("rejectionReason"),
        "notes": job.get("notes") or "Generated draft approval anchor. Needs creative, cultural, child-safety, and crop review.",
        "culturalReviewStatus": job.get("culturalReviewStatus", "not_reviewed"),
        "childSafetyReviewStatus": job.get("childSafetyReviewStatus", "not_reviewed"),
        "productionApprovalStatus": job.get("productionApprovalStatus", "not_approved"),
    }
    if job.get("reviewerNotes"):
        metadata["reviewerNotes"] = job["reviewerNotes"]
    if job.get("reviewScores"):
        metadata["reviewScores"] = job["reviewScores"]
    return metadata


def manifest_candidate(job: dict, *, provider: str, model: str, source_file: str | None) -> dict:
    status = job.get("status") if job.get("status") in IMAGE_STATUSES else "generated_draft"
    candidate = {
        "outputFile": job["outputFile"],
        "status": status,
        "provider": provider,
        "model": model,
        "generationStatus": "generated" if provider != "manual_import" else "imported",
        "prompt": job["prompt"],
        "seed": None,
        "timestamp": utc_now(),
        "sourceFile": source_file,
    }
    candidate.update(review_defaults(job))
    return candidate


def image_entry(job: dict, *, provider: str, model: str, source_file: str | None) -> dict:
    width, height = png_dimensions(CONTENT / job["outputFile"])
    status = job.get("status") if job.get("status") in IMAGE_STATUSES else "generated_draft"
    entry = {
        "assetType": "approval_anchor",
        "storyId": job["storyId"],
        "storySlug": job["storySlug"],
        "sceneId": job.get("sceneId"),
        "pageNumber": job.get("pageNumber"),
        "jobId": job["jobId"],
        "prompt": job["prompt"],
        "characterBible": job.get("characterBible"),
        "styleBible": job.get("styleBible"),
        "outputFile": job["outputFile"],
        "status": status,
        "generationTool": provider,
        "generationModel": model,
        "timestamp": utc_now(),
        "seed": None,
        "generationStatus": "generated" if provider != "manual_import" else "imported",
        "dimensions": {"width": width, "height": height},
        "safeMarginStatus": "needs_review",
        "textWatermarkStatus": "needs_review",
        "cropReviewStatus": "needs_review",
        "tigerToneReviewStatus": "needs_review" if "tiger" in job["jobId"] or "scene" in job["jobId"] else "not_applicable",
        "candidates": [manifest_candidate(job, provider=provider, model=model, source_file=source_file)],
    }
    entry.update(review_defaults(job))
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Import/register approval anchor PNGs for Moon Jar Stories.")
    parser.add_argument("--source-dir", type=Path, default=CONTENT / "assets/generated-draft/images/approval/sun-and-moon")
    parser.add_argument("--provider", default="built_in_image_gen")
    parser.add_argument("--model", default="built-in image_gen")
    parser.add_argument("--copy", action="store_true", help="Copy source PNGs into each job output path before registration.")
    args = parser.parse_args()

    if "generated_draft" not in IMAGE_STATUSES:
        raise SystemExit("generated_draft status is not registered.")

    jobs_manifest = load_json(ART_JOBS)
    image_manifest = load_json(IMAGE_MANIFEST)
    registered: list[dict] = []

    for job in jobs_manifest.get("jobs", []):
        output = CONTENT / job["outputFile"]
        source = args.source_dir / output.name
        if args.copy:
            if not source.exists():
                raise SystemExit(f"Missing source PNG for {job['jobId']}: {source}")
            output.parent.mkdir(parents=True, exist_ok=True)
            if source.resolve() != output.resolve():
                shutil.copy2(source, output)
        if not output.exists():
            raise SystemExit(f"Missing generated anchor PNG for {job['jobId']}: {output}")
        png_dimensions(output)

        job["status"] = job.get("status") if job.get("status") in IMAGE_STATUSES else "generated_draft"
        job["generationStatus"] = "generated" if args.provider != "manual_import" else "imported"
        job["provider"] = args.provider
        job["generationModel"] = args.model
        job["timestamp"] = utc_now()
        job["outputFile"] = str(output.relative_to(CONTENT))
        job.setdefault("reviewer", None)
        job.setdefault("reviewDate", None)
        job.setdefault("reviewerNotes", "")
        job.setdefault("culturalReviewStatus", "not_reviewed")
        job.setdefault("childSafetyReviewStatus", "not_reviewed")
        job.setdefault("productionApprovalStatus", "not_approved")

        registered.append(image_entry(job, provider=args.provider, model=args.model, source_file=str(source) if source.exists() else None))

    jobs_manifest["bulkGenerationAllowed"] = False
    jobs_manifest["status"] = "anchors_generated_pending_review"
    jobs_manifest["generatedAt"] = utc_now()
    write_json(ART_JOBS, jobs_manifest)

    existing = {
        entry.get("jobId"): entry
        for entry in image_manifest.get("approvalAnchorEntries", [])
        if entry.get("jobId")
    }
    for entry in registered:
        existing[entry["jobId"]] = entry
    image_manifest["approvalAnchorEntries"] = [existing[key] for key in sorted(existing)]
    image_manifest["generatedAt"] = utc_now()
    write_json(IMAGE_MANIFEST, image_manifest)

    print(f"Registered approval anchors: {len(registered)}")
    for entry in registered:
        print(f"- {entry['jobId']}: {entry['outputFile']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
