"""research-agent — a tool-using agent that researches a company for an interview."""

from .agent import Agent
from .models import Briefing, Development, ResearchResult, Step
from .search import DdgSearch, FakeSearch, SearchHit
from .tools import FetchPageTool, WebSearchTool, html_to_text

__all__ = [
    "Agent",
    "Briefing",
    "DdgSearch",
    "Development",
    "FakeSearch",
    "FetchPageTool",
    "ResearchResult",
    "SearchHit",
    "Step",
    "WebSearchTool",
    "html_to_text",
]
__version__ = "0.1.0"
