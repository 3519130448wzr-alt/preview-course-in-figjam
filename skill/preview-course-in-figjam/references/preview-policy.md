# Preview policy

Use this policy when writing any page-level preview content.

## Evidence boundary

- Use only uploaded syllabi, decks, and speaker notes.
- Do not browse or silently import general knowledge.
- Distinguish a slide's explicit statement from a cautious explanation of its internal relationship.
- Do not invent a definition when the uploaded material does not support one; mark it for class confirmation instead.

## Page modes

### Content

Write a compact side note in this order:

1. `本页核心` — one or two Chinese sentences.
2. `生词与术语` — one structured entry per English term with a short Chinese meaning.
3. `重要概念` — explain relationships, contrasts, sequence, or causality shown by the slide.
4. `课堂确认` — only genuine ambiguity or a point the lecturer is likely to expand.

Use the original English keyword inside Chinese explanations. Do not include part of speech, pronunciation, quiz questions, exercises, flashcards, or generic study encouragement.

### Low information

Write one factual sentence only. Use this mode for module dividers, agendas, assessments, examples with almost no explanatory text, recap titles, and end pages. Do not manufacture terminology or conceptual analysis.

### Image only

Write exactly:

`纯图片页：本页默认不做预习推导；如有需要可单独分析。`

Do not send the image to a vision model during ordinary initialization or module preview. Analyze it only after the user explicitly identifies that page.

### Blank

Write exactly:

`空白页：保留原始页码，不生成预习内容。`

## Terminology

- Add only terms that materially help the user understand the course.
- Supply one term per structured entry; split `Quantitative / Qualitative research` into two entries before deduplication.
- Keep fixed expressions such as `Garbage in, garbage out` as one entry.
- Preserve the first occurrence page and original display capitalization.
- Deduplicate by Unicode-normalized, case-insensitive term text.
- Build the complete weekly glossary from the terms already selected in page notes; do not mine unrelated ordinary vocabulary from slide body text.

## Module completion

- Process the requested module in one batch and then report the completed page range.
- Let the user ask about doubtful pages afterward.
- Do not interrupt after each page unless the user explicitly requests page-by-page pacing.
