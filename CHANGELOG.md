# Changelog

All notable changes to this repo are documented here. Format inspired by
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Patches use IDs
documented in `docs/PATCH-CATALOG.md`.

## [Unreleased]

### Added

- Initial scaffold with patch catalog, render harness, and tooling.
- **Qwen3.5** — patches P1–P10 + R1–R3 (catalog entries; patched templates
  pending fixture-driven verification).
- **Qwen3.6** — patch Q3.6-1 (`preserve_thinking` default-on flip) for the
  35B-A3B size. Verified against `unsloth/Qwen3.6-35B-A3B-MLX-8bit` upstream.
- **Qwen3.6** — patch Q3.6-12 (Anthropic-style `message.thinking` reasoning
  support) added to the shipped 35B-A3B stack; additive — byte-identical for
  all non-`thinking` inputs. Opt-in Q3.6-13 (`tool_call_format="json"` Hermes
  tool calls) ships a `.patch`, not in the default stack. Both ported from
  froggeric's v21.1/v21.3 during the 2026-07-10 froggeric source-sweep
  (v20 → v21.3); README + template snapshotted at
  `docs/sources/hf-snapshots/froggeric-Qwen-Fixed-Chat-Templates-{README-v21.3.md,v21.3.jinja}`.
  Sweep also recorded convergence (froggeric now defaults `preserve_thinking`
  ON, per Q3.6-1) and watch items (v21.1 think-close anchoring vs our Q3.6-3;
  sentinel-scope divergence vs our Q3.6-5; 80-char FP scoping for the Q3.6-8
  watch).
- **Gemma 4** — patch G7 (empty-content tool-call assistant turn closure)
  for the 26B-A4B-it / 31B-it / E2B-it / E4B-it sizes. Bug originally reported
  upstream as Blaizzy/mlx-vlm#1033 and #1034.
- **Gemma 4** — catalog entry G8 (sigjhl JSON Schema robustness; HF disc #91).
  Opt-in reference patch in `patches/gemma4/G8-jsonschema-robustness.patch`;
  not applied to default `patched/`. Pastebin source snapshotted at
  `docs/sources/pastebins/tBAHN6FV-sigjhl-gemma4-jsonschema-robustness.jinja`.

### Changed

- **Gemma 4 upstream sync (2026-07-20) — G7 / G9 / G10 RETIRED.** Bumped all
  `upstream/*.jinja` snapshots to Google's **2026-07-09** template rewrite
  ("Fixed tool-calling loops, turn closures, and thinking content-ordering").
  Big-family SHAs `94899c0f` → `ae53464b`; small-family `33204f1a` →
  `0a2c8073`. Added the previously-untracked **`12B-it`** size (big family),
  bringing tracked sizes to five.
  The rewrite fixes **every patch in the Gemma 4 default stack**: **G7**
  (close conditional gained `and not next_nt.found`), **G9** (upstream added
  a structurally equivalent forward-scan + `continues_into_next`), and
  **G10** (upstream added a *native* `preserve_thinking` kwarg with the same
  default-OFF contract). All three `.patch` files and the whole
  `templates/gemma4/patched/` set were removed; `gemma4` joins `qwen3.5` in
  `CATALOG_ONLY_FAMILIES`. The retirement was detected automatically by the
  repo's upstream-sentinel tests, which are now **inverted** — they assert
  upstream *stays* fixed so a regression re-surfaces the bug.
- **Gemma 4 G1 now ships a `.patch`** (`G1-portable-iterable-check.patch`).
  Still required for minijinja (LM Studio MCP); Google's rewrite **grew** the
  surface from 3 to 4 `is sequence` sites. Byte-identical under jinja2 for
  normal inputs, and additionally fixes a latent dict-valued-`content` crash
  (jinja2's `sequence` test is true for mappings).
- **Upstream drift detection (`scripts/fetch-upstream.sh --check`).** Read-only
  mode that fetches every tracked template and reports SHA drift without
  writing, exiting 1 on drift or unreachable source. Also adds the previously
  untracked `gemma4/12B-it` and a froggeric tracker that reports its
  `template_version`. Google's 2026-07-09 Gemma rewrite went unnoticed for 11
  days, while the shipped Qwen3.6 template was separately unrenderable on
  llama.cpp — both surfaced only because someone asked. Now the repo says so.
- **Source snapshot verification (`scripts/check-sources.py`).** Re-fetches
  every row in `docs/sources/README.md` and classifies OK / MOVED / CHANGED
  (pinned URL changed — always a finding) / GONE (404) / BLOCKED (403, host
  gates automation) / NOCHECK. Implements the re-fetch policy that
  `docs/sources/README.md` already prescribed but nothing enforced.
  First sweep since the snapshots were taken found:
  - **froggeric's `qwen3.5/chat_template.jinja` is 404** — consolidated to a
    single root template at v17, per-family files moved under `archive/`. No
    archived version is byte-identical to our snapshot (checked v10–v18), so
    those exact bytes now survive only here. P12's provenance updated.
  - **Both Reddit snapshots return 403** — gating, not deletion. Tiers
    unchanged; noted that our copies are now the only machine-readable ones.
  - One duplicated manifest row removed.
- **Upstream tracker state recorded (checked 2026-07-22).** HF disc **#118 is
  MERGED** and *is* the 2026-07-09 rewrite — several catalog entries described
  it as unmerged and were stale. G8's fix is **already filed upstream as #91
  (open)**, so no duplicate should be opened. #114 (repetition collapse on
  `continue_final_message`) may be a downstream symptom of the G11 defect, and
  #119 argues that *preserving* reasoning causes repetition loops — the inverse
  of the G10 / Q3.6-1 stance. Also noted: #118's description claims
  `preserve_thinking` defaults true while the shipped template defaults false.
- **Qwen3.5 marked NOT TESTED.** The family is catalog-only and is not run on
  our side: no patches ship, `patched/` is empty, and its entries are
  documented analysis rather than validated fixes. Stated in the catalog,
  README, and the family's PATCHES/PROVENANCE.
- **Gemma 4 G8 revised** — fixed two defects found in review. (1) Upstream's
  object fallback recurses with `filter_keys=true` over a `standard_keys` list
  naming none of the schema vocabulary, so stock renders
  `{"type":"object","anyOf":[…]}` as `properties:{anyOf:{…}}` — losing the real
  `anyOf` and inventing a property. The previous G8 restored the real `anyOf`
  but left the bogus pseudo-property beside it, showing the model contradictory
  constraints. `standard_keys` now names every keyword G8 emits, and the
  fallback is skipped when no unhandled key remains (no more hollow
  `properties:{}`); an explicit empty `properties:{}` still renders.
  (2) `anyOf: []`, `oneOf: []`, `allOf: []`, `enum: []` and `$ref: ""` were
  gated on truthiness and silently dropped — now gated on presence. G8's tests
  assert exact output instead of token presence, which is why the old ones
  passed while the bug was live.
- **Gemma 4 G1 claim narrowed** — `is iterable` also admits sets and
  generators, which `is sequence` rejects; a set renders nondeterministically
  and a one-shot generator can vanish if an earlier pass consumes it. The
  no-change guarantee now explicitly covers JSON-compatible inputs (strings,
  lists, dicts) rather than claiming mappings were the only affected class.
- **Gemma 4 docs reconciled** — the detailed G7/G9/G10 entries carry explicit
  RETIRED banners (G9's notes that its separator half lives on as G11),
  PROVENANCE lists four opt-in patches and the string-args breaking change, and
  the G8 entry no longer claims no tests ship.
- **Gemma 4 G11 (new, opt-in) — consecutive assistant messages were gluing.**
  Google's rewrite fixed G9's turn-marker imbalance but emits no separator, so
  `"LEFT"`+`"RIGHT"` rendered as `LEFTRIGHT` (and `A1A2A3` for longer runs).
  The G9 retirement sentinel missed it because markers still balance. G11 emits
  the newline, gated on `has_content` — strictly better than the retired G9,
  which emitted it unconditionally and injected a stray blank line when the
  first message of the pair was empty.
- **Gemma 4: documented an upstream breaking change.** The 2026-07-09 template
  now REJECTS string-form `tool_calls[].function.arguments` with a hard error —
  the shape the OpenAI spec mandates — so histories that rendered before the
  sync can stop rendering after it. No compatibility patch ships: converting
  JSON to Gemma's `call:NAME{k:v}` form needs a JSON-parse filter absent from
  both jinja2 and minja, and unlike Qwen's Q3.6-4 case upstream fails loudly
  rather than silently dropping. Migration snippet in the catalog; a sentinel
  test pins the behaviour.
- **Qwen3.6 Q3.6-14 — the shipped template could not render on llama.cpp.**
  minja (llama.cpp / LM Studio GGUF) implements no position-returning string
  method: `rfind`, `find` and `index` are Undefined and abort the render.
  Q3.6-3 and Q3.6-5 both used them, so the shipped `patched/35B-A3B.jinja`
  failed outright there — `llama-template-analysis` reported
  `supports_tools: false`. Both are reformulated with `split`/`join`
  (byte-identical under jinja2, 120 render combos verified); the same tool now
  reports `supports_tools: true` / `supports_tool_calls: true`.
  Found by an independent review (gpt-5.6-sol) running the real minja binary —
  the repo's jinja2-only harness was structurally blind to it.
- **New minja gate in the test suite.** Every shipped template and every opt-in
  patch applied to its base is now parsed by `llama-template-analysis`, plus a
  static ban on `rfind`/`find`/`index`. Skips cleanly when llama.cpp is absent.
  Validated by reverting the fix and confirming the gate fails. This is the
  third jinja2/minja divergence the repo has hit (P4 `| safe`, Q3.6-5
  `.replace()` index-0, now Q3.6-14), hence the permanent guard.
- **Gemma 4 G4 revised before shipping.** The first cut used `rfind` (fatal on
  the very minja runtime it targets), crashed on a system content part with no
  `text` key, and could synthesise a sentinel across two text parts that render
  apart. All three fixed; verified under minja on all five sizes.
- **Gemma 4 G4 now ships a `.patch`** (`G4-thinking-toggle-sentinels.patch`),
  re-specified to this repo's standard rather than ported verbatim. The Reddit
  prior art matched bare `ENABLE_THINKING` / `DISABLE_THINKING` substrings and
  stripped them with `.replace()`; the shipped form uses delimited
  `<|think_on|>` / `<|think_off|>` tokens (same spelling as Qwen's Q3.6-5),
  `split|join` stripping (minja index-0 payload-drop safety), handles
  sequence-form system content, and resolves conflicts rightmost-in-text.
  Scanned only from the first system/developer message (prompt-injection
  guard). **Stacks on G1** — apply order `G1 → G4 → G8`. Also corrects a stale
  failure-mode description in the G4 catalog entry: the template never scanned
  the system prompt for `<|think|>`; `enable_thinking` was simply
  kwarg-only.
- **Gemma 4 G8 regenerated** against the 2026-07-09 template (7 → 6 hunks;
  the dropped hunk only added a trailing newline Google's file now has).
  Still unmerged upstream — `anyOf`/`oneOf`/`allOf`/`$ref`/`$defs`/`const`
  remain silently dropped from tool declarations.
- **Gemma 4 upstream sync (2026-05-06).** Bumped all four
  `upstream/*.jinja` snapshots to Google's commit `145dc25` (PR #86,
  "fix(chat_template): update SI and tool call handling"). Big-variant
  SHAs `85a08664` → `94899c0f`; small-variant SHAs `781d10940` →
  `33204f1a`. PR #86 ships `format_parameters` `filter_keys` parameter,
  multimodal first-system-message handling, and `captured_content` /
  `has_content` refactor of the assistant turn-close conditional.
- **G7 patch regenerated** against the new upstream line anchors. Same
  `{%- else -%}` rewrite; matched line is now
  `{%- elif not (ns_tr_out.flag and not has_content) -%}` (was
  `not message.get('content')`). G7's bug remains unfixed by PR #86 —
  `has_content` evaluates falsy for the empty-content tool-call case
  the same way `message.get('content')` did, so the `<|else|>` rewrite
  is still required. All four `patched/*.jinja` regenerated.

### Notes

- G3 (Gemma 4 Apr-2026 official template alignment) is upstream as of
  llama.cpp commit 451ef08 / b8243 and is reflected in the upstream/
  templates we shipped. Catalog entry retained for historical context.
- P2 (Qwen3.5 `is mapping` guard) is upstream in unsloth's Mar 2026
  Qwen3.5 GGUF re-uploads. Catalog entry retained as it is still missing
  from older quants from other publishers.
