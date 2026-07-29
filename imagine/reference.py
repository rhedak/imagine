"""Reference images and the prompt legend that anchors them.

Multi-image, reference-guided generation only works if the model actually
knows which attached image is which. Google's own multi-reference prompting
guidance is to "reference each input by index and description (e.g. 'Image
1: product photo... Image 2: style reference...')"; xAI's documented
convention for its images/edits endpoint is that images are addressed by
the order they're sent, not a special token. `build_reference_legend`
covers both conventions in the same line (`Image 1 (IMAGE_0): ...`) so
whichever a given model expects, it's covered -- and critically, this text
goes into the prompt string itself, not a side channel, since not every
provider's API re-attaches a caption directly next to its image (only
Gemini's multimodal `contents` list does that; see `imagine.gemini`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Reference:
    """One reference image plus what it represents.

    caption should be a short, factual description of the image's role
    (e.g. "Style anchor." or "Character design sheet for X."), not an
    instruction -- instructions belong in the prompt's instruction text.
    """

    path: Path
    caption: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))


def build_reference_legend(references: list[Reference]) -> str:
    """One line per reference: 'Image N (IMAGE_n): caption'.

    Empty for an empty reference list, so callers can safely prepend this
    to a prompt unconditionally.
    """
    if not references:
        return ""
    lines = ["Reference images attached, in this exact order:"]
    for i, ref in enumerate(references):
        caption = ref.caption or f"Reference image {i + 1}."
        lines.append(f"  Image {i + 1} (IMAGE_{i}): {caption}")
    return "\n".join(lines)


def combine_prompt(
    instruction: str,
    references: list[Reference] = (),
    negative: str = "",
) -> str:
    """Build the final prompt text: reference legend + instruction + negative.

    references may be empty for a bare text-to-image call. negative, if
    given, is appended as an explicit "do not include" list -- most image
    APIs have no separate negative-prompt field, so this is folded into the
    same prompt string.
    """
    legend = build_reference_legend(list(references))
    body = f"{legend}\n\n{instruction}" if legend else instruction
    if negative:
        return f"{body}\n\nDo NOT include any of the following:\n{negative}"
    return body
