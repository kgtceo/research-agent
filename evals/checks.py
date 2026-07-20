"""Deterministic agent evals — no model calls.

The headline check is source-grounding: every cited source_url must be a URL the
agent ACTUALLY encountered in its trace (searched or fetched). An agent that cites a
URL it never visited is fabricating provenance — caught here without an LLM, the same
anti-fabrication stance as the rest of the portfolio. Plus guardrail + completeness
checks (stayed within the step budget; briefing has the essential sections).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from research_agent.config import Settings
from research_agent.models import ResearchResult

_URL = re.compile(r"https?://[^\s\"'<>)\]]+")


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str
    severity: str = "gate"


def _trace_urls(result: ResearchResult) -> set[str]:
    """Every URL the agent saw — from tool inputs (fetch) and outputs (search)."""
    urls: set[str] = set()
    for s in result.trace:
        urls.update(_URL.findall(s.input))
        urls.update(_URL.findall(s.output))
    return {u.rstrip("/.,") for u in urls}


def check_sources_grounded(result: ResearchResult) -> CheckResult:
    seen = _trace_urls(result)
    fabricated = [
        d.source_url
        for d in result.briefing.recent_developments
        if not any(d.source_url.rstrip("/.,").startswith(u) or u.startswith(d.source_url.rstrip("/.,"))
                   for u in seen)
    ]
    return CheckResult(
        "sources_grounded",
        not fabricated,
        "ok" if not fabricated else f"cited URLs the agent never visited: {fabricated}",
    )


def check_within_step_budget(result: ResearchResult) -> CheckResult:
    cap = Settings.from_env().max_steps if _has_key() else 8
    ok = result.steps_used <= cap * 2  # each turn may batch tools; allow headroom
    return CheckResult("within_step_budget", ok, f"{result.steps_used} tool calls (cap≈{cap})")


def check_has_essentials(result: ResearchResult) -> CheckResult:
    b = result.briefing
    ok = bool(b.summary.strip()) and (b.what_they_do or b.likely_interview_questions)
    return CheckResult(
        "has_essentials",
        ok,
        "ok" if ok else "missing summary and/or what_they_do / interview questions",
    )


def check_used_tools(result: ResearchResult) -> CheckResult:
    """A research agent that produced a briefing without any research is a red flag."""
    ok = result.steps_used > 0
    return CheckResult(
        "used_tools", ok, f"{result.steps_used} tool calls", severity="advisory"
    )


def _has_key() -> bool:
    import os

    return bool(os.getenv("ANTHROPIC_API_KEY"))


ALL_CHECKS = [
    check_sources_grounded,
    check_within_step_budget,
    check_has_essentials,
    check_used_tools,
]


def run_all(result: ResearchResult) -> list[CheckResult]:
    return [c(result) for c in ALL_CHECKS]
