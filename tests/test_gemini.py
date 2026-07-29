import os

import pytest

from imagine.gemini import GeminiError, api_key_present, generate


def test_api_key_present_false_when_unset(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert api_key_present() is False


def test_api_key_present_true_with_gemini_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    assert api_key_present() is True


def test_api_key_present_true_with_google_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    assert api_key_present() is True


def test_generate_rejects_empty_prompt(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    with pytest.raises(GeminiError, match="non-empty"):
        generate(prompt="   ")


def test_generate_without_key_raises_before_any_call(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(GeminiError, match="GEMINI_API_KEY"):
        generate(prompt="a scene")
