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
- **Gemma 4** — patch G7 (empty-content tool-call assistant turn closure)
  for the 26B-A4B-it / 31B-it / E2B-it / E4B-it sizes. Bug originally reported
  upstream as Blaizzy/mlx-vlm#1033 and #1034.

### Notes

- G3 (Gemma 4 Apr-2026 official template alignment) is upstream as of
  llama.cpp commit 451ef08 / b8243 and is reflected in the upstream/
  templates we shipped. Catalog entry retained for historical context.
- P2 (Qwen3.5 `is mapping` guard) is upstream in unsloth's Mar 2026
  Qwen3.5 GGUF re-uploads. Catalog entry retained as it is still missing
  from older quants from other publishers.
