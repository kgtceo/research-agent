"""Tool guardrails + the deterministic source-grounding check (offline)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))

from checks import check_sources_grounded  # noqa: E402

from research_agent.models import Briefing, Development, ResearchResult, Step  # noqa: E402
from research_agent.search import FakeSearch  # noqa: E402
from research_agent.tools import FetchPageTool, WebSearchTool, html_to_text  # noqa: E402


# --- tool guardrails --------------------------------------------------------
def test_fetch_refuses_non_http():
    out = FetchPageTool().run({"url": "file:///etc/passwd"})
    assert out.startswith("Refused")  # rejected before any network call


def test_html_to_text_strips_markup_and_scripts():
    html = "<html><script>bad()</script><h1>Hi</h1><p>Body &amp; more</p></html>"
    text = html_to_text(html)
    assert "bad()" not in text and "<" not in text
    assert "Hi" in text and "Body & more" in text


def test_web_search_formats_hits():
    out = WebSearchTool(FakeSearch()).run({"query": "acme"})
    assert "example.com" in out and "Acme" in out


# --- source-grounding check -------------------------------------------------
def _result(dev_url: str, trace_url: str) -> ResearchResult:
    return ResearchResult(
        task="t",
        briefing=Briefing(
            company="Acme", summary="s",
            recent_developments=[Development(fact="raised money", source_url=dev_url)],
        ),
        trace=[Step(n=1, tool="web_search", input="{}", output=f"result {trace_url}")],
        steps_used=1,
    )


def test_grounded_source_passes():
    r = _result("https://example.com/a", "https://example.com/a")
    assert check_sources_grounded(r).passed is True


def test_fabricated_source_is_caught():
    r = _result("https://made-up.example/x", "https://example.com/a")
    res = check_sources_grounded(r)
    assert res.passed is False and "never visited" in res.detail
