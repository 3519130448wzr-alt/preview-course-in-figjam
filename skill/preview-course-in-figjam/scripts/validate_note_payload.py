#!/usr/bin/env python3
"""Validate source-grounded page-note payloads before writing them to FigJam."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import sys
import unicodedata


PAGE_PATTERN = re.compile(r"^(?:W\d{2,3}-)?P\d{3,4}$", re.IGNORECASE)
PAGE_TOKEN_PATTERN = re.compile(
    r"^(?:W\d{2,3}-)?P\d{3,4}(?:[–-]P?\d{3,4})?$", re.IGNORECASE
)
TERM_LINE_PATTERN = re.compile(r"^[•*-]\s*([^｜]+?)\s*｜\s*(.+?)\s*$")
CONCEPT_LINE_PATTERN = re.compile(r"^(?:[•*-]|\d+[.)])\s+\S")
ENGLISH_SEQUENCE_PATTERN = re.compile(
    r"[A-Za-z][A-Za-z0-9’'&.\-/]*(?:\s+[A-Za-z0-9][A-Za-z0-9’'&.\-/]*)*"
)
ACRONYM_PATTERN = re.compile(r"\b[A-Z][A-Z0-9-]{1,}\b")
URL_PATTERN = re.compile(r"https?://\S+")
HEADINGS = ("本页核心", "生词与术语", "重要概念")
OPTIONAL_HEADINGS = ("阅读补充 Reading Support", "外部核实 External Check")
MODES = {"content", "low_information", "image_only", "blank", "preserve"}
IMAGE_ONLY_TEXT = "纯图片页：本页默认不做预习推导；如有需要可单独分析。"
BLANK_TEXT = "空白页：保留原始页码，不生成预习内容。"


@dataclass
class Result:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, page: str, message: str) -> None:
        self.errors.append(f"{page}: {message}")

    def warn(self, page: str, message: str) -> None:
        self.warnings.append(f"{page}: {message}")


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value or "")).strip()


def normalized(value: str) -> str:
    return clean(value).casefold()


def canonical_page(value: str) -> str:
    return clean(value).upper()


def parse_csv_pages(value: str | None) -> set[str]:
    if not value:
        return set()
    return {canonical_page(part) for part in value.split(",") if clean(part)}


def parse_csv_phrases(value: str | None) -> set[str]:
    if not value:
        return set()
    return {normalized(part) for part in value.split(",") if clean(part)}


def read_payload(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if isinstance(raw, dict) and "pages" in raw:
        raw = raw["pages"]
    pages: list[dict] = []
    if isinstance(raw, dict):
        for page, value in raw.items():
            if not isinstance(value, dict):
                raise ValueError(f"{page}: page entry must be an object")
            pages.append({"page": page, **value})
    elif isinstance(raw, list):
        for index, value in enumerate(raw, start=1):
            if not isinstance(value, dict):
                raise ValueError(f"entry {index} must be an object")
            pages.append(value)
    else:
        raise ValueError("payload must be a page mapping, a pages mapping, or a page list")
    return pages


def section(text: str, heading: str, later_headings: tuple[str, ...]) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    start += len(heading)
    end = len(text)
    for candidate in later_headings:
        position = text.find(candidate, start)
        if position >= 0:
            end = min(end, position)
    return text[start:end].strip()


def explanatory_text(text: str) -> str:
    core = section(text, "本页核心", ("生词与术语", "重要概念", *OPTIONAL_HEADINGS))
    concepts = section(text, "重要概念", OPTIONAL_HEADINGS)
    return f"{core}\n{concepts}".strip()


def technical_scan_text(text: str) -> str:
    """Return visible explanatory prose, excluding terminology and source labels."""

    parts = [explanatory_text(text)]
    for index, heading in enumerate(OPTIONAL_HEADINGS):
        if heading not in text:
            continue
        block = section(text, heading, OPTIONAL_HEADINGS[index + 1 :])
        support_lines = [
            line for line in block.splitlines() if not line.strip().startswith("来源｜")
        ]
        parts.append("\n".join(support_lines).strip())
    return "\n".join(part for part in parts if part).strip()


def parse_terms(text: str, page: str, result: Result) -> list[tuple[str, str]]:
    block = section(text, "生词与术语", ("重要概念", *OPTIONAL_HEADINGS))
    entries: list[tuple[str, str]] = []
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = TERM_LINE_PATTERN.fullmatch(line)
        if not match:
            result.error(page, f"malformed terminology line: {line}")
            continue
        term, zh = clean(match.group(1)), clean(match.group(2))
        if not re.search(r"[A-Za-z]", term):
            result.error(page, f"terminology entry lacks an English term: {line}")
        if not re.search(r"[\u3400-\u9fff]", zh):
            result.error(page, f"terminology entry lacks a Chinese explanation: {line}")
        entries.append((term, zh))
    if not entries:
        result.error(page, "生词与术语 has no structured entries")
    return entries


def term_aliases(term: str) -> set[str]:
    aliases = {clean(term)}
    for acronym in ACRONYM_PATTERN.findall(term):
        aliases.add(acronym)
    without_parenthetical = clean(re.sub(r"\s*\([^)]*\)\s*", " ", term))
    if without_parenthetical:
        aliases.add(without_parenthetical)
    return {alias for alias in aliases if re.search(r"[A-Za-z]", alias)}


def chinese_gloss_after(text: str, end: int) -> str | None:
    tail = text[end:]
    # "Immediate" means no intervening whitespace. Closing punctuation that is
    # grammatically part of a quoted English term is allowed before the gloss.
    tail = re.sub(r"^[\"'”’》】]{0,2}", "", tail)
    match = re.match(r"^（([^）]*[\u3400-\u9fff][^）]*)）", tail)
    return match.group(1) if match else None


def has_chinese_parenthesis_after(text: str, end: int) -> bool:
    return chinese_gloss_after(text, end) is not None


def chinese_parenthetical_spans(text: str) -> list[tuple[int, int]]:
    return [match.span() for match in re.finditer(r"（[^）]*）", text)]


def glossed_english_spans(text: str) -> list[tuple[int, int]]:
    """Return English phrases immediately followed by a full-width Chinese gloss."""

    return [
        match.span()
        for match in ENGLISH_SEQUENCE_PATTERN.finditer(text)
        if has_chinese_parenthesis_after(text, match.end())
    ]


def span_is_contained(start: int, end: int, containers: list[tuple[int, int]]) -> bool:
    return any(start >= left and end <= right for left, right in containers)


def maximal_known_term_matches(
    text: str, terms: list[tuple[str, str]]
) -> list[tuple[int, int, str, str]]:
    """Return longest, non-overlapping catalogued term occurrences.

    A glossary can contain both ``modality`` and ``modality affordance``.  The
    longer occurrence owns the span, so the nested shorter term is not reported
    as a second unglossed occurrence.
    """

    aliases = {
        (alias, zh) for term, zh in terms for alias in term_aliases(term)
    }
    candidates: list[tuple[int, int, str, str]] = []
    for alias, expected_zh in aliases:
        pattern = re.compile(
            rf"(?<![A-Za-z0-9]){re.escape(alias)}(?![A-Za-z0-9])", re.IGNORECASE
        )
        for match in pattern.finditer(text):
            candidates.append(
                (match.start(), match.end(), match.group(0), expected_zh)
            )

    # At a shared start, prefer the longest alias. Across different starts, keep
    # the first maximal phrase and discard any shorter span nested inside it.
    candidates.sort(
        key=lambda item: (
            item[0],
            -(item[1] - item[0]),
            item[2].casefold(),
            normalized(item[3]),
        )
    )
    selected: list[tuple[int, int, str, str]] = []
    for candidate in candidates:
        start, end, _, _ = candidate
        if any(
            start < kept_end and end > kept_start
            for kept_start, kept_end, _, _ in selected
        ):
            continue
        selected.append(candidate)
    return selected


def check_known_terms_have_glosses(
    page: str, text: str, terms: list[tuple[str, str]], result: Result
) -> list[tuple[int, int, str]]:
    prose = URL_PATTERN.sub("", technical_scan_text(text))
    matches = maximal_known_term_matches(prose, terms)
    glossed_spans = glossed_english_spans(prose)
    parenthetical_spans = chinese_parenthetical_spans(prose)
    for start, end, matched_text, expected_zh in matches:
        if span_is_contained(start, end, parenthetical_spans):
            continue
        actual_zh = chinese_gloss_after(prose, end)
        if actual_zh is not None:
            if normalized(actual_zh) != normalized(expected_zh):
                result.error(
                    page,
                    f"inline translation for {matched_text} is {actual_zh}; "
                    f"expected {expected_zh}",
                )
        elif not span_is_contained(start, end, glossed_spans):
            result.error(
                page,
                f"technical English term lacks immediate Chinese parentheses: {matched_text}",
            )
    return [(start, end, matched_text) for start, end, matched_text, _ in matches]


def check_unlisted_english(
    page: str,
    text: str,
    terms: list[tuple[str, str]],
    known_spans: list[tuple[int, int, str]],
    english_exemptions: set[str],
    result: Result,
    *,
    direct_prose: bool = False,
) -> None:
    prose = URL_PATTERN.sub("", text if direct_prose else technical_scan_text(text))
    known = {normalized(alias) for term, _ in terms for alias in term_aliases(term)}
    masked = list(prose)
    for start, end in chinese_parenthetical_spans(prose):
        masked[start:end] = " " * (end - start)
    for start, end in glossed_english_spans(prose):
        masked[start:end] = " " * (end - start)
    for start, end, _ in known_spans:
        masked[start:end] = " " * (end - start)
    unknown_prose = "".join(masked)
    for match in ENGLISH_SEQUENCE_PATTERN.finditer(unknown_prose):
        phrase = clean(match.group(0))
        if not phrase:
            continue
        if (
            normalized(phrase) in known
            or normalized(phrase) in english_exemptions
            or has_chinese_parenthesis_after(prose, match.end())
        ):
            continue
        if PAGE_TOKEN_PATTERN.fullmatch(phrase) or re.fullmatch(r"\d{4}", phrase):
            continue
        if len(phrase) == 1 and phrase.isupper():
            continue
        result.warn(page, f"review possibly unglossed English phrase: {phrase}")


def check_source_blocks(page: str, text: str, result: Result) -> None:
    for index, heading in enumerate(OPTIONAL_HEADINGS):
        if heading not in text:
            continue
        later = OPTIONAL_HEADINGS[index + 1 :]
        block = section(text, heading, later)
        source_lines = [line.strip() for line in block.splitlines() if line.strip().startswith("来源｜")]
        if len(source_lines) != 1:
            result.error(page, f"{heading} requires exactly one 来源｜ line")
        elif "↗" not in source_lines[0]:
            result.error(page, f"{heading} source line must end with a link marker ↗")


def validate_page(
    entry: dict,
    result: Result,
    allow_classroom: set[str],
    allow_short: set[str],
    english_exemptions: set[str],
) -> tuple[str, list[tuple[str, str]]]:
    page = canonical_page(str(entry.get("page", "")))
    mode = clean(str(entry.get("mode", "")))
    text = str(entry.get("text", ""))
    if not PAGE_PATTERN.fullmatch(page):
        result.error(page or "<missing-page>", "invalid or missing page label")
    if mode not in MODES:
        result.error(page, f"invalid mode: {mode or '<missing>'}")
        return page, []
    if mode == "preserve":
        return page, []
    if not text.strip():
        result.error(page, "text is empty")
        return page, []
    if "课堂确认" in text and page not in allow_classroom:
        result.error(page, "new notes must not add a 课堂确认 section")
    if mode == "image_only":
        if text.strip() != IMAGE_ONLY_TEXT:
            result.error(page, "image_only text must match the fixed skip note")
        return page, []
    if mode == "blank":
        if text.strip() != BLANK_TEXT:
            result.error(page, "blank text must match the fixed blank-page note")
        return page, []
    if mode == "low_information":
        if any(heading in text for heading in (*HEADINGS, *OPTIONAL_HEADINGS)):
            result.error(page, "low_information must remain one factual sentence without sections")
        nonempty = [line for line in text.splitlines() if line.strip()]
        if len(nonempty) != 1:
            result.error(page, "low_information must contain exactly one non-empty line")
        check_unlisted_english(
            page,
            text,
            [],
            [],
            english_exemptions,
            result,
            direct_prose=True,
        )
        return page, []

    positions = [text.find(heading) for heading in HEADINGS]
    for heading, position in zip(HEADINGS, positions):
        if position < 0:
            result.error(page, f"missing required section: {heading}")
        elif text.count(heading) != 1:
            result.error(page, f"section must appear exactly once: {heading}")
    if all(position >= 0 for position in positions) and positions != sorted(positions):
        result.error(page, "required sections are out of order")
    if any(position < 0 for position in positions):
        return page, []

    core = section(text, "本页核心", ("生词与术语", "重要概念", *OPTIONAL_HEADINGS))
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", core) if part.strip()]
    if len(paragraphs) not in {2, 3}:
        result.error(page, f"本页核心 needs 2–3 short paragraphs; found {len(paragraphs)}")

    concepts = section(text, "重要概念", OPTIONAL_HEADINGS)
    concept_lines = [line.strip() for line in concepts.splitlines() if CONCEPT_LINE_PATTERN.match(line.strip())]
    if not 3 <= len(concept_lines) <= 5:
        result.error(page, f"重要概念 needs 3–5 points; found {len(concept_lines)}")

    cjk_count = len(re.findall(r"[\u3400-\u9fff]", explanatory_text(text)))
    if cjk_count < 300 and page not in allow_short:
        result.warn(page, f"explanatory prose is shorter than the usual 300 Chinese characters: {cjk_count}")
    if cjk_count > 440:
        result.warn(page, f"explanatory prose exceeds the usual 440 Chinese characters: {cjk_count}")

    terms = parse_terms(text, page, result)
    known_spans = check_known_terms_have_glosses(page, text, terms, result)
    check_unlisted_english(
        page, text, terms, known_spans, english_exemptions, result
    )
    check_source_blocks(page, text, result)
    return page, terms


def validate(
    pages: list[dict],
    allow_classroom: set[str],
    allow_short: set[str],
    english_exemptions: set[str],
) -> tuple[Result, dict]:
    result = Result()
    page_seen: set[str] = set()
    translations: dict[str, tuple[str, str, str]] = {}
    mode_counts: dict[str, int] = {mode: 0 for mode in sorted(MODES)}
    for entry in pages:
        page, terms = validate_page(
            entry, result, allow_classroom, allow_short, english_exemptions
        )
        mode = clean(str(entry.get("mode", "")))
        if mode in mode_counts:
            mode_counts[mode] += 1
        if page in page_seen:
            result.error(page, "duplicate page label")
        page_seen.add(page)
        for term, zh in terms:
            key = normalized(term)
            if key in translations and normalized(zh) != normalized(translations[key][1]):
                first_term, first_zh, first_page = translations[key]
                result.error(
                    page,
                    f"inconsistent translation for {term}: {zh}; first used as {first_term}｜{first_zh} on {first_page}",
                )
            else:
                translations[key] = (term, zh, page)
    summary = {
        "pages": len(pages),
        "modes": mode_counts,
        "uniqueTerms": len(translations),
        "errors": len(result.errors),
        "warnings": len(result.warnings),
    }
    return result, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument(
        "--allow-classroom-on",
        help="comma-separated legacy page labels allowed to retain an existing 课堂确认 block",
    )
    parser.add_argument(
        "--allow-short-on",
        help="comma-separated source-limited content pages allowed below the usual length range",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="return failure when review warnings remain",
    )
    parser.add_argument(
        "--english-exempt",
        help=(
            "comma-separated exact English phrases exempt from unknown-English review "
            "(authors, brands, titles, or other documented non-technical names)"
        ),
    )
    args = parser.parse_args()
    try:
        pages = read_payload(args.input.expanduser().resolve())
        result, summary = validate(
            pages,
            parse_csv_pages(args.allow_classroom_on),
            parse_csv_pages(args.allow_short_on),
            parse_csv_phrases(args.english_exempt),
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        for message in result.errors:
            print(f"ERROR: {message}", file=sys.stderr)
        for message in result.warnings:
            print(f"WARNING: {message}", file=sys.stderr)
        if result.errors or (args.strict_warnings and result.warnings):
            return 2
    except Exception as exc:
        print(f"validate_note_payload: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
