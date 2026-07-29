from pathlib import Path

import pytest

from imagine.grok import GrokError, api_key_present, generate
from imagine.reference import Reference


def test_api_key_present_false_when_unset(monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    assert api_key_present() is False


def test_api_key_present_true_when_set(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "x")
    assert api_key_present() is True


def test_generate_rejects_empty_prompt(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "x")
    with pytest.raises(GrokError, match="non-empty"):
        generate(prompt="   ", references=[Reference(Path("a.png"))])


def test_generate_requires_at_least_one_reference(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "x")
    with pytest.raises(GrokError, match="at least one reference"):
        generate(prompt="a scene", references=[])


def test_generate_without_key_raises(monkeypatch, tmp_path):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    img = tmp_path / "a.png"
    img.write_bytes(b"fake")
    with pytest.raises(GrokError, match="XAI_API_KEY"):
        generate(prompt="a scene", references=[Reference(img)])
