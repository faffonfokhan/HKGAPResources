from __future__ import annotations

import re
from dataclasses import dataclass

from .schemas import RefereeItem


@dataclass(frozen=True)
class KnownIssue:
    pattern_regex: str
    severity: str
    category: str
    comment: str
    integrity_flag: bool = False


KNOWN_ISSUES: list[KnownIssue] = [
    KnownIssue(
        pattern_regex=r"1\.2\s*k_?b?t|5\.2\s*k_?b?t",
        severity="show-stopper",
        category="Internal consistency",
        comment=(
            "Abstract reports barrier minimum near 1.2 k_BT while §4.1 reports approximately 5.2 k_BT; "
            "resolve this contradiction before submission."
        ),
        integrity_flag=True,
    ),
    KnownIssue(
        pattern_regex=r"committor|p_?b|0\.50|proposed protocol",
        severity="show-stopper",
        category="Academic integrity",
        comment=(
            "Committor ⟨p_B⟩≈0.50 is presented as a result in Abstract/Conclusions while §4.3 frames it as "
            "a proposed protocol; claims must match executed methods."
        ),
        integrity_flag=True,
    ),
    KnownIssue(
        pattern_regex=r"USER INPUT|re-running the full pipeline|0\.7\s*k_?b?t|f\s*=\s*0\.30|f\s*=\s*0\.65",
        severity="show-stopper",
        category="Result support",
        comment=(
            "Shuffled-MJ barrier values are marked as placeholder/user-input yet conclusions assert precise "
            "numeric outcomes; remove or recompute with full pipeline."
        ),
        integrity_flag=True,
    ),
    KnownIssue(
        pattern_regex=r"N_NONNATIVE|D3",
        severity="major",
        category="Presentation",
        comment="Methods still contains placeholder token [N_NONNATIVE — see D3]; replace with final value.",
    ),
    KnownIssue(
        pattern_regex=r"3,57|U\s*→\s*I",
        severity="major",
        category="Presentation",
        comment="Typo detected: U → I barrier should be 3.57 (decimal point), not 3,57.",
    ),
    KnownIssue(
        pattern_regex=r"\b4\b.*\b6\b|Conclusions",
        severity="major",
        category="Presentation",
        comment="Section numbering jumps from §4 to §6; add missing §5 or renumber sections consistently.",
    ),
    KnownIssue(
        pattern_regex=r"f_c\s*=\s*0\.60|fixed|predicted",
        severity="major",
        category="Statistical rigor",
        comment=(
            "Regression appears circular: f_c = 0.60 is fixed and then reported as predicted; refit with "
            "independent estimation and uncertainty."
        ),
    ),
    KnownIssue(
        pattern_regex=r"never been continuously mapped|for the first time|any protein",
        severity="major",
        category="Novelty claim",
        comment=(
            "Absolute novelty phrasing is over-strong; prior work (e.g., Karanicolas & Brooks 2003) already "
            "varied non-native strength in Gō-like frameworks."
        ),
    ),
    KnownIssue(
        pattern_regex=r"single\s*1\s*μ?s|single\s*1\s*us|no replicates|error bars",
        severity="show-stopper",
        category="Methodological rigor",
        comment=(
            "Only a single ~1 μs trajectory per f with no replicates/error bars is insufficient for robust barrier "
            "claims; add replicate simulations and uncertainty estimates."
        ),
    ),
    KnownIssue(
        pattern_regex=r"cmap\s*=\s*jet|jet",
        severity="minor",
        category="Presentation",
        comment="Using cmap=jet is not color-blind friendly; switch to a perceptually uniform palette.",
    ),
]


def match_known_issues(section: str, paragraph_text: str) -> tuple[list[RefereeItem], list[str]]:
    matched_items: list[RefereeItem] = []
    integrity_flags: list[str] = []
    haystack = f"{section}\n{paragraph_text}"
    for issue in KNOWN_ISSUES:
        if re.search(issue.pattern_regex, haystack, flags=re.IGNORECASE | re.DOTALL):
            matched_items.append(
                RefereeItem(category=issue.category, comment=issue.comment, severity=issue.severity)  # type: ignore[arg-type]
            )
            if issue.integrity_flag:
                integrity_flags.append(issue.comment)
    return matched_items, integrity_flags
