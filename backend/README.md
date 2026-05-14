# Moon Jar Stories Backend Stub

This backend folder is implementation-ready scaffolding, not a production service.

Run the local stub:

```bash
python3 backend/service_stub.py
```

The stub now behaves like a small local CMS contract exerciser:

- public catalog, book metadata, entitlement, purchase-sync, and asset-manifest endpoints;
- local persisted review/import/purchase state in `.agent/tmp/backend_state.json`;
- admin asset review, story review, asset import, and review-queue endpoints;
- complete-book CMS export from canonical `shared-content/`;
- release-readiness summary that keeps final art/audio/backend blockers explicit.

Admin endpoints are open for local development by default. Set `MOONJAR_ADMIN_TOKEN` to require either `Authorization: Bearer <token>` or `X-MoonJar-Admin-Token: <token>`.

Primary contract:

```bash
backend/openapi.yaml
```

Useful smoke probes:

```bash
curl http://127.0.0.1:8080/v1/cms/release/readiness
curl http://127.0.0.1:8080/v1/cms/export/books/book.sun_moon
curl http://127.0.0.1:8080/v1/admin/reviews/queue
```

The production backend should verify App Store Server API and Google Play purchase tokens before granting entitlements. It should not create child accounts. Use anonymous install/user IDs controlled by the parent device account, and keep child-facing app flows free of ads, third-party tracking, and external links. Production still needs deployed persistence, real admin auth, audit logs, CMS UI, receipt/token verification, and operational monitoring.
