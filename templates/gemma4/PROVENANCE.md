# Gemma 4 chat template provenance

| File | SHA-256 | Source | Fetch date |
|---|---|---|---|
| `upstream/26B-A4B-it.jinja` | `85a08664d16d8f3be4416c92427b3ac10df1024ac566cc0b4bc3bab409393f98` | `mlx-community/gemma-4-26b-a4b-it-8bit` (re-distribution of `google/gemma-4-26B-A4B-it`) | 2026-04-22 |
| `upstream/31B-it.jinja` | `85a08664d16d8f3be4416c92427b3ac10df1024ac566cc0b4bc3bab409393f98` | `unsloth/gemma-4-31b-it-MLX-8bit` (re-distribution of `google/gemma-4-31B-it`) | 2026-04-22 |
| `upstream/E2B-it.jinja` | `781d10940fbc44be40064b5d43a056fc486c84ceaa55538226368b57314132bf` | `unsloth/gemma-4-E2B-it-MLX-8bit` (re-distribution of `google/gemma-4-E2B-it`) | 2026-04-22 |
| `upstream/E4B-it.jinja` | `781d10940fbc44be40064b5d43a056fc486c84ceaa55538226368b57314132bf` | `unsloth/gemma-4-E4B-it-MLX-8bit` (re-distribution of `google/gemma-4-E4B-it`) | 2026-04-22 |

## Observations

- **Two distinct templates as of fetch date.** Big variants (26B-A4B, 31B)
  share `85a08664`. Small variants (E2B, E4B) share `781d10940`. The small
  template lacks the post-thinking-channel logic in the generation prompt
  (small Gemma 4 doesn't support thinking mode).
- All four files reflect Google's Apr 2026 official template update (HF
  commit `e51e7dc` in `google/gemma-4-31B-it`) — see catalog entry G3.
- Both templates contain the `<turn|>` close-marker suppression bug that G7
  fixes (lines ~332–336 in the big variant, ~332–336 in the small).
- Template authors: Google LLC. License: Gemma Terms of Use (use
  restrictions on the model apply; the template files themselves are
  permissively licensed for redistribution under those terms).
