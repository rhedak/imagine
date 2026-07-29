from pathlib import Path

from imagine.reference import Reference
from imagine.runner import PROVIDERS, api_key_present, default_model, format_dry_run, format_web


def test_providers_tuple():
    assert set(PROVIDERS) == {"gemini", "grok", "openai"}


def test_default_model_dispatch():
    assert default_model("gemini") == "gemini-3.1-flash-image"
    assert default_model("grok") == "grok-imagine-image-quality"
    assert default_model("openai") == "gpt-image-1"


def test_api_key_present_dispatch(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "x")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert api_key_present("grok") is True
    assert api_key_present("gemini") is False


def test_format_dry_run_includes_model_and_references():
    refs = [Reference(Path("a.png"), "Style anchor.")]
    out = format_dry_run("openai", prompt="a scene", references=refs, extra={"quality": "high"})
    assert "DRY RUN - openai" in out
    assert "gpt-image-1" in out
    assert "quality: high" in out
    assert "a.png" in out
    assert "a scene" in out


def test_format_web_lists_attach_order():
    refs = [Reference(Path("a.png"), "cap a"), Reference(Path("b.png"), "cap b")]
    out = format_web("grok", prompt="a scene", references=refs)
    assert "WEB MODE - grok" in out
    assert "grok.com Imagine" in out
    assert "1. a.png  (cap a)" in out
    assert "2. b.png  (cap b)" in out


def test_format_web_no_references():
    out = format_web("gemini", prompt="a scene")
    assert "ATTACH" not in out
    assert "a scene" in out
