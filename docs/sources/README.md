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

> **Both Reddit rows return HTTP 403 to automated re-fetch as of 2026-07-22.**
> Reddit now gates the JSON API for non-browser agents. This is *gating, not
> deletion* — the threads are still reachable by hand — but it means these
> snapshots are now the only machine-readable copies, which raises their value
> rather than invalidating them. Provenance tiers are unchanged; re-verify by
> hand if a claim is ever challenged.

| File | SHA-256 | Original URL | Author / context | Fetch date |
|---|---|---|---|---|
| `reddit/1sqpsut-expensive_register_5-qwen36-tool-calling-tests.json` | `5ce6d606f419` | https://www.reddit.com/r/LocalLLM/comments/1sqpsut/ | u/Expensive-Register-5 — field-tested whether the Qwen3.5 tool-calling fixes (incl. `qwen3.5-enhanced.jinja` + `preserve_thinking: true`) carry over to Qwen3.6-35B-A3B. Contains contradictory community data points on `preserve_thinking` for Qwen3.6 that inform **Q3.6-1**'s field-reports section. | 2026-04-22 |
| `reddit/1t4cev0-fakezeta-qwen36-merged-template.json` | `44a1d9ed4cd1` | https://www.reddit.com/r/LocalLLaMA/comments/1t4cev0/ | u/fakezeta — announcement of a Claude-Opus-assisted merge of allanchan339's + froggeric's Qwen3.6 templates (100↑ / 0.95 ratio). Surfaced the auto-close-`<think>`-before-`<tool_call>` fix and triggered the attribution diff that traced it to allanchan339 (commit `13556c0`, 2026-05-02) rather than froggeric (added 2026-05-05). Top comment captures community skepticism toward LLM-merged Jinja. Supports the **Q3.6-3** (Qwen3.6 shipped) + **P11** (Qwen3.5 sibling, deferred) attribution narrative. | 2026-05-06 |

## Pastebins (highest decay risk)

| File | SHA-256 | Original URL | Author / context | Fetch date |
|---|---|---|---|---|
| `pastebins/4wZPFui9-substantial_swan_144-qwen35-no_thinking.jinja` | `6498187c615a` | https://pastebin.com/raw/4wZPFui9 | u/Substantial_Swan_144 — original `/no_thinking` system-message detector for Qwen3.5 (the foundation patch P5 derives from) | 2026-04-22 |
| `pastebins/W9VxRw09-no_information9314-gemma4-enable_thinking.jinja` | `71d8f3b656de` | https://pastebin.com/raw/W9VxRw09 | u/No_Information9314 — Gemma 4 ENABLE_THINKING/DISABLE_THINKING sentinel template (G4 reference) | 2026-04-22 |
| `pastebins/hnPGq0ht-sadman782-gemma4-alt-template.jinja` | `34dd08298843` | https://pastebin.com/raw/hnPGq0ht | Sadman782 — Gemma 4 alternative template recommended in r/LocalLLaMA "PSA: Gemma 4 template improvements" (G3-adjacent) | 2026-04-22 |
| `pastebins/HDt34yA8-gohab2001-qwen35-model.yaml` | `48aef89dad89` | https://pastebin.com/raw/HDt34yA8 | u/Gohab2001 — example LM Studio `model.yaml` exposing `enableThinking` toggle (G5 / cross-cutting reference) | 2026-04-22 |
| `pastebins/tBAHN6FV-sigjhl-gemma4-jsonschema-robustness.jinja` | `d6f83e366f35` | https://pastebin.com/raw/tBAHN6FV | u/sigjhl — iterated Gemma 4 chat template with JSON Schema robustness fixes (`anyOf`/`oneOf`/`allOf`/`$ref`/`$defs`/`enum`/`const`/array-type/null). Superset of the HF PR at `google/gemma-4-31B-it/discussions/91`. Reference template for **G8** (opt-in patch); CRLF normalized to LF on import. | 2026-05-06 |

## Gists (medium decay risk — tied to GitHub account state)

| File | SHA-256 | Original URL | Author / context | Fetch date |
|---|---|---|---|---|
| `gists/aldehir-de036c259-gemma4-open-webui.jinja` | `137b28d20c0c` | https://gist.github.com/aldehir/de036c259ecfe2571b9f1e573f9340e7 | aldegr (GitHub: aldehir) — Gemma 4 template variant with OpenWebUI `<think>`-tag content recovery; cross-referenced from llama.cpp PR #21760 | 2026-04-22 |
| `gists/sudoingX-c2facf7d-qwen35-27b-fixed.jinja` | `169dbbb7d9f0` | https://gist.github.com/sudoingX/c2facf7d8f7608c65c1024ef3b22d431 | sudoingX — Qwen3.5 27B template with developer-role + thinking-mode preservation fixes (parallel rediscovery of P10 + R1) | 2026-04-22 |
| `gists/lekoOwO-c6aed944-qwen35-fork.jinja` | `254084a6e696` | https://gist.github.com/lekoOwO/c6aed944a636abccfe2c3912be34b904 | lekoOwO — fork of sudoingX's gist (Apr 2026); confirms the pattern is widely observed | 2026-04-22 |
| `gists/fakezeta-9e8e039c-qwen36-merged.jinja` | `fa19bcf78e93` | https://gist.github.com/fakezeta/9e8e039c60332fcb143c6e805558afe0 | fakezeta — derivative LLM-assisted merge of allanchan339's `qwen3.6-enhanced.jinja` + froggeric's `qwen3.6/chat_template.jinja` (announced in r/LocalLLaMA `1t4cev0`). Improves both parents in the auto-close path by checking *both* `</think>` and `</thinking>` rfind positions before injecting the closer — that combined form is fakezeta's own contribution. Snapshotted as historical context, not as primary source for any patch. | 2026-05-06 |
| `gists/jscott3201-e4b15588-qwen36-custom.jinja` | `253fa327c524` | https://gist.github.com/jscott3201/e4b155885cc68c038d6ac8909a3bd9fe | jscott3201 — public "harness-friendly" fork of canonical `Qwen/Qwen3.6` for agentic coding harnesses, bundling six patches (Q1-Q6). Forked from *canonical* Qwen (not the unsloth redistribution this repo tracks), so its Q1/Q2/Q3/Q4 overlap with what this repo already ships (Q3.6-1, the unsloth-upstream developer-role + `is mapping` fixes, Q3.6-4, Q3.6-3) or are weaker (Q3 *raises* on string args where Q3.6-4 renders them). Two patches were extracted: **Q5 → Q3.6-6** (tool-definition envelope unwrap) and **Q6 → Q3.6-7** (strengthened tool instructions, opt-in). Labels the model "Qwen3.6-27B" — note this repo's PROVENANCE records only 35B-A3B as released for Qwen3.6; the template logic is family-identical so the patches port cleanly. | 2026-05-30 |

## Third-party GitHub repos (medium decay risk)

| File | SHA-256 | Original URL | Author / context | Fetch date |
|---|---|---|---|---|
| `github-snapshots/asf0-gemma4_jinja-chat_template.jinja` | `98ba9089e440` | https://github.com/asf0/gemma4_jinja | asfbrz96 — Gemma 4 template that strips reasoning replay to suppress `<\|channel>thought` leakage; superseded by Google's Apr-2026 official update (G2 historical) | 2026-04-22 |
| `github-snapshots/markqvist-lc-qwen35_tool_thoughts.py` | `709771f8a1f2` | https://github.com/markqvist/lc/blob/master/lc/quirks/qwen35_tool_thoughts.py | markqvist — client-side quirk handler for the Qwen3.5 tool-call-inside-thinking-block bug (llama.cpp issue #20837 workaround) | 2026-04-22 |
| `github-snapshots/allanchan339-vllm-qwen35-enhanced.jinja` | `7b4ad5a7cd94` | https://github.com/allanchan339/vLLM-Qwen3-3.5-3.6-chat-template-fix (`chat-template/qwen3.5-enhanced.jinja`; repo renamed from `vLLM-Qwen3.5-27B` May 2026, old URL still 301-redirects) | u/Expensive-Register-5 (allanchan339) — M2.5-style interleaved-thinking template for vLLM stack (R5 reference, vLLM-only) | 2026-04-22 |
| `github-snapshots/allanchan339-vllm-qwen36-enhanced.jinja` | `5d7b7fbc6ec1` | https://github.com/allanchan339/vLLM-Qwen3-3.5-3.6-chat-template-fix (`chat-template/qwen3.6-enhanced.jinja`, commit `13556c0` 2026-05-02) | u/Expensive-Register-5 (allanchan339) — Qwen3.6 variant. **Originator of the `<think>`-auto-close-before-`<tool_call>` fix**: commit timestamps confirm allanchan339 published it 2026-05-02; froggeric added a byte-equivalent block to its qwen3.6 template 2026-05-05 (commit `2179960`). Shipped as **Q3.6-3** in this repo (Qwen3.6) and reserved as **P11** for the Qwen3.5 sibling port (deferred). | 2026-05-06 |
| `github-snapshots/allanchan339-vllm-qwen36-README.md` | `79a914e71ff1` | https://github.com/allanchan339/vLLM-Qwen3-3.5-3.6-chat-template-fix/blob/main/README.md | Companion to the `qwen3.6-enhanced.jinja` snapshot — documents the seven failure modes the template addresses (Jinja instability, transformers ≥5.3, FP8 precision drift, quantization tradeoffs, context-vs-VRAM, tool-call parser selection, env vars) and the vLLM/parser configuration each one requires. Cross-links allanchan339's r/Vllm `1skks8n` deep-dive. | 2026-05-06 |

## HuggingFace community templates (snapshotted)

| File | SHA-256 | Original URL | Author / context | Fetch date |
|---|---|---|---|---|
| `hf-snapshots/froggeric-Qwen-Fixed-Chat-Templates-qwen35.jinja` | `1acf46b19dbb` | ~~https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates/raw/main/qwen3.5/chat_template.jinja~~ — **404 since at least 2026-07-22.** froggeric consolidated to a single root `chat_template.jinja` at v17 and moved the per-family files to `archive/qwen3.5/chat_template-v*.jinja`. **No archived version is byte-identical to this snapshot** (checked v10–v18; v17/v18 do not exist), so these exact bytes now survive ONLY here. | froggeric — Qwen3.5 fixes (developer role, `</think>`/`</thinking>` recognition, string-arg tojson guard, etc). Companion to the Qwen3.6 snapshots; cross-referenced from r/LocalLLaMA `1t4cev0` and used by fakezeta as one of the two parents of the merged template at `gists/fakezeta-9e8e039c-...`. | 2026-05-06 |
| `hf-snapshots/froggeric-Qwen-Fixed-Chat-Templates-qwen36-e1eb965.jinja` | `ce3f4fafa573` | https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates/raw/e1eb965/qwen3.6/chat_template.jinja | froggeric — initial qwen3.6 upload (2026-05-01). **Crucially does NOT contain the `<think>`-auto-close-before-`<tool_call>` block** — proof for the attribution claim that allanchan339 (commit `13556c0`, 2026-05-02) originated that fix, not froggeric. | 2026-05-06 |
| `hf-snapshots/froggeric-Qwen-Fixed-Chat-Templates-qwen36-2179960.jinja` | `94e944287ffa` | https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates/raw/2179960/qwen3.6/chat_template.jinja | froggeric — qwen3.6 update on 2026-05-05 that **adds** the auto-close block, byte-equivalent to allanchan339's earlier `13556c0`. The `diff -u e1eb965 2179960` is the smoking gun for the attribution chain. | 2026-05-06 |
| `hf-snapshots/froggeric-Qwen-Fixed-Chat-Templates-v18.jinja` | `1839b811093c` | https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates/raw/main/archive/qwen3.6/chat_template-v18.jinja | froggeric **v18** (2026-05-16). Source for the **Q3.6-8 structural false-positive detection** the eval gate requires: line ~235 reads `'"error":' / 'exception:' / 'traceback' / 'command not found' / 'invalid syntax'` from short tool responses instead of broad substring matching. Also replaces `loop.previtem` with `messages[loop.index0 - 1]` for minija/old-llama.cpp portability. | 2026-06-11 |
| `hf-snapshots/froggeric-Qwen-Fixed-Chat-Templates-v20.jinja` | `27d22ab352ef` | https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates/raw/main/chat_template.jinja (as of 2026-06-11; **`main` now serves v21.3** — see below) | froggeric **v20** "Architect Patch" (2026-06-05). Source for the **Q3.6-5 minja-safety hardening**: sentinel strip uses `_sc.split('<\|think_off\|>') \| join('')` (lines 74/77/153/156), NOT `.replace()` — minja silently drops the whole string when the replaced target is at index 0. Independently confirms the fix applied to our Q3.6-5. | 2026-06-11 |
| `hf-snapshots/froggeric-Qwen-Fixed-Chat-Templates-README-v20.md` | `b24fa2a71ee5` | https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates/raw/main/README.md (as of 2026-06-11) | froggeric README (v20), the authoritative changelog for v8–v20. Backs the version-specific claims cited above (v18 structural detection, v20 minja `replace` hotfix). Note: the repo advanced **v15/v16 (our earlier snapshots) → v20** between 2026-05-13 and 2026-06-05. | 2026-06-11 |
| `hf-snapshots/froggeric-Qwen-Fixed-Chat-Templates-v21.3.jinja` | `d203f3342d8a` | https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates/raw/main/chat_template.jinja | froggeric **v21.3** (2026-07-02), current `main`. Sweep delta v20→v21.3 (`diff -u`): (1) **`_preserve_thinking` default flipped `false`→`true`** — froggeric now converges on our **Q3.6-1** default-on position (v20's template still shipped `else false` despite the README's v19 claim). (2) **`message.thinking` (Anthropic reasoning) branch** added to reasoning_content sourcing — shipped here as **Q3.6-12** (active; string-only port — non-string `thinking` ignored, not coerced). (3) **`tool_call_format="json"` kwarg** adds a Hermes-JSON tool-call branch (default stays `xml`) — shipped as **Q3.6-13** (opt-in `.patch`, parser-lock-in; not catalog-only since it is non-lossy — whitespace-only string args trimmed to `{}`). (4) sentinel strip now scoped to `is_system or role=='user'` (prompt-injection guard; our Q3.6-5 is already system-only via `merged_system`). (5) think-close detection changed from `'</think>' in content` to `startswith`/`'\n</think>'` anchoring (quoted-`</think>` history-corruption fix; refines **Q3.6-3**). (6) FP error-detection scoped to first 80 chars + adds `err!`/`fatal:` (refines **Q3.6-8** watch). (7) reasoning-bypass prefix restored to `<think>\n\n</think>\n\n` (P9/R1 whitespace symmetry). (8) default `<IMPORTANT>` tool-call instruction text rewritten to drop explicit `</think>` mentions (froggeric v21.2 reasoning-bypass-hallucination fix) — a change to shipped *instruction text*, our Q3.6-7 class. (9) trailing `\n` after the final `</tool_call>` **dropped** in XML serialization (v20 emitted `</tool_call>\n` on `loop.last`; v21.3 does not) — P8-class streaming/cache whitespace. (10) malformed-close recognition (`</ think>`/`</think >`) retained but now newline-anchored (`\n</ think>`/`\n</think >`); our Q3.6-3 recognizes neither spelling. | 2026-07-10 |
| `hf-snapshots/froggeric-Qwen-Fixed-Chat-Templates-README-v21.3.md` | `80a9cf294079` | https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates/raw/main/README.md | froggeric README (v21.3), authoritative changelog through v21.3. New blocks since v20: **v21.1** (2026-07-02) "Reliability Overhaul & XML Revert" — reverted a JSON-format PR that broke vLLM's `qwen3_coder` parser, restored `preserve_thinking=true` default, added `<\|think_off\|>` prompt-injection guard, quoted-`</think>` fix, Anthropic `message.thinking`, 80-char FP-error scope, canonical `\n\n` bypass spacing; **v21.2** removed explicit `</think>` mentions from the `<IMPORTANT>` block to stop reasoning-bypass hallucination; **v21.3** added the opt-in `tool_call_format="json"` escape hatch. | 2026-07-10 |

## HuggingFace community templates (failed to snapshot)

| Source | Status | Notes |
|---|---|---|
| `huggingface.co/barubary/qwen3.5-barubary-attuned-chat-template` | **401 Unauthorized** at fetch time | Source for catalog entries P6, P7, P8, P9, P10, R2. Repo may be gated, deleted, or temporarily unavailable. Mitigation: catalog entries reference individual barubary "Fix N" identifiers; the linked PR comments and commit messages on llama.cpp / Qwen3 issues quote the relevant Jinja snippets. If barubary's repo becomes accessible again, run `scripts/fetch-sources.sh` (planned) to capture it. |

## Verifying (automated)

    scripts/check-sources.py          # re-fetch every row, compare SHA-256
    scripts/check-sources.py --quiet  # findings only

Classifies each row as OK / MOVED (moving ref, expected) / CHANGED (a
commit-pinned URL changed — always a finding) / GONE (404, deleted) / BLOCKED
(401/403/429, host gates automation) / NOCHECK (the recorded URL is a human
landing page whose raw form cannot be derived) and exits non-zero on findings.

The companion check for *upstream model templates* is
`scripts/fetch-upstream.sh --check` (read-only drift detection).

Run both periodically. The 2026-07-22 sweep — the first since these snapshots
were taken — found one dead URL and two newly-gated hosts, none of which
anything would have surfaced on its own.

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
