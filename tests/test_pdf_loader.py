from pathlib import Path

import hkgap_review.pdf_loader as pdf_loader


class _FakePage:
    def extract_text(self) -> str:
        return """ABSTRACT
First abstract paragraph.

Second abstract paragraph.

INTRODUCTION
Intro paragraph.

References
Ref one.
Ref two.
"""


class _FakeReader:
    def __init__(self, _: str):
        self.pages = [_FakePage()]


def test_extract_paragraphs_sections_and_reference_block(monkeypatch) -> None:
    fixture_pdf = Path(__file__).parent / "fixtures" / "tiny.pdf"
    monkeypatch.setattr(pdf_loader, "PdfReader", _FakeReader)

    paragraphs = pdf_loader.extract_paragraphs(fixture_pdf)

    assert [p.section for p in paragraphs] == ["ABSTRACT", "ABSTRACT", "INTRODUCTION", "References"]
    assert paragraphs[-1].index == 1
    assert "Ref one." in paragraphs[-1].text
    assert "Ref two." in paragraphs[-1].text
