"""The agent loop: plan → call tools → observe → repeat → emit a structured briefing.

A real tool-use loop that WE orchestrate (not delegated to a black box): the model
picks tools, we execute them, feed results back, and record every call in a trace.
Guardrails: a hard step budget (from settings) so it can't loop forever or overspend,
and a forced final `emit_briefing` if the budget runs out. The final answer is a
validated `Briefing`, so it's structured data with sources — never free text.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pydantic import ValidationError

from .config import Settings
from .models import Briefing, ResearchResult, Step
from .prompts import AGENT_SYSTEM
from .tools import Tool

if TYPE_CHECKING:
    from anthropic import Anthropic

_FINISH_TOOL = "emit_briefing"


class Agent:
    def __init__(self, client: "Anthropic", tools: list[Tool], settings: Settings) -> None:
        self._client = client
        self._tools = {t.name: t for t in tools}
        self._settings = settings

    def _specs(self) -> list[dict]:
        specs = [t.spec() for t in self._tools.values()]
        specs.append(
            {
                "name": _FINISH_TOOL,
                "description": "Emit the final structured briefing and finish the task.",
                "input_schema": Briefing.model_json_schema(),
            }
        )
        return specs

    def _create(self, messages: list[dict], specs: list[dict], *, force_finish: bool = False):
        kwargs: dict = dict(
            model=self._settings.model,
            max_tokens=self._settings.max_tokens,
            system=AGENT_SYSTEM,
            tools=specs,
            messages=messages,
        )
        if force_finish:
            kwargs["tool_choice"] = {"type": "tool", "name": _FINISH_TOOL}
        return self._client.messages.create(**kwargs)

    def run(self, task: str) -> ResearchResult:
        specs = self._specs()
        messages: list[dict] = [{"role": "user", "content": task}]
        trace: list[Step] = []
        n = 0

        for _ in range(self._settings.max_steps):
            resp = self._create(messages, specs)
            tool_uses = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]

            finish = next((b for b in tool_uses if b.name == _FINISH_TOOL), None)
            if finish is not None:
                return ResearchResult(
                    task=task, briefing=self._briefing(finish.input), trace=trace, steps_used=n
                )

            messages.append({"role": "assistant", "content": resp.content})
            if not tool_uses:
                messages.append(
                    {"role": "user", "content": "Continue: use a tool, or call emit_briefing to finish."}
                )
                continue

            results = []
            for tu in tool_uses:
                n += 1
                tool = self._tools.get(tu.name)
                output = tool.run(tu.input) if tool else f"Unknown tool: {tu.name}"
                trace.append(
                    Step(n=n, tool=tu.name, input=json.dumps(tu.input)[:200], output=output[:600])
                )
                results.append({"type": "tool_result", "tool_use_id": tu.id, "content": output})
            messages.append({"role": "user", "content": results})

        # Step budget exhausted — force a final briefing with what we have.
        messages.append(
            {"role": "user", "content": "Tool-call budget reached. Call emit_briefing now with what you have."}
        )
        resp = self._create(messages, specs, force_finish=True)
        finish = next(
            (b for b in resp.content if getattr(b, "type", None) == "tool_use" and b.name == _FINISH_TOOL),
            None,
        )
        data = finish.input if finish else {"company": "unknown", "summary": "Research incomplete."}
        return ResearchResult(task=task, briefing=self._briefing(data), trace=trace, steps_used=n)

    @staticmethod
    def _briefing(data: dict) -> Briefing:
        try:
            return Briefing.model_validate(data)
        except ValidationError:
            # A malformed final tool call shouldn't crash the run.
            return Briefing(
                company=str(data.get("company", "unknown")),
                summary=str(data.get("summary", "")),
                notes="The final briefing failed schema validation; showing partial data.",
            )
