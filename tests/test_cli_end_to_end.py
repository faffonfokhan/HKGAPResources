import asyncio
from pathlib import Path

from hkgap_review import cli
from hkgap_review.schemas import Paragraph


def test_cli_run_review_with_mock_provider(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        cli,
        "extract_paragraphs",
        lambda _: [
            Paragraph(
                section="ABSTRACT",
                index=1,
                text="Short claim with never been continuously mapped for any protein.",
            )
        ],
    )

    out_path = tmp_path / "short_paper_review.md"
    exit_code = asyncio.run(
        cli._run_review(
            pdf_path=tmp_path / "dummy.pdf",
            out_path=out_path,
            provider="mock",
            model="mock-model",
        )
    )

    rendered = out_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert out_path.exists()
    assert "# Critical Review — HKGAP Short Paper v1.1" in rendered
    assert "## Paragraph-by-paragraph review" in rendered
    assert "### §ABSTRACT — Paragraph 1" in rendered
