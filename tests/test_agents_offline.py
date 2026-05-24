import asyncio

from hkgap_review.agents.base import MockLLMProvider
from hkgap_review.agents.editor_in_chief import EditorInChiefAgent
from hkgap_review.config import Settings
from hkgap_review.known_issues import KNOWN_ISSUES
from hkgap_review.renderer import render_report
from hkgap_review.schemas import Paragraph


def test_editor_in_chief_offline_known_issues_surface() -> None:
    canned = {
        "StructuralBiophysicistAgent": {
            "agent": "StructuralBiophysicistAgent",
            "commentary": None,
            "referee_items": [{"category": "Factual", "comment": "Check units", "severity": "major"}],
            "checklist": [{"item": "Verify unit conversions", "category": "Methods"}],
            "integrity_flags": [],
            "unsupported_claims": [],
        },
        "SimulationMethodologistAgent": {
            "agent": "SimulationMethodologistAgent",
            "commentary": None,
            "referee_items": [],
            "checklist": [{"item": "Report replicate count", "category": "Methods"}],
            "integrity_flags": [],
            "unsupported_claims": [],
        },
        "StatisticsAndReproducibilityAgent": {
            "agent": "StatisticsAndReproducibilityAgent",
            "commentary": None,
            "referee_items": [],
            "checklist": [{"item": "Add error bars", "category": "Statistics"}],
            "integrity_flags": [],
            "unsupported_claims": ["committor claim lacks executed protocol evidence"],
        },
        "PriorArtAgent": {
            "agent": "PriorArtAgent",
            "commentary": None,
            "referee_items": [],
            "checklist": [{"item": "Tone down novelty wording", "category": "Prior art"}],
            "integrity_flags": [],
            "unsupported_claims": [],
        },
        "ScienceCommunicatorAgent": {
            "agent": "ScienceCommunicatorAgent",
            "commentary": "The paragraph is understandable. Think of it as traffic flowing through narrowing lanes.",
            "referee_items": [],
            "checklist": [],
            "integrity_flags": [],
            "unsupported_claims": [],
        },
    }

    settings = Settings.from_env(provider_override="mock", model_override="mock-model")
    editor = EditorInChiefAgent(MockLLMProvider(canned), settings)

    paragraph = Paragraph(
        section="ABSTRACT",
        index=1,
        text=(
            "Barrier is 1.2 kBT and 5.2 kBT; committor p_B 0.50 is result though protocol is proposed protocol; "
            "USER INPUT requires re-running the full pipeline; [N_NONNATIVE — see D3]; U → I barrier  0.49  3,57; "
            "section 4 then 6 Conclusions; f_c = 0.60 fixed and predicted; never been continuously mapped for any protein; "
            "single 1 μs trajectory no replicates no error bars; cmap=jet"
        ),
    )

    report = asyncio.run(editor.review_document([paragraph]))
    markdown = render_report(report)

    for issue in KNOWN_ISSUES:
        assert issue.comment in markdown

    assert "#### 🚨 Academic-integrity flags" in markdown
    assert "Think of it as" in markdown
