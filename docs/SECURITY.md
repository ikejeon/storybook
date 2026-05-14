# Security

Moon Jar Stories is a children/family product. Security and privacy rules should be conservative.

## Secrets

- Do not commit API keys, private tokens, signing credentials, Play Store/App Store secrets, or cloud credentials.
- Use `.env.example` for variable names only.
- Keep real secrets in local environment or a secret manager outside the repo.

## Child Safety Boundaries

The child-facing app must not include:

- live image generation;
- live TTS generation;
- ads;
- third-party tracking in the child experience;
- child accounts;
- child-facing external links;
- purchase/settings flows without parent gate.

## Dependency Hygiene

- Prefer existing platform tooling and standard libraries.
- Do not add paid SaaS dependencies.
- Before adding dependencies, document why they are needed and what data they access.
- Payment helper services such as RevenueCat require a privacy/compliance decision before adoption.

## Input Validation

- Treat JSON content and manifests as untrusted input until validated.
- Run `python3 tools/validate_books.py` and `python3 tools/validate_assets.py` after content changes.
- Backend endpoints should validate request fields before production implementation.

## Agent Rules

- Do not paste secrets into docs or examples.
- Do not mark generated or synthetic assets final without required review metadata.
- Do not bypass production-readiness failures by weakening checks.
- If a tool requires credentials, create a provider-ready adapter or documented command rather than faking production output.
