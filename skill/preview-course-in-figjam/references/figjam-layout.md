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

Append new term and week sections below the current course bounds with at least 200 canvas units of separation. Never position content from one course file using coordinates read from another file.

## Course Hub

- Use a width of 9400 canvas units.
- Show course identity, syllabus summary when present, term/week navigation, week completion status, term counts, and Master Glossary index cards.
- Make each week index card link to the corresponding Week section.
- Represent the Master Glossary as counts and weekly links, not a duplicated long table.

## Weekly page area

- Use a 9400-unit outer Week section and a three-column card grid.
- Use 180-unit outer margins, cards up to 2960 units wide, and at least 80-unit gutters.
- Fit the slide image into a 1780 by 1000 region without changing its aspect ratio.
- Put the note panel to the right of the slide, approximately 1000 units wide, with a 40-unit internal gap.
- Derive card height from the taller of slide and note, plus 120 units of padding.
- Keep every page number visible even when the page is blank or image-only.
- Make Module headers span the full weekly width and keep pages in original order.

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
- Use one native three-column FigJam table: `English term | 中文释义 | 首次出现页面 ↗`.
- Size columns from content and clamp them to: English 650–1100, Chinese 650–1100, page 450–650.
- Use approximately 46 units for the header row and the smallest readable native table body height.
- Link every page cell to its `Wxx-Pxxx` node.
- Resize the Week section to the maximum bottom edge plus 200 units; do not leave the previous full-width empty canvas.

## Write and QA rules

- Write page cards and notes in batches of about 12 pages to avoid Figma timeouts.
- Keep operations idempotent by finding stable names before creating nodes.
- Treat a failed `use_figma` execution as atomic; fix the script before retrying.
- After each module, screenshot the module section once.
- After weekly completion, screenshot Concept Map and Week Wrap-up separately, then validate counts, links, overlap, clipping, and minimum readable text.
