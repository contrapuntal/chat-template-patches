# Patch catalog

Master table of every patch maintained in this repo. For a flat-index bibliography of every Reddit thread, GitHub issue/PR, and HF discussion cited below, see [`REFERENCES.md`](REFERENCES.md).

**Status legend:**

- **active** — applied in our `patched/` set; bug is current and unresolved upstream.
- **upstream** — fix has been merged by the model authors or shipped in canonical community quants. Catalog entry kept for historical record and as a regression sentinel.
- **historical** — applied to an older template revision; the affected code path no longer exists in current upstream.
- **opt-in** — patch is correct but only applies in specific environments (e.g., LM Studio's minijinja); not in the default `patched/` set.

**Provenance tier legend** (durability of the source the patch traces to):

- **publisher** — model author published the fix or the bug acknowledgment in their own repo / docs / release notes.
- **upstream-tracker** — bug or fix is in a long-lived public issue/PR tracker (HF discussions on the publisher's repo, llama.cpp / mlx-vlm GitHub, etc.). Survives even if the original poster's account goes away.
- **community-tracker** — third-party GitHub repo, gist, or HF community repo. Account-state-dependent, but git history persists. **Snapshotted in `docs/sources/`** where applicable.
- **community-ephemeral** — Reddit thread, pastebin, or other host that can lock/expire/delete with no recovery. **Snapshotted in `docs/sources/`** where applicable.
- **derived** — original analysis by this repo, no external prior art beyond a bug report.

| ID | Family | One-liner | Status | Provenance tier | Applies to |
|---|---|---|---|---|---|
| P1 | Qwen3.5 | Replace `raise_exception('No user query found')` with safe fallback | **active** | derived (prior art: barubary, community-tracker — snapshot pending; HF repo 401 at fetch time) | All Qwen3.5 sizes |
| P2 | Qwen3.5 | `tool_call.arguments is mapping` guard (was `is defined`) | **upstream** (unsloth Mar 2026) | publisher | All non-unsloth Qwen3.5 GGUFs |
| P3 | Qwen3.5 | Flip `enable_thinking` polarity on small models | **active** (partial upstream — fixed in 4B/9B as of Mar 2026; broken in 0.8B/2B) | publisher (the polarity diff is observable across publisher templates) | Qwen3.5-0.8B, -2B |
| P4 | Multi | Replace ` \| safe` with spaces (minijinja) | **opt-in** (LM Studio only) | derived | Qwen3.5 + Step-3.5-Flash + any model with `\| tojson \| safe` |
| P5 | Qwen3.5 | Inject `/no_thinking` system-message detector | **opt-in** (replaced by `--reasoning off` in current llama.cpp) | community-ephemeral (Reddit + pastebin; **snapshotted** at `docs/sources/pastebins/4wZPFui9-...jinja`) | All Qwen3.5 |
| P6 | Qwen3.5 | Parallel tool-call separator `\n\n` | **active** | community-tracker (barubary HF repo 401 at fetch time; parallel rediscoveries in `docs/sources/gists/`) | All Qwen3.5 |
| P7 | Qwen3.5 | Auto-disable thinking when tools are present | **active** | community-tracker (barubary HF repo 401 at fetch time) | All Qwen3.5 |
| P8 | Qwen3.5 | Streaming-safe trailing `\n` after `</tool_call>` | **active** | community-tracker (barubary HF repo 401 at fetch time) | All Qwen3.5 |
| P9 | Qwen3.5 | Empty `<think>` history alignment with current turn | **active** | community-tracker (barubary HF repo 401 at fetch time) | All Qwen3.5 |
| P10 | Qwen3.5 | Developer role + unknown role fallback | **active** | community-tracker (barubary HF repo 401 at fetch time; parallel rediscoveries snapshotted in `docs/sources/gists/sudoingX-...` and `lekoOwO-...`) | All Qwen3.5 |
| R1 | Qwen3.5 | `and reasoning_content` guard on history `<think>` emission | **upstream — ready to merge** (per-size HF PRs by latent-variable open) | upstream-tracker (HF discussion threads on publisher repos) | All Qwen3.5 |
| R2 | Qwen3.5 | String-argument tool-call passthrough | **active** | community-tracker (barubary HF repo 401 at fetch time) | All Qwen3.5 |
| R3 | Qwen3.5 | P5 sentinel hardening (`<\|think_off\|>`) + `ns_flags` simplification | **active** (revision of P5) | community-ephemeral (Reddit thread comments) | All Qwen3.5 |
| Q3.6-1 | Qwen3.6 | `preserve_thinking` default-on flip | **active** (LM Studio MLX path); **upstream-equivalent** in oMLX (auto-set server-side) | derived (bug report: community-ephemeral Reddit; cross-runtime fix at upstream-tracker `jundot/omlx#814`) | Qwen3.6-35B-A3B |
| G1 | Gemma 4 | Replace `is sequence` test with portable iterable check | **opt-in** (LM Studio MCP path only) | community-ephemeral (Reddit thread) | Gemma 4 26B-A4B-it, 31B-it |
| G2 | Gemma 4 | Suppress `<\|channel>thought` token leakage in clients that don't consume reasoning channels | **historical** (superseded by G3 upstream + G7 here) | community-tracker (asfbrz96 GitHub repo + aldegr gist; both **snapshotted** at `docs/sources/github-snapshots/asf0-...` and `docs/sources/gists/aldehir-...`) | Gemma 4 26B-A4B-it (Apr-pre-update template) |
| G3 | Gemma 4 | Apr 2026 official template realignment | **upstream** (Google HF + llama.cpp #21704 #21760) | publisher | Gemma 4 26B-A4B-it, 31B-it |
| G4 | Gemma 4 | `ENABLE_THINKING` / `DISABLE_THINKING` system-message sentinel | **opt-in** | community-ephemeral (Reddit + pastebin; **snapshotted** at `docs/sources/pastebins/W9VxRw09-...jinja`) | Gemma 4 26B-A4B-it, 31B-it |
| G5 | Gemma 4 | LM Studio thinking-toggle `model.yaml` workaround | **active** (config-side, not a template patch) | community-ephemeral (Reddit; example yaml **snapshotted** at `docs/sources/pastebins/HDt34yA8-...yaml`) | Gemma 4 (LM Studio non-community quants) |
| G6 | Gemma 4 | Tool-calling / system-prompt compliance grab-bag | **active** (open upstream; configuration recommendations rather than a discrete template patch) | community-ephemeral (multiple Reddit threads) | Gemma 4 26B-A4B-it primarily |
| G7 | Gemma 4 | Empty-content tool-call assistant turn closure | **active** | derived (bug report: upstream-tracker `Blaizzy/mlx-vlm#1033` + `#1034`) | Gemma 4 26B-A4B-it, 31B-it, E2B-it, E4B-it |

---

## Detailed entries

### P1 — Agentic no-user-query crash fallback

**Target:** All Qwen3.5 sizes.

**Failure mode.** Upstream template raises:
```
raise_exception('No user query found in messages.')
```
when conversation history is truncated to remove all `role: "user"` messages
(common in long agentic loops where only system + assistant + tool messages
remain in context).

**Fix.** Replace the raise with `{%- set ns.last_query_index = 0 %}` so the
template falls through to render the (system + assistant + tool) prefix
gracefully.

**Prior art.** Discovered locally; barubary's Fix 17 proposes a more nuanced
variant that uses `_last_idx if _last_idx > 50 else 0` — see `R4` (not
implemented; deferred until a deep-loop edge case is observed).

**Verification fixture.** `tests/fixtures/qwen35_no_user.json` — a
conversation with system + assistant + tool messages but no user message.
Upstream raises; patched renders.

---

### P2 — Tool-calling argument type guard

**Target:** Qwen3.5 GGUFs from publishers other than unsloth (unsloth's Mar
2026 update applied this fix).

**Failure mode.** Iterating `tool_call.arguments` assuming it's a `dict`
crashes when an OpenAI-compat client sends `arguments` as a JSON string.

**Fix.** Change the type guard from `tool_call.arguments is defined` to
`tool_call.arguments is mapping`. **Crash-safety only** — the corresponding
correctness fix that emits the string-form arguments is `R2`.

**Verification fixture.** `tests/fixtures/qwen35_string_args_tool.json`.

---

### P3 — Enable thinking on small models (polarity flip)

**Target:** Qwen3.5-0.8B, Qwen3.5-2B (Qwen3.5-4B and -9B were fixed upstream
in Mar 2026; verify per-quant before applying).

**Failure mode.** Small models historically used `enable_thinking is true`
(opt-in), so unless the inference engine passes the kwarg, thinking never
fires. Large models use `enable_thinking is false` (opt-out, default ON).

**Fix.** Flip the polarity to match the large-model convention so thinking
defaults ON without requiring kwarg passthrough.

**Caveat.** Upstream templates shift over time — verify the small-model
template still has the broken polarity before re-applying.

---

### P4 — Remove `| safe` filter (minijinja crash)

**Target:** Any model whose template uses `| tojson | safe` (Qwen3.5,
Step-3.5-Flash, others).

**Failure mode.** LM Studio's minijinja rejects `| safe` with
`Unknown StringValue filter: safe`. The filter is a no-op outside HTML
auto-escaping contexts, so removal is semantically safe.

**Fix.** Replace `| safe` with spaces (preserves byte length when applied as
an in-place GGUF mmap edit).

**Status: opt-in.** Upstream `jinja2` accepts `| safe`; this patch is only
needed for minijinja-based runtimes (LM Studio).

---

### P5 — `/no_thinking` system message toggle

**Target:** All Qwen3.5 sizes — for the LM Studio runtime that historically
lacked a working `chat_template_kwargs` passthrough.

**Failure mode.** No way to toggle thinking per-request without reloading the
model.

**Fix.** Inject a detector that scans the system message for `/no_thinking`
and sets `enable_thinking = false`. See `R3` for the hardened sentinel form.

**Status: opt-in.** Modern llama.cpp's `--reasoning on/off` flag (PR #20297,
merged Mar 2026) makes this unnecessary. Kept for users on older builds.

**Original author.** u/Substantial_Swan_144, r/LocalLLaMA, Nov 2025.

---

### P6 — Parallel tool-call separation

**Target:** All Qwen3.5.

**Failure mode.** Multiple `<tool_call>` blocks in one assistant turn are
separated by a single `\n` instead of `\n\n`. Some XML parsers concatenate
them and miss the second call.

**Fix.** Change `'\n<tool_call>'` to `'\n\n<tool_call>'` in the non-first
tool-call branch.

**Prior art.** barubary's Fix 15.

---

### P7 — Auto-disable thinking when tools are present

**Target:** All Qwen3.5.

**Failure mode.** When tools are defined, Qwen3.5 sometimes leaks
`<tool_call>` blocks inside `<think>` blocks, breaking tool-call parsers and
causing infinite loops in regex-based parsers.

**Fix.** Insert
```jinja
{%- if tools is defined and tools %}{%- set enable_thinking = false %}{%- endif %}
```
before the generation prompt block.

**Prior art.** barubary's Fix 19.

---

### P8 — Streaming-safe tool-call closing

**Target:** All Qwen3.5.

**Fix.** Add a trailing `\n` after `</tool_call>` so streaming XML parsers
that detect block boundaries on newline can finalize the tool call without
waiting for additional data.

**Prior art.** barubary's Fix 18.

---

### P9 — KV-cache thinking alignment (disabled-thinking path)

**Target:** All Qwen3.5.

**Failure mode.** When thinking is disabled, historical assistant turns
render without `<think></think>` markers while the current generation prompt
emits empty markers. Same assistant turn tokenizes differently as history vs
current → prefix-cache misses on every subsequent turn.

**Fix.** Add an inner `enable_thinking` check in the history-turn branch so
the empty `<think>\n\n</think>` wrapper is emitted symmetrically.

**Prior art.** barubary's Fix 12.

**Relationship to R1.** P9 fixes the **thinking-disabled** path; R1 fixes the
**thinking-enabled** path (when `reasoning_content` is empty). Apply both for
full symmetry.

---

### P10 — Developer role + unknown role fallback

**Target:** All Qwen3.5.

**Failure mode.** Stock template crashes on unknown roles via
`raise_exception('Unexpected message role.')`. Modern agentic clients
(Claude Code, Codex, OpenCode, Aider) commonly send `role: "developer"`.

**Fix.** Replace the raise with a two-tier fallback:
- `developer` → render as `system`
- everything else → render as `user`

**Prior art.** barubary's Fixes 3 + 20. Independently rediscovered by
sudoingX (Mar 2026) and lekoOwO (Apr 2026) gists.

---

### R1 — Empty-`<think>` cache-reuse guard

**Target:** All Qwen3.5.

**Failure mode.** In the history branch, the stock template emits
`<think>\n\n</think>` wrappers even when `reasoning_content` is empty.
The same assistant turn serializes differently as "current" vs "historical"
→ zero prefix-cache hits → full cold prefill on every follow-up turn after
a tool call. ~25× TTFT regression measured on Qwen3.5-35B-A3B turn-2+ by
Giant-Space-Bee (QwenLM/Qwen3 issue #1826).

**Fix (minimal).** Add `and reasoning_content` to the existing guard:
```
Old: {%- if loop.index0 > ns.last_query_index %}
New: {%- if loop.index0 > ns.last_query_index and reasoning_content %}
```

**Status.** **Ready to merge upstream.** latent-variable opened the same PR
on every Qwen3.5 size — see `huggingface.co/Qwen/Qwen3.5-*/discussions/...`.
Author tested a stricter "remove historical `<think>` entirely" variant and
explicitly reverted to this safer minimal form.

**Prior art.** latent-variable (HF PRs); related GitHub issues
QwenLM/Qwen3#1826 (Giant-Space-Bee, with TTFT benchmark) and #1831.

**Scope caveat.** R1 only kicks in when `loop.index0 > ns.last_query_index`,
i.e., the **multi-step tool scenario** (assistant issued a tool_call → tool
response came back → same assistant turn re-rendered as "current" without a
new user message). Plain conversational multi-turn chat never hits this
branch. The 25× TTFT speedup is real for **agent loops**, not vanilla chat.

---

### R2 — Tool-call string-argument passthrough

**Target:** All Qwen3.5. **Apply with P2** (P2 alone is crash-safety only —
arguments are silently dropped).

**Failure mode.** P2's `is mapping` guard prevents the crash but **silently
drops** tool-call arguments when the client sends them as a pre-serialized
JSON string. The whole tool-call render block is skipped → history forgets
the tool was called with any particular input.

**Fix.** Add an `elif tc.arguments is string` branch that passes the string
through verbatim.

**Prior art.** barubary's Fix 9.

---

### R3 — P5 sentinel hardening + `ns_flags` simplification

**Target:** All Qwen3.5 (revision of P5).

**Failure mode.** P5's `'/no_thinking' in sys_text_check` substring match
fires on any literal occurrence — including documentation excerpts, file
paths (`/proj/no_thinking/`), or tool outputs referenced in the system
prompt. Thinking silently flips off unexpectedly.

**Fix (combined).**
1. Switch to a delimited sentinel that cannot appear in normal content:
   `<|think_off|>` (matches Qwen's delimited-tag convention).
2. Drop the `ns_flags` namespace and set `enable_thinking` directly inside
   the inner `if` block (saves bytes, no semantic change).

**Breaking change.** Users with existing `/no_thinking` in system prompts
must update.

**Prior art.** Sentinel discussion: u/ex-arman68 in r/LocalLLaMA
"definitive" thread. `ns_flags` simplification: u/Zealousideal_Lie_850 on
the original P5 thread.

---

### Q3.6-1 — Qwen3.6 `preserve_thinking` default-on flip

**Target:** Qwen3.6-35B-A3B (and any future Qwen3.6 sizes that ship with the
same template).

**Failure mode.** Qwen3.6's chat template line 103:
```jinja
{%- if (preserve_thinking is defined and preserve_thinking is true) or (loop.index0 > ns.last_query_index) %}
```
defaults `preserve_thinking` to OFF. When the kwarg is undefined, the
template falls through to the same cache-thrashing path that Qwen3.5
exhibited (R1). Qwen explicitly recommends `preserve_thinking=true` for
agentic flows; the model card itself documents this.

**Fix.** Flip the default polarity so the patch behaves correctly when no
kwarg is passed:
```
Old: (preserve_thinking is defined and preserve_thinking is true)
New: (preserve_thinking is not defined or preserve_thinking is not false)
```

**Cross-runtime status.**
- **oMLX** (`jundot/omlx`): auto-sets `preserve_thinking=True` server-side via
  PR #814 (merged Apr 2026). **No template patch needed for oMLX users.**
- **LM Studio MLX, mlx-lm server, llama.cpp, raw `apply_chat_template`
  callers**: kwarg is not auto-set. **Apply this patch.**

**Caveat.** Qwen3.6's template *also* still emits `<think>\n\n</think>` empty
wrappers in history when `reasoning_content` is empty (the R1 family-wide
bug). Patching `preserve_thinking` doesn't fix that — applying R1's
`and reasoning_content` guard on top is recommended for the cleanest cache
reuse.

**Attribution.**
- *Reporter:* u/onil_gova (Reddit) — r/LocalLLaMA *"PSA: Qwen3.6 ships
  with preserve_thinking. Make sure you have it on."* (Apr 2026, ~387
  upvotes). Documents the publisher recommendation and the
  default-OFF behaviour.
- *Fix author:* original to this repo. Mechanical polarity flip on the
  publisher-provided `preserve_thinking` kwarg gate.
- *Template author:* Alibaba Cloud / Qwen Team (Qwen3.6 chat template).
- *Provenance tier:* derived (bug report is community-ephemeral; the
  cross-runtime fix at `jundot/omlx#814` by latent-variable is on a
  durable upstream tracker — see "Cross-runtime status" above).

---

### G1 — Gemma 4 `is sequence` minijinja crash

**Target:** Gemma 4 26B-A4B-it, 31B-it. **LM Studio MCP path only.**

**Failure mode.** Google's official Gemma 4 template uses `argument is sequence`
in the `format_argument` macro. LM Studio's minijinja doesn't implement the
`sequence` test → `Error rendering prompt with jinja template: "Unknown
test: sequence"` → all MCP tool calls fail.

**Fix.** Replace with portable predicates:
```
Old: {%- elif argument is sequence -%}
New: {%- elif argument is iterable and argument is not string and argument is not mapping -%}
```

**Status: opt-in.** Standard `jinja2` accepts `is sequence`; this patch is
only required for minijinja-based runtimes.

**Prior art.** u/Reaper_9382, r/LocalLLaMA, Apr 2026.

---

### G2 — `<|channel>thought` token leakage (historical)

**Target:** Gemma 4 26B-A4B-it, pre-Apr-2026 template.

**Failure mode.** Pre-update template assumed the serving stack consumed
`<|channel>thought` reasoning tokens server-side. Stacks that didn't (e.g.,
llama.cpp + OpenWebUI) leaked the tokens into visible output.

**Status: historical.** G3 (Google's Apr-2026 template update) supersedes
this. Kept for context. The new G7 patch addresses a different empty-content
edge case in the post-G3 template.

**Prior art.** Independent fixes by asfbrz96 (`github.com/asf0/gemma4_jinja`)
and aldegr (gist + `llama.cpp` PRs #21704, #21760).

---

### G3 — Gemma 4 Apr-2026 official template realignment

**Status: upstream — done.** This is a synchronization marker, not a patch
this repo applies. Documented because:

- The current `templates/gemma4/upstream/*` reflect this update — they were
  fetched after Google's HF commit `e51e7dc` and after llama.cpp PRs #21704
  and #21760 landed.
- Several patch entries (G1, G7, G6) reference *post-G3* template state.
  Don't apply this catalog's patches against pre-G3 templates without
  re-validating the line anchors.

**Authoring lineage.** Google (HF commit `e51e7dc`); aldegr aligned the
llama.cpp internal workarounds in PRs #21704 (template detection) and
#21760 (Gemma-4-26B-A4B parser edge cases).

---

### G4 — Gemma 4 ENABLE_THINKING / DISABLE_THINKING system-message sentinel

**Target:** Gemma 4 26B-A4B-it, 31B-it.

**Failure mode.** Google's template enables thinking when the system prompt
*starts with* the literal `<|think|>` token. Not toggleable per-request via
the OpenAI-compat API without rebuilding the request body. Users report
inconsistency with `chat_template_kwargs={"enable_thinking": ...}`
passthrough.

**Fix.** Defaults thinking OFF; scans the system message for sentinel
strings and flips `enable_thinking` accordingly:
- `ENABLE_THINKING` → enable
- `DISABLE_THINKING` → disable (also strips the sentinel from rendered
  output)

**Status: opt-in.** Use only if your client doesn't reliably pass
`chat_template_kwargs` and you want a one-off escape hatch via system text.

**Prior art.** u/No_Information9314, r/LocalLLaMA, Apr 2026.

---

### G5 — LM Studio thinking-toggle `model.yaml` workaround

**Target:** Gemma 4 in LM Studio when using non-community quants.

**Mechanism.** Author a `model.yaml` under
`~/.lmstudio/hub/models/<publisher>/<model>/` that exposes `enableThinking`
as a `customField` with `setJinjaVariable enable_thinking`.

**Status: active configuration workaround.** Not a template patch — kept in
the catalog so the index of "Gemma 4 thinking-toggle solutions" is complete.

---

### G6 — Tool-calling and system-prompt compliance grab-bag

**Target:** Gemma 4 26B-A4B-it primarily.

**Status: active, open upstream.** The Gemma 4 26B-A4B variant has reported
issues following system prompts and reliably calling tools, regardless of
template state. Recommendations rather than a discrete patch:

- Update llama.cpp to ≥ b8243 for the `common_chat_peg_parse` UTF-8 fix
  (PR #20191) and ≥ commit 59d8402 for the grammar-trigger-during-thinking
  fix (PR #20970).
- Re-pull GGUFs from a publisher who has rebuilt against the current
  llama.cpp (Apr 2026 or later).
- Use the `models/templates/google-gemma-4-31B-it-interleaved.jinja`
  internal template if the Apr-2026 official template hasn't propagated to
  your quant yet.
- The 31B variant follows system prompts more reliably than 26B-A4B based on
  multiple community reports.

---

### G7 — Empty-content tool-call assistant turn closure

**Target:** Gemma 4 26B-A4B-it, 31B-it, E2B-it, E4B-it.

**Failure mode.** When an assistant message contains tool calls (with
matching `tool_responses` flagged) AND `content` is the empty string, the
template's close-marker conditional evaluates:
```jinja
{%- elif not (ns_tr_out.flag and not message.get('content')) -%}
    {{- '<turn|>\n' -}}
{%- endif -%}
```
to `not (true and true)` → `false` → the `<turn|>` close marker is
**suppressed**. The next assistant turn opens without a turn boundary, and
the model interprets this as "continue the previous assistant turn" → emits
another tool call → **infinite tool-call loop**.

**Fix.** Replace the suppress-on-empty-content elif with an unconditional
`else` so the close marker is emitted whenever the special tool_call/no-flag
branch above isn't taken:
```
Old: {%- elif not (ns_tr_out.flag and not message.get('content')) -%}
New: {%- else -%}
```

This is stronger than dropping just the `and not message.get('content')`
clause — testing showed that the narrower fix (`not ns_tr_out.flag`) still
suppresses the close marker when `ns_tr_out.flag` is true, which is the
actual failure path. The `else` form always emits the close on the
content/tool-response branch and leaves the upstream `<|tool_response>`
emission on the pure-tool-call branch unchanged.

**Verification fixture.**
`tests/fixtures/gemma4_empty_content_tool_call.json` — an assistant message
with `tool_calls` + matching `tool_responses` + empty `content`. Upstream
render is missing the `<turn|>` marker between this turn and the next
prompt; patched render contains it.

**Attribution.**
- *Reporter:* reza-yousefi (GitHub) — `Blaizzy/mlx-vlm#1033` + `#1034`
  (duplicates), Apr 17 2026. Reported the failure mode; no fix included.
- *Fix author:* original to this repo. Derived by inspecting the
  template's branch logic and verified by render harness fixture.
- *Template author:* Google LLC (Gemma 4 chat template).
- *Provenance tier:* derived (bug report itself sits in a durable
  upstream tracker — GitHub).
- *Upstream status:* open as of fetch date; this patch predates any
  upstream resolution.
