# Gemma 4 chat template provenance

| File | SHA-256 | Source | Fetch date |
|---|---|---|---|
| `upstream/26B-A4B-it.jinja` | `94899c0f917d93f6fe81c95744d1e8ddab2d21d39228d2e4aec1fb2a25bff413` | `google/gemma-4-26B-A4B-it` (HF main, post-PR #86) | 2026-05-06 |
| `upstream/31B-it.jinja` | `94899c0f917d93f6fe81c95744d1e8ddab2d21d39228d2e4aec1fb2a25bff413` | `google/gemma-4-31B-it` (HF main, commit `145dc25`) | 2026-05-06 |
| `upstream/E2B-it.jinja` | `33204f1acb5bd0002713e16a593847f24ceeafe711ed88bda2a352dc996a3373` | `google/gemma-4-E2B-it` (HF main, post-PR #86) | 2026-05-06 |
| `upstream/E4B-it.jinja` | `33204f1acb5bd0002713e16a593847f24ceeafe711ed88bda2a352dc996a3373` | `google/gemma-4-E4B-it` (HF main, post-PR #86) | 2026-05-06 |

## Observations

- **Two distinct templates as of fetch date.** Big variants (26B-A4B, 31B)
  share `94899c0f`. Small variants (E2B, E4B) share `33204f1a`. The small
  template lacks the post-thinking-channel injection in the generation
  prompt (small Gemma 4 doesn't support thinking mode).
- All four files reflect Google's **PR #86** (`fix(chat_template): update
  SI and tool call handling`) by Douglas Reid, merged as commit `145dc25`
  ~2026-04-28. PR #86 ships:
  - `format_parameters` macro `filter_keys=false` parameter and recursive
    `filter_keys=true` descent into mappings without explicit `properties`.
  - Multimodal-friendly first-system-message handling (string OR
    sequence-of-text-parts).
  - `captured_content` / `has_content` refactor of the assistant
    turn-close conditional (uses post-`strip_thinking` content length
    instead of raw `message.get('content')`).
- **G7 still required** on top of PR #86. PR #86's `has_content` rewrite
  doesn't fix the empty-content tool-call bug — `has_content` still
  evaluates falsy for the affected case, so the close-marker remains
  suppressed unless G7's `{%- else -%}` rewrite is applied. See
  catalog entry G7 for the regenerated patch line anchors.
- Previous fetch (2026-04-22, SHAs `85a08664` / `781d10940`) was the
  pre-PR #86 baseline. Bumped to `145dc25` on 2026-05-06.
- Template authors: Google LLC. License: Gemma Terms of Use (use
  restrictions on the model apply; the template files themselves are
  permissively licensed for redistribution under those terms).
