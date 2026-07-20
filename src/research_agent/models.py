"""Typed contracts for the agent.

`Briefing` is the tool schema the agent calls to finish, so the final output is
validated data with sources — not free text. `Step` records every tool call so the
agent's work is transparent and auditable (and evaluable).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Step(BaseModel):
    """One tool call in the agent's trace."""

    n: int
    tool: str
    input: str = Field(description="Truncated tool input for display.")
    output: str = Field(description="Truncated tool output for display.")


class Development(BaseModel):
    fact: str
    source_url: str = Field(description="The URL this fact came from (must be one the agent visited).")


class Briefing(BaseModel):
    """The interview-prep briefing. Every factual section should trace to a source."""

    company: str
    summary: str = Field(description="2–3 sentences: what the company is.")
    what_they_do: list[str] = Field(default_factory=list, description="Products / how they make money.")
    recent_developments: list[Development] = Field(
        default_factory=list, description="Recent news/updates, each with a source URL."
    )
    culture_signals: list[str] = Field(default_factory=list)
    likely_interview_questions: list[str] = Field(default_factory=list)
    talking_points: list[str] = Field(
        default_factory=list, description="Specific, grounded points to raise in the interview."
    )
    sources: list[str] = Field(default_factory=list, description="All source URLs used.")
    notes: str = Field(
        default="",
        description="Caveats — e.g. what couldn't be verified, or where research was thin.",
    )


class ResearchResult(BaseModel):
    task: str
    briefing: Briefing
    trace: list[Step] = Field(default_factory=list)
    steps_used: int
