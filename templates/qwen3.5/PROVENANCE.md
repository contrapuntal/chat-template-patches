# Qwen3.5 chat template provenance

All files fetched 2026-04-22 from the canonical Hugging Face model repos
(curl from `https://huggingface.co/Qwen/Qwen3.5-<size>/raw/main/chat_template.jinja`).

| File | SHA-256 | Source URL | Fetch date |
|---|---|---|---|
| `upstream/0.8B.jinja` | `273d8e0e683b885071fb17e08d71e5f2a5ddfb5309756181681de4f5a1822d80` | https://huggingface.co/Qwen/Qwen3.5-0.8B | 2026-04-22 |
| `upstream/2B.jinja` | `273d8e0e683b885071fb17e08d71e5f2a5ddfb5309756181681de4f5a1822d80` | https://huggingface.co/Qwen/Qwen3.5-2B | 2026-04-22 |
| `upstream/4B.jinja` | `a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715` | https://huggingface.co/Qwen/Qwen3.5-4B | 2026-04-22 |
| `upstream/9B.jinja` | `a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715` | https://huggingface.co/Qwen/Qwen3.5-9B | 2026-04-22 |
| `upstream/27B.jinja` | `a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715` | https://huggingface.co/Qwen/Qwen3.5-27B | 2026-04-22 |
| `upstream/35B-A3B.jinja` | `a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715` | https://huggingface.co/Qwen/Qwen3.5-35B-A3B | 2026-04-22 |
| `upstream/122B-A10B.jinja` | `a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715` | https://huggingface.co/Qwen/Qwen3.5-122B-A10B | 2026-04-22 |

## Observations

- **Two distinct templates as of fetch date.** Sizes 4B / 9B / 27B / 35B-A3B
  / 122B-A10B share `a4aee8`. Sizes 0.8B / 2B share `273d8e`. The small
  template differs in the `enable_thinking` polarity (defaults OFF on small;
  defaults ON on large) — this is what `P3` addresses for sizes that need it.
- The 4B and 9B templates moved from the `273d8e`-style polarity to the
  `a4aee8`-style polarity in an upstream Mar 2026 update. Verify before
  applying P3 to either size.
- Template authors: Alibaba Cloud / Qwen Team. License: Apache-2.0.
