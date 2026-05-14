# CMS Schema

The CMS manages story production, review, localization, art, audio, and release state. It should export JSON matching `shared-content/schemas/book.schema.json`.

## Book

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Stable ID such as `book.sun_moon` |
| `slug` | string | URL/build-safe slug |
| `title.ko` | string | Korean title |
| `title.en` | string | English title |
| `access` | enum | `free` or `premium` |
| `ageRange` | string | Example: `3-8` |
| `summary` | string | Parent-facing summary |
| `sensitivityNotes` | string[] | Cultural and child-safety notes |
| `themes` | string[] | Discovery tags |
| `characters` | string[] | References to character bible IDs |
| `pages` | page[] | 20-40 scenes |

## Page

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Stable page ID |
| `pageNumber` | int | 1-based order |
| `koreanText` | string | Child-safe original Korean retelling |
| `englishText` | string | Natural English translation |
| `narrationScript` | string | Korean narration copy |
| `vocabulary` | object[] | Tap-word support |
| `imagePrompt` | string | Art generation / illustrator brief |
| `audioPrompt` | string | Narration and ambience direction |
| `animation` | object | Native renderer motion metadata |

## Review Status

Each page should carry CMS-only workflow fields before export:

- `draft`
- `copy_review`
- `cultural_review`
- `sensitivity_review`
- `audio_ready`
- `art_ready`
- `animation_ready`
- `approved`

## Export Rules

- Export only approved pages.
- Preserve stable IDs forever.
- Do not export reviewer comments into the app bundle.
- Do not duplicate content in platform repositories.

## Local CMS Contract Endpoints

The local backend stub exposes CMS handoff endpoints so agents can test workflow shape before a production CMS exists:

| Endpoint | Purpose |
| --- | --- |
| `GET /v1/cms/export/books/{bookId}` | Export a complete book from canonical `shared-content/` with metadata and local review state. |
| `GET /v1/cms/release/readiness` | Summarize content counts, asset statuses, local capabilities, and release blockers. |
| `GET /v1/admin/reviews/queue` | List assets and stories that still need review approval. |
| `PATCH /v1/admin/stories/{bookId}/review` | Persist story editorial/cultural/child-safety review status locally. |
| `PATCH /v1/admin/assets/{assetId}/status` | Persist asset review and production-approval status locally. |
| `POST /v1/admin/assets/import` | Register a locally imported/reviewed asset into stub CMS state. |

Local state lives at `.agent/tmp/backend_state.json` and is safe to delete. Production CMS work still needs a real database, role-based auth, audit logs, moderation UI, deployment, backups, and release promotion controls.
