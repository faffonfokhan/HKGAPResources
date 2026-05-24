from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

from .schemas import Paragraph

_SECTION_PATTERNS = [
    (re.compile(r"^abstract$", re.IGNORECASE), "ABSTRACT"),
    (re.compile(r"^introduction$", re.IGNORECASE), "INTRODUCTION"),
    (re.compile(r"^literature review$", re.IGNORECASE), "LITERATURE REVIEW"),
    (re.compile(r"^methods?$", re.IGNORECASE), "Methods"),
    (re.compile(r"^4\.1"), "4.1"),
    (re.compile(r"^4\.2"), "4.2"),
    (re.compile(r"^4\.3"), "4.3"),
    (re.compile(r"^4\.4"), "4.4"),
    (re.compile(r"^6\.?\s*conclusions?$", re.IGNORECASE), "6. Conclusions"),
    (re.compile(r"^references$", re.IGNORECASE), "References"),
]


def _normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.replace("\xa0", " ")).strip()


def _as_section_heading(line: str) -> str | None:
    cleaned = _normalize_line(line)
    if not cleaned:
        return None
    for pattern, canonical in _SECTION_PATTERNS:
        if pattern.search(cleaned):
            return canonical
    return None


def _extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    page_text: list[str] = []
    for page in reader.pages:
        extracted = page.extract_text() or ""
        page_text.append(extracted)
    return "\n".join(page_text)


def segment_paragraphs(raw_text: str) -> list[Paragraph]:
    lines = raw_text.splitlines()
    current_section = "UNSECTIONED"
    section_counts: dict[str, int] = {}
    paragraphs: list[Paragraph] = []
    paragraph_buffer: list[str] = []
    references_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_buffer
        if not paragraph_buffer or current_section == "References":
            paragraph_buffer = []
            return
        text = _normalize_line(" ".join(paragraph_buffer))
        if text:
            section_counts[current_section] = section_counts.get(current_section, 0) + 1
            paragraphs.append(
                Paragraph(section=current_section, index=section_counts[current_section], text=text)
            )
        paragraph_buffer = []

    for line in lines:
        heading = _as_section_heading(line)
        if heading:
            flush_paragraph()
            current_section = heading
            continue

        cleaned = _normalize_line(line)
        if current_section == "References":
            if cleaned:
                references_lines.append(cleaned)
            continue

        if not cleaned:
            flush_paragraph()
            continue
        paragraph_buffer.append(cleaned)

    flush_paragraph()

    if references_lines:
        section_counts["References"] = 1
        paragraphs.append(
            Paragraph(section="References", index=1, text=_normalize_line(" ".join(references_lines)))
        )

    return paragraphs


def extract_paragraphs(pdf_path: Path) -> list[Paragraph]:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    text = _extract_pdf_text(pdf_path)
    paragraphs = segment_paragraphs(text)
    if not paragraphs:
        raise ValueError(f"No paragraphs extracted from: {pdf_path}")
    return paragraphs
