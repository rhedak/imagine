"""Common dispatch across providers: dry-run text, web-workflow text, or a
real generate() call.

This module has no opinion about CLI flags or safety policy -- it just
keeps the three code paths next to each other so callers wire them up the
same way every time. The convention this package is built around: a
dry-run or web-workflow render never touches the network and never needs
an API key, so it's safe to run automatically; only `generate()` spends
money, so callers should gate it behind an explicit, human-driven flag
(never invoke it from an automated/agentic path without that gate).
"""

from __future__ import annotations

from typing import Any

from . import gemini, grok
from . import openai as openai_client
from .image import GeneratedImage
from .reference import Reference

PROVIDERS = ("gemini", "grok", "openai")

_MODULES = {"gemini": gemini, "grok": grok, "openai": openai_client}

_WEB_SITE = {
    "gemini": "Gemini app / Google AI Studio (image generation)",
    "grok": "grok.com Imagine",
    "openai": "chatgpt.com (image generation) or platform.openai.com playground",
}


def api_key_present(provider: str) -> bool:
    return _MODULES[provider].api_key_present()


def default_model(provider: str) -> str:
    return _MODULES[provider].DEFAULT_MODEL


def generate(
    provider: str,
    *,
    prompt: str,
    references: list[Reference] = (),
    model: str | None = None,
    n: int = 1,
    aspect_ratio: str = "1:1",
    **provider_kwargs: Any,
) -> list[GeneratedImage]:
    """The real, billed call. Dispatches to the named provider's generate()."""
    mod = _MODULES[provider]
    return mod.generate(
        prompt=prompt,
        references=list(references),
        model=model or default_model(provider),
        n=n,
        aspect_ratio=aspect_ratio,
        **provider_kwargs,
    )


def format_dry_run(
    provider: str,
    *,
    prompt: str,
    references: list[Reference] = (),
    model: str | None = None,
    n: int = 1,
    aspect_ratio: str = "1:1",
    extra: dict[str, Any] | None = None,
) -> str:
    """Render exactly what a live call would send, for a --dry-run flag."""
    model = model or default_model(provider)
    extra_str = "  " + "  ".join(f"{k}: {v}" for k, v in extra.items()) if extra else ""
    lines = [
        "=" * 60,
        f"DRY RUN - {provider} (no API call made)",
        "=" * 60,
        f"model: {model}  n: {n}  aspect_ratio: {aspect_ratio}{extra_str}",
        f"key present: {api_key_present(provider)}",
        "",
        f"references ({len(references)}):",
    ]
    for ref in references:
        lines.append(f"  {ref.path}  -- {ref.caption}")
    lines += ["", "--- combined prompt sent to the API ---", prompt, "=" * 60]
    return "\n".join(lines)


def format_web(provider: str, *, prompt: str, references: list[Reference] = ()) -> str:
    """Render a manual copy-paste workflow for the provider's own web UI."""
    lines = [
        "=" * 60,
        f"WEB MODE - {provider} (manual workflow, no API call)",
        f"Use: {_WEB_SITE[provider]}",
        "=" * 60,
        "",
    ]
    if references:
        lines.append(f"ATTACH THESE {len(references)} IMAGES, IN THIS EXACT ORDER:")
        for i, ref in enumerate(references, start=1):
            lines.append(f"  {i}. {ref.path}  ({ref.caption})")
        lines.append("")
    lines += ["--- PROMPT TEXT (copy-paste as a single message) ---", "", prompt, "", "=" * 60]
    return "\n".join(lines)
