"""OpenAI (gpt-image-1) image generation client.

Env: OPENAI_API_KEY. Requires the openai package
(`pip install imagine[openai]`). Uses the images.edit endpoint when any
reference images are given, falling back to images.generate for a bare
text prompt.
"""

from __future__ import annotations

import base64
import os
from typing import Any

from .errors import ImagineError
from .image import GeneratedImage
from .reference import Reference

DEFAULT_MODEL = "gpt-image-1"

# gpt-image-1 only accepts a fixed set of output sizes.
_SIZE_BY_ASPECT = {
    "1:1": "1024x1024",
    "3:2": "1536x1024",
    "4:3": "1536x1024",
    "2:3": "1024x1536",
    "3:4": "1024x1536",
}


class OpenAIError(ImagineError):
    """OpenAI API or client failure."""


def api_key_present() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def _get_client() -> Any:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise OpenAIError("OPENAI_API_KEY is not set.")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise OpenAIError("openai package not installed. Run: pip install imagine[openai]") from exc
    return OpenAI(api_key=key)


def generate(
    *,
    prompt: str,
    references: list[Reference] = (),
    model: str = DEFAULT_MODEL,
    n: int = 1,
    aspect_ratio: str = "1:1",
    input_fidelity: str | None = "high",
    quality: str | None = "high",
) -> list[GeneratedImage]:
    """input_fidelity="high" (the default) tells gpt-image-1 to preserve the
    input images' distinctive features (style, character identity) more
    strongly; per OpenAI's own prompting guide, this is the documented knob
    for reference adherence on this model (ignored on gpt-image-2, which is
    always high fidelity, and not accepted by images.generate since that
    path has no input image at all). quality="high" trades cost/latency for
    the best output quality on both the edit and generate endpoints.
    """
    if not prompt.strip():
        raise OpenAIError("prompt must be non-empty")

    client = _get_client()
    size = _SIZE_BY_ASPECT.get(aspect_ratio, "auto")
    refs = list(references)

    try:
        if refs:
            files = [open(ref.path, "rb") for ref in refs]
            try:
                kwargs: dict[str, Any] = {}
                if input_fidelity and "gpt-image-2" not in model:
                    kwargs["input_fidelity"] = input_fidelity
                if quality:
                    kwargs["quality"] = quality
                resp = client.images.edit(model=model, image=files, prompt=prompt, n=n, size=size, **kwargs)
            finally:
                for f in files:
                    f.close()
        else:
            kwargs = {"quality": quality} if quality else {}
            resp = client.images.generate(model=model, prompt=prompt, n=n, size=size, **kwargs)
    except OpenAIError:
        raise
    except Exception as exc:
        raise OpenAIError(f"OpenAI API error: {exc}") from exc

    if not resp.data:
        raise OpenAIError("OpenAI returned no images.")
    return [
        GeneratedImage(index=i, image_bytes=base64.b64decode(item.b64_json), mime_type="image/png")
        for i, item in enumerate(resp.data)
    ]
