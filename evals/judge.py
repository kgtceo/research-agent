"""LLM-as-judge for briefing quality — the subjective layer atop the deterministic
source-grounding checks. Runs on the strongest model."""

from __future__ import annotations

from pydantic import BaseModel, Field

from research_agent.config import Settings
from research_agent.models import ResearchResult


class BriefingGrade(BaseModel):
    usefulness: int = Field(ge=1, le=5, description="Would this genuinely help in an interview?")
    specificity: int = Field(ge=1, le=5, description="Concrete and company-specific vs generic?")
    groundedness: int = Field(ge=1, le=5, description="Claims supported by the sources, nothing invented?")
    overall: int = Field(ge=1, le=5)
    rationale: str

    @property
    def mean(self) -> float:
        return round((self.usefulness + self.specificity + self.groundedness + self.overall) / 4, 2)


JUDGE_SYSTEM = (
    "You grade an interview-prep briefing produced by a research agent. Reward "
    "specificity and usefulness; penalise generic filler and any claim that looks "
    "invented rather than sourced. Groundedness is the most important axis. Score 1–5."
)


class BriefingJudge:
    def __init__(self, client) -> None:
        self._client = client

    def grade(self, result: ResearchResult) -> BriefingGrade:
        sources = "\n".join(result.briefing.sources) or "(none)"
        user = (
            f"TASK: {result.task}\n\n"
            f"BRIEFING:\n{result.briefing.model_dump_json(indent=2)}\n\n"
            f"SOURCES THE AGENT LISTED:\n{sources}"
        )
        return self._client.structured(
            schema=BriefingGrade,
            system=JUDGE_SYSTEM,
            user=user,
            model=Settings.from_env().judge_model,
        )
