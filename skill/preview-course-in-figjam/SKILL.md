---
name: preview-course-in-figjam
description: Turn uploaded course syllabi and PDF or PPTX slide decks into isolated per-course FigJam preview workspaces with slide-aligned Chinese annotations, English-to-Chinese terminology, module-based batch preview, complete weekly glossaries, and linked concept maps. Use when Codex is asked to preview or pre-study course slides, annotate a weekly deck in Figma or FigJam, build a reusable course-notes workspace, continue a previously initialized course or week, or organize a syllabus and lecture materials without mixing courses.
---

# Preview Course in FigJam

Build one persistent FigJam per course, initialize every slide for the requested week, and add detailed preview notes one module at a time. Keep different courses isolated through a local registry and stable node names.

## Load required guidance

1. Load the `pdf` skill for PDF sources and the `presentations` skill for PPTX sources.
2. Load workspace dependencies before running the bundled Python scripts; use the returned Python, Poppler, and LibreOffice paths.
3. Load `figma-create-new-file` immediately before every Figma `create_new_file` call.
4. Load both `figma-use` and `figma-use-figjam` immediately before every `use_figma` call.
5. Read [references/preview-policy.md](references/preview-policy.md) before writing preview notes.
6. Read [references/figjam-layout.md](references/figjam-layout.md) before creating or rearranging FigJam content.
7. Read [references/state-schema.md](references/state-schema.md) before reading or updating the course registry.

Do not browse the web or add outside knowledge by default. Use only the uploaded syllabus, deck, and speaker notes. Browse only if the user explicitly changes this rule.

## Identify the course and week

1. Inspect the syllabus first when supplied, then the deck title, filename, and first content pages.
2. Derive the canonical course key in this order: `institution:course-code`, `course-code`, normalized full course name.
3. Treat the term as a grouping inside the course file, never as part of the course key.
4. Derive the week from `Week`, `W`, lecture date, or the user's statement. Ask only for the course identity or week when neither can be established reliably.
5. Use one module named `Main Deck` when no Module, Part, or Section boundaries can be inferred.

## Inspect and classify the deck

Run:

```bash
python scripts/deck_manifest.py SOURCE --output MANIFEST.json
```

Use the manifest as the page-order source of truth. Do not repeatedly extract the same slide text.

- `content`: create the full note template.
- `low_information`: write one short factual sentence only.
- `image_only`: preserve the slide and page number, but insert the fixed skip note; do not send the image to a vision model.
- `blank`: preserve the page number and mark it as blank; do not infer content.

Treat short assessment, agenda, divider, recap, and end pages as low-information even if their text count narrowly exceeds the automatic threshold.

## Resolve the course FigJam

1. Run `course_registry.py lookup --course-key KEY` against the default registry.
2. When found, use only the returned `figmaFileKey`. Verify it before every write.
3. When absent, call Figma `whoami`; use the only available plan or ask the user to select when multiple plans exist.
4. Create a FigJam named `{course code or course name} · Preview Notes`.
5. Commit the new registry entry only after Figma creation succeeds.

Never place two canonical course keys in the same FigJam. Never hardcode an example course file key or node ID.

## Initialize the whole week

1. Render the full deck into a temporary directory with `render_deck.py`.
2. Upload and place every page image, including image-only and blank pages.
3. Create the Course Hub, term section, week section, module headers, and every `Wxx-Pxxx` page card before detailed preview begins.
4. Keep the original slide on the left and its note panel on the right.
5. Link the Course Hub week entry to the week section.
6. Write Figma changes in batches of about 12 slides. Record `lastBatch` only after each successful batch.
7. Set the week status to `initialized` when all page cards exist.

Do not automatically write detailed notes for the entire week. Wait for the user to name a Module, Part, Section, or page range.

## Preview a requested module

1. Read only that module's extracted text and any relevant syllabus text.
2. Apply the note policy exactly. Use Chinese explanations with the original English keywords.
3. Do not create quizzes, exercises, flashcards, pronunciation, or parts of speech.
4. Do not visually analyze `image_only` pages unless the user explicitly requests a specific page later.
5. Write notes in page order and update FigJam in batches of about 12 pages.
6. Mark the week `in_progress` and preserve the last successful batch for retry.
7. Give one concise completion update for the module instead of pausing after every page.

## Complete the weekly review

After all modules are complete:

1. Collect one structured glossary entry per term and run `glossary_dedupe.py`.
2. Create the complete native FigJam glossary table: `English term | 中文释义 | 首次出现页面 ↗`.
3. Link every page cell to its `Wxx-Pxxx` card.
4. Build a left-to-right concept map with one root, 4–7 main branches, and 18–30 total nodes according to the material.
5. Put English keywords, a concise Chinese relationship, and relevant page labels in every node; link each node to its representative page.
6. Place Concept Map and Week Wrap-up in one compact, top-aligned row.
7. Keep only weekly counts and navigation links in Course Hub; do not duplicate the full glossary there.
8. Set the week status to `complete` only after screenshots and link validation pass.

## Preserve isolation and recover safely

- Use the registry and naming rules in `state-schema.md` for every read and write.
- Reuse the existing week when the source fingerprint matches.
- When the same week has a different fingerprint, record `revision_pending`, stop before overwriting, and ask whether to update the existing week or create a revision. Use `--allow-fingerprint-replace` only after explicit approval.
- Use `--allow-rebind` only after the user explicitly approves changing a course's stored FigJam file.
- Do not mark a failed Figma batch complete. Resume from the last recorded batch.
- Store no slide text, notes, absolute source paths, or rendered images in the persistent registry.
- Delete temporary render directories after successful upload when safe.

## Validate before handoff

Verify all of the following:

- Page-card count equals the manifest page count.
- Every original page number exists exactly once.
- Image-only pages retain the fixed skip note and were not visually analyzed.
- All glossary entries are unique under case-insensitive Unicode normalization.
- Every glossary page link and concept-map link resolves to an existing card.
- Concept Map and Week Wrap-up share the same top coordinate and do not overlap.
- No node outside the resolved course file was changed.

Take section-level screenshots for visual QA; do not take one screenshot per slide unless diagnosing a specific defect.
