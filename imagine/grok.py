"""xAI Grok Imagine image client (stdlib HTTP only, no extra dependency).

Env: XAI_API_KEY. Uses POST /v1/images/edits, which accepts 1-3 reference
images. xAI's documented convention is order-based ("images are specified
in the order they are sent in the request"), not a special per-image
token, so describe each image's role by position in the prompt text itself
(see imagine.reference.build_reference_legend).
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import urllib.error
import urllib.request
from pathlib import Path

from .errors import ImagineError
from .image import GeneratedImage
from .reference import Reference

API_BASE = "https://api.x.ai/v1"
EDIT_PATH = "/images/edits"
MAX_IMAGES = 3
DEFAULT_MODEL = "grok-imagine-image-quality"

# 10_000_000_000 ticks == $1, per xAI's usage.cost_in_usd_ticks field.
_TICKS_PER_USD = 10_000_000_000


class GrokError(ImagineError):
    """xAI API or client failure."""


def api_key_present() -> bool:
    return bool(os.environ.get("XAI_API_KEY", "").strip())


def _api_key() -> str:
    key = os.environ.get("XAI_API_KEY", "").strip()
    if not key:
        raise GrokError("XAI_API_KEY is not set.")
    return key


def _file_to_data_uri(path: Path) -> str:
    if not path.is_file():
        raise GrokError(f"reference image not found: {path}")
    data = path.read_bytes()
    if len(data) > 20 * 1024 * 1024:
        raise GrokError(f"image exceeds 20MiB limit: {path}")
    mime, _ = mimetypes.guess_type(str(path))
    if mime not in ("image/png", "image/jpeg", "image/webp"):
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(
            path.suffix.lower().lstrip("."), "image/png"
        )
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def _http_get_bytes(url: str, timeout: float = 120.0) -> bytes:
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        raise GrokError(f"GET {url} failed HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise GrokError(f"GET {url} failed: {exc}") from exc


def _http_post_json(path: str, payload: dict, timeout: float = 300.0) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_BASE + path,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_api_key()}",
            "User-Agent": "imagine-python/0.1",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise GrokError(f"POST {path} failed HTTP {exc.code}: {err_body[:1000]}") from exc
    except urllib.error.URLError as exc:
        raise GrokError(f"POST {path} failed: {exc}") from exc
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise GrokError(f"invalid JSON from {path}: {raw[:500]!r}") from exc


def generate(
    *,
    prompt: str,
    references: list[Reference] = (),
    model: str = DEFAULT_MODEL,
    n: int = 1,
    aspect_ratio: str | None = "auto",
    resolution: str | None = "2k",
) -> list[GeneratedImage]:
    """Call /v1/images/edits with up to MAX_IMAGES reference images.

    resolution defaults to "2k" (vs. the API's own "1k" default) for the
    highest quality this model offers. At least one reference image is
    required -- xAI's edits endpoint has no bare text-to-image mode; use
    /v1/images/generations (not wrapped here) for that.
    """
    if not prompt.strip():
        raise GrokError("prompt must be non-empty")
    refs = list(references)
    if not refs:
        raise GrokError("at least one reference image is required (xAI's edits endpoint has no text-only mode)")
    used = refs[:MAX_IMAGES]

    images_payload = [{"url": _file_to_data_uri(r.path)} for r in used]
    payload: dict = {"model": model, "prompt": prompt, "n": n, "response_format": "b64_json"}
    if len(images_payload) == 1:
        payload["image"] = images_payload[0]
    else:
        payload["images"] = images_payload
    if aspect_ratio:
        payload["aspect_ratio"] = aspect_ratio
    if resolution:
        payload["resolution"] = resolution

    raw = _http_post_json(EDIT_PATH, payload)
    data = raw.get("data")
    if not isinstance(data, list) or not data:
        raise GrokError(f"edit response missing data[]: {raw!r}"[:800])

    usage = raw.get("usage") if isinstance(raw.get("usage"), dict) else {}
    ticks = usage.get("cost_in_usd_ticks")
    cost_usd = ticks / _TICKS_PER_USD if isinstance(ticks, int) else None

    images: list[GeneratedImage] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise GrokError(f"edit data[{i}] is not an object")
        b64 = item.get("b64_json")
        url = item.get("url")
        if b64:
            image_bytes = base64.b64decode(b64)
        elif url:
            image_bytes = _http_get_bytes(url)
        else:
            raise GrokError(f"edit result {i} has neither b64_json nor url")
        images.append(
            GeneratedImage(
                index=i,
                image_bytes=image_bytes,
                mime_type=item.get("mime_type") or "image/png",
                cost_usd=cost_usd,
            )
        )
    return images
