"""Agent scorecard: run the agent on a set of companies, then grade each briefing
with deterministic checks (source-grounding, budget, essentials) + an LLM judge.

    python evals/run_evals.py               # full (agent + judge)
    python evals/run_evals.py --no-judge    # deterministic only (still runs the agent)

Needs ANTHROPIC_API_KEY (+ web access for the tools). Non-zero exit if a gate check
fails. Reports → evals/reports/.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

from checks import run_all  # noqa: E402
from judge import BriefingJudge  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from research_agent.agent import Agent  # noqa: E402
from research_agent.client import LLMClient  # noqa: E402
from research_agent.config import Settings  # noqa: E402
from research_agent.prompts import build_task  # noqa: E402
from research_agent.search import DdgSearch  # noqa: E402
from research_agent.tools import FetchPageTool, WebSearchTool  # noqa: E402

console = Console()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-judge", action="store_true")
    args = parser.parse_args()

    from anthropic import Anthropic

    settings = Settings.from_env()
    anthropic = Anthropic(api_key=settings.anthropic_api_key)
    judge = None if args.no_judge else BriefingJudge(LLMClient(settings, anthropic))
    cases = json.loads((HERE / "dataset" / "companies.json").read_text())

    rows, gate_ok = [], True
    for case in cases:
        tools = [WebSearchTool(DdgSearch()), FetchPageTool()]
        agent = Agent(anthropic, tools, settings)
        with console.status(f"[bold]Researching {case['company']}…[/]"):
            result = agent.run(build_task(case["company"], case.get("role")))
        checks = run_all(result)
        gate = [c for c in checks if c.severity == "gate"]
        gate_pass = sum(c.passed for c in gate)
        gate_ok &= gate_pass == len(gate)
        grade = judge.grade(result) if judge else None
        rows.append((case["company"], result.steps_used, gate_pass, len(gate), checks, grade))

    table = Table(title="Agent scorecard", show_lines=True)
    for col in ("Company", "Tool calls", "Gate checks", "Judge/5"):
        table.add_column(col)
    for company, steps, gp, gt, _checks, grade in rows:
        table.add_row(company, str(steps), f"{gp}/{gt}", str(grade.mean) if grade else "—")
    console.print(table)

    for company, _s, _gp, _gt, checks, _g in rows:
        for c in checks:
            if not c.passed:
                mark = "[red]✗ FAIL" if c.severity == "gate" else "[yellow]⚠ advisory"
                console.print(f"  {mark}[/] {company} · {c.name}: {c.detail}")

    reports = HERE / "reports"
    reports.mkdir(exist_ok=True)
    out = reports / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    out.write_text(json.dumps(
        [{"company": c, "steps": s, "gate": f"{gp}/{gt}",
          "checks": {ck.name: {"passed": ck.passed, "detail": ck.detail} for ck in cks},
          "judge": (g.model_dump() if g else None)}
         for c, s, gp, gt, cks, g in rows], indent=2))
    console.print(f"[dim]report → {out.relative_to(HERE.parent)}[/]")
    return 0 if gate_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
