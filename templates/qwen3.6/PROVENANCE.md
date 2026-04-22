# Qwen3.6 chat template provenance

| File | SHA-256 | Source | Fetch date |
|---|---|---|---|
| `upstream/35B-A3B.jinja` | `55d4931433fe502b794226ee7f4d206a6bdd436ac9f80eb7d8ebb4c639f9ea0c` | `unsloth/Qwen3.6-35B-A3B-MLX-8bit` (re-distribution of `Qwen/Qwen3.6-35B-A3B`) | 2026-04-22 |

## Observations

- Only one Qwen3.6 size has been released as of the fetch date.
- Template introduces the `preserve_thinking` chat-template kwarg, gated as
  `(preserve_thinking is defined and preserve_thinking is true)`. Default
  behaviour (kwarg undefined) reproduces the cache-thrashing path that R1
  fixes for Qwen3.5. See patch `Q3.6-1` in `docs/PATCH-CATALOG.md`.
- Template authors: Alibaba Cloud / Qwen Team. License: Apache-2.0.

## Source choice: unsloth's redistribution vs canonical Qwen

This repo tracks the **unsloth redistribution** rather than canonical
`Qwen/Qwen3.6-35B-A3B`. As of 2026-04-22 the two diverge: unsloth's quant
ships several patches on top of canonical (developer-role fallback at the
bottom of the message loop, `is mapping` tool-argument type guard, and an
in-template `merged_system` helper). Canonical Qwen still raises
`'No user query found in messages.'` and `'Unexpected message role.'` —
so a Q3.6-1 patch generated against the canonical upstream would be
intermixed with what are effectively the upstream-Qwen-equivalent of our
P1, P2, and P10 patches.

Tracking the unsloth redistribution keeps `Q3.6-1` a clean single-line
diff, matches what's actually on disk for users running the dominant MLX
or GGUF quants (unsloth, mlx-community), and avoids re-deriving the
unsloth-side fixes here. If you need to apply Q3.6-1 against canonical
`Qwen/Qwen3.6-35B-A3B`, the line anchor is the same; just diff against
that source.

## Cross-reference

- Qwen's own model card recommends `preserve_thinking: true` for agentic
  scenarios, citing improved KV cache utilization and reduced redundant
  reasoning.
- The `jundot/omlx` runtime auto-sets `preserve_thinking=True` server-side
  via PR #814 (merged Apr 2026). oMLX users do not need to apply Q3.6-1 to
  the template — it's a no-op when the kwarg is already true.
