# Gemma 4 patched templates

**Gemma 4 currently ships NO default `patched/` templates.** As of Google's
2026-07-09 template rewrite, every patch that was in the default stack
(G7, G9, G10) is fixed upstream, so `templates/gemma4/` contains
`upstream/` only and the family is listed in `CATALOG_ONLY_FAMILIES`
(`tests/conftest.py`) alongside qwen3.5.

Use Google's stock template unless you hit one of the two opt-in cases below.

## Retired — fixed upstream 2026-07-09

| Patch | What it fixed | How upstream fixed it |
|---|---|---|
| **G7** | Empty-content tool-call assistant turn dropped its `<turn\|>` close, causing an agentic loop | Close conditional gained `and not next_nt.found` |
| **G9** | Two consecutive assistant messages left an orphaned `<turn\|>` (closes > opens) | Upstream added the same forward-scan + a `continues_into_next` suppression branch this repo had derived independently |
| **G10** | `preserve_thinking` kwarg to retain historical tool-call reasoning | Upstream added a **native** `preserve_thinking` kwarg with the same default-OFF contract |

Their catalog entries are kept in `docs/PATCH-CATALOG.md` as historical
record, and `tests/test_render.py` keeps **inverted sentinels** — tests that
now assert upstream *stays* fixed, so a future upstream regression
re-surfaces the bug instead of silently returning.

## Opt-in patches (apply yourself; none are in a default stack)

| Patch | Apply when |
|---|---|
| `patches/gemma4/G1-portable-iterable-check.patch` | You run **minijinja** (LM Studio's MCP path), which has no `sequence` test → `Unknown test: sequence` and every tool call fails. Google's rewrite **grew** this surface from 3 sites to 4. Byte-identical under jinja2 for normal inputs; also fixes a latent dict-valued-`content` crash. |
| `patches/gemma4/G8-jsonschema-robustness.patch` | Your tools use `anyOf` / `oneOf` / `allOf` / `$ref` / `$defs` / `const`, or `enum` on a non-STRING type (i.e. most Pydantic-v2 / MCP tool schemas). Upstream silently **drops** all of these from the tool declaration. HF discussion #91 still unmerged. |

Both patches apply cleanly to all five sizes and **stack together** (apply G1
first, then G8). Each diffs against `templates/gemma4/upstream/<size>.jinja`;
the reference hunks are taken from `26B-A4B-it` and the affected lines are
identical across sizes.

```bash
# example: minijinja + Pydantic-generated tools
cp templates/gemma4/upstream/26B-A4B-it.jinja /tmp/gemma4.jinja
patch /tmp/gemma4.jinja < patches/gemma4/G1-portable-iterable-check.patch
patch /tmp/gemma4.jinja < patches/gemma4/G8-jsonschema-robustness.patch
```

## Tracked sizes

`12B-it`, `26B-A4B-it`, `31B-it` (big family, `ae53464b…`) and
`E2B-it`, `E4B-it` (small family, `0a2c8073…`). `12B-it` was added
2026-07-20. The `-assistant` model flavours ship no standalone
`chat_template.jinja` and are out of scope.

## Historical / configuration-side entries (not template patches)

- **G2** (channel/thought leakage) — superseded by Google's Apr-2026 update.
- **G3** (Apr-2026 official template realignment) — in `upstream/`.
- **G4** (ENABLE_THINKING/DISABLE_THINKING sentinel) — opt-in, catalog-only;
  apply if your client can't pass `chat_template_kwargs`.
- **G5** (LM Studio thinking-toggle) — `model.yaml` workaround.
- **G6** (tool-calling/system-prompt compliance) — runtime recommendations.

See `docs/PATCH-CATALOG.md` §§ G1–G10 and `templates/gemma4/PROVENANCE.md`.
