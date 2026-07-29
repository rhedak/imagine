# imagine

Thin, provider-agnostic Python clients for reference-guided AI image
generation across Google Gemini, xAI Grok Imagine, and OpenAI, behind one
shared `Reference` model and prompt-building convention.

## Why

Reference-guided generation (a style anchor image plus one or more subject
references, asked to produce a *new* scene rather than edit one of the
inputs) only works if the model actually knows which attached image is
which. The three providers don't attach captions to individual images the
same way:

- **Gemini** can be sent an interleaved `[caption, image, caption, image,
  ..., prompt]` content list, so each reference gets its own caption right
  next to it.
- **Grok** and **OpenAI** only see the final prompt string plus a bare,
  ordered list of image files -- no per-image caption channel.

So for those two, the *only* place a caption can reach the model at all is
inside the prompt text itself. This package's `build_reference_legend`
labels every reference two ways in the same line -- `Image 1 (IMAGE_0):
...` -- covering both a 1-based "Image N" convention (Google's own
documented multi-reference prompting guidance) and a 0-based `IMAGE_N`
token (xAI's documented convention for its edits endpoint) -- and that
legend is embedded directly in the prompt text sent to every provider, not
left to a side channel only one of them supports.

Each provider client also defaults to that provider's own documented
highest-fidelity settings for reference-guided work (see below), since the
API defaults are usually tuned for cheaper/faster output, not for
matching a reference closely.

## Install

```
pip install "imagine[all] @ git+https://github.com/rhedak/imagine"
```

Or install a subset: `imagine[gemini]`, `imagine[openai]`. The Grok Imagine
client uses stdlib HTTP only, no extra dependency.

## Usage

```python
from pathlib import Path
from imagine import Reference, combine_prompt
from imagine import runner

refs = [
    Reference(Path("style_anchor.png"), "Style anchor."),
    Reference(Path("subject.png"), "Subject reference."),
]
prompt = combine_prompt(
    "A quiet interior scene, matching the attached style and subject exactly.",
    refs,
    negative="text, watermark, photorealism",
)

# Safe, free, no API key needed -- see exactly what would be sent:
print(runner.format_dry_run("gemini", prompt=prompt, references=refs))

# The real, billed call:
images = runner.generate("gemini", prompt=prompt, references=refs, aspect_ratio="4:3")
images[0].save("out.png")
```

Or call a provider module directly for full control over its specific
knobs:

```python
from imagine import gemini
images = gemini.generate(
    prompt=prompt,
    references=refs,
    aspect_ratio="4:3",
    image_size="2K",       # gemini-3.x only
    thinking_level="HIGH", # gemini-3.x only
)
```

## Design

- **`imagine.Reference(path, caption)`** -- one reference image plus a
  short factual description of its role. Not an instruction; instructions
  belong in the prompt text.
- **`imagine.build_reference_legend(references)`** / **`combine_prompt(instruction,
  references, negative)`** -- the shared prompt-building convention
  described above.
- **`imagine.gemini` / `imagine.grok` / `imagine.openai`** -- one
  `generate(*, prompt, references, model, n, aspect_ratio, ...)` function
  per provider, each returning a list of `GeneratedImage` (bytes + mime
  type + optional `cost_usd` when the API reports it). Each also exposes
  `DEFAULT_MODEL` and `api_key_present()`.
- **`imagine.runner`** -- a provider-name-driven dispatch (`generate`,
  `format_dry_run`, `format_web`, `default_model`, `api_key_present`) for
  callers that want to loop over multiple providers generically, e.g. for
  side-by-side comparison, without a chain of if/elif.

This package intentionally does not include: a CLI, an asset registry, or
any opinion about where to load a prompt from or where to save output --
those are inherently specific to whatever you're building, and belong in
your own thin wrapper around this package.

## Default quality settings

Chosen from each provider's own documented reference-adherence guidance,
not guessed. These cost more per image than each API's own defaults, which
is usually the right tradeoff for a one-off "get this right" generation,
but override them if you're doing high-volume/draft work.

| Provider | Setting | Why |
|---|---|---|
| Gemini | `image_size="2K"`, `thinking_level="HIGH"` (gemini-3.x only) | More output resolution and reasoning before generating. |
| Grok | `resolution="2k"` | The API's own default is `"1k"`. |
| OpenAI | `input_fidelity="high"`, `quality="high"` | `input_fidelity` is OpenAI's documented knob for preserving input images' distinctive features on `gpt-image-1`/`gpt-image-1.5` (ignored on `gpt-image-2`, which is always high-fidelity). |

## License

Apache-2.0
