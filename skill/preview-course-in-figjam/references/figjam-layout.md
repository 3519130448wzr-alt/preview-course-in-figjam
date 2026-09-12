# FigJam layout specification

Use native FigJam sections, shapes, connectors, tables, and internal `NODE` hyperlinks. Load all existing fonts before text mutations and return every mutated node ID from each `use_figma` call.

## File hierarchy

Use this hierarchy in every course file:

1. `Course Hub · {course key}`
2. `Term · {term or Unspecified term}`
3. `Week · Wxx · {week title}`
4. `Module · Wxx-Mxx · {module title}`
5. Page cards named exactly `Wxx-Pxxx`
6. `Concept Map · Wxx`
7. `Week Wrap-up · Wxx`
8. `Glossary · Wxx`

Append new term and week sections below the current course bounds with at least 200 canvas units of separation. Never position content from one course file using coordinates read from another file.

## Course Hub

- Use a width of 9400 canvas units.
- Show course identity, syllabus summary when present, term/week navigation, week completion status, term counts, and Master Glossary index cards.
- Make each week index card link to the corresponding Week section.
- Represent the Master Glossary as counts and weekly links, not a duplicated long table.

## Weekly page area

- Use a 9400-unit outer Week section and a three-column card grid.
- Use 120–180-unit outer margins, 2920-unit cards, and at least 80-unit gutters.
- Fit the slide image into an approximately 1330 by 1000 region without changing its aspect ratio.
- Put a 1400-unit note panel to the right of the slide, leaving about 55–60 units between the slide and panel and 60 units of inner text padding.
- Start from a minimum card height of about 1700 units. Derive each row's height from the tallest note or slide in that three-card row, plus safe bottom padding.
- Keep every page number visible even when the page is blank or image-only.
- Make Module headers span the full weekly width and keep pages in original order.

### Page-note typography

- Use FigJam `Large` for every right-side page-note body. If the API does not expose named text presets, use 32 px regular as the fallback.
- Use 36 px semibold for `本页核心`, `生词与术语`, `重要概念`, `阅读补充 Reading Support`, and `外部核实 External Check` labels.
- Keep line height around 1.35 and at least 20 units of separation between note sections.
- Give reading and external supplements a distinct heading color, one explicit source line, and a clickable source link.
- Never reduce body text below the Large size to make it fit. Grow the note panel and page card vertically.
- After any content-height change, calculate the maximum required height for all three cards in that row. Apply that height to every card and note panel in the row, then reflow every later row and module.
- After the modules move, reposition Concept Map, Week Wrap-up, and Glossary in that order. Expand the Week, Term, and Course section bounds to contain the new maximum bottom and right edges.
- Validate the sidebar at a practical half-screen reading zoom, not only in a whole-week thumbnail.

## Concept Map

- Use one root, 4–7 pastel-colored main branches, and enough leaves for 18–30 total nodes.
- Use a three-column left-to-right tree: root, branch, knowledge node.
- Use curved connectors without arrowheads when supported.
- Put English keyword, concise Chinese relationship, and page label in each node.
- Link the entire node to the first representative page; show additional page labels in text.
- Estimate width from the longest line: `characters × font size × 0.58 + 96`.
- Clamp root width to 460–620, branch width to 600–900, and leaf width to 700–1150.
- Calculate height from wrapped line count using `line count × font size × 1.35 + 36`.
- Never stretch every leaf to a uniform oversized width.

## Week Wrap-up

- Place Concept Map and Week Wrap-up on the same top coordinate with an 180-unit gap.
- Target Concept Map width 3200–3600 and Wrap-up width 3000–3400; let height follow content.

## Weekly glossary

- Place `Glossary · Wxx` below the lower edge of Concept Map and Week Wrap-up with at least 180 units of separation.
- Use native three-column FigJam tables: `English term | 中文释义 | 首次出现页面 ↗`.
- Split a long glossary into a compact three-column grid of tables rather than making one extremely tall table. Repeat the header in every table and preserve global first-occurrence order.
- Size columns from content and clamp them to: English 650–1100, Chinese 650–1100, page 450–650.
- Use approximately 46 units for the header row and the smallest readable native table body height.
- Link every page cell to its `Wxx-Pxxx` node.
- Resize the Week section to the maximum bottom edge plus 200 units; do not leave the previous full-width empty canvas.

## Write and QA rules

- Write page cards and notes in batches of about 12 pages to avoid Figma timeouts.
- Keep operations idempotent by finding stable names before creating nodes.
- Do not assume a failed or disconnected `use_figma` execution was atomic. Re-read stable node names and actual content, then retry with an idempotent script that converges on the intended state.
- Before writing, run `scripts/validate_note_payload.py` to check required sections, new `课堂确认` blocks, technical-English parentheses, terminology consistency, and supplement source markers.
- After writing, programmatically verify 32 px body text, 36 px section labels, note bounds inside cards, equal heights within each row, downstream section order, and no overlaps.
- Verify that every `Reading Support`, `External Check`, glossary-page, and concept-map page label has a real Figma URL or NODE hyperlink, not only a visible arrow glyph.
- After each module, screenshot the module section once and inspect at least one dense content card at a practical half-screen zoom. The module thumbnail cannot substitute for the card-level readability check.
- After weekly completion, screenshot Concept Map, Week Wrap-up, and Glossary separately, then validate page counts, unique normalized terms, links, overlap, clipping, and minimum readable text.
