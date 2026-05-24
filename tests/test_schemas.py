from hkgap_review.schemas import AgentReview, ChecklistItem, Paragraph, RefereeItem


def test_schema_validation_roundtrip() -> None:
    paragraph = Paragraph(section="ABSTRACT", index=1, text="Sample paragraph")
    review = AgentReview(
        agent="StructuralBiophysicistAgent",
        commentary=None,
        referee_items=[RefereeItem(category="Factual", comment="Looks plausible", severity="minor")],
        checklist=[ChecklistItem(item="Add uncertainty bars", category="Statistics")],
        integrity_flags=[],
        unsupported_claims=[],
    )

    assert paragraph.section == "ABSTRACT"
    assert review.referee_items[0].severity == "minor"
    assert review.checklist[0].category == "Statistics"
