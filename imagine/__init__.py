"""Thin, provider-agnostic clients for reference-guided AI image generation.

Supports Google Gemini, xAI Grok Imagine, and OpenAI behind one shared
Reference/prompt model and a common dry-run/web/live dispatch pattern
(see `imagine.runner`). Each provider module (`imagine.gemini`,
`imagine.grok`, `imagine.openai`) can be used directly, or through
`imagine.runner` for the common "print what would be sent / print a
manual web-UI workflow / actually call the API" flow.
"""

from . import gemini, grok, openai, runner
from .errors import ImagineError
from .image import GeneratedImage
from .reference import Reference, build_reference_legend, combine_prompt

__all__ = [
    "GeneratedImage",
    "ImagineError",
    "Reference",
    "build_reference_legend",
    "combine_prompt",
    "gemini",
    "grok",
    "openai",
    "runner",
]
