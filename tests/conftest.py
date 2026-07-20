"""Offline fakes: a scripted Anthropic-shaped client so the agent loop runs with no
network or API key."""

from __future__ import annotations


class Block:
    """Namespace mimicking an Anthropic content block (tool_use or text)."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


def tool_use(name: str, tool_input: dict, id: str = "tool_1") -> Block:
    return Block(type="tool_use", name=name, input=tool_input, id=id)


def text(t: str) -> Block:
    return Block(type="text", text=t)


class _Resp:
    def __init__(self, content: list[Block]):
        self.content = content
        self.stop_reason = "tool_use"


class _Messages:
    def __init__(self, scripted: list[list[Block]]):
        self._scripted = list(scripted)
        self.calls: list[dict] = []

    def create(self, **kwargs) -> _Resp:
        self.calls.append(kwargs)
        content = self._scripted.pop(0) if self._scripted else [text("done")]
        return _Resp(content)


class FakeAnthropic:
    """Returns scripted content lists, one per `messages.create` call."""

    def __init__(self, scripted: list[list[Block]]):
        self.messages = _Messages(scripted)
