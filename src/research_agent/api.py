"""FastAPI service for the research agent.

    uvicorn research_agent.api:app --reload   # docs at /docs
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .agent import Agent
from .config import Settings
from .models import ResearchResult
from .prompts import build_task
from .search import DdgSearch
from .tools import FetchPageTool, WebSearchTool

app = FastAPI(
    title="research-agent",
    version="0.1.0",
    description="A tool-using agent that researches a company for an interview.",
)

_origins = os.getenv("AGENT_CORS_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()],
    # Any Vercel deployment of this project (prod + preview URLs) and localhost dev.
    allow_origin_regex=r"https://research-agent[a-z0-9-]*\.vercel\.app|http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)


class BriefRequest(BaseModel):
    company: str = Field(min_length=2)
    role: str | None = None


@app.get("/health")
def health() -> dict:
    return {"ok": True, "configured": bool(os.getenv("ANTHROPIC_API_KEY"))}


@app.post("/api/brief", response_model=ResearchResult)
def brief(req: BriefRequest) -> ResearchResult:
    from anthropic import Anthropic

    try:
        settings = Settings.from_env()
        tools = [WebSearchTool(DdgSearch()), FetchPageTool()]
        agent = Agent(Anthropic(api_key=settings.anthropic_api_key), tools, settings)
        return agent.run(build_task(req.company, req.role))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
