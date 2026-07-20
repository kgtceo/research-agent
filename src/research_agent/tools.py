"""Agent tools: web_search and fetch_page.

Each tool exposes a JSON-schema `spec` for the Anthropic tools API and a `run` that
executes it and returns a string the model reads back. Tools own their guardrails —
fetch_page only allows http(s), times out, caps response size, and strips HTML — so
the agent can't be steered into fetching `file://` or a 200 MB binary.
"""

from __future__ import annotations

import re
from typing import Protocol

from pydantic import BaseModel

from .search import SearchProvider

_SCRIPT_STYLE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.I | re.S)
_TAGS = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t\r\f\v]+")
_NL = re.compile(r"\n\s*\n\s*")


def html_to_text(html: str) -> str:
    """Cheap, dependency-free HTML → readable text (enough to feed an LLM)."""
    text = _SCRIPT_STYLE.sub(" ", html)
    text = _TAGS.sub(" ", text)
    text = (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&#39;", "'")
        .replace("&quot;", '"')
    )
    text = _WS.sub(" ", text)
    return _NL.sub("\n\n", text).strip()


class Tool(Protocol):
    name: str
    description: str

    def spec(self) -> dict: ...
    def run(self, tool_input: dict) -> str: ...


class _WebSearchInput(BaseModel):
    query: str


class WebSearchTool:
    name = "web_search"
    description = (
        "Search the web for a query. Returns a ranked list of results with title, "
        "URL, and a snippet. Use this to find pages worth fetching."
    )

    def __init__(self, provider: SearchProvider, *, max_results: int = 5) -> None:
        self._provider = provider
        self._max_results = max_results

    def spec(self) -> dict:
        return {"name": self.name, "description": self.description,
                "input_schema": _WebSearchInput.model_json_schema()}

    def run(self, tool_input: dict) -> str:
        query = _WebSearchInput.model_validate(tool_input).query
        hits = self._provider.search(query, max_results=self._max_results)
        if not hits:
            return "No results."
        return "\n\n".join(f"{h.title}\n{h.url}\n{h.snippet}" for h in hits)


class _FetchPageInput(BaseModel):
    url: str


class FetchPageTool:
    name = "fetch_page"
    description = (
        "Fetch a web page by URL and return its readable text (truncated). Only "
        "http/https URLs are allowed. Use after web_search to read a promising result."
    )

    def __init__(self, *, timeout: float = 10.0, max_bytes: int = 400_000,
                 max_chars: int = 6_000) -> None:
        self._timeout = timeout
        self._max_bytes = max_bytes
        self._max_chars = max_chars

    def spec(self) -> dict:
        return {"name": self.name, "description": self.description,
                "input_schema": _FetchPageInput.model_json_schema()}

    def run(self, tool_input: dict) -> str:
        url = _FetchPageInput.model_validate(tool_input).url.strip()
        if not url.lower().startswith(("http://", "https://")):
            return f"Refused: only http/https URLs are allowed (got {url!r})."
        try:
            import httpx

            with httpx.Client(timeout=self._timeout, follow_redirects=True) as c:
                resp = c.get(url, headers={"User-Agent": "research-agent/0.1"})
            resp.raise_for_status()
            body = resp.content[: self._max_bytes].decode(resp.encoding or "utf-8", "replace")
            text = html_to_text(body)
            return text[: self._max_chars] + ("…" if len(text) > self._max_chars else "")
        except Exception as exc:  # network/HTTP errors are reported to the model, not raised
            return f"Failed to fetch {url}: {exc}"
