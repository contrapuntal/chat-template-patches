# Qwen3.5 patched templates

> **Status: catalog entries only as of initial scaffold.** The `patched/`
> directory for Qwen3.5 is intentionally empty in this initial release —
> the patch catalog (P1–P10, R1–R3) is documented in
> `docs/PATCH-CATALOG.md` and the per-patch diff files will be added in a
> follow-up that includes the full default stack applied against
> `upstream/35B-A3B.jinja` (the canonical large-model template) and
> `upstream/2B.jinja` (the canonical small-model template, for P3).

## Default stack (when published)

| File | Patches applied | Notes |
|---|---|---|
| `patched/35B-A3B.jinja` | P1 + P2 + P5 + P6–P10 + R1 + R2 + R3 | Default for sizes 4B, 9B, 27B, 35B-A3B, 122B-A10B (all share `a4aee8` upstream) |
| `patched/2B.jinja` | P1 + P2 + P3 + P5 + P6–P10 + R1 + R2 + R3 | Default for sizes 0.8B, 2B (share `273d8e` upstream); adds P3 polarity flip |

## Opt-in patches not in default stack

- **P4** (`| safe` filter removal) — LM Studio / minijinja runtime only.
- **R4** (deep-loop fallback for P1) — defer until needed.
- **R5** (vLLM-specific tool-call parser pairing with custom enhanced.jinja)
  — vLLM stack only; not adoptable into XML-preserving default stack.

## See also

- Catalog with full per-patch detail: `docs/PATCH-CATALOG.md`
- Provenance: `templates/qwen3.5/PROVENANCE.md`
