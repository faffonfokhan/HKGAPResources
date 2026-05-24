from datetime import datetime, timezone

from hkgap_review.renderer import render_report
from hkgap_review.schemas import (
    ChecklistItem,
    MergedCommentary,
    Paragraph,
    RefereeItem,
    ReviewReport,
)


def test_renderer_generates_required_sections() -> None:
    merged = MergedCommentary(
        paragraph=Paragraph(section="ABSTRACT", index=1, text="Claim text."),
        verbatim="Claim text.",
        explainer_commentary="This is clear. Think of it as a marble crossing a hill.",
        referee_critique=[
            RefereeItem(category="Factual", comment="Needs citation", severity="major")
        ],
        checklist=[ChecklistItem(item="Add citation", category="References")],
        integrity_flags=["Unsupported-by-methods claim flagged."],
        agent_raw_outputs={"ScienceCommunicatorAgent": {"agent": "ScienceCommunicatorAgent"}},
    )
    report = ReviewReport(
        generated_at_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
        model_name="mock-model",
        executive_summary="Summary",
        paragraphs=[merged],
    )

    markdown = render_report(report)

    assert "# Critical Review — HKGAP Short Paper v1.1" in markdown
    assert "#### 🧭 Explainer-in-Residence" in markdown
    assert "Think of it as" in markdown
    assert "#### 🚨 Academic-integrity flags" in markdown
    assert "## Consolidated pre-submission checklist" in markdown
    assert "## Appendix A — Agent-level raw outputs" in markdown
