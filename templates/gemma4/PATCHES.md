# Gemma 4 patched templates

Default stack applied in `patched/` (per-file basis):

| File | Patches applied | Bytes vs upstream | Notes |
|---|---|---|---|
| `patched/26B-A4B-it.jinja` | G7 | -25 | Active fix for empty-content tool-call infinite loop |
| `patched/31B-it.jinja` | G7 | -25 | Same template family as 26B-A4B |
| `patched/E2B-it.jinja` | G7 | -25 | Small variant; lacks thinking-channel logic |
| `patched/E4B-it.jinja` | G7 | -25 | Same template family as E2B |

Opt-in patches not applied to `patched/`:

- **G1** (`is sequence` minijinja gap) — apply only for LM Studio MCP path.
- **G4** (ENABLE_THINKING/DISABLE_THINKING sentinel) — apply if your client
  doesn't reliably pass `chat_template_kwargs={"enable_thinking": ...}`.
- **G8** (sigjhl JSON Schema robustness) — apply when your tools use
  `anyOf`/`oneOf`/`allOf`/`$ref`/`$defs`/`enum`/`const` schema patterns
  (common for Pydantic-v2-generated MCP tools). Pending upstream merge
  in HF discussion #91; reference patch in
  `patches/gemma4/G8-jsonschema-robustness.patch`.

Historical / configuration-side entries (not template patches):

- **G2** (channel/thought leakage) — superseded by Google's Apr-2026 update
  that ships in current `upstream/`.
- **G3** (Apr-2026 official template realignment) — already in `upstream/`.
- **G5** (LM Studio thinking-toggle) — `model.yaml` workaround, see
  `docs/PATCH-CATALOG.md`.
- **G6** (tool-calling/system-prompt compliance) — runtime version
  recommendations, see `docs/PATCH-CATALOG.md`.

## Upstream-shipped enhancements (2026-05-06 sync)

The current `upstream/` snapshots include Google's PR #86 (commit
`145dc25`, "fix(chat_template): update SI and tool call handling"):

- `format_parameters` macro `filter_keys` parameter (suppresses
  schema-meta keys when recursing into nested mappings without
  explicit `properties`).
- Multimodal first-system-message handling (string OR content-parts
  sequence).
- `captured_content` / `has_content` refactor of the assistant
  turn-close logic.

These are pure improvements with no downstream-patch interaction; G7
remains correct on top of them (the bug G7 fixes is independent of
how `has_content` is computed — `has_content` is also false for the
empty-content tool-call case).

## Applying

```bash
# Symlink (recommended — tracks future repo updates):
./scripts/apply.sh gemma4 26B-A4B-it /Path/to/your/model/dir --symlink

# Copy (snapshot at apply time):
./scripts/apply.sh gemma4 26B-A4B-it /Path/to/your/model/dir
```
