from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from app.services import llm


class Pong(BaseModel):
    message: str


class FakeCompletions:
    def __init__(self, replies: list[str]):
        self.replies = list(replies)
        self.calls = 0

    async def create(self, **kwargs):
        self.calls += 1
        content = self.replies.pop(0)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def install_fake(monkeypatch, replies):
    fake = FakeCompletions(replies)
    client = SimpleNamespace(chat=SimpleNamespace(completions=fake))
    monkeypatch.setattr(llm, "get_client", lambda: client)
    return fake


async def test_valid_output_first_try(monkeypatch):
    fake = install_fake(monkeypatch, ['{"message": "hi"}'])
    result = await llm.generate_structured("sys", "user", Pong)
    assert result.message == "hi"
    assert fake.calls == 1


async def test_retries_after_invalid_json(monkeypatch):
    fake = install_fake(monkeypatch, ["not json at all", '{"message": "fixed"}'])
    result = await llm.generate_structured("sys", "user", Pong)
    assert result.message == "fixed"
    assert fake.calls == 2


async def test_gives_up_after_retries(monkeypatch):
    install_fake(monkeypatch, ["bad", "still bad"])
    with pytest.raises(llm.LLMError):
        await llm.generate_structured("sys", "user", Pong)