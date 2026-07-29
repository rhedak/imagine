"""Google Gemini image generation, with reference images as context.

Env: GEMINI_API_KEY (or GOOGLE_API_KEY). Requires the google-genai package
(`pip install imagine[gemini]`).
"""

from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Any

from .errors import ImagineError
from .image import GeneratedImage
from .reference import Reference

DEFAULT_MODEL = "gemini-3.1-flash-image"

# gemini-2.5-flash-image ("Nano Banana") is the legacy model; gemini-3.1-flash-image
# ("Nano Banana 2") is the current versatile tier and supports the extra
# quality knobs below (image_size, thinking_level). gemini-3-pro-image is a
# pricier premium tier, usable by passing model= explicitly.
_GEMINI_3_PREFIX = "gemini-3"


class GeminiError(ImagineError):
    """Gemini API or client failure."""


def api_key_present() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GOOGLE_API_KEY", "").strip())


def _api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GOOGLE_API_KEY", "").strip()
    if not key:
        raise GeminiError("GEMINI_API_KEY (or GOOGLE_API_KEY) is not set.")
    return key


def _get_client() -> Any:
    key = _api_key()
    try:
        from google import genai
    except ImportError as exc:
        raise GeminiError("google-genai package not installed. Run: pip install imagine[gemini]") from exc
    return genai.Client(api_key=key)


def _guess_mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    if mime in ("image/png", "image/jpeg", "image/webp"):
        return mime
    return {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(
        path.suffix.lower().lstrip("."), "image/png"
    )


def generate(
    *,
    prompt: str,
    references: list[Reference] = (),
    model: str = DEFAULT_MODEL,
    n: int = 1,
    aspect_ratio: str = "1:1",
    image_size: str | None = "2K",
    thinking_level: str | None = "HIGH",
) -> list[GeneratedImage]:
    """Generate images, sending each reference as a (caption, image) pair.

    image_size ("1K"/"2K"/"4K") and thinking_level (more reasoning before
    generating, at the cost of latency) are gemini-3.x-only quality knobs;
    both are skipped automatically on the legacy gemini-2.5-flash-image,
    which doesn't support them.
    """
    if not prompt.strip():
        raise GeminiError("prompt must be non-empty")

    client = _get_client()
    is_gemini_3 = model.startswith(_GEMINI_3_PREFIX)

    try:
        from google.genai import types

        images: list[GeneratedImage] = []
        for _ in range(n):
            contents: list[Any] = []
            for ref in references:
                if not ref.path.is_file():
                    raise GeminiError(f"reference image not found: {ref.path}")
                if ref.caption:
                    contents.append(types.Part.from_text(text=ref.caption))
                contents.append(types.Part.from_bytes(data=ref.path.read_bytes(), mime_type=_guess_mime(ref.path)))
            contents.append(prompt)

            image_config_kwargs: dict[str, Any] = {"aspect_ratio": aspect_ratio}
            config_kwargs: dict[str, Any] = {"response_modalities": ["IMAGE"]}
            if is_gemini_3:
                if image_size:
                    image_config_kwargs["image_size"] = image_size
                if thinking_level:
                    config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=thinking_level)
            config_kwargs["image_config"] = types.ImageConfig(**image_config_kwargs)

            config = types.GenerateContentConfig(**config_kwargs)
            resp = client.models.generate_content(model=model, contents=contents, config=config)
            for part in resp.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    images.append(
                        GeneratedImage(
                            index=len(images),
                            image_bytes=part.inline_data.data,
                            mime_type=getattr(part.inline_data, "mime_type", "image/png"),
                        )
                    )
        if not images:
            raise GeminiError("Gemini returned no images. The prompt may have been rejected.")
        return images
    except GeminiError:
        raise
    except Exception as exc:
        msg = str(exc)
        if "API_KEY_INVALID" in msg or "api_key" in msg.lower():
            raise GeminiError(f"Invalid API key. Check GEMINI_API_KEY: {exc}") from exc
        raise GeminiError(f"Gemini API error: {exc}") from exc
