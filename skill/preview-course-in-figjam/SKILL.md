---
name: preview-course-in-figjam
description: Turn uploaded course syllabi and PDF or PPTX slide decks into isolated per-course FigJam preview workspaces with slide-aligned Chinese annotations, English-to-Chinese terminology, module-based batch preview, complete weekly glossaries, and linked concept maps. Use when Codex is asked to preview or pre-study course slides, annotate a weekly deck in Figma or FigJam, build a reusable course-notes workspace, continue a previously initialized course or week, or organize a syllabus and lecture materials without mixing courses.
---

# Preview Course in FigJam

Build one persistent FigJam per course, initialize every slide for the requested week, and add source-grounded, deeply explained bilingual preview notes. Keep different courses isolated through a local registry and stable node names.

## Load required guidance

1. Load the `pdf` skill for PDF sources and the `presentations` skill for PPTX sources.
2. Load workspace dependencies before running the bundled Python scripts; use the returned Python, Poppler, and LibreOffice paths.
3. Load `figma-create-new-file` immediately before every Figma `create_new_file` call.
4. Load both `figma-use` and `figma-use-figjam` immediately before every `use_figma` call.
5. Read [references/preview-policy.md](references/preview-policy.md) before writing preview notes.
6. Read [references/figjam-layout.md](references/figjam-layout.md) before creating or rearranging FigJam content.
7. Read [references/state-schema.md](references/state-schema.md) before reading or updating the course registry.
8. Read [references/validation.md](references/validation.md) before validating a note batch or marking a week complete.

Use the current slide and adjacent pages first, then user-designated local course readings. Only when those sources still cannot clarify a concept, perform a limited concept-cluster web check using primary papers or authoritative academic sources. Obey an explicit request not to browse. Put reading and web material in separately labeled, linked support blocks; never blend it into the lecture's own claims.

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
- `low_information`: write one short factual sentence only, with immediate Chinese parentheses after professional English terms.
- `image_only`: preserve the slide and page number, but insert the fixed skip note; do not send the image to a vision model.
- `blank`: preserve the page number and mark it as blank; do not infer content.

Treat short assessment, agenda, divider, recap, and end pages as low-information even if their text count narrowly exceeds the automatic threshold.

Treat automatic `low_information` classification as provisional when a sparse page contains a diagram, model, process, comparison, or other visually meaningful structure. Render and visually inspect those candidates before writing notes; promote the page to `content` when the visual carries a substantive claim, and record the reason in the working payload or audit notes. Do not infer this promotion from text length alone.

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
5. Set all right-side page-note body text to FigJam `Large`; when no named preset is available, use 32 px. Use 36 px semibold section labels, and increase the card height instead of shrinking note text below the Large size.
6. Link the Course Hub week entry to the week section.
7. Write Figma changes in batches of about 12 slides. Record `lastBatch` only after each successful batch.
8. Set the week status to `initialized` when all page cards exist.

Default to the Module, Part, Section, or page range the user names. Complete every module continuously only when the user explicitly requests the whole week.

## Preview a requested module

1. Read the requested pages together with their adjacent pages and relevant syllabus text. Load only the user-designated local readings needed for that concept cluster.
2. Apply the deep note structure in `preview-policy.md`: 2–3 explanatory core paragraphs, structured terminology, and 3–5 mechanism or comparison points. Do not add a new `课堂确认` section.
3. In every Chinese explanation, immediately gloss every occurrence of a professional English term with its canonical Chinese rendering. Keep acronym expansions in the terminology section.
4. Keep `阅读补充 Reading Support` and `外部核实 External Check` visually separate and attach a clickable source to each block.
5. Do not create quizzes, exercises, flashcards, pronunciation, or parts of speech. Do not visually analyze `image_only` pages unless the user explicitly requests a specific page later.
6. Save the working page-note payload outside the persistent registry and run `scripts/validate_note_payload.py --strict-warnings` before each Figma write. Resolve every error and warning against the source material. Pass documented author, brand, title, or model-node exceptions through the exact-phrase `--english-exempt` option; never use an exemption for a technical term.
7. Write notes in page order and update FigJam in batches of about 12 pages. Reflow all three cards in an affected row to the maximum needed height; never shrink 32 px body text.
8. Mark the week `in_progress` and advance `lastBatch` only after the Figma write and read-back audit both succeed.
9. Give one concise completion update for the module instead of pausing after every page.

## Complete the weekly review

After all modules are complete:

1. Assemble the week's working page payload outside the registry and run `validate_note_payload.py --strict-warnings` across the full week so translation conflicts between batches cannot escape detection.
2. Collect one structured glossary entry per term and run `glossary_dedupe.py`.
3. Create the complete native FigJam glossary table: `English term | 中文释义 | 首次出现页面 ↗`.
4. Link every page cell to its `Wxx-Pxxx` card.
5. Build a left-to-right concept map with one root, 4–7 main branches, and 18–30 total nodes according to the material.
6. Put English keywords, a concise Chinese relationship, and relevant page labels in every node; link each node to its representative page.
7. Place Concept Map and Week Wrap-up in one compact, top-aligned row.
8. Update Concept Map and Week Wrap-up only when the completed notes add a genuinely new key concept; deeper prose alone is not a reason to rebuild them.
9. Keep only weekly counts and navigation links in Course Hub; do not duplicate the full glossary there.
10. Set the week status to `complete` only after local payload validation, live read-back checks, screenshots, and link validation pass.

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
- Every content page contains the required three explanation sections; new notes contain no `课堂确认` block.
- Every professional English term in explanatory prose is immediately followed by its canonical Chinese rendering, except the explicit exemption classes in `preview-policy.md`.
- Terminology translations are consistent across notes, concept map, wrap-up, and glossary.
- Reading and external supplements remain visually separate and their source labels are clickable.
- Every right-side page-note panel uses Large body text (32 px fallback), every section label uses 36 px semibold, and no text is clipped or overflowed.
- All cards in a row share the maximum required row height, and later rows, modules, summary areas, and enclosing section bounds are reflowed without overlap.
- Image-only pages retain the fixed skip note and were not visually analyzed.
- All glossary entries are unique under case-insensitive Unicode normalization.
- Every glossary page link and concept-map link resolves to an existing card.
- Concept Map and Week Wrap-up share the same top coordinate and do not overlap.
- No node outside the resolved course file was changed.

Run the skill structure validator after modifying this skill:

```bash
python /path/to/skill-creator/scripts/quick_validate.py /path/to/preview-course-in-figjam
```

Take section-level screenshots plus one dense half-screen card per module for visual QA; do not take one screenshot per slide unless diagnosing a specific defect.
