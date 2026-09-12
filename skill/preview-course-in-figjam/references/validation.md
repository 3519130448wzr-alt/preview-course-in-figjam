# Preview validation

Use this reference before a note batch is written and again after the Figma write succeeds.

## Local note-payload check

Prepare a UTF-8 JSON payload as either a page mapping or a list:

```json
{
  "P029": {
    "mode": "content",
    "text": "本页核心\n……\n\n……\n\n生词与术语\n• modality｜模态／呈现方式\n\n重要概念\n• ……\n• ……\n• ……"
  },
  "P030": {
    "mode": "low_information",
    "text": "本页进入 MAIN Model（MAIN 模型）的结构说明。"
  }
}
```

Run:

```bash
python scripts/validate_note_payload.py NOTES.json
```

The validator checks:

- page labels and modes;
- the ordered `本页核心`, `生词与术语`, and `重要概念` sections;
- 2–3 core paragraphs and 3–5 concept points;
- new `课堂确认` blocks;
- structured `English｜中文` term entries;
- immediate Chinese parentheses for catalogued terms, plus warnings for any remaining English phrase that needs review;
- agreement between each catalogued term's inline gloss and its `English｜中文` canonical rendering;
- conflicting Chinese renderings of the same normalized English term;
- source markers for `阅读补充 Reading Support` and `外部核实 External Check`;
- the usual 300–440-Chinese-character depth range as a warning rather than a reason to invent content.

Run the final pre-write check with `--strict-warnings`. When a warning is an author name, brand, publication title, or other legitimate non-technical English exception, document it with an exact phrase rather than weakening the scan:

```bash
python scripts/validate_note_payload.py NOTES.json \
  --strict-warnings \
  --english-exempt "McLuhan,Best Buy"
```

Never exempt a technical term. For explicitly preserved legacy pages, pass their exact labels to `--allow-classroom-on`. For a genuinely source-limited page, use `--allow-short-on` rather than padding it.

The payload contains working text only. Do not persist it in the course registry.

Validate each write batch, then validate the combined full-week working payload before generating the final glossary or marking the week complete. The combined pass is what detects translation conflicts across separate write batches.

Before accepting a `low_information` mode from the manifest, visually review sparse candidates that contain a diagram, model, process, or comparison. A short extracted string does not prove that the slide lacks substantive visual content. Record every manual promotion to `content` in the working audit notes.

## Live FigJam audit

After each successful batch, use `use_figma` to read the actual nodes back. Do not infer success from the write request alone and do not assume a failed transport was atomic.

Check these invariants programmatically:

1. The scoped page-card names are unique and each card has exactly one note panel and one note text node.
2. Rendered note text matches the validated payload for every non-preserved page.
3. Body text is 32 px regular; the five possible section labels are 36 px semibold.
4. The note bottom stays inside the panel with safe padding, and the panel stays inside the card.
5. All cards in a three-card row share the row's maximum required height and expected x positions.
6. Later rows and modules start below the previous bottom edge; Concept Map, Week Wrap-up, Glossary, Week, Term, and Course bounds follow the new layout.
7. Every visible `Reading 01`, `Reading 02`, external source label, glossary page label, and concept-map page label carries a real Figma URL or NODE hyperlink.
8. Glossary terms are unique under Unicode NFKC normalization, collapsed whitespace, and case-insensitive comparison.
9. Existing `课堂确认` text appears only on explicitly preserved legacy pages.

Return counts and a compact issue list from the audit call. A zero transport error is not sufficient; only advance the registry checkpoint when the read-back audit passes.

## Visual QA

- Screenshot each completed module once to inspect the grid and downstream spacing.
- Screenshot at least one dense content card per module at a practical half-screen reading scale to verify 32/36 px typography and bilingual parentheses.
- Screenshot one low-information card, the Concept Map, Week Wrap-up, and Glossary.
- Reflow instead of shrinking text whenever a screenshot reveals crowding.
- Set the week to `complete` only after local validation, live audit, hyperlinks, and screenshots all pass.
