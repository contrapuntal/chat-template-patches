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
