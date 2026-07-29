"""Common result type returned by every provider's generate()."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GeneratedImage:
    """One generated/edited image, provider-agnostic.

    cost_usd is populated when the provider's API reports per-call cost
    (currently only xAI does); it's None otherwise, not zero, so callers
    can distinguish "unknown" from "free."
    """

    index: int
    image_bytes: bytes
    mime_type: str = "image/png"
    cost_usd: float | None = None

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.image_bytes)
        return path
