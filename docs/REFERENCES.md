# References — flat index

A grep-friendly bibliography of every external source cited from this
repo, organized by source type. Each entry cross-references the patch
ID(s) it supports. For the per-patch detail (problem statement, fix
text, status), see `PATCH-CATALOG.md`. For verbatim snapshots of
ephemeral sources, see `docs/sources/README.md`.

## Reddit threads

| Thread | Title | Author | Date | Supports |
|---|---|---|---|---|
| [r/LocalLLaMA `1sg076h`](https://www.reddit.com/r/LocalLLaMA/comments/1sg076h/) | I tracked a major cache reuse issue down to Qwen 3.5's chat template | u/onil_gova | Apr 2026 | R1 (cross-reference); see also HF discussions |
| [r/LocalLLaMA `1sne4gh`](https://www.reddit.com/r/LocalLLaMA/comments/1sne4gh/) | PSA: Qwen3.6 ships with preserve_thinking. Make sure you have it on. | u/onil_gova | Apr 2026 (~387↑) | **Q3.6-1** (reporter) |
| [r/LocalLLaMA `1recpjw`](https://www.reddit.com/r/LocalLLaMA/comments/1recpjw/) | Qwen 3.5 Jinja Template – Restores Qwen /no_thinking behavior! | u/Substantial_Swan_144 | Nov 2025 | **P5** (reporter, original template) |
| [r/LocalLLaMA `1sis1vn`](https://www.reddit.com/r/LocalLLaMA/comments/1sis1vn/) | The definitive Qwen 3.5 jinja template | u/ex-arman68 | 2026 | **R3** (sentinel-vs-substring discussion) |
| [r/LocalLLaMA `1sdhvc5`](https://www.reddit.com/r/LocalLLaMA/comments/1sdhvc5/) | Qwen 3.5 tool calling fixes for agentic use — what's still broken? | froggeric | 2026 | **R2** (independent confirmation) |
| [r/LocalLLaMA `1shbqmx`](https://www.reddit.com/r/LocalLLaMA/comments/1shbqmx/) | PSA: Gemma 4 template improvements | u/FastHotEmu | Apr 2026 (112↑) | **G3** (cross-reference); cites Sadman782's hnPGq0ht |
| [r/LocalLLaMA `1sic351`](https://www.reddit.com/r/LocalLLaMA/comments/1sic351/) | Gemma 4 template fix `<\|channel>` / thought leakage | u/asfbrz96 | Apr 2026 | **G2** (reporter); also cites aldegr's gist + llama.cpp PR #21760 |
| [r/LocalLLaMA `1sfjhsx`](https://www.reddit.com/r/LocalLLaMA/comments/1sfjhsx/) | Gemma 4 thinking system prompt | u/No_Information9314 | Apr 2026 | **G4** (reporter, original template) |
| [r/LocalLLaMA `1sbst46`](https://www.reddit.com/r/LocalLLaMA/comments/1sbst46/) | For anyone having issues with Gemma 4 31b in LM Studio | u/WyattTheSkid | Apr 2026 | **G5** (workaround surfaced) |
| [r/LocalLLaMA `1slef6w`](https://www.reddit.com/r/LocalLLaMA/comments/1slef6w/) | [Fix] Gemma 4 MCP tool calls broken in LM Studio — "Unknown test: sequence" | u/Reaper_9382 | Apr 2026 | **G1** (reporter) |
| [r/LocalLLaMA `1sh1bwv`](https://www.reddit.com/r/LocalLLaMA/comments/1sh1bwv/) | Gemma 4 is terrible with system prompts and tools | u/RealChaoz | Apr 2026 (124↑) | **G6** (primary thread) |
| [r/Vllm `1skks8n`](https://www.reddit.com/r/Vllm/comments/1skks8n/) | Qwen 3.5 27B/35BA3B Tool Calling Issues: Why It Breaks & How I Fixed It | u/Expensive-Register-5 | Apr 2026 | catalog-only — vLLM-specific (R5 reference) |
| [r/LocalLLM `1sqpsut`](https://www.reddit.com/r/LocalLLM/comments/1sqpsut/) | Qwen 3.6-35B-A3B: Reddit Asked, So I Tested If the 3.5 Tool Calling Fixes Carry Over | u/Expensive-Register-5 | Apr 2026 | follow-up to 1skks8n |
| [r/LocalLLaMA `1sgl3qz`](https://www.reddit.com/r/LocalLLaMA/comments/1sgl3qz/) | Gemma 4 on llama.cpp should be stable now | — | Apr 2026 | G3 stabilization context |

## HuggingFace discussions — Qwen publisher repos

R1 was opened by `latent-variable` on every Qwen3.5 size as the same minimal-empty-`<think>` cache-reuse PR:

| Thread | Repo | Status | Reactions |
|---|---|---|---|
| [`Qwen/Qwen3.5-122B-A10B/discussions/22`](https://huggingface.co/Qwen/Qwen3.5-122B-A10B/discussions/22) | 122B-A10B | Ready to merge | 24 |
| [`Qwen/Qwen3.5-35B-A3B/discussions/56`](https://huggingface.co/Qwen/Qwen3.5-35B-A3B/discussions/56) | 35B-A3B | Open | — |
| [`Qwen/Qwen3.5-27B/discussions/44`](https://huggingface.co/Qwen/Qwen3.5-27B/discussions/44) | 27B | Open | — |
| [`Qwen/Qwen3.5-9B/discussions/48`](https://huggingface.co/Qwen/Qwen3.5-9B/discussions/48) | 9B | Open | — |
| [`Qwen/Qwen3.5-4B/discussions/14`](https://huggingface.co/Qwen/Qwen3.5-4B/discussions/14) | 4B | Open | — |
| [`Qwen/Qwen3.5-2B/discussions/6`](https://huggingface.co/Qwen/Qwen3.5-2B/discussions/6) | 2B | Open | — |
| [`Qwen/Qwen3.5-0.8B/discussions/14`](https://huggingface.co/Qwen/Qwen3.5-0.8B/discussions/14) | 0.8B | Open | — |

All seven supports **R1** (`upstream-tracker` provenance).

Other relevant Qwen-publisher discussions:

| Thread | Topic | Notes |
|---|---|---|
| [`Qwen/Qwen3.5-35B-A3B/discussions/18`](https://huggingface.co/Qwen/Qwen3.5-35B-A3B/discussions/18) | Reasoning content leaks into `message.content` with JSON schema response format | Open; not currently a catalog entry |
| [`Qwen/Qwen3.5-35B-A3B/discussions/61`](https://huggingface.co/Qwen/Qwen3.5-35B-A3B/discussions/61) | Fixed jinja template causing stalling/stopping responses on tool use (deladuck) | May overlap with R1+R2+P10 |
| [`Qwen/Qwen3.5-35B-A3B/discussions/67`](https://huggingface.co/Qwen/Qwen3.5-35B-A3B/discussions/67) | Thinking mode emits closing `</think>` without opening `<think>` | Possibly related to R1 |
| [`Qwen/Qwen3.5-35B-A3B/discussions/71`](https://huggingface.co/Qwen/Qwen3.5-35B-A3B/discussions/71) | Multiple system messages cause template breakage | Not currently a catalog entry |
| [`Qwen/Qwen3.5-35B-A3B/discussions/72`](https://huggingface.co/Qwen/Qwen3.5-35B-A3B/discussions/72) | Compact tool-rendering template (49% fewer prompt tokens) (Evita) | Potential future patch |
| [`Qwen/Qwen3.5-27B/discussions/33`](https://huggingface.co/Qwen/Qwen3.5-27B/discussions/33) | Stray `.cw` suffix at end of reasoning content | Output-side artifact, not template |
| [`Qwen/Qwen3.5-9B/discussions/10`](https://huggingface.co/Qwen/Qwen3.5-9B/discussions/10) | Tool call stops in middle of conversation | Same family as llama.cpp #20837 |
| [`Qwen/Qwen3.5-9B/discussions/39`](https://huggingface.co/Qwen/Qwen3.5-9B/discussions/39) | Proposal: `enable_history_reasoning` chat-template kwarg | Functional twin of Q3.6-1 |
| [`Qwen/Qwen3.6-35B-A3B/discussions`](https://huggingface.co/Qwen/Qwen3.6-35B-A3B/discussions) | (40+ open issues) | General reference for Q3.6 issues |

## HuggingFace discussions — community quants

| Thread | Topic | Supports |
|---|---|---|
| [`unsloth/Qwen3.5-35B-A3B-GGUF/discussions/9`](https://huggingface.co/unsloth/Qwen3.5-35B-A3B-GGUF/discussions/9) | Add support for developer role (Codex compatibility) | **P10** (independent confirmation) |
| [`unsloth/Qwen3.5-35B-A3B-GGUF/discussions/34`](https://huggingface.co/unsloth/Qwen3.5-35B-A3B-GGUF/discussions/34) + [`#36`](https://huggingface.co/unsloth/Qwen3.5-35B-A3B-GGUF/discussions/36) | Multi-system messages + developer role | Multi-system not yet a catalog patch |
| [`unsloth/Qwen3.5-35B-A3B-GGUF/discussions/10`](https://huggingface.co/unsloth/Qwen3.5-35B-A3B-GGUF/discussions/10) | Feb 27: GGUF Update + Tool-calling fixes (pinned) | **P2** confirmed upstream |
| [`unsloth/Qwen3.5-35B-A3B-GGUF/discussions/31`](https://huggingface.co/unsloth/Qwen3.5-35B-A3B-GGUF/discussions/31) | Mar 5: 'Final' Update: iMatrix + Benchmarks (pinned) | publisher status snapshot |
| [`unsloth/Qwen3.6-35B-A3B-GGUF/discussions/2`](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF/discussions/2) | 2-bit Qwen3.6 Tool-calling is amazing!! (pinned) | publisher confirmation |
| [`unsloth/Qwen3.6-35B-A3B-GGUF/discussions/4`](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF/discussions/4) | Developer Role Support | Same gap as Qwen3.5 P10 |
| [`unsloth/Qwen3.6-35B-A3B-GGUF/discussions/5`](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF/discussions/5) | Tool calls fail sometimes even in BF16 | Track for Qwen3.6 |
| [`bartowski/Qwen_Qwen3.5-35B-A3B-GGUF/discussions/3`](https://huggingface.co/bartowski/Qwen_Qwen3.5-35B-A3B-GGUF/discussions/3) | LM Studio Jinja "No user query found" Fix (Dopey24) | **P1** (independent rediscovery) |
| [`bartowski/google_gemma-4-26B-A4B-it-GGUF/discussions/3`](https://huggingface.co/bartowski/google_gemma-4-26B-A4B-it-GGUF/discussions/3) | Will these be updated re: recent llama.cpp updates? | Confirms bartowski Gemma 4 lag post-G3 |
| [`lmstudio-community/Qwen3.5-35B-A3B-GGUF/discussions/1`](https://huggingface.co/lmstudio-community/Qwen3.5-35B-A3B-GGUF/discussions/1) | lmstudio temp fix for tool calling (rkuovc, 5↑) | Alternative JSON tool-call format; LM Studio 0.4.5+1 fixed natively |

## GitHub — `ggml-org/llama.cpp`

### Merged PRs

| PR | Title | Author | Merge date | Supports |
|---|---|---|---|---|
| [`#18675`](https://github.com/ggml-org/llama.cpp/pull/18675) | Autoparser - complete refactoring of parser architecture | pwilkin | 2026-03-06 (commit `566059a`) | foundational; bug-source for many catalog entries |
| [`#20191`](https://github.com/ggml-org/llama.cpp/pull/20191) | common: gracefully handle incomplete output | aldehir | 2026-03-08 (commit `451ef08`, b8243) | engine UTF-8 fix |
| [`#20297`](https://github.com/ggml-org/llama.cpp/pull/20297) | Handle reasoning budget | pwilkin | 2026-03-11 | introduces `--reasoning on/off` (replaces P5/R3 in current builds) |
| [`#20970`](https://github.com/ggml-org/llama.cpp/pull/20970) | common: inhibit lazy grammar sampler while reasoning is active | aldehir | 2026-03-27 (commit `59d8402`) | engine fix for grammar trigger inside reasoning |
| [`#21697`](https://github.com/ggml-org/llama.cpp/pull/21697) | thinking_start_tag/end_tag for gemma4, kimi_k2, lfm2, ministral_3 | berkidem | 2026-04 | engine template metadata |
| [`#21704`](https://github.com/ggml-org/llama.cpp/pull/21704) | common: better align to the updated official gemma4 template | aldehir | 2026-04-10 | **G3** llama.cpp side |
| [`#21760`](https://github.com/ggml-org/llama.cpp/pull/21760) | common/gemma4: handle parsing edge cases | aldehir | 2026-04-11 | Gemma 4 26B-A4B parser fixes |
| [`#21870`](https://github.com/ggml-org/llama.cpp/pull/21870) | common: skip reasoning budget sampler when no budget is requested | berkidem | 2026-04-14 | perf fix for #21697 regression |
| [`#21699`](https://github.com/ggml-org/llama.cpp/pull/21699) | fix: `$refs` in JSON schema | aldehir | merged | engine structured-output fix |
| [`#18604`](https://github.com/ggml-org/llama.cpp/pull/18604) | common/grammar: prevent stack overflow and hangs | — | merged (commit `990e4d9`) | bug-source for `MAX_REPETITION_THRESHOLD` issues |

### Closed-without-merge PRs

| PR | Title | Author | Notes |
|---|---|---|---|
| [`#20844`](https://github.com/ggml-org/llama.cpp/pull/20844) | Do not trigger grammar inside tool calling section | pwilkin | Closed Mar 27 — superseded by #20970 |
| [`#20660`](https://github.com/ggml-org/llama.cpp/pull/20660) | Fix chat parser regressions | jpohhhh | Closed unmerged Mar 17 |
| [`#20708`](https://github.com/ggml-org/llama.cpp/pull/20708) | chat: new parser should not crash inference | jpohhhh | Closed unmerged Mar 18 |

### Open / in-flight PRs

| PR | Title | Notes |
|---|---|---|
| [`#20329`](https://github.com/ggml-org/llama.cpp/pull/20329) | cli: fix --reasoning-budget and --chat-template-kwargs being ignored (TrevorS) | Awaiting review; pwilkin says superseded by #20297 |
| [`#21003`](https://github.com/ggml-org/llama.cpp/pull/21003) | grammar: `MAX_REPETITION_THRESHOLD` envvar (pwilkin) | Status unclear |
| [`#21216`](https://github.com/ggml-org/llama.cpp/pull/21216) | common: simplify autoparser tagged parser rules (aldehir) | Closed #20867; otaviojr Apr 1 reports fix incomplete |

### Open issues

| Issue | Title | Reporter | Notes |
|---|---|---|---|
| [`#19869`](https://github.com/ggml-org/llama.cpp/issues/19869) | llama-cli crash in `common_chat_peg_parse` (Qwen 3.5 Thinking) | NatTuck | Closed (auto-stale Apr 20). Root-caused: incomplete UTF-8 at max_tokens cutoff. PR #20191 |
| [`#20178`](https://github.com/ggml-org/llama.cpp/issues/20178) | Structured json fails when using enums with Qwen3.5-35B-A3B | Galunid | **CLOSED Apr 10 via PR #21699** |
| [`#20182`](https://github.com/ggml-org/llama.cpp/issues/20182) | enable_thinking param cannot turn off thinking for qwen3.5 | Goulustis | Open; PR #20329 in flight. Bisected to b8227 |
| [`#20193`](https://github.com/ggml-org/llama.cpp/issues/20193) | llama-server 500 + "Failed to parse input" when max_tokens reached | fairydreaming | **CLOSED Mar 8 via PR #20191** |
| [`#20196`](https://github.com/ggml-org/llama.cpp/issues/20196) | Disabling reasoning does not work anymore on certain models | gelim | **wontfix**, stale. Foundational design statement by pwilkin |
| [`#20409`](https://github.com/ggml-org/llama.cpp/issues/20409) | Qwen3.5 enable_thinking=false via --chat-template-kwargs ignored across all shells | lucksufe | Open. PowerShell escaping + llama-cli silent ignore |
| [`#20516`](https://github.com/ggml-org/llama.cpp/issues/20516) | Response always starts with `</think>` tag (Qwen3.5 9B) | ZUIcat | Open. Same family as #21511 |
| [`#20761`](https://github.com/ggml-org/llama.cpp/issues/20761) | Broken tool-use for unsloth/Qwen3.5-9B-GGUF | deven367 | Stale. `Failed to parse input at pos 12: </tool_call>` |
| [`#20768`](https://github.com/ggml-org/llama.cpp/issues/20768) | Qwen3.5: `<think>` tags inserted on resume | — | Related to #21511 |
| [`#20789`](https://github.com/ggml-org/llama.cpp/issues/20789) | b8400: ngram params corrupted + `<think>` injected despite reasoning_format=none | thorory | Stale |
| [`#20814`](https://github.com/ggml-org/llama.cpp/issues/20814) | Autoparser throws on final parse after streaming succeeds | jpohhhhh | CLOSED. Bot surfaced 6 related sharing bad commit `566059a` |
| [`#20833`](https://github.com/ggml-org/llama.cpp/issues/20833) | Qwen3.5-2B thinks by default | grapevine-AI | Open. **`--reasoning off` workaround** |
| [`#20837`](https://github.com/ggml-org/llama.cpp/issues/20837) | Qwen3.5 9B prints tool calls in XML inside thinking block | kik4444 | Open. Fix in #20970 |
| [`#20860`](https://github.com/ggml-org/llama.cpp/issues/20860) | Failed to parse grammar | tha80 | CLOSED dup of #20867 |
| [`#20861`](https://github.com/ggml-org/llama.cpp/issues/20861) | Qwen3.5 + Opencode: Assistant prefill incompatible with enable_thinking | alefranz | Open; **affects Qwen3.6 too**. Workaround: `--no-prefill-assistant` |
| [`#20867`](https://github.com/ggml-org/llama.cpp/issues/20867) | `MAX_REPETITION_THRESHOLD` (2000) breaks tool-calling | Whamp | CLOSED via #21216 (but otaviojr Apr 1: fix incomplete) |
| [`#21511`](https://github.com/ggml-org/llama.cpp/issues/21511) | llama-server returns template-injected `<think>` in prefill responses | lacerbi | Open. Specific repro |
| [`#21784`](https://github.com/ggml-org/llama.cpp/issues/21784) | Gemma 4 template changes causing degraded inference speed | CMay | CLOSED via PR #21870 |
| [`#21255`](https://github.com/ggml-org/llama.cpp/issues/21255) + [`#21371`](https://github.com/ggml-org/llama.cpp/issues/21371) | CUDA 13.2 cicc miscompilation | — | Cross-ref unsloth#4849 |

## GitHub — `QwenLM/Qwen3` (publisher tracker)

| Issue | Title | Notes |
|---|---|---|
| [`#1826`](https://github.com/QwenLM/Qwen3/issues/1826) | Chat template breaks KV-cache reuse when enable_thinking=false (Giant-Space-Bee) | **R1** alt variant with ~25× TTFT benchmark |
| [`#1831`](https://github.com/QwenLM/Qwen3/issues/1831) | [Template] 21-fix chat template for Qwen 3.5 — fixes tool calling crash, parallel calls, thinking bleed (blockoracle) | community thread |
| [`#1748`](https://github.com/QwenLM/Qwen3/issues/1748) | Undefined role causes infinite GPU loop / no termination | **P10** mitigates |
| [`#1817`](https://github.com/QwenLM/Qwen3/issues/1817) | Thinking mode plans tool calls but fails to execute ~60% (vLLM) | Not template-side |
| [`#1821`](https://github.com/QwenLM/Qwen3/issues/1821) | Tool args: spaces inserted between CJK and ASCII/digits | **wontfix** Apr 2026 |

## GitHub — `Blaizzy/mlx-vlm`

| Issue / PR | Title | Author | Supports |
|---|---|---|---|
| [`#1033`](https://github.com/Blaizzy/mlx-vlm/issues/1033) + [`#1034`](https://github.com/Blaizzy/mlx-vlm/issues/1034) | Gemma 4 chat template: assistant tool-call turn not closed → infinite tool-call loop | reza-yousefi | **G7** (reporter) |
| [`#943`](https://github.com/Blaizzy/mlx-vlm/issues/943) | Gemma 4 26b-a4b-4bit: vision produces garbage, text-only works | sanjay3290 | not template |
| [`#941`](https://github.com/Blaizzy/mlx-vlm/issues/941) | Gemma 4 outputs "No text generated" — models missing chat_template | nnorris7 | mlx-community quant gap |
| [`#988`](https://github.com/Blaizzy/mlx-vlm/issues/988) | broadcast_shapes error on Qwen3.5-397B-A17B vision — corrupts KV cache | trevorgordon981 | not template |
| [`#999`](https://github.com/Blaizzy/mlx-vlm/issues/999) | Server clears Metal cache after every request | trevorgordon981 | major perf bug |
| [`#1008`](https://github.com/Blaizzy/mlx-vlm/issues/1008) | mlx-community/gemma-4-31b-bf16 fails to describe image | jrp2014 | not template |
| [`#1011`](https://github.com/Blaizzy/mlx-vlm/issues/1011) | Gemma 4 loading fails on transformers 5.5.x (ReasoningEffort ImportError) | Glademist | install gap |
| [`#1022`](https://github.com/Blaizzy/mlx-vlm/issues/1022) | Gemma-4 mxfp8 missing per_layer_model_projection.scales | nightmedia | quant-side |
| Closed issues (Apr 2026): `#914`, `#915`, `#917`, `#962`, `#965`, `#997` | Various Gemma 4 fixes | — | confirms Apr-2026 stabilization wave |

## GitHub — `ml-explore/mlx-lm`

| Issue / PR | Title | Status | Notes |
|---|---|---|---|
| [`#829`](https://github.com/ml-explore/mlx-lm/pull/829) | server: support `chat_template_kwargs` and `top_logprobs` | **MERGED** Feb 3 2026 | foundational kwarg passthrough |
| [`#1114`](https://github.com/ml-explore/mlx-lm/pull/1114) | Gemma4 final fixes and multi-token think/tool start/end | **MERGED** Apr 6 by `angeloskath` | MLX analogue to llama.cpp #21704 + #21760 |
| [`#1030`](https://github.com/ml-explore/mlx-lm/issues/1030) | Per-request enable_thinking toggle in server | open, in-progress | analogue to llama.cpp #20297 |
| [`#1061`](https://github.com/ml-explore/mlx-lm/issues/1061) | Qwen3.5-35B-A3B-4bit malformed tool-call around 20k prompt tokens | open | long-context regression |
| [`#1065`](https://github.com/ml-explore/mlx-lm/issues/1065) | tool_calls.arguments dict-vs-string TypeError | open | same family as **R2** |
| [`#984`](https://github.com/ml-explore/mlx-lm/issues/984) | Tool calling not detected for multi-token delimiters | open | same family as #1114 |
| [`#1125`](https://github.com/ml-explore/mlx-lm/issues/1125) | Gemma 4 26b-a4b-it-4bit tool call failure | open | — |
| [`#905`](https://github.com/ml-explore/mlx-lm/issues/905) | mlx_lm.server failed in Qwen3.5 tools | open | — |
| [`#903`](https://github.com/ml-explore/mlx-lm/issues/903) | Qwen3.5 multi-turn cache reuse not working | open | same family as **R1** |
| [`#1163`](https://github.com/ml-explore/mlx-lm/issues/1163) | Auto-discover tool-call markers from tokenizer config | open Apr 18 | future generic fix |

## GitHub — `lmstudio-ai/mlx-engine`

| Issue / PR | Title | Status |
|---|---|---|
| [`#298`](https://github.com/lmstudio-ai/mlx-engine/pull/298) | Qwen 3.5 Unified | **MERGED** Mar 31 |
| [`#317`](https://github.com/lmstudio-ai/mlx-engine/pull/317) | Sync Qwen3.5 vision path with current mlx-vlm | **MERGED** Apr 20 |
| [`#285`](https://github.com/lmstudio-ai/mlx-engine/issues/285) | Wide perf discrepancy LM Studio MLX vs mlx_vlm.generate (Qwen3.5-35B-A3B) | open Mar 6 |
| [`#286`](https://github.com/lmstudio-ai/mlx-engine/issues/286) | KV cache quantization not supported for Qwen3.5 vision | open |
| [`#284`](https://github.com/lmstudio-ai/mlx-engine/issues/284) | `ValueError: Model type qwen3_5 not supported` | open Mar 3 |
| [`#314`](https://github.com/lmstudio-ai/mlx-engine/issues/314) | Multi-round inference OOM crash | open Apr 17 |
| [`#176`](https://github.com/lmstudio-ai/mlx-engine/issues/176) | Qwen3 cache wastage | open |
| [`#169`](https://github.com/lmstudio-ai/mlx-engine/issues/169) | Failed to parse Jinja template when using Qwen3 DWQ model | open since Jun 2025 |

## GitHub — `jundot/omlx`

| Issue / PR | Title | Status / Notes |
|---|---|---|
| [`#814`](https://github.com/jundot/omlx/pull/814) | preserve thinking across turns for Qwen 3.6+ incl. external clients (latent-variable) | **MERGED Apr 19 2026**. Cross-runtime support for **Q3.6-1** |
| [`#856`](https://github.com/jundot/omlx/pull/856) | Gate preserve_thinking auto-set on template detection | open follow-up |
| [`#857`](https://github.com/jundot/omlx/pull/857) | Pass reasoning_content as message field for native templates | open follow-up |
| [`#748`](https://github.com/jundot/omlx/pull/748) | (referenced) precedence model: per-request kwargs > model settings > auto-set > template default | — |
| [`#854`](https://github.com/jundot/omlx/issues/854) | Qwen3.6-35B-A3B-8bit + Hermes bug | open |
| [`#866`](https://github.com/jundot/omlx/issues/866) | Speculative decoding strips thinking tokens | open |
| [`#871`](https://github.com/jundot/omlx/issues/871) | `/v1/chat/completions` 500: `'dict object' has no attribute 'type'` | open chat-template render crash |
| [`#834`](https://github.com/jundot/omlx/issues/834) | Gemma-4-31B not supported in oMLX 0.36 | open |
| [`#839`](https://github.com/jundot/omlx/issues/839) | SSE `: keep-alive` comment lines break OpenClaw | open |

## GitHub — `unslothai/unsloth`

| Issue / PR | Title | Status |
|---|---|---|
| [`#4849`](https://github.com/unslothai/unsloth/issues/4849) | llama.cpp CUDA 13.2 gibberish for IQ3_S/IQ3_XXS/IQ2_M — use CUDA <13.0 or Unsloth Studio | **fixed** label; root-caused to cicc -O2 |
| [`#5107`](https://github.com/unslothai/unsloth/issues/5107) | Unable to change the chat template in studio | open Apr 19 2026 |

## GitHub — third-party (snapshotted)

| URL | Author | Snapshot | Supports |
|---|---|---|---|
| [`asf0/gemma4_jinja`](https://github.com/asf0/gemma4_jinja) | asfbrz96 | `docs/sources/github-snapshots/asf0-gemma4_jinja-chat_template.jinja` | **G2** |
| [`markqvist/lc/blob/master/lc/quirks/qwen35_tool_thoughts.py`](https://github.com/markqvist/lc/blob/master/lc/quirks/qwen35_tool_thoughts.py) | markqvist | `docs/sources/github-snapshots/markqvist-lc-qwen35_tool_thoughts.py` | client-side workaround for llama.cpp #20837 |
| [`allanchan339/vLLM-Qwen3.5-27B`](https://github.com/allanchan339/vLLM-Qwen3.5-27B) (`qwen3.5-enhanced.jinja`) | u/Expensive-Register-5 | `docs/sources/github-snapshots/allanchan339-vllm-qwen35-enhanced.jinja` | R5 reference (vLLM-only) |
| [`Addy-ad/AIstuff/tree/main/lms`](https://github.com/Addy-ad/AIstuff/tree/main/lms) | u/Addyad | not snapshotted (batch script, not a template) | LM Studio model.yaml batch generator |

## GitHub — community templates (HF)

| Repo | Status |
|---|---|
| [`barubary/qwen3.5-barubary-attuned-chat-template`](https://huggingface.co/barubary/qwen3.5-barubary-attuned-chat-template) | **401 Unauthorized at fetch time** (gated, private, or deleted). Snapshot pending. Source for catalog entries P6, P7, P8, P9, P10, R2 |

## Pastebins (snapshotted)

| URL | Author | Snapshot path | Supports |
|---|---|---|---|
| [`pastebin.com/raw/4wZPFui9`](https://pastebin.com/raw/4wZPFui9) | u/Substantial_Swan_144 | `docs/sources/pastebins/4wZPFui9-substantial_swan_144-qwen35-no_thinking.jinja` | **P5** original template |
| [`pastebin.com/raw/W9VxRw09`](https://pastebin.com/raw/W9VxRw09) | u/No_Information9314 | `docs/sources/pastebins/W9VxRw09-no_information9314-gemma4-enable_thinking.jinja` | **G4** original template |
| [`pastebin.com/raw/hnPGq0ht`](https://pastebin.com/raw/hnPGq0ht) | Sadman782 | `docs/sources/pastebins/hnPGq0ht-sadman782-gemma4-alt-template.jinja` | G3-adjacent Gemma 4 alt template |
| [`pastebin.com/raw/HDt34yA8`](https://pastebin.com/raw/HDt34yA8) | u/Gohab2001 | `docs/sources/pastebins/HDt34yA8-gohab2001-qwen35-model.yaml` | **G5** model.yaml example |

## Gists (snapshotted)

| URL | Author | Snapshot path | Supports |
|---|---|---|---|
| [`gist.github.com/aldehir/de036c259ecfe2571b9f1e573f9340e7`](https://gist.github.com/aldehir/de036c259ecfe2571b9f1e573f9340e7) | aldegr (GH `aldehir`) | `docs/sources/gists/aldehir-de036c259-gemma4-open-webui.jinja` | **G2** alt fix; cross-referenced from llama.cpp PR #21760 |
| [`gist.github.com/sudoingX/c2facf7d8f7608c65c1024ef3b22d431`](https://gist.github.com/sudoingX/c2facf7d8f7608c65c1024ef3b22d431) | sudoingX | `docs/sources/gists/sudoingX-c2facf7d-qwen35-27b-fixed.jinja` | parallel rediscovery of P10 + R1 |
| [`gist.github.com/lekoOwO/c6aed944a636abccfe2c3912be34b904`](https://gist.github.com/lekoOwO/c6aed944a636abccfe2c3912be34b904) | lekoOwO | `docs/sources/gists/lekoOwO-c6aed944-qwen35-fork.jinja` | fork of sudoingX |

## Standards / external docs

| URL | Topic |
|---|---|
| [Z.ai thinking-mode docs](https://docs.z.ai/guides/capabilities/thinking-mode) | Canonical interleaved-vs-preserved-thinking taxonomy (referenced in **Q3.6-1** background) |
| [LM Studio model.yaml docs](https://lmstudio.ai/docs/app/modelyaml) | LM Studio config-side template overrides (**G5** mechanism) |

## Index of contributors (alphabetical)

Names of authors / reporters cited from at least one source above:

aldegr (GH `aldehir`), allanchan339, asfbrz96, Addyad, barubary, berkidem,
CMay, deladuck, deven367, Dopey24, Evita, ex-arman68, fairydreaming,
FastHotEmu, froggeric, Galunid, gelim, Giant-Space-Bee, Glademist, Gohab2001,
Goulustis, grapevine-AI, jrp2014, jpohhhh / jpohhhhh, Jacksao1970,
kik4444, lacerbi, latent-variable, lekoOwO, lucksufe, manfred_exz,
markqvist, mlhher, NatTuck, nightmedia, nnorris7, No_Information9314,
notdba, onil_gova, pwilkin, Reaper_9382, RealChaoz, reza-yousefi, rkuovc,
Sadman782, sanjay3290, Substantial_Swan_144, sudoingX, taronaeo, tha80,
TomTheWise, TrevorS, trevorgordon981, trshimizu, Whamp, will-lms,
WyattTheSkid, ZUIcat, Zealousideal_Lie_850.

If you are listed and would like a different attribution form (real name,
org affiliation, removal), open an issue or PR.
