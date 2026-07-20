"""Web search providers behind an interface.

Default is DuckDuckGo (`ddgs`) — **no API key**, which keeps the demo zero-friction.
Swappable for Tavily (agent-optimised, more reliable, free tier) or a FakeSearch for
offline tests. The agent doesn't care which.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel


class SearchHit(BaseModel):
    title: str
    url: str
    snippet: str


class SearchProvider(Protocol):
    def search(self, query: str, *, max_results: int = 5) -> list[SearchHit]: ...


class DdgSearch:
    """DuckDuckGo via the `ddgs` package — no key required."""

    def search(self, query: str, *, max_results: int = 5) -> list[SearchHit]:
        from ddgs import DDGS

        hits: list[SearchHit] = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                hits.append(
                    SearchHit(
                        title=r.get("title", ""),
                        url=r.get("href", "") or r.get("url", ""),
                        snippet=r.get("body", ""),
                    )
                )
        return hits


class FakeSearch:
    """Deterministic canned results for tests (no network)."""

    def __init__(self, hits: list[SearchHit] | None = None) -> None:
        self._hits = hits or [
            SearchHit(
                title="Acme raises Series B",
                url="https://example.com/acme-series-b",
                snippet="Acme Cloud raised $40M to expand its platform.",
            )
        ]
        self.calls: list[str] = []

    def search(self, query: str, *, max_results: int = 5) -> list[SearchHit]:
        self.calls.append(query)
        return self._hits[:max_results]
