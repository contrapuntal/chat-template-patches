# Source snapshots

Verbatim copies of upstream chat-template work that we reference in
`docs/PATCH-CATALOG.md` and `NOTICE`. Snapshotted here because the
original hosts (Reddit, pastebin, gists, third-party GitHub repos) are
ephemeral relative to the lifetime of model deployments.

Each snapshot file is unmodified from the source as fetched on the date
recorded below. SHA-256 lets you verify against a re-fetched copy.

**Snapshots are reference material.** They are *not* part of the patch
sources — patches in `patches/` apply only to the templates in
`templates/<family>/upstream/`. Snapshots in this directory exist so that
attribution and prior art remain auditable even if the original hosts
disappear.

## Reddit threads (high decay risk — locks/deletes/account suspensions)

Reddit's JSON API (`<thread-url>.json`) returns the post + comment tree as
structured JSON, which is what we snapshot here (not the rendered HTML).
Re-fetch with: `curl -A "Mozilla/5.0 chat-template-patches archival"
"<thread-url>.json"`.

| File | SHA-256 | Original URL | Author / context | Fetch date |
|---|---|---|---|---|
| `reddit/1sqpsut-expensive_register_5-qwen36-tool-calling-tests.json` | `5ce6d606f419` | https://www.reddit.com/r/LocalLLM/comments/1sqpsut/ | u/Expensive-Register-5 — field-tested whether the Qwen3.5 tool-calling fixes (incl. `qwen3.5-enhanced.jinja` + `preserve_thinking: true`) carry over to Qwen3.6-35B-A3B. Contains contradictory community data points on `preserve_thinking` for Qwen3.6 that inform **Q3.6-1**'s field-reports section. | 2026-04-22 |

## Pastebins (highest decay risk)

| File | SHA-256 | Original URL | Author / context | Fetch date |
|---|---|---|---|---|
| `pastebins/4wZPFui9-substantial_swan_144-qwen35-no_thinking.jinja` | `6498187c615a` | https://pastebin.com/raw/4wZPFui9 | u/Substantial_Swan_144 — original `/no_thinking` system-message detector for Qwen3.5 (the foundation patch P5 derives from) | 2026-04-22 |
| `pastebins/W9VxRw09-no_information9314-gemma4-enable_thinking.jinja` | `71d8f3b656de` | https://pastebin.com/raw/W9VxRw09 | u/No_Information9314 — Gemma 4 ENABLE_THINKING/DISABLE_THINKING sentinel template (G4 reference) | 2026-04-22 |
| `pastebins/hnPGq0ht-sadman782-gemma4-alt-template.jinja` | `34dd08298843` | https://pastebin.com/raw/hnPGq0ht | Sadman782 — Gemma 4 alternative template recommended in r/LocalLLaMA "PSA: Gemma 4 template improvements" (G3-adjacent) | 2026-04-22 |
| `pastebins/HDt34yA8-gohab2001-qwen35-model.yaml` | `48aef89dad89` | https://pastebin.com/raw/HDt34yA8 | u/Gohab2001 — example LM Studio `model.yaml` exposing `enableThinking` toggle (G5 / cross-cutting reference) | 2026-04-22 |

## Gists (medium decay risk — tied to GitHub account state)

| File | SHA-256 | Original URL | Author / context | Fetch date |
|---|---|---|---|---|
| `gists/aldehir-de036c259-gemma4-open-webui.jinja` | `137b28d20c0c` | https://gist.github.com/aldehir/de036c259ecfe2571b9f1e573f9340e7 | aldegr (GitHub: aldehir) — Gemma 4 template variant with OpenWebUI `<think>`-tag content recovery; cross-referenced from llama.cpp PR #21760 | 2026-04-22 |
| `gists/sudoingX-c2facf7d-qwen35-27b-fixed.jinja` | `169dbbb7d9f0` | https://gist.github.com/sudoingX/c2facf7d8f7608c65c1024ef3b22d431 | sudoingX — Qwen3.5 27B template with developer-role + thinking-mode preservation fixes (parallel rediscovery of P10 + R1) | 2026-04-22 |
| `gists/lekoOwO-c6aed944-qwen35-fork.jinja` | `254084a6e696` | https://gist.github.com/lekoOwO/c6aed944a636abccfe2c3912be34b904 | lekoOwO — fork of sudoingX's gist (Apr 2026); confirms the pattern is widely observed | 2026-04-22 |

## Third-party GitHub repos (medium decay risk)

| File | SHA-256 | Original URL | Author / context | Fetch date |
|---|---|---|---|---|
| `github-snapshots/asf0-gemma4_jinja-chat_template.jinja` | `98ba9089e440` | https://github.com/asf0/gemma4_jinja | asfbrz96 — Gemma 4 template that strips reasoning replay to suppress `<\|channel>thought` leakage; superseded by Google's Apr-2026 official update (G2 historical) | 2026-04-22 |
| `github-snapshots/markqvist-lc-qwen35_tool_thoughts.py` | `709771f8a1f2` | https://github.com/markqvist/lc/blob/master/lc/quirks/qwen35_tool_thoughts.py | markqvist — client-side quirk handler for the Qwen3.5 tool-call-inside-thinking-block bug (llama.cpp issue #20837 workaround) | 2026-04-22 |
| `github-snapshots/allanchan339-vllm-qwen35-enhanced.jinja` | `7b4ad5a7cd94` | https://github.com/allanchan339/vLLM-Qwen3.5-27B | u/Expensive-Register-5 (allanchan339) — M2.5-style interleaved-thinking template for vLLM stack (R5 reference, vLLM-only) | 2026-04-22 |

## HuggingFace community templates (failed to snapshot)

| Source | Status | Notes |
|---|---|---|
| `huggingface.co/barubary/qwen3.5-barubary-attuned-chat-template` | **401 Unauthorized** at fetch time | Source for catalog entries P6, P7, P8, P9, P10, R2. Repo may be gated, deleted, or temporarily unavailable. Mitigation: catalog entries reference individual barubary "Fix N" identifiers; the linked PR comments and commit messages on llama.cpp / Qwen3 issues quote the relevant Jinja snippets. If barubary's repo becomes accessible again, run `scripts/fetch-sources.sh` (planned) to capture it. |

## Refreshing snapshots

Pastebins and gists rarely change in place — the more common failure is
deletion. Treat any 4xx on re-fetch as a finding to record in the
catalog (e.g., update the patch's provenance tier from
`community-tracker` to `community-deleted`).

To re-fetch and verify SHAs match (or update them):

```bash
# Manual for now — a fetch-sources.sh helper is a follow-up.
curl -sSLfo /tmp/x https://pastebin.com/raw/4wZPFui9
shasum -a 256 /tmp/x docs/sources/pastebins/4wZPFui9-*
```
