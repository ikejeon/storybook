# Admin Workflow Notes

1. Content editor marks story text `ready_for_review`.
2. Cultural reviewer approves Korean language, folktale adaptation, names, clothing, food, settings, and sensitivity choices.
3. Child-safety reviewer approves tone for ages 3-8 and confirms no graphic danger, ads, tracking prompts, or external links are introduced.
4. Art/audio producer imports or generates assets offline.
5. Asset reviewer updates manifest review fields.
6. Production approver marks only commissioned final images or human-recorded final audio as production-ready.
7. Backend publishes the newest catalog and asset manifests after validation passes.

## Local Stub Coverage

`backend/service_stub.py` exercises this workflow locally without becoming a production service.

- `GET /v1/admin/reviews/queue` lists complete-book stories and assets still awaiting approval.
- `PATCH /v1/admin/assets/{assetId}/status` persists asset review state under `.agent/tmp/backend_state.json`.
- `PATCH /v1/admin/stories/{bookId}/review` persists story editorial/cultural/child-safety review state.
- `POST /v1/admin/assets/import` records a local asset import and review record.
- `GET /v1/admin/assets/{assetId}` returns a persisted asset review record or a not-reviewed default.
- `GET /v1/cms/export/books/{bookId}` exports complete canonical shared-content book JSON for CMS handoff.
- `GET /v1/cms/release/readiness` summarizes counts, local CMS/backend capabilities, and production blockers.

Admin auth is local-token ready: set `MOONJAR_ADMIN_TOKEN` and send either `Authorization: Bearer <token>` or `X-MoonJar-Admin-Token: <token>`. Without the env var, admin routes remain open for local smoke tests.

Production still needs durable database persistence, role-based access control, audit history, deployed receipt/token verification, admin UI, and operational monitoring.
