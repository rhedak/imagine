import pytest

from imagine.openai import OpenAIError, api_key_present, generate


def test_api_key_present_false_when_unset(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert api_key_present() is False


def test_api_key_present_true_when_set(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    assert api_key_present() is True


def test_generate_rejects_empty_prompt(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    with pytest.raises(OpenAIError, match="non-empty"):
        generate(prompt="   ")


def test_generate_without_key_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(OpenAIError, match="OPENAI_API_KEY"):
        generate(prompt="a scene")
