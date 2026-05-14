# Shared Art Assets

This directory is the canonical home for production art exported from the shared story pipeline.

Suggested structure:

```text
assets/
  books/
    sun-and-moon/
      page-001/
        background.webp
        clouds.webp
        characters.webp
        moon.webp
      cover.webp
  ui/
    moon-jar-logo.webp
    hanji-texture.webp
```

The native apps should copy these assets at build time or download them through the CMS. Do not commit duplicate platform-specific copies unless they are generated build artifacts.

