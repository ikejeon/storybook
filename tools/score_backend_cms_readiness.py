#!/usr/bin/env python3
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SERVICE = BACKEND / "service_stub.py"
OPENAPI = BACKEND / "openapi.yaml"
README = BACKEND / "README.md"
CMS_SCHEMA = BACKEND / "cms_schema.md"
ADMIN_WORKFLOW = BACKEND / "admin_workflow.md"
HARNESS = ROOT / "scripts" / "agent" / "agent_harness.py"
REPORT = ROOT / "tools" / "output" / "backend_cms_readiness_report.md"


@dataclass(frozen=True)
class Check:
    label: str
    ok: bool
    fix: str


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def has_all(text: str, needles: list[str]) -> bool:
    return all(needle in text for needle in needles)


def score(checks: list[Check]) -> int:
    return round(100 * sum(1 for check in checks if check.ok) / max(1, len(checks)))


def main() -> int:
    service = read(SERVICE)
    openapi = read(OPENAPI)
    docs = "\n".join(read(path) for path in [README, CMS_SCHEMA, ADMIN_WORKFLOW])
    harness = read(HARNESS)

    contract_checks = [
        Check(
            "OpenAPI includes CMS export and release readiness endpoints",
            has_all(openapi, ["/v1/cms/export/books/{bookId}", "/v1/cms/release/readiness", "CmsBookExportResponse", "ReleaseReadinessResponse"]),
            "Add CMS export/readiness endpoints and schemas to backend/openapi.yaml.",
        ),
        Check(
            "OpenAPI includes admin review queue, asset lookup, and asset import",
            has_all(openapi, ["/v1/admin/reviews/queue", "/v1/admin/assets/{assetId}", "/v1/admin/assets/import", "ReviewQueueResponse", "AssetImportRequest"]),
            "Add admin review queue, asset lookup, and asset import contracts.",
        ),
        Check(
            "OpenAPI documents optional admin token security",
            has_all(openapi, ["AdminBearer", "AdminTokenHeader", "MOONJAR_ADMIN_TOKEN"]),
            "Document local admin token security schemes.",
        ),
    ]

    implementation_checks = [
        Check(
            "Stub persists local CMS state under .agent/tmp",
            has_all(service, ["STATE_FILE", "load_state", "save_state", "backend_state.json", "assetReviews", "storyReviews", "assetImports"]),
            "Persist local review/import state so smoke tests can exercise CMS workflows.",
        ),
        Check(
            "Stub exposes CMS export and release readiness handlers",
            has_all(service, ["build_release_readiness", "book_payload", "/v1/cms/export/books/", "/v1/cms/release/readiness"]),
            "Implement CMS export and release readiness endpoints.",
        ),
        Check(
            "Stub exposes admin review queue, asset lookup, and asset import handlers",
            has_all(service, ["build_review_queue", "/v1/admin/reviews/queue", "/v1/admin/assets/import", "assetImports"]),
            "Implement admin review queue, asset lookup, and asset import endpoints.",
        ),
        Check(
            "Stub supports optional local admin token enforcement",
            has_all(service, ["require_admin", "MOONJAR_ADMIN_TOKEN", "Authorization", "X-MoonJar-Admin-Token"]),
            "Require admin token automatically when MOONJAR_ADMIN_TOKEN is set.",
        ),
        Check(
            "Purchase sync state is persisted for backend workflow realism",
            has_all(service, ["purchaseStates", "transactionCount", "save_state(state)"]),
            "Persist purchase-sync state in the local stub.",
        ),
    ]

    docs_checks = [
        Check(
            "Backend docs describe local persistence, CMS endpoints, and admin token",
            has_all(docs, [".agent/tmp/backend_state.json", "/v1/cms/release/readiness", "/v1/admin/reviews/queue", "MOONJAR_ADMIN_TOKEN"]),
            "Update backend docs so future agents can exercise the CMS workflow.",
        ),
        Check(
            "Docs keep production blockers explicit",
            has_all(docs, ["Production still needs", "receipt/token verification", "CMS UI"]),
            "Keep deployed persistence, auth, CMS UI, receipt validation, and monitoring blockers explicit.",
        ),
    ]

    harness_checks = [
        Check(
            "Backend smoke covers CMS readiness and export endpoints",
            has_all(harness, ["/v1/cms/release/readiness", "/v1/cms/export/books/book.sun_moon", "release readiness"]),
            "Add new CMS endpoints to backend smoke assertions.",
        ),
        Check(
            "Backend smoke covers admin review queue, asset import, and persisted asset lookup",
            has_all(harness, ["/v1/admin/reviews/queue", "/v1/admin/assets/import", "/v1/admin/assets/local-asset"]),
            "Add admin review workflow endpoints to backend smoke assertions.",
        ),
    ]

    categories = [
        ("Contract", contract_checks),
        ("Implementation", implementation_checks),
        ("Docs", docs_checks),
        ("Smoke coverage", harness_checks),
    ]

    rows = [
        "# Backend CMS Readiness Report",
        "",
        "This is a repo-local Backend/CMS readiness score. It validates contract coverage, local stub behavior, docs, and smoke coverage. It does not claim deployed production infrastructure, a real CMS UI, receipt verification, or production admin auth.",
        "",
        "| Category | Score | Status |",
        "| --- | ---: | --- |",
    ]
    failed: list[str] = []
    details: list[str] = []
    all_checks: list[Check] = []
    for name, checks in categories:
        all_checks.extend(checks)
        category_score = score(checks)
        rows.append(f"| {name} | {category_score} | {'pass' if category_score >= 95 else 'fail'} |")
        details.extend(["", f"## {name}", ""])
        for check in checks:
            details.append(f"- {'PASS' if check.ok else 'FAIL'}: {check.label}")
            if not check.ok:
                failed.append(f"{name}: {check.label} -- {check.fix}")

    overall = score(all_checks)
    rows.extend(
        [
            "",
            f"Overall Backend/CMS readiness: {overall}/100",
            "",
            "## Honest Caveat",
            "",
            "- This is an implementation-ready local CMS/backend scaffold, not a deployed service.",
            "- Production still needs durable database infrastructure, real auth/RBAC, audit logs, CMS UI, receipt/token verification, backups, monitoring, and release promotion.",
        ]
    )
    rows.extend(details)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")

    print(f"Backend/CMS readiness: {overall}/100")
    print(f"Report: {REPORT.relative_to(ROOT)}")
    if failed or overall < 95:
        for item in failed:
            print(f"- {item}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
