# Qwen3.6 patched templates

Default stack applied in `patched/`:

| File | Patches applied | Bytes vs upstream | Notes |
|---|---|---:|---|
| `patched/35B-A3B.jinja` | Q3.6-1 | +29 | Flips `preserve_thinking` default to ON |

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

- Patch source: `patches/qwen3.6/Q3.6-1-preserve-thinking-default-on.patch`
- Catalog entry: `docs/PATCH-CATALOG.md` § Q3.6-1
- Provenance: `templates/qwen3.6/PROVENANCE.md`
