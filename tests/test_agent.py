"""The agent loop: executes tools, records a trace, finishes with a Briefing, and
respects the step-budget guardrail. All offline via a scripted fake client."""

from __future__ import annotations

from conftest import FakeAnthropic, tool_use

from research_agent.agent import Agent
from research_agent.config import Settings
from research_agent.search import FakeSearch
from research_agent.tools import FetchPageTool, WebSearchTool


def _tools():
    return [WebSearchTool(FakeSearch()), FetchPageTool()]


def _settings(max_steps=4):
    return Settings(anthropic_api_key="test", max_steps=max_steps)


_BRIEFING = {
    "company": "Acme",
    "summary": "Acme Cloud is a SaaS platform.",
    "recent_developments": [
        {"fact": "Raised $40M Series B", "source_url": "https://example.com/acme-series-b"}
    ],
    "likely_interview_questions": ["Why Acme?"],
    "sources": ["https://example.com/acme-series-b"],
}


def test_agent_searches_then_emits_briefing():
    client = FakeAnthropic([
        [tool_use("web_search", {"query": "Acme Cloud"})],
        [tool_use("emit_briefing", _BRIEFING)],
    ])
    result = Agent(client, _tools(), _settings()).run("Research Acme")

    assert result.briefing.company == "Acme"
    assert result.steps_used == 1  # one tool call before finishing
    assert [s.tool for s in result.trace] == ["web_search"]


def test_agent_forces_finish_at_step_budget():
    # Never voluntarily finishes; keeps searching. Budget=2 → 2 searches, then the
    # forced final call returns the briefing.
    client = FakeAnthropic([
        [tool_use("web_search", {"query": "a"})],
        [tool_use("web_search", {"query": "b"})],
        [tool_use("emit_briefing", _BRIEFING)],  # served on the forced final create()
    ])
    result = Agent(client, _tools(), _settings(max_steps=2)).run("Research Acme")

    assert result.steps_used == 2  # capped by the budget
    assert result.briefing.company == "Acme"


def test_agent_handles_malformed_final_briefing():
    client = FakeAnthropic([[tool_use("emit_briefing", {"summary": "no company field"})]])
    # 'company' is required; the agent must not crash — it returns a partial briefing.
    result = Agent(client, _tools(), _settings()).run("Research Acme")
    assert result.briefing.company == "unknown"
    assert "validation" in result.briefing.notes.lower()
