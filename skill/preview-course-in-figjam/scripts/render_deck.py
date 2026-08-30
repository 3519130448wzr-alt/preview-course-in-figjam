#!/usr/bin/env python3
"""Render selected PDF or PPTX slides to numbered PNG files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def page_count(pdf_path: Path) -> int:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is required; use the bundled workspace Python runtime") from exc
    return len(PdfReader(str(pdf_path)).pages)


def parse_pages(value: str | None, total: int) -> list[int]:
    if not value:
        return list(range(1, total + 1))
    selected: set[int] = set()
    for raw in value.split(","):
        token = raw.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start = int(start_text) if start_text else 1
            end = int(end_text) if end_text else total
            if start > end:
                raise ValueError(f"invalid descending page range: {token}")
            selected.update(range(start, end + 1))
        else:
            selected.add(int(token))
    if not selected:
        raise ValueError("page range selected no pages")
    invalid = sorted(page for page in selected if page < 1 or page > total)
    if invalid:
        raise ValueError(f"page numbers outside 1-{total}: {invalid}")
    return sorted(selected)


def contiguous_runs(pages: list[int]) -> list[list[int]]:
    runs: list[list[int]] = []
    for page in pages:
        if not runs or page != runs[-1][-1] + 1:
            runs.append([page])
        else:
            runs[-1].append(page)
    return runs


def convert_pptx(source: Path, work_dir: Path) -> Path:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError("LibreOffice/soffice is required to render PPTX files")
    command = [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(work_dir), str(source)]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"PPTX conversion failed: {completed.stderr.strip() or completed.stdout.strip()}")
    expected = work_dir / f"{source.stem}.pdf"
    if expected.is_file():
        return expected
    candidates = sorted(work_dir.glob("*.pdf"))
    if len(candidates) != 1:
        raise RuntimeError("PPTX conversion did not produce exactly one PDF")
    return candidates[0]


def render_pdf(pdf_path: Path, output_dir: Path, pages: list[int], dpi: int) -> list[Path]:
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("Poppler pdftoppm is required to render slides")
    output_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []
    with tempfile.TemporaryDirectory(prefix="course-preview-render-") as temporary:
        temporary_dir = Path(temporary)
        for run_index, run in enumerate(contiguous_runs(pages)):
            prefix = temporary_dir / f"chunk-{run_index:03d}"
            command = [
                pdftoppm,
                "-f",
                str(run[0]),
                "-l",
                str(run[-1]),
                "-r",
                str(dpi),
                "-png",
                str(pdf_path),
                str(prefix),
            ]
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            if completed.returncode != 0:
                raise RuntimeError(f"PDF rendering failed: {completed.stderr.strip()}")
            chunk_files = sorted(temporary_dir.glob(f"{prefix.name}-*.png"))
            if len(chunk_files) != len(run):
                raise RuntimeError(f"expected {len(run)} rendered pages, found {len(chunk_files)}")
            for page, source_file in zip(run, chunk_files):
                destination = output_dir / f"page-{page:03d}.png"
                shutil.copy2(source_file, destination)
                rendered.append(destination)
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pages", help="1-based pages, e.g. 1-3,7,10-")
    parser.add_argument("--dpi", type=int, default=144)
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if not source.is_file():
        parser.error(f"source file does not exist: {source}")
    if source.suffix.casefold() not in {".pdf", ".pptx"}:
        parser.error("SOURCE must be a .pdf or .pptx file")
    if args.dpi < 72 or args.dpi > 300:
        parser.error("--dpi must be between 72 and 300")

    try:
        with tempfile.TemporaryDirectory(prefix="course-preview-convert-") as temporary:
            converted = source.suffix.casefold() == ".pptx"
            pdf_path = convert_pptx(source, Path(temporary)) if converted else source
            total = page_count(pdf_path)
            pages = parse_pages(args.pages, total)
            outputs = render_pdf(pdf_path, output_dir, pages, args.dpi)
        json.dump(
            {
                "sourceName": source.name,
                "convertedFromPptx": converted,
                "pageCount": total,
                "renderedPages": pages,
                "files": [str(path) for path in outputs],
            },
            sys.stdout,
            ensure_ascii=False,
            indent=2,
        )
        sys.stdout.write("\n")
    except Exception as exc:
        print(f"render_deck: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
