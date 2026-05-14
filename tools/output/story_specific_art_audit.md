# Story-Specific Art Audit

This audit validates current repo artifacts. It fails if selected runtime art still uses the old abstract static renderer or if premium catalog art lacks story-specific evidence.

| Book | Access | Scenes | Scene Art | Cover Art | Character Sheet | Gaps |
| --- | --- | ---: | --- | --- | --- | --- |
| sun-and-moon | free | 32 | pass | pass | pass | none |
| gold-axe-silver-axe | free | 24 | pass | pass | pass | none |
| tiger-and-persimmon | free | 24 | pass | pass | pass | none |
| heungbu-and-nolbu | free | 32 | pass | pass | pass | none |
| red-bean-porridge-grandma | free | 26 | pass | pass | pass | none |
| simcheong | premium | 38 | pass | pass | pass | none |
| rabbit-and-turtle | premium | 30 | pass | pass | pass | none |
| dokkaebi-club | premium | 28 | pass | pass | pass | none |
| dangun-story | premium | 30 | pass | pass | pass | none |
| grateful-magpie | premium | 28 | pass | pass | pass | none |
| kongjwi-and-patjwi | premium | 34 | pass | pass | pass | none |
| geumgang-mountain-tiger | premium | 28 | pass | pass | pass | none |
| lump-old-man | premium | 30 | pass | pass | pass | none |
| gyeonwu-and-jiknyeo | premium | 32 | pass | pass | pass | none |
| bari-princess-part-1 | premium | 26 | pass | pass | pass | none |
| bari-princess-part-2 | premium | 26 | pass | pass | pass | none |
| snail-bride | premium | 30 | pass | pass | pass | none |
| janghwa-and-hongryeon | premium | 32 | pass | pass | pass | none |
| fairy-and-woodcutter | premium | 32 | pass | pass | pass | none |
| green-frog | premium | 24 | pass | pass | pass | none |
| kind-brothers | premium | 24 | pass | pass | pass | none |
| byeoljubu | premium | 32 | pass | pass | pass | none |
| farting-daughter-in-law | premium | 24 | pass | pass | pass | none |
| serpent-bridegroom | premium | 32 | pass | pass | pass | none |

## Totals

- Complete scenes checked: 698
- Premium story-specific scenes checked: 560
- Premium story-specific covers checked: 19
- Character sheets checked: 24

## Rule

- Free-book imported/image-generated art may remain as selected runtime art.
- Premium-book selected runtime art must use either the story-specific local renderer or the reviewed built-in sheet importer, and carry `visualSpecificity: story_specific_illustration`.
- No selected runtime art may use `local_static_storyboard_renderer` or `deterministic_repo_renderer`.
