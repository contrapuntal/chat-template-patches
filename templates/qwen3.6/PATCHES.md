# Qwen3.6 patched templates

Default stack applied in `patched/`:

| File | Patches applied | Bytes vs upstream | Notes |
|---|---|---:|---|
| `patched/35B-A3B.jinja` | Q3.6-1, Q3.6-2, Q3.6-3, Q3.6-4, Q3.6-5 | +2444 | **Q3.6-1**: flips `preserve_thinking` default to ON. **Q3.6-2**: adds `and reasoning_content` guard so the history `<think>` wrapper is only emitted when reasoning content is non-empty (R1 port; closes the empty-wrapper case Q3.6-1 alone exposed). **Q3.6-3**: auto-closes unclosed `<think>` before `<tool_call>` and recognizes `</thinking>` as a valid alternative close form (handles model hallucination). **Q3.6-4**: tool-call string-form `arguments` are emitted verbatim instead of being silently dropped (R2 port). **Q3.6-5**: `<\|think_off\|>` / `<\|think_on\|>` system-message sentinels for per-request thinking-mode control (R3 port + extension). |

## Patch stacking order

The `.patch` files in `patches/qwen3.6/` apply sequentially:

1. `Q3.6-1-preserve-thinking-default-on.patch` — diffs against `upstream/35B-A3B.jinja`.
2. `Q3.6-2-empty-think-history-guard.patch` — diffs against the result of step 1.
3. `Q3.6-3-auto-close-think-and-thinking-recognition.patch` — diffs against the result of step 2.
4. `Q3.6-4-tool-call-string-args-passthrough.patch` — diffs against the result of step 3.
5. `Q3.6-5-think-toggle-sentinels.patch` — diffs against the result of step 4.

Apply with `patch -p1 < <patch>` from the repo root, in order. The
shipped `patched/35B-A3B.jinja` reflects the cumulative result.

## When to apply

Apply Q3.6-1 if your runtime doesn't auto-set `preserve_thinking=true`:

| Runtime | Auto-sets `preserve_thinking`? | Q3.6-1 needed? |
|---|---|---|
| `jundot/omlx` | ✅ via PR #814 | ❌ No (no-op) |
| `mlx-lm` server | ❌ (as of #1030 still in-progress) | ✅ Recommended |
| LM Studio (MLX path) | ❌ | ✅ Recommended |
| LM Studio (GGUF path) | ❌ | ✅ Recommended |
| `llama.cpp` server with `--chat-template-kwargs '{"preserve_thinking": true}'` | ✅ via flag | ❌ No (kwarg already true) |
| `llama.cpp` server without the flag | ❌ | ✅ Recommended |
| `transformers.AutoTokenizer.apply_chat_template(... preserve_thinking=True)` | ✅ via kwarg | ❌ No (kwarg already true) |
| `transformers` without the kwarg | ❌ | ✅ Recommended |

## Applying

```bash
./scripts/apply.sh qwen3.6 35B-A3B /Path/to/your/model/dir --symlink
```

## See also

- Patch sources:
  - `patches/qwen3.6/Q3.6-1-preserve-thinking-default-on.patch`
  - `patches/qwen3.6/Q3.6-2-empty-think-history-guard.patch`
  - `patches/qwen3.6/Q3.6-3-auto-close-think-and-thinking-recognition.patch`
  - `patches/qwen3.6/Q3.6-4-tool-call-string-args-passthrough.patch`
  - `patches/qwen3.6/Q3.6-5-think-toggle-sentinels.patch`
- Catalog entries: `docs/PATCH-CATALOG.md` §§ Q3.6-1, Q3.6-2, Q3.6-3, Q3.6-4, Q3.6-5
- Provenance: `templates/qwen3.6/PROVENANCE.md`
