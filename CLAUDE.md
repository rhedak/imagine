# imagine: Project Context

## What this is

A small, provider-agnostic Python library for reference-guided AI image
generation across Google Gemini, xAI Grok Imagine, and OpenAI. See
`README.md` for the full pitch and usage examples.

## Package layout

- `imagine/reference.py`: `Reference` (path + caption) and the prompt-building
  convention (`build_reference_legend`, `combine_prompt`). This is the core
  design idea of the package: read its module docstring before touching it.
- `imagine/gemini.py`, `imagine/grok.py`, `imagine/openai.py`: one
  `generate()` per provider, plus `DEFAULT_MODEL` and `api_key_present()`.
  Each provider's quality-tuning defaults are documented in its own
  docstring and in the README's "Default quality settings" table; don't
  change a default without updating both.
- `imagine/image.py`: the shared `GeneratedImage` return type.
- `imagine/runner.py`: provider-name-driven dispatch (`generate`,
  `format_dry_run`, `format_web`, `default_model`, `api_key_present`) for
  callers that loop over multiple providers generically.
- `imagine/errors.py`: `ImagineError` base class; each provider subclasses it.

## Design principles

- **Reference captions are policy, not decoration.** Every reference image
  needs a short, factual caption describing its role. Only Gemini's
  multimodal API re-attaches a caption directly next to its image; Grok and
  OpenAI only see the final prompt string plus a bare file list, so the
  reference legend (`build_reference_legend`) is the only channel that
  reaches them. Never add a code path that skips building this legend for
  Grok/OpenAI "since it's simpler" — that reintroduces the exact bug this
  package exists to fix.
- **Never invented tuning.** Every default in a provider's `generate()`
  (`input_fidelity`, `quality`, `resolution`, `image_size`,
  `thinking_level`, model IDs) must trace back to that provider's own
  documented guidance, cited in the module docstring or README. If you
  can't find a documented source for a proposed default, don't add it as a
  default; expose it as a parameter instead.
- **Cost safety is the caller's job, this package's job is to make it
  easy.** `generate()` on each provider (and `runner.generate`) makes a
  real, billed API call with no confirmation step. `runner.format_dry_run`
  / `runner.format_web` exist so callers can build a "print what would
  happen" mode that costs nothing, ahead of any code path that calls
  `generate()`. When adding a new capability, add the dry-run/web-format
  equivalent in the same change, don't ship a paid-only path.
- **No project-specific policy in this library.** No CLI, no opinion about
  where prompts or reference images come from, no asset registry, no
  "chapter" or "asset" concept. Those belong in whatever project consumes
  this package.

## Testing

```
uv sync --extra all --group dev
uv run pytest -q
```

Tests must never make a real network call or require a real API key. Use
`monkeypatch.setenv`/`delenv` to exercise both "key present" and "key
missing" paths, and rely on the fact that every `generate()` validates
its arguments (empty prompt, missing key, missing reference file) before
it ever reaches the network.

## Adding a new provider

1. New module `imagine/<provider>.py` with `DEFAULT_MODEL`,
   `api_key_present()`, an error class subclassing `ImagineError`, and
   `generate(*, prompt, references, model, n, aspect_ratio, ...)`
   returning `list[GeneratedImage]`.
2. Register it in `runner._MODULES` and `runner._WEB_SITE`.
3. Add it to `imagine/__init__.py`'s imports/`__all__`.
4. Add tests mirroring the existing provider test files (key-presence,
   empty-prompt, missing-key paths; no live calls).
5. Document its quality-tuning defaults in both the module docstring and
   the README table, with a source.

## misc

- Do NOT commit unless asked.
- Even if you commit, do not write a "co-authored" trailer.
- No em dashes ("—", U+2014), double hyphens ("--"), or similar
  pause-substitutes in prose; hyphens are fine for compound words,
  prefixes, and ranges, but in running text prefer a period, comma, or
  restructured sentence instead.
- Keep this repo free of any reference to specific downstream
  projects/products that use this package (no project names, character
  names, asset schemas, or business logic) — this is a public repo. A
  gitignored `CLAUDE.local.md` may exist locally with that context; never
  copy anything from it into a file that gets committed.
- If you disagree (you don't think an instruction here adds value), push
  back once and ask for confirmation.
