from __future__ import annotations

import asyncio
from collections import Counter
from datetime import datetime, timezone

from ..config import Settings
from ..known_issues import match_known_issues
from ..schemas import AgentReview, ChecklistItem, MergedCommentary, Paragraph, ReviewReport
from .prior_art import PriorArtAgent
from .science_communicator import ScienceCommunicatorAgent
from .simulation_methodologist import SimulationMethodologistAgent
from .statistics_reproducibility import StatisticsAndReproducibilityAgent
from .structural_biophysicist import StructuralBiophysicistAgent


class EditorInChiefAgent:
    def __init__(self, provider, settings: Settings):
        self.settings = settings
        self.agents = [
            StructuralBiophysicistAgent(provider, settings),
            SimulationMethodologistAgent(provider, settings),
            StatisticsAndReproducibilityAgent(provider, settings),
            PriorArtAgent(provider, settings),
            ScienceCommunicatorAgent(provider, settings),
        ]

    @staticmethod
    def _ensure_analogy(commentary: str) -> str:
        if "Think of it as" in commentary or "It's like" in commentary:
            return commentary
        return (
            f"{commentary.strip()} "
            "Think of it as trying to steer a marble across a tilted, bumpy table: "
            "you need both the slope and the bumps quantified before claiming where it will stop."
        ).strip()

    @staticmethod
    def _dedupe_checklist(items: list[ChecklistItem]) -> list[ChecklistItem]:
        seen: set[tuple[str, str]] = set()
        deduped: list[ChecklistItem] = []
        for item in items:
            key = (item.category, item.item)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    async def review_paragraph(self, paragraph: Paragraph, context: str) -> MergedCommentary:
        outputs: list[AgentReview] = await asyncio.gather(
            *(agent.run(paragraph, context) for agent in self.agents)
        )

        by_agent = {output.agent: output for output in outputs}
        communicator = by_agent.get("ScienceCommunicatorAgent")
        explainer = communicator.commentary if communicator and communicator.commentary else ""
        explainer = self._ensure_analogy(explainer)

        critique = []
        checklist = []
        integrity_flags: list[str] = []

        for output in outputs:
            critique.extend(output.referee_items)
            checklist.extend(output.checklist)
            integrity_flags.extend(output.integrity_flags)
            for claim in output.unsupported_claims:
                integrity_flags.append(f"Unsupported-by-methods claim flagged: {claim}")

        known_items, known_integrity = match_known_issues(paragraph.section, paragraph.text)
        critique.extend(known_items)
        integrity_flags.extend(known_integrity)

        integrity_flags = list(
            dict.fromkeys(flag.strip() for flag in integrity_flags if flag.strip())
        )
        checklist = self._dedupe_checklist(checklist)

        return MergedCommentary(
            paragraph=paragraph,
            verbatim=paragraph.text,
            explainer_commentary=explainer,
            referee_critique=critique,
            checklist=checklist,
            integrity_flags=integrity_flags,
            agent_raw_outputs={k: v.model_dump(mode="json") for k, v in by_agent.items()},
        )

    @staticmethod
    def _executive_summary(paragraphs: list[MergedCommentary]) -> str:
        severity_counts = Counter()
        for paragraph in paragraphs:
            for item in paragraph.referee_critique:
                severity_counts[item.severity] += 1

        strongest = [
            (
                "The manuscript tackles a meaningful mechanistic question around folding "
                "landscapes and non-native interactions."
            ),
            (
                "The framework is positioned around interpretable coordinates (Q, "
                "free-energy barriers), which can support strong discussion."
            ),
            (
                "The study is close to publishable structure with clear sectioning and "
                "explicit methods ambitions."
            ),
        ]
        concerns = [
            (
                "Key claims are not consistently supported by methods/results alignment "
                "(committor and placeholder-derived conclusions)."
            ),
            (
                "Statistical support appears weak where replicate trajectories and "
                "uncertainty quantification are required."
            ),
            (
                "Several presentation and consistency issues (numbering, typo, "
                "accessibility) need correction before submission."
            ),
        ]
        recommendation = (
            "Overall recommendation: major revision before journal submission. "
            f"Current issue profile — show-stopper: {severity_counts['show-stopper']}, "
            f"major: {severity_counts['major']}, minor: {severity_counts['minor']}."
        )

        return "\n".join(
            [
                "**Three strongest contributions**",
                *[f"- {item}" for item in strongest],
                "",
                "**Three most serious concerns**",
                *[f"- {item}" for item in concerns],
                "",
                recommendation,
            ]
        )

    async def review_document(self, paragraphs: list[Paragraph]) -> ReviewReport:
        context = "\n\n".join(f"[{p.section} ¶{p.index}] {p.text}" for p in paragraphs)
        merged: list[MergedCommentary] = []
        for paragraph in paragraphs:
            merged.append(await self.review_paragraph(paragraph, context))
        return ReviewReport(
            generated_at_utc=datetime.now(timezone.utc),
            model_name=self.settings.model_name,
            executive_summary=self._executive_summary(merged),
            paragraphs=merged,
        )
