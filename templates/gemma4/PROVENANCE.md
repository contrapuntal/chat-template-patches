# Gemma 4 chat template provenance

| File | SHA-256 | Source | Fetch date |
|---|---|---|---|
| `upstream/12B-it.jinja` | `ae53464bf3be25802b3a5b37def7fd89667067d7577049b3b2d74c4d8de4c6d4` | `google/gemma-4-12B-it` (HF main, 2026-07-09 template) | 2026-07-20 |
| `upstream/26B-A4B-it.jinja` | `ae53464bf3be25802b3a5b37def7fd89667067d7577049b3b2d74c4d8de4c6d4` | `google/gemma-4-26B-A4B-it` (HF main, 2026-07-09 template) | 2026-07-20 |
| `upstream/31B-it.jinja` | `ae53464bf3be25802b3a5b37def7fd89667067d7577049b3b2d74c4d8de4c6d4` | `google/gemma-4-31B-it` (HF main, 2026-07-09 template) | 2026-07-20 |
| `upstream/E2B-it.jinja` | `0a2c8073c878ab1da004bee933a998606537bbb62016310352c7285c3f01c5b5` | `google/gemma-4-E2B-it` (HF main, 2026-07-09 template) | 2026-07-20 |
| `upstream/E4B-it.jinja` | `0a2c8073c878ab1da004bee933a998606537bbb62016310352c7285c3f01c5b5` | `google/gemma-4-E4B-it` (HF main, 2026-07-09 template) | 2026-07-20 |

## Observations

- **Two distinct templates as of fetch date.** Big variants (12B, 26B-A4B,
  31B) share `ae53464b…`. Small variants (E2B, E4B) share `0a2c8073…`. The
  small template omits the `<|channel>thought\n<channel|>` injection in the
  generation prompt (small Gemma 4 has no thinking mode) and one blank line
  after the turn opener; otherwise the two are identical.
- **`12B-it` added 2026-07-20.** Previously untracked; it carries the
  byte-identical big-family template.
- All five files reflect Google's **2026-07-09** rewrite, which the file
  itself documents in a new header comment:
  *"Template: Google Gemma 4 Canonical Chat Template / Author: Google Gemma
  Engineering Team / Published: 2026-07-09 / Context: Fixed tool-calling
  loops, turn closures, and thinking content-ordering."*
  It ships:
  - **Turn-close rewrite** — a forward-scan (`next_nt`) plus a
    `continues_into_next` suppression branch, and `and not next_nt.found`
    added to the close conditional. **This fixes G7 and G9.**
  - **Native `preserve_thinking` kwarg** with a default-OFF gate
    (`thinking_gate`). **This fixes G10.**
  - `format_argument` `is none` → `null` handling.
  - Empty-`messages` guard (`messages and messages[0][…]`) — crash fix.
  - Multimodal parts (`image` / `audio` / `video`) inside tool responses,
    and `image_url` / `input_audio` aliases in content parts.
  - Defensive `.get()` access on `content` / `tool_calls`.
  - O(1) `ns.prev_non_tool_role` tracking replacing the O(n) backward scan.
  - A new generation-prompt branch emitting `<|channel>thought` after a tool
    response when `enable_thinking` is set.
- **G7 / G9 / G10 retired** as a result — see `docs/PATCH-CATALOG.md`. Gemma 4
  now ships **no** `patched/` templates; the family is catalog-only with two
  opt-in patches (G1, G8).
- **G1 still required, and its surface grew** from 3 `is sequence` sites to 4
  (the new multimodal tool-response branch adds `tool_body is sequence`).
- **G8 still required** — upstream still handles only `enum` (and only for
  `type == 'STRING'`); `anyOf` / `oneOf` / `allOf` / `$ref` / `$defs` /
  `const` remain silently dropped. HF discussion #91 still unmerged. Upstream
  additionally turns unhandled keys into **pseudo-properties** via its
  `filter_keys` object fallback (`{"type":"object","anyOf":[…]}` renders as
  `properties:{anyOf:{…}}`, losing the real `anyOf`); G8 corrects that for the
  JSON Schema vocabulary.
- **G11 required for histories with consecutive assistant messages** — the
  2026-07-09 rewrite merges them into one balanced turn but emits no
  separator, so their bodies glue together.
- **Breaking change: string-form `tool_calls[].function.arguments` is now
  REJECTED** with a hard error — the shape the OpenAI spec mandates.
  Deserialize before calling the template; see `docs/PATCH-CATALOG.md`.
- Previous fetch (2026-05-06, SHAs `94899c0f` / `33204f1a`) was the PR #86
  (`145dc25`) baseline.
- Template authors: Google LLC. License: Gemma Terms of Use (use
  restrictions on the model apply; the template files themselves are
  permissively licensed for redistribution under those terms).
