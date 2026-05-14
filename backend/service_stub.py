#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from collections import Counter
from json import JSONDecodeError
from datetime import date, datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
STATE_FILE = ROOT / ".agent" / "tmp" / "backend_state.json"

IMAGE_ASSET_STATUSES = {
    "placeholder",
    "generated_draft",
    "generated_reviewed",
    "commissioned_draft",
    "commissioned_reviewed",
    "commissioned_final",
    "rejected",
}
REVIEW_STATUSES = {"not_reviewed", "ready_for_review", "needs_changes", "approved", "rejected"}
EDITORIAL_STATUSES = {"draft", "ready_for_review", "needs_changes", "approved", "rejected"}
PRODUCTION_APPROVAL_STATUSES = {"not_approved", "approved", "rejected"}
PURCHASE_PLATFORMS = {"ios", "android"}
TRANSACTION_STATES = {"purchased", "restored", "refunded", "expired", "revoked"}
BASE_PRODUCT_IDS = {
    "com.moonjarstories.subscription.monthly",
    "com.moonjarstories.subscription.annual",
    "com.moonjarstories.lifetime.korean_library",
}
ASSET_IMPORT_TYPES = {"scene", "cover", "approval_anchor", "narration", "ambient", "sfx", "ui_sound"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def default_state() -> dict:
    return {
        "schemaVersion": "1.0.0",
        "assetReviews": {},
        "storyReviews": {},
        "assetImports": {},
        "purchaseStates": {},
        "createdAt": utc_now(),
        "updatedAt": utc_now(),
    }


def load_state() -> dict:
    if not STATE_FILE.exists():
        return default_state()
    try:
        value = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (JSONDecodeError, OSError):
        return default_state()
    if not isinstance(value, dict):
        return default_state()
    state = default_state()
    state.update(value)
    for key in ["assetReviews", "storyReviews", "assetImports", "purchaseStates"]:
        if not isinstance(state.get(key), dict):
            state[key] = {}
    return state


def save_state(state: dict) -> None:
    state["updatedAt"] = utc_now()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def catalog() -> dict:
    return load_json(CONTENT / "catalog.json")


def catalog_entry(book_id: str) -> dict | None:
    return next((item for item in catalog()["books"] if item["id"] == book_id), None)


def complete_book_entries() -> list[dict]:
    return [entry for entry in catalog()["books"] if entry.get("status") == "complete"]


def book_payload(book_id: str) -> dict | None:
    entry = catalog_entry(book_id)
    if not entry or entry.get("status") != "complete" or not entry.get("bookPath"):
        return None
    return load_json(CONTENT / entry["bookPath"])


def image_manifest() -> dict:
    return load_json(CONTENT / "assets" / "manifests" / "image_manifest.json")


def audio_manifest() -> dict:
    return load_json(CONTENT / "audio" / "manifests" / "audio_manifest.json")


def build_asset_id(entry: dict) -> str:
    parts = [entry.get("storyId"), entry.get("assetType"), entry.get("sceneId") or entry.get("pageNumber") or entry.get("outputFile")]
    return ":".join(str(part) for part in parts if part not in (None, ""))


def build_review_queue(state: dict) -> dict:
    images = image_manifest()
    complete_ids = {entry["id"] for entry in complete_book_entries()}
    scene_entries = [entry for entry in images.get("sceneEntries", []) if entry.get("storyId") in complete_ids]
    cover_entries = [entry for entry in images.get("coverEntries", []) if entry.get("storyId") in complete_ids]
    asset_reviews = state.get("assetReviews", {})
    story_reviews = state.get("storyReviews", {})
    queued_assets = []
    for entry in scene_entries + cover_entries:
        asset_id = build_asset_id(entry)
        review = asset_reviews.get(asset_id, {})
        production_status = review.get("productionApprovalStatus") or entry.get("productionApprovalStatus") or "not_approved"
        if production_status != "approved":
            queued_assets.append(
                {
                    "assetId": asset_id,
                    "storyId": entry.get("storyId"),
                    "assetType": entry.get("assetType"),
                    "status": review.get("status") or entry.get("status"),
                    "productionApprovalStatus": production_status,
                    "outputFile": entry.get("outputFile"),
                }
            )
    queued_stories = []
    for entry in complete_book_entries():
        review = story_reviews.get(entry["id"], {})
        if review.get("editorialStatus") != "approved":
            queued_stories.append(
                {
                    "bookId": entry["id"],
                    "title": entry.get("title", {}),
                    "status": entry.get("status"),
                    "editorialStatus": review.get("editorialStatus", "ready_for_review"),
                    "culturalReviewStatus": review.get("culturalReviewStatus", "not_reviewed"),
                    "childSafetyReviewStatus": review.get("childSafetyReviewStatus", "not_reviewed"),
                }
            )
    return {
        "backendMode": "local_persistent_stub",
        "generatedAt": utc_now(),
        "counts": {
            "queuedAssets": len(queued_assets),
            "queuedStories": len(queued_stories),
            "storedAssetReviews": len(asset_reviews),
            "storedStoryReviews": len(story_reviews),
            "assetImports": len(state.get("assetImports", {})),
        },
        "assets": queued_assets[:50],
        "stories": queued_stories,
    }


def build_release_readiness(state: dict) -> dict:
    images = image_manifest()
    audio = audio_manifest()
    complete_ids = {entry["id"] for entry in complete_book_entries()}
    scene_entries = [entry for entry in images.get("sceneEntries", []) if entry.get("storyId") in complete_ids]
    cover_entries = [entry for entry in images.get("coverEntries", []) if entry.get("storyId") in complete_ids]
    narration_entries = [entry for entry in audio.get("narrationEntries", []) if entry.get("storyId") in complete_ids]
    scene_statuses = Counter(entry.get("status", "missing") for entry in scene_entries)
    cover_statuses = Counter(entry.get("status", "missing") for entry in cover_entries)
    narration_statuses = Counter(entry.get("status", "missing") for entry in narration_entries)
    blockers = []
    if scene_statuses.get("commissioned_final", 0) != len(scene_entries):
        blockers.append("Scene art is not fully commissioned_final.")
    if cover_statuses.get("commissioned_final", 0) != len(cover_entries):
        blockers.append("Cover art is not fully commissioned_final.")
    if narration_statuses.get("human_recorded_final", 0) != len(narration_entries):
        blockers.append("Narration is not fully human_recorded_final.")
    blockers.extend(
        [
            "Receipt/token verification backend is not deployed.",
            "Admin auth is optional in local mode unless MOONJAR_ADMIN_TOKEN is set.",
            "CMS UI is not implemented.",
        ]
    )
    return {
        "backendMode": "local_persistent_stub",
        "generatedAt": utc_now(),
        "counts": {
            "completeBooks": len(complete_ids),
            "sceneImages": len(scene_entries),
            "coverImages": len(cover_entries),
            "narrationEntries": len(narration_entries),
            "storedAssetReviews": len(state.get("assetReviews", {})),
            "storedStoryReviews": len(state.get("storyReviews", {})),
            "assetImports": len(state.get("assetImports", {})),
            "purchaseStates": len(state.get("purchaseStates", {})),
        },
        "statuses": {
            "sceneImages": dict(sorted(scene_statuses.items())),
            "coverImages": dict(sorted(cover_statuses.items())),
            "narration": dict(sorted(narration_statuses.items())),
        },
        "localCapabilities": [
            "catalog_service",
            "asset_manifest_service",
            "entitlement_contract",
            "purchase_sync_contract",
            "local_state_persistence",
            "admin_asset_review",
            "admin_story_review",
            "admin_review_queue",
            "asset_import_contract",
            "cms_book_export",
            "release_readiness_summary",
            "optional_admin_token",
        ],
        "releaseCandidate": False,
        "blockers": blockers,
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/v1/catalog":
            self.respond_json(catalog())
            return
        if path.startswith("/v1/books/"):
            book_id = path.rsplit("/", 1)[-1]
            entry = catalog_entry(book_id)
            if not entry:
                self.respond_json({"error": "not_found"}, status=404)
                return
            self.respond_json(entry)
            return
        if path == "/v1/assets/manifest":
            self.respond_json(
                {
                    "version": "local-dev",
                    "imageManifestUrl": "/shared-content/assets/manifests/image_manifest.json",
                    "audioManifestUrl": "/shared-content/audio/manifests/audio_manifest.json",
                    "effectiveAt": None,
                }
            )
            return
        if path == "/v1/cms/release/readiness":
            self.respond_json(build_release_readiness(load_state()))
            return
        if path.startswith("/v1/cms/export/books/"):
            book_id = path.rsplit("/", 1)[-1]
            entry = catalog_entry(book_id)
            if not entry:
                self.respond_json({"error": "not_found"}, status=404)
                return
            book = book_payload(book_id)
            if book is None:
                self.respond_json({"error": "not_exportable", "reason": "book_is_not_complete"}, status=409)
                return
            self.respond_json(
                {
                    "exportedAt": utc_now(),
                    "source": "shared-content",
                    "bookId": book_id,
                    "metadata": entry,
                    "book": book,
                    "reviewState": load_state().get("storyReviews", {}).get(book_id, {}),
                }
            )
            return
        if path == "/v1/admin/reviews/queue":
            if not self.require_admin():
                return
            self.respond_json(build_review_queue(load_state()))
            return
        if path.startswith("/v1/admin/assets/"):
            if not self.require_admin():
                return
            asset_id = path.rsplit("/", 1)[-1]
            state = load_state()
            self.respond_json(
                state.get("assetReviews", {}).get(
                    asset_id,
                    {"assetId": asset_id, "status": "not_reviewed", "productionApprovalStatus": "not_approved"},
                )
            )
            return
        self.respond_json({"error": "not_found"}, status=404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/v1/entitlements/check":
            payload = self.read_json()
            if payload is None:
                return
            if not self.require_fields(payload, ["anonymousUserId", "bookId"]):
                return
            book_id = payload.get("bookId")
            catalog = json.loads((CONTENT / "catalog.json").read_text(encoding="utf-8"))
            entry = next((item for item in catalog["books"] if item["id"] == book_id), None)
            can_read = bool(entry and entry.get("access") == "free")
            self.respond_json({"canRead": can_read, "reason": "free_book" if can_read else "locked", "expiresAt": None})
            return
        if path == "/v1/purchases/sync":
            payload = self.read_json()
            if payload is None:
                return
            if not self.require_fields(payload, ["anonymousUserId", "platform", "transactions"]):
                return
            if payload.get("platform") not in PURCHASE_PLATFORMS:
                self.respond_json({"error": "invalid_field", "field": "platform"}, status=400)
                return
            if not isinstance(payload.get("transactions"), list) or not payload.get("transactions"):
                self.respond_json({"error": "invalid_field", "field": "transactions"}, status=400)
                return
            invalid_transaction = self.invalid_transaction_index(payload["transactions"])
            if invalid_transaction is not None:
                self.respond_json(
                    {
                        "error": "invalid_transaction",
                        "index": invalid_transaction,
                        "required": ["productId", "transactionToken"],
                        "allowedState": sorted(TRANSACTION_STATES),
                    },
                    status=400,
                )
                return
            response = {
                "anonymousUserId": payload.get("anonymousUserId", "local"),
                "subscriptionExpiresAt": None,
                "isInGracePeriod": False,
                "hasLifetimeUnlock": False,
                "unlockedBookIds": [],
            }
            state = load_state()
            state["purchaseStates"][response["anonymousUserId"]] = {
                **response,
                "platform": payload.get("platform"),
                "transactionCount": len(payload.get("transactions", [])),
                "updatedAt": utc_now(),
            }
            save_state(state)
            self.respond_json(response)
            return
        if path == "/v1/admin/assets/import":
            if not self.require_admin():
                return
            payload = self.read_json()
            if payload is None:
                return
            if not self.require_fields(
                payload,
                [
                    "assetId",
                    "storyId",
                    "assetType",
                    "status",
                    "outputFile",
                    "reviewer",
                    "reviewDate",
                    "culturalReviewStatus",
                    "childSafetyReviewStatus",
                    "productionApprovalStatus",
                ],
            ):
                return
            if not self.validate_enum(payload, "assetType", ASSET_IMPORT_TYPES):
                return
            if not self.validate_enum(payload, "status", IMAGE_ASSET_STATUSES):
                return
            if not self.validate_review_fields(payload, ["culturalReviewStatus", "childSafetyReviewStatus"]):
                return
            if not self.validate_enum(payload, "productionApprovalStatus", PRODUCTION_APPROVAL_STATUSES):
                return
            if not self.validate_date(payload, "reviewDate"):
                return
            record = {"updatedAt": utc_now(), **payload}
            state = load_state()
            state["assetImports"][payload["assetId"]] = record
            state["assetReviews"][payload["assetId"]] = {
                "assetId": payload["assetId"],
                "status": payload["status"],
                "reviewer": payload["reviewer"],
                "reviewDate": payload["reviewDate"],
                "culturalReviewStatus": payload["culturalReviewStatus"],
                "childSafetyReviewStatus": payload["childSafetyReviewStatus"],
                "productionApprovalStatus": payload["productionApprovalStatus"],
                "updatedAt": record["updatedAt"],
            }
            save_state(state)
            self.respond_json(record)
            return
        self.respond_json({"error": "not_found"}, status=404)

    def do_PATCH(self) -> None:
        path = urlparse(self.path).path
        if path.startswith("/v1/admin/") and not self.require_admin():
            return
        payload = self.read_json()
        if payload is None:
            return
        if path.startswith("/v1/admin/assets/") and path.endswith("/status"):
            if not self.require_fields(
                payload,
                ["status", "reviewer", "reviewDate", "culturalReviewStatus", "childSafetyReviewStatus", "productionApprovalStatus"],
            ):
                return
            if not self.validate_enum(payload, "status", IMAGE_ASSET_STATUSES):
                return
            if not self.validate_review_fields(payload, ["culturalReviewStatus", "childSafetyReviewStatus"]):
                return
            if not self.validate_enum(payload, "productionApprovalStatus", PRODUCTION_APPROVAL_STATUSES):
                return
            if not self.validate_date(payload, "reviewDate"):
                return
            asset_id = path.strip("/").split("/")[3]
            record = {"assetId": asset_id, "updatedAt": utc_now(), **payload}
            state = load_state()
            state["assetReviews"][asset_id] = record
            save_state(state)
            self.respond_json(record)
            return
        if path.startswith("/v1/admin/stories/") and path.endswith("/review"):
            if not self.require_fields(
                payload,
                ["editorialStatus", "culturalReviewStatus", "childSafetyReviewStatus", "reviewer", "reviewDate"],
            ):
                return
            if not self.validate_enum(payload, "editorialStatus", EDITORIAL_STATUSES):
                return
            if not self.validate_review_fields(payload, ["culturalReviewStatus", "childSafetyReviewStatus"]):
                return
            if not self.validate_date(payload, "reviewDate"):
                return
            book_id = path.strip("/").split("/")[3]
            if not catalog_entry(book_id):
                self.respond_json({"error": "not_found"}, status=404)
                return
            record = {"bookId": book_id, "updatedAt": utc_now(), **payload}
            state = load_state()
            state["storyReviews"][book_id] = record
            save_state(state)
            self.respond_json(record)
            return
        self.respond_json({"error": "not_found"}, status=404)

    def read_json(self) -> dict | None:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        try:
            value = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, JSONDecodeError):
            self.respond_json({"error": "invalid_json"}, status=400)
            return None
        if not isinstance(value, dict):
            self.respond_json({"error": "invalid_json_object"}, status=400)
            return None
        return value

    def require_fields(self, payload: dict, fields: list[str]) -> bool:
        missing = [field for field in fields if payload.get(field) in (None, "")]
        if missing:
            self.respond_json({"error": "missing_required_fields", "fields": missing}, status=400)
            return False
        return True

    def validate_enum(self, payload: dict, field: str, allowed: set[str]) -> bool:
        if payload.get(field) not in allowed:
            self.respond_json({"error": "invalid_enum", "field": field, "allowed": sorted(allowed)}, status=400)
            return False
        return True

    def validate_review_fields(self, payload: dict, fields: list[str]) -> bool:
        for field in fields:
            if not self.validate_enum(payload, field, REVIEW_STATUSES):
                return False
        return True

    def validate_date(self, payload: dict, field: str) -> bool:
        try:
            date.fromisoformat(str(payload.get(field)))
        except ValueError:
            self.respond_json({"error": "invalid_date", "field": field, "format": "YYYY-MM-DD"}, status=400)
            return False
        return True

    def require_admin(self) -> bool:
        token = os.environ.get("MOONJAR_ADMIN_TOKEN")
        if not token:
            return True
        bearer = self.headers.get("Authorization", "")
        header = self.headers.get("X-MoonJar-Admin-Token", "")
        if bearer == f"Bearer {token}" or header == token:
            return True
        self.respond_json({"error": "unauthorized"}, status=401)
        return False

    def valid_product_id(self, product_id: str) -> bool:
        if product_id in BASE_PRODUCT_IDS:
            return True
        if not product_id.startswith("com.moonjarstories.book."):
            return False
        book_id = product_id.removeprefix("com.moonjarstories.book.")
        return bool(book_id and all(char.isalnum() or char in {"_", "-"} for char in book_id))

    def invalid_transaction_index(self, transactions: list[object]) -> int | None:
        for index, transaction in enumerate(transactions):
            if not isinstance(transaction, dict):
                return index
            product_id = transaction.get("productId")
            state = transaction.get("transactionState")
            if (
                not isinstance(product_id, str)
                or not self.valid_product_id(product_id)
                or not transaction.get("transactionToken")
                or (state is not None and state not in TRANSACTION_STATES)
            ):
                return index
        return None

    def respond_json(self, payload: object, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> int:
    server = HTTPServer(("127.0.0.1", 8080), Handler)
    print("Moon Jar backend stub listening on http://127.0.0.1:8080")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
