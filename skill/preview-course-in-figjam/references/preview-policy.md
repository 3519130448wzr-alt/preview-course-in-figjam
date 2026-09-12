# Preview policy

Use this policy when writing any page-level preview content.

## Evidence hierarchy and boundaries

Use sources in this order:

1. The current lecture page, its adjacent pages, and speaker notes.
2. User-designated local readings from the same course.
3. Only when the first two levels still cannot clarify a concept, perform a small web check for the whole concept cluster and use primary papers or authoritative academic sources.

Obey an explicit request not to browse. Never use outside material merely to make a note longer. Keep the source layers visibly separate:

- Put material from local readings in `阅读补充 Reading Support`.
- Put web-verified material in `外部核实 External Check`.
- End each supplement with one `来源｜... ↗` line and make the source text clickable in FigJam.
- Do not blend a supplement into what the lecture itself claims.

When evidence is insufficient, write less and state the evidence boundary inside `重要概念`; do not invent a definition, fill space with general knowledge, or add a new `课堂确认` section.

## Page modes

### Content

Write the sidebar in this order:

1. `本页核心` — 2–3 short Chinese paragraphs explaining what the page says, why it matters, and how it connects to adjacent pages.
2. `生词与术语` — one `English｜中文` entry per useful term. Expand acronyms here.
3. `重要概念` — 3–5 points that unpack the definition, mechanism chain, comparison dimension, lecture example, and evidence boundary when the source supports them.
4. Optional `阅读补充 Reading Support`.
5. Optional `外部核实 External Check`.

Aim for roughly 300–440 Chinese characters of explanatory prose across `本页核心` and `重要概念`. This is a depth guide, not a quota: a source-limited page may be shorter, while a genuinely dense mechanism page may be longer. Never pad the note or repeat the slide to hit the range.

Use professional but direct logic. Prefer explicit links such as “因为—所以—这意味着” over compressed restatement. Explain a mechanism or comparison rather than merely repeating a conclusion.

Do not add a new `课堂确认` block. A pre-existing block may remain only when the user explicitly asks to preserve that legacy page.

Do not include part of speech, pronunciation, quiz questions, exercises, flashcards, or generic study encouragement.

### Low information

Write one factual sentence only. Use this mode for module dividers, agendas, assessments, examples with almost no explanatory text, recap titles, and end pages. Do not manufacture terminology or conceptual analysis. Professional English terms in this sentence still require immediate Chinese parentheses.

### Image only

Write exactly:

`纯图片页：本页默认不做预习推导；如有需要可单独分析。`

Do not send the image to a vision model during ordinary initialization or module preview. Analyze it only after the user explicitly identifies that page.

### Blank

Write exactly:

`空白页：保留原始页码，不生成预习内容。`

## Bilingual terminology

- In Chinese explanatory prose, every occurrence of a professional English term must immediately carry its established Chinese meaning: `modality（模态／呈现方式）`.
- Apply this rule to repeated occurrences, not only the first one.
- Write an acronym in prose as `CAS（计算机作为信息来源）`; put its full English expansion in `生词与术语`.
- The immediate-parenthesis rule does not apply to author names, years, brand names, publication titles, URLs, or single-letter model nodes.
- A short English quotation is acceptable only when its Chinese translation immediately follows the closing quotation mark.
- In `生词与术语`, use `English｜中文` without repeating parentheses.
- Maintain one canonical Chinese rendering for each normalized English term across the week's sidebars, concept map, wrap-up, and glossary.
- Add terms that materially help the learner understand the course. Do not mine unrelated ordinary vocabulary from slide body text.
- Split paired concepts such as `Quantitative / Qualitative research` before deduplication, but keep fixed expressions such as `Garbage in, garbage out` as one entry.
- Preserve the first occurrence page and original display capitalization. Deduplicate with Unicode NFKC normalization, collapsed whitespace, and case-insensitive comparison.

## Module completion

- Process the requested module or page range in one continuous batch and then report the completed range.
- If the user explicitly asks for the whole week, continue through all modules without asking for a separate module name.
- Let the user ask about doubtful pages afterward; do not interrupt after every page unless they request page-by-page pacing.
- Run the note-payload validator before Figma writes and resolve errors. Review warnings against the evidence boundary rather than padding notes mechanically.
