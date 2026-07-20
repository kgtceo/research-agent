"""`research-agent` CLI.

    research-agent brief --company "Anthropic" --role "AI Engineer"
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel

from .agent import Agent
from .config import Settings
from .prompts import build_task
from .search import DdgSearch
from .tools import FetchPageTool, WebSearchTool

app = typer.Typer(add_completion=False, help="A tool-using agent that researches a company.")
console = Console()


@app.callback()
def _root() -> None:
    """A tool-using agent that researches a company for an interview."""


@app.command()
def brief(
    company: str = typer.Option(..., "--company", "-c", help="Company to research."),
    role: str = typer.Option(None, "--role", "-r", help="Role you're interviewing for."),
) -> None:
    from anthropic import Anthropic

    settings = Settings.from_env()
    tools = [WebSearchTool(DdgSearch()), FetchPageTool()]
    agent = Agent(Anthropic(api_key=settings.anthropic_api_key), tools, settings)

    with console.status(f"[bold]Researching {company}…[/] (search → fetch → synthesise)"):
        result = agent.run(build_task(company, role))

    b = result.briefing
    console.print(Panel(f"[bold]{b.company}[/]\n\n{b.summary}", title="Briefing", border_style="cyan"))
    if b.recent_developments:
        console.print("\n[bold]Recent developments:[/]")
        for d in b.recent_developments:
            console.print(f"  • {d.fact}\n    [dim]{d.source_url}[/]")
    if b.likely_interview_questions:
        console.print("\n[bold]Likely interview questions:[/]")
        for q in b.likely_interview_questions:
            console.print(f"  • {q}")
    if b.talking_points:
        console.print("\n[bold]Talking points:[/]")
        for t in b.talking_points:
            console.print(f"  • {t}")
    if b.notes:
        console.print(Panel(b.notes, title="Notes / caveats", border_style="yellow"))

    console.print(
        f"\n[dim]{result.steps_used} tool calls: "
        + ", ".join(s.tool for s in result.trace)
        + "[/]"
    )


if __name__ == "__main__":
    app()
