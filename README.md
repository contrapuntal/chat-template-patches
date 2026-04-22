# chat-template-patches

Curated, tested patches for Hugging Face Jinja chat templates, focused on
fixing real-world bugs in **Qwen3.5**, **Qwen3.6**, and **Gemma 4** that block
agentic workflows (tool calling, multi-turn reasoning, KV-cache reuse).

Each patch is documented, attributed to its original discoverer/author, and
verified by a render harness (`tests/test_render.py`) that asserts both
correctness *and* that the patch actually addresses the failure mode.

## What this repo contains

- **`templates/<family>/upstream/`** — verbatim chat templates as published by
  the original model authors (Qwen Team, Google) or shipped in canonical
  community quants (unsloth, mlx-community). SHA-256 + fetch date in
  `PROVENANCE.md`.
- **`templates/<family>/patched/`** — derivative templates with one or more
  patches applied. Diff vs. upstream lives in `patches/<family>/<patch-id>.patch`.
- **`patches/`** — unified-diff form of each patch, applicable with `patch -p1`
  or via `scripts/apply.sh`.
- **`docs/PATCH-CATALOG.md`** — every patch with: id, target model(s),
  problem statement, fix, upstream status, **provenance tier**, prior art,
  applicability matrix.
- **`docs/sources/`** — verbatim snapshots of community-authored prior art
  (templates from Reddit, pastebin, gists, third-party GitHub repos).
  Cited from `PATCH-CATALOG.md` and `NOTICE`. See `docs/sources/README.md`
  for the manifest with SHA-256s. Patches do not depend on these
  snapshots — they exist to preserve attribution if the original hosts
  disappear.
- **`tests/`** — render harness + fixtures. Each patch has at least one
  fixture that *fails* on the upstream template and *passes* on the patched
  template.
- **`scripts/`** — `apply.sh` (copy or symlink patched template into a model
  directory), `verify.py` (render-and-diff against goldens),
  `fetch-upstream.sh` (refresh `upstream/` from canonical sources).

## Quick start

```bash
# 1) Install test dependencies (jinja2 only — no transformers required)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-test.txt

# 2) Run the harness against all patches
pytest -v

# 3) Apply a patched template to your local model directory
./scripts/apply.sh gemma4 26B-A4B-it /path/to/your/model/dir

# 4) Refresh upstream templates from HF (e.g., after a model card update)
./scripts/fetch-upstream.sh qwen3.5
```

## Why patches and not full-template forks

Templates evolve. Pinning a fork detaches us from upstream improvements;
maintaining a patch series lets us:

1. Re-apply on top of the next official template revision.
2. Ship only the deltas (which usually compile to <50 lines of Jinja per patch).
3. Retire patches cleanly when upstream merges them — see the **upstream
   status** column in `docs/PATCH-CATALOG.md`.

Several patches in this repo have already been retired: G3 (Gemma 4 Apr-2026
template alignment) is now upstream in `llama.cpp` and Google's HF templates;
P2 (Qwen3.5 tool-call type guard) was merged by unsloth in Mar 2026. They
remain in the catalog as historical context and as a sanity check that future
upstream regressions don't re-introduce them.

## Render harness — what it tests

`tests/test_render.py` loads each `(upstream, patched)` pair and renders
canonical message-set fixtures (`tests/fixtures/`) using `jinja2`. For each
patch:

- **Correctness:** the patched template produces a non-empty render with
  expected delimiters present (e.g., `<turn|>`, `<|im_end|>`).
- **Bug-fix verification:** for the failure mode the patch targets, the
  upstream render exhibits the bug and the patched render does not.
- **Coverage assertions:** every family declared in scope (`README` /
  `PATCH-CATALOG`) must ship at least one patched template — or be
  explicitly listed as catalog-only — so an empty `patched/` directory
  fails the suite instead of skipping silently.

**Optional drift detection (`scripts/verify.py`).** A separate, opt-in
golden-file harness lets you bootstrap baseline renderings and assert that
no template change drifts the output for unrelated fixtures:

```bash
scripts/verify.py --write-goldens   # capture current renderings as baseline
scripts/verify.py                   # report any drift vs the captured baseline
```

Goldens are not shipped in this repo — bootstrap them locally if you want
this kind of regression coverage. The pytest suite does not require them.

Adding a new patch means: write a fixture that exposes the bug (declare
which families it `_applies_to` in the JSON), capture the "upstream is
wrong" assertion, write the patch, then re-render to capture the "patched
is right" assertion.

## Scope

This repo is opinionated about three things:

1. **Real-world bugs only.** No stylistic refactors, no theoretical
   improvements. Each patch must either fix a published upstream issue, an
   observed failure in a popular client (LM Studio, oMLX, llama.cpp, mlx-vlm,
   opencode, Open WebUI), or a measurable correctness/performance regression
   reproducible from a fixture.
2. **Plain text.** All patches are text edits to `chat_template.jinja` files.
   Binary patches against GGUF embedded templates are out of scope here —
   apply the same patch with whatever GGUF-mmap helper you prefer.
3. **No vendor lock-in.** Patches that only make sense for one inference
   runtime (e.g., minijinja-only workarounds for LM Studio) are flagged as
   such in the catalog and live under a clearly labeled subset, not in the
   default `patched/` set.

## Status snapshot

See `docs/PATCH-CATALOG.md` for the full table. High-level summary:

| Family | Patches in repo | Of which already upstream | Affecting active runtimes |
|---|---:|---:|---:|
| Qwen3.5 | P1–P10, R1–R3 (13 total) | P2, R1 (partial) | 8 |
| Qwen3.6 | Q3.6-1 (1) | 0 | 1 (LM Studio MLX path only — oMLX auto-handles) |
| Gemma 4 | G1, G2, G4, G5, G7 (5 active; G3, G6 historical) | G3 | 4 |

## Contributing

Each new patch needs:

1. A reproducible failure mode — link to an upstream issue, a client report,
   or a falsifying fixture.
2. A unified diff against the current upstream template in `templates/<family>/upstream/`.
3. A test in `tests/test_render.py` that verifies both the bug and the fix.
4. An entry in `docs/PATCH-CATALOG.md` with attribution to the original
   discoverer if the patch isn't original to this repo.
5. A `NOTICE` update if a new contributor or upstream source is involved.

## Provenance and attribution

Every shipped patch documents three roles separately in `NOTICE`:

- **Reporter** — who first publicly surfaced the bug.
- **Fix author** — who wrote the actual code change applied here.
- **Template author** — the upstream model author whose work is modified.

Each patch in `docs/PATCH-CATALOG.md` also carries a **provenance tier**
indicating how durable the source the patch traces to is:

- `publisher` (most durable) → `upstream-tracker` → `community-tracker` →
  `community-ephemeral` (least durable) → `derived` (original to this repo).

Sources at risk of disappearing (Reddit, pastebin, gists, small third-party
GitHub repos) are snapshotted under `docs/sources/` with fetch date and
SHA-256.

## License

- Repo (patches, tooling, docs): Apache License 2.0 (see `LICENSE`).
- Upstream templates under `templates/<family>/upstream/` retain their
  original copyright and license (Qwen: Apache-2.0; Gemma: Gemma Terms of
  Use). See `NOTICE` for full attribution.
- Snapshotted prior art under `docs/sources/` retains its original
  authors' rights — files are unmodified verbatim copies recorded for
  attribution purposes per fair-use / archival convention. Each snapshot
  is annotated with the original URL and author in `docs/sources/README.md`.
