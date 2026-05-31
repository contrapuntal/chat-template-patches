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
| P11 | Qwen3.5 | Auto-close unclosed `<think>` before `<tool_call>` | **deferred** (Qwen3.5 patched/ empty; ship alongside other Qwen3.5 patches) | community-tracker (allanchan339 — Qwen3.6 originator; not yet ported back to Qwen3.5) | All Qwen3.5 (only when P7 not also applied — P7 prevents this failure mode entirely by disabling thinking when tools defined) |
| P12 | Qwen3.5 | Remove Python-only `\|items` filter from tool-call argument iteration | **deferred** (Qwen3.5 patched/ empty) | derived (verified by inspection of `templates/qwen3.5/upstream/35B-A3B.jinja` line 120) | All Qwen3.5 — minijinja and other C++-runtime Jinja implementations that don't support the `\|items` filter (Qwen3.6 doesn't use it; only Qwen3.5 affected) |
| Q3.6-1 | Qwen3.6 | `preserve_thinking` default-on flip | **active** (LM Studio MLX path); **upstream-equivalent** in oMLX (auto-set server-side) | derived (bug report: community-ephemeral Reddit; cross-runtime fix at upstream-tracker `jundot/omlx#814`) | Qwen3.6-35B-A3B |
| Q3.6-2 | Qwen3.6 | `and reasoning_content` guard on history `<think>` emission (R1 port; stacks on Q3.6-1) | **active** | upstream-tracker (HF discussion threads on Qwen3.5 publisher repos by latent-variable, applied analogously to Qwen3.6) | Qwen3.6-35B-A3B |
| Q3.6-3 | Qwen3.6 | Auto-close unclosed `<think>` before `<tool_call>` + recognize `</thinking>` hallucination as valid close (stacks on Q3.6-2) | **active** | community-tracker (allanchan339 GH for auto-close + froggeric HF for `</thinking>` recognition; merged form by fakezeta in r/LocalLLaMA `1t4cev0` — all three **snapshotted** in `docs/sources/`) | Qwen3.6-35B-A3B |
| Q3.6-4 | Qwen3.6 | Tool-call string-argument passthrough (R2 port; stacks on Q3.6-3) | **active** | community-tracker (barubary's Fix 9 for Qwen3.5; same pattern applied to Qwen3.6) | Qwen3.6-35B-A3B |
| Q3.6-5 | Qwen3.6 | `<\|think_off\|>` / `<\|think_on\|>` system-message sentinels for per-request thinking-mode control (R3 port + `think_on` extension; stacks on Q3.6-4) | **opt-in** (only relevant when the runtime doesn't reliably pass `chat_template_kwargs={"enable_thinking": ...}`) | community-tracker (R3 base from u/ex-arman68 r/LocalLLaMA "definitive" thread + `<\|think_on\|>` companion from froggeric **snapshotted** at `docs/sources/hf-snapshots/froggeric-Qwen-Fixed-Chat-Templates-qwen36-*.jinja`) | Qwen3.6-35B-A3B |
| Q3.6-6 | Qwen3.6 | Unwrap OpenAI tool-**definition** envelope (`{"type":"function","function":{...}}`) to the inner function spec at the `<tools>` site (stacks on Q3.6-5) | **active** | derived (mirrors the unwrap the same template already does at the tool-**call** site; prior art: jscott3201 gist **snapshotted** + Qwen3-Coder-Next publisher convention) | Qwen3.6-35B-A3B |
| Q3.6-7 | Qwen3.6 | Strengthened `<IMPORTANT>` tool-call instructions (+3 bullets: don't-omit-`<tool_call>`, no-indentation, no-nesting) | **opt-in** (in-prompt instruction text, not render-verifiable; ships a `.patch` but is **not** in the default `patched/` set) | community-tracker (jscott3201 gist **snapshotted**; cites QwenLM/Qwen3-Coder#475 + block/goose#6883) | Qwen3.6-35B-A3B |
| G1 | Gemma 4 | Replace `is sequence` test with portable iterable check | **opt-in** (LM Studio MCP path only) | community-ephemeral (Reddit thread) | Gemma 4 26B-A4B-it, 31B-it |
| G2 | Gemma 4 | Suppress `<\|channel>thought` token leakage in clients that don't consume reasoning channels | **historical** (superseded by G3 upstream + G7 here) | community-tracker (asfbrz96 GitHub repo + aldegr gist; both **snapshotted** at `docs/sources/github-snapshots/asf0-...` and `docs/sources/gists/aldehir-...`) | Gemma 4 26B-A4B-it (Apr-pre-update template) |
| G3 | Gemma 4 | Apr 2026 official template realignment | **upstream** (Google HF + llama.cpp #21704 #21760) | publisher | Gemma 4 26B-A4B-it, 31B-it |
| G4 | Gemma 4 | `ENABLE_THINKING` / `DISABLE_THINKING` system-message sentinel | **opt-in** | community-ephemeral (Reddit + pastebin; **snapshotted** at `docs/sources/pastebins/W9VxRw09-...jinja`) | Gemma 4 26B-A4B-it, 31B-it |
| G5 | Gemma 4 | LM Studio thinking-toggle `model.yaml` workaround | **active** (config-side, not a template patch) | community-ephemeral (Reddit; example yaml **snapshotted** at `docs/sources/pastebins/HDt34yA8-...yaml`) | Gemma 4 (LM Studio non-community quants) |
| G6 | Gemma 4 | Tool-calling / system-prompt compliance grab-bag | **active** (open upstream; configuration recommendations rather than a discrete template patch) | community-ephemeral (multiple Reddit threads) | Gemma 4 26B-A4B-it primarily |
| G7 | Gemma 4 | Empty-content tool-call assistant turn closure | **active** | derived (bug report: upstream-tracker `Blaizzy/mlx-vlm#1033` + `#1034`) | Gemma 4 26B-A4B-it, 31B-it, E2B-it, E4B-it |
| G8 | Gemma 4 | JSON Schema robustness in tool declarations (`anyOf`/`oneOf`/`allOf`/`$ref`/`$defs`/`enum`/`const`/array-type) | **opt-in** (pending upstream merge — HF disc #91) | community-tracker (HF discussion + Reddit; **snapshotted** at `docs/sources/pastebins/tBAHN6FV-sigjhl-...jinja`) | Gemma 4 26B-A4B-it, 31B-it, E2B-it, E4B-it |
| G9 | Gemma 4 | Balance turn open/close for consecutive assistant messages — the open-suppression (`continue_same_model_turn`) left an orphaned `<turn\|>` close; G9 adds the symmetric forward-scan to defer the prior message's close | **active** | upstream-tracker (HF `google/gemma-4-31B-it` disc #62, Google-reproduced + OPEN; **reproduced locally**) | Gemma 4 26B-A4B-it, 31B-it, E2B-it, E4B-it |

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

### P11 — Auto-close unclosed `<think>` before `<tool_call>` (Qwen3.5)

**Target:** All Qwen3.5 sizes — but only when **P7 is NOT applied**. P7
already disables thinking entirely when tools are defined, which makes the
unclosed-`<think>` scenario unreachable. P11 is the recovery path for
deployments that want both thinking AND tools (i.e., they didn't apply P7).

**Status: deferred.** No Qwen3.5 patched template currently ships in this
repo (`qwen3.5` is in `tests/conftest.py:CATALOG_ONLY_FAMILIES`). Ship
alongside the rest of the Qwen3.5 patch series.

**Failure mode.** Model emits `<think>...` then a tool call without first
closing the think block. Downstream parsers see the `<tool_call>` inside
the unclosed think and either ignore it (no tool execution) or wrap the
tool block in reasoning_content.

**Fix.** In the assistant-render branch, if both `<think>` and `<tool_call>`
appear in `content` and the last `</think>` precedes the last `<think>`,
inject `</think>` before the tool-call boundary. See **Q3.6-3** for the
shipped Qwen3.6 form (which generalizes the rfind to also handle the
`</thinking>` hallucination case).

**Prior art.** Originated by allanchan339 in `qwen3.6-enhanced.jinja`
commit `13556c0`, 2026-05-02 (Qwen3.6 only). Not currently in any
Qwen3.5 community template — proposed P11 is the back-port.

---

### P12 — Remove Python-only `|items` filter from Qwen3.5 tool-call args

**Target:** All Qwen3.5 — minijinja and other C++ Jinja implementations
that don't ship the `|items` filter.

**Status: deferred.** No Qwen3.5 patched template currently ships in this
repo. Ship alongside the rest of the Qwen3.5 patch series.

**Failure mode.** Qwen3.5 upstream `templates/qwen3.5/upstream/*.jinja`
line 120 reads:
```jinja
{%- for args_name, args_value in tool_call.arguments|items %}
```
The `|items` filter does not exist in standard Jinja (it's a Python-only
extension exposed by some `transformers` integrations). minijinja, vLLM's
template engine when running through certain configs, and other C++
runtimes throw `Unknown filter: items`.

**Fix.** Replace the two-variable form with a key-iteration that looks up
the value, as done in Qwen3.6 upstream (line 123):
```
Old: {%- for args_name, args_value in tool_call.arguments|items %}
New: {%- for args_name in tool_call.arguments %}
         {%- set args_value = tool_call.arguments[args_name] %}
```

**Note.** Qwen3.6 upstream does NOT use `|items` (it already uses the
key-iteration form), so this patch is Qwen3.5-only. froggeric's Fix #1
("Tool Calls on C++ Engines") observes the same issue for Qwen3.5 and
applies the same fix.

**Prior art.** froggeric's `qwen3.5/chat_template.jinja` (HF
`Qwen-Fixed-Chat-Templates`, **snapshotted** at
`docs/sources/hf-snapshots/froggeric-Qwen-Fixed-Chat-Templates-qwen35.jinja`).

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

**Field reports.** Community signal on `preserve_thinking: true` for Qwen3.6
is mixed — the polarity flip is the right default, but it does **not**
eliminate Qwen3.6's separate tool-calling instability:

- **u/Expensive-Register-5** (r/LocalLLM `1sqpsut`, Apr 2026): tested
  `--default-chat-template-kwargs '{"preserve_thinking": true}'` against
  `Qwen3.6-35B-A3B-FP8` on vLLM during a $10k-token agentic coding run.
  Verdict: *"toggled preserve_thinking on to see if tool calling problem
  fixed, doesnt work"*. Run with the 3.5-derived `qwen3.5-enhanced.jinja`
  template + `qwen3_xml` parser still died at ~111K tokens with malformed
  tool calls. **Implication:** Q3.6-1 is necessary but not sufficient for
  agentic stability — separate runtime/parser issues compound on top.
- **u/sb6_6_6_6** (same thread): *"had loops around 174k context adding
  --default-chat-template-kwargs '{"preserve_thinking": true}' - did
  help"*. Confirms the polarity flip is correct for the failure mode it
  targets (long-context cache thrashing).
- **u/Wise-Hunt7815** (same thread): *"'preserve_thinking' doesn't seem
  to work. I tested it: guessing numbers, and in its response, the secret
  number in the thought chain kept changing"*. **Open question:** whether
  this is a separate `reasoning_content`-vs-`<think>`-wrapper accounting
  bug downstream of the kwarg, or an artifact of the user's specific
  client. Not currently in scope for Q3.6-1.

These contradictory data points reinforce that Q3.6-1 is a polarity fix
on a single template branch — it makes the kwarg behave correctly when
unset, but does not fix the downstream R1-class empty-`<think>` emission
or any tool-call-parser issues.

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

### Q3.6-2 — Qwen3.6 empty-`<think>` history guard (R1 port)

**Target:** Qwen3.6-35B-A3B. **Stacks on Q3.6-1** — the patch as
shipped diffs against the Q3.6-1-applied state, not raw upstream.

**Failure mode.** Q3.6-1 flips `preserve_thinking` default-on, which
causes the existing unconditional `<think>...</think>` wrapper in the
history-emit branch to fire even when `reasoning_content` is empty.
Result: `<think>\n\n</think>` empty wrappers on every history turn that
lacks reasoning, which:

- Wastes context tokens.
- Breaks prefix-cache symmetry: the same assistant turn tokenizes
  differently when emitted as history (with empty wrapper) vs. when it
  was originally generated (without wrapper) — same TTFT regression
  class as R1's Qwen3.5 fix (QwenLM/Qwen3 issue #1826).

**Fix.** Add `and reasoning_content` to the existing combined guard:
```
Old: {%- if (preserve_thinking is not defined or preserve_thinking is not false) or (loop.index0 > ns.last_query_index) %}
New: {%- if ((preserve_thinking is not defined or preserve_thinking is not false) or (loop.index0 > ns.last_query_index)) and reasoning_content %}
```

The new guard is conjunctive: the wrapper is emitted only if (a) the
preserve-thinking conditions still hold AND (b) there is actual
reasoning content to wrap. Empty history turns render naked
(`<|im_start|>assistant\nCONTENT<|im_end|>`), byte-identical to the
no-thinking path.

**Verification fixture.** `tests/fixtures/qwen36_empty_history_reasoning.json`
— a conversation with a history assistant turn carrying empty
`reasoning_content`. The test harness asserts:

1. The Q3.6-1-only state (synthesized in-test by applying just the
   polarity flip to upstream) emits the empty wrapper — confirms the
   bug exists in the intermediate state.
2. The fully patched template (Q3.6-1 + Q3.6-2) emits exactly one
   `<think>` (the generation prompt), with no empty `<think>\n\n</think>`
   in history.

The Q3.6-1 regression suite (`HISTORICAL_REASONING_MARKER` retained
when present, omitted when `preserve_thinking=False`) continues to pass
unchanged.

**Relationship to Q3.6-1 (cumulative effect).**

| `preserve_thinking` | Has reasoning_content | Pre-Q3.6-1 | Post-Q3.6-1 only | Post-Q3.6-1 + Q3.6-2 |
|---|---|---|---|---|
| undefined | yes | drop | preserve ✅ | preserve ✅ |
| undefined | no  | drop | empty wrapper ❌ | drop ✅ |
| `true`    | yes | preserve | preserve | preserve |
| `true`    | no  | empty wrapper ❌ | empty wrapper ❌ | drop ✅ |
| `false`   | yes | drop | drop | drop |
| `false`   | no  | drop | drop | drop |

Q3.6-2 closes both empty-wrapper cells.

**Attribution.**
- *Reporter:* Giant-Space-Bee (QwenLM/Qwen3 issue #1826) for the original
  Qwen3.5 R1 failure mode (~25× TTFT regression measured); same family
  here for Qwen3.6.
- *Fix author:* latent-variable (HF discussion PRs against Qwen3.5
  publisher repos), porting pattern reused here for Qwen3.6.
- *Template author:* Alibaba Cloud / Qwen Team.
- *Provenance tier:* upstream-tracker (HF discussions on publisher
  repos for the Qwen3.5 origin, ported analogously).

---

### Q3.6-3 — Qwen3.6 auto-close `<think>` + `</thinking>` hallucination recovery

**Target:** Qwen3.6-35B-A3B. **Stacks on Q3.6-1 + Q3.6-2.**

**Failure modes (two related bugs, one combined fix).**

1. **Unclosed `<think>` before `<tool_call>`.** Qwen3.6 sometimes emits a
   tool call mid-reasoning without first closing the think tag. The
   rendered assistant content looks like `<think>thinking...<tool_call>
   ... </tool_call>` with no `</think>`. Downstream parsers either
   ignore the tool call (it appears inside reasoning) or fold it into
   `reasoning_content`. Result: tools never execute. Originated by
   allanchan339 in `chat-template/qwen3.6-enhanced.jinja` (commit
   `13556c0`, 2026-05-02).
2. **`</thinking>` hallucination.** Qwen3.6 occasionally emits
   `</thinking>` (with the extra "ing") instead of the canonical
   `</think>` to close reasoning blocks. The current Qwen3.6
   reasoning_content extractor only recognizes `</think>`, so the
   hallucination form leaks the literal `</thinking>` token into
   downstream rendering. Originated by froggeric in
   `Qwen-Fixed-Chat-Templates/qwen3.6/chat_template.jinja` (initial
   commit `e1eb965`, 2026-05-01).

**Why one patch.** fakezeta's merged template (gist `9e8e039c`,
**snapshotted** at `docs/sources/gists/fakezeta-9e8e039c-...jinja`)
unifies both: the auto-close uses
`max(rfind('</think>'), rfind('</thinking>'))` to detect either close
form when deciding whether to inject, and the reasoning_content
extractor adds an `elif '</thinking>' in content` branch that splits on
the hallucination form. The two changes share the same target lines
and the same conceptual normalization — keeping them in one patch
matches how the community thinks about the fix.

**Fix.** Insert at the top of the assistant-render branch (before
`reasoning_content` extraction):
```jinja
{#- auto-close unclosed <think> before <tool_call>; recognize both close forms -#}
{%- if '<tool_call>' in content and '<think>' in content %}
    {%- set last_think = content.rfind('<think>') %}
    {%- set last_close_think = content.rfind('</think>') %}
    {%- set last_close_thinking = content.rfind('</thinking>') %}
    {%- set last_close = last_close_think if last_close_think > last_close_thinking else last_close_thinking %}
    {%- set tool_pos = content.find('<tool_call>', last_think) %}
    {%- if last_close < last_think %}
        {%- if tool_pos > last_think %}
            {%- set content = content[:tool_pos] + '</think>' + content[tool_pos:] %}
        {%- else %}
            {%- set content = content + '</think>' %}
        {%- endif %}
    {%- endif %}
{%- endif %}
```
And extend the existing `</think>`-split extraction with an `elif`
branch that splits on `</thinking>`.

**Adversarial-review fix (2026-05-06).** The initial form used
`content.find('<tool_call>')` (unscoped), which returned the FIRST
`<tool_call>` in the assistant content regardless of position relative
to `last_think`. If an EARLIER completed tool_call appeared before a
LATER unclosed `<think>...<tool_call>` block, the auto-close would
take the else branch and append `</think>` at end-of-content — leaving
the wrapped tool_call still inside the unclosed think. Codex caught
this in commit `bbce429`; the fix is `content.find('<tool_call>', last_think)`
so the search only considers tool_calls AT OR AFTER the unclosed
think. Regression covered by
`test_q36_3_patched_handles_earlier_completed_tool_call`.

**Verification fixture.** `tests/fixtures/qwen36_unclosed_think_before_tool_call.json`
renders an assistant turn with `<think>...<tool_call>...</tool_call>`
content (no `</think>`). The harness asserts:

1. Upstream renders the turn with the `<think>` still unclosed when
   `<tool_call>` appears.
2. Patched template auto-injects `</think>` before the `<tool_call>`
   position.
3. An in-memory variant of the fixture replaces `</think>` with
   `</thinking>` to verify the hallucination recovery: the literal
   `</thinking>` token must not appear in the rendered output, and the
   canonical `</think>` must.

**Attribution.**
- *Reporter:* fakezeta (Reddit) — r/LocalLLaMA `1t4cev0` (2026-05-04,
  100↑) — surfaced both fixes in one merged template.
- *Auto-close fix author:* allanchan339 (GitHub) —
  `vLLM-Qwen3-3.5-3.6-chat-template-fix` commit `13556c0`. Verified by
  upstream commit-timestamp diff: froggeric did not have the auto-close
  block until commit `2179960` (2026-05-05), three days after
  allanchan339 published it. Snapshots in
  `docs/sources/hf-snapshots/froggeric-Qwen-Fixed-Chat-Templates-qwen36-{e1eb965,2179960}.jinja`
  preserve the smoking gun.
- *`</thinking>` recognition fix author:* froggeric (HuggingFace) —
  `Qwen-Fixed-Chat-Templates/qwen3.6/chat_template.jinja` commit
  `e1eb965`. **Snapshotted** at
  `docs/sources/hf-snapshots/froggeric-Qwen-Fixed-Chat-Templates-qwen36-e1eb965.jinja`.
- *Combined dual-rfind form:* fakezeta's contribution — neither parent
  uses both close-tag rfinds in the auto-close position search.
  **Snapshotted** at
  `docs/sources/gists/fakezeta-9e8e039c-qwen36-merged.jinja`.
- *Template author:* Alibaba Cloud / Qwen Team (Qwen3.6 chat template).
- *Provenance tier:* community-tracker (allanchan339 GH + froggeric
  HF; both durable enough to track via API).

**Sibling deferred patch.** P11 (Qwen3.5 auto-close) is the catalog
sibling for Qwen3.5 — deferred because qwen3.5 currently has no
patched/ template. See P11 entry above.

---

### Q3.6-4 — Qwen3.6 tool-call string-argument passthrough (R2 port)

**Target:** Qwen3.6-35B-A3B. **Stacks on Q3.6-1 + Q3.6-2 + Q3.6-3.**

**Failure mode.** OpenAI-compat clients (Codex, OpenWebUI, mlx-lm
server in some configurations) send
`tool_calls[*].function.arguments` as a **JSON-encoded string** rather
than the mapping form Qwen3.6's template expects. The upstream
`is mapping` guard (line 122) silently drops the entire parameter
body — the rendered tool call has `<function=NAME>` immediately
followed by `</function>` with no payload. The model loses the record
of the arguments it allegedly used; subsequent turns cannot reason
about prior tool calls correctly.

**Fix.** Add an `elif tool_call.arguments is string` branch that emits
the trimmed string verbatim (with trailing newline) inside the
`<function=...>` block:
```jinja
{%- elif tool_call.arguments is string %}
    {%- if tool_call.arguments|trim %}
        {{- tool_call.arguments }}
        {{- '\n' }}
    {%- endif %}
{%- endif %}
```

Mapping arguments still take the original `<parameter=...>` per-key
path. String-form arguments are emitted as a single JSON blob that
downstream parsers can extract directly from `<function=...>` …
`</function>` — matching how barubary's R2 fix shipped for Qwen3.5.

**Why string-form happens.** OpenAI's chat completion API requires
`arguments` to be a string. Many compatibility shims preserve that
shape verbatim instead of round-tripping through `json.loads`. The
template should accept either form rather than presupposing the
upstream shim normalized them.

**Why two grammars (intentional design decision, flagged by adversarial review).**
The mapping path emits per-key `<parameter=NAME>VALUE</parameter>`
blocks; the string-form path emits the JSON string verbatim inside
`<function=...>` (e.g., `<function=get_weather>{"city":"SF"}</function>`).
The shipped template tells the model to emit `<parameter>` form during
generation (lines 60-66 of upstream), so a history turn rendered via
the string path is **grammatically inconsistent** with how the model
itself emits.

We accept this inconsistency for two reasons:

1. **Portability beats grammar uniformity.** Parsing a JSON string
   inside Jinja requires a `from_json` filter that is **not in
   standard Jinja2** — it's an extension missing from minijinja,
   vLLM's renderer in many configurations, and the HF
   `apply_chat_template` sandbox by default. Adopting it would
   violate the repo's no-vendor-lock-in scope rule (3).
2. **String-form is recovery, not happy-path.** Q3.6-4 fires only
   when an OpenAI-compat shim has already converted the dict to a
   string. The dominant case is the mapping path; the string path is
   the recovery branch for clients that mangled the shape. Silent
   drop (the upstream behavior) is strictly worse than grammar-shift.

Downstream parsers (Qwen XML tool-call parser, `qwen3_xml`,
`qwen3_coder`) generally accept either form — they extract the
function name and treat anything inside `<function>...</function>` as
the argument payload. If a deployment uses a parser strict about
`<parameter>` form, the right fix is **upstream client normalization**
(get the shim to preserve dict shape), not template-side JSON parsing.

The pinned regression test
`test_q36_4_patched_pins_raw_json_grammar_for_string_args` asserts the
exact byte form (`<function=NAME>\n{...}\n</function>`) so future
drift is caught explicitly. Codex adversarial review (2026-05-06)
caught this grammar-shift; the response is to document and pin it as
intentional, not to add a non-portable extension filter.

**Verification fixture.**
`tests/fixtures/qwen36_string_args_tool_call.json` — assistant turn
with `tool_calls[0].function.arguments` set to a JSON string.
Harness asserts:

1. Upstream Qwen3.6 drops the string-form arguments (the marker is
   absent from the rendered prompt).
2. Patched template emits the string verbatim INSIDE the
   `<tool_call>...</tool_call>` block.
3. The mapping-args path (synthesized in-test) still emits
   `<parameter=...>` blocks — no regression.

**Attribution.**
- *Reporter:* same family as R2 (barubary's Fix 9 for Qwen3.5).
  Cross-confirmed for Qwen3.6 by the field reports in
  r/LocalLLM `1sqpsut` snapshot and `ml-explore/mlx-lm#1065`.
- *Fix author:* barubary (Qwen3.5 origin); pattern reapplied here for
  Qwen3.6 — mechanical port. Trim guard + trailing-newline behavior
  matches fakezeta's gist `9e8e039c` (snapshotted).
- *Template author:* Alibaba Cloud / Qwen Team.
- *Provenance tier:* community-tracker (barubary HF repo 401 at
  fetch time but pattern is reproduced in multiple snapshotted
  community templates).

---

### Q3.6-5 — Qwen3.6 `<|think_off|>` / `<|think_on|>` sentinels (R3 port + extension)

**Target:** Qwen3.6-35B-A3B. **Stacks on Q3.6-1 + Q3.6-2 + Q3.6-3 + Q3.6-4.**

**Status: opt-in.** Only worth applying when the runtime doesn't
reliably pass `chat_template_kwargs={"enable_thinking": ...}`. Modern
llama.cpp (`--reasoning on/off` PR #20297) and oMLX handle this
server-side; Q3.6-5 is for older llama.cpp builds, certain LM Studio
configurations, or users who want a per-request escape hatch via the
system prompt itself.

**Two related sentinels.**

1. **`<|think_off|>`** (R3 port from Qwen3.5): when present in the
   merged system message, sets `enable_thinking=False`. Sentinel is
   stripped from the rendered system block.
2. **`<|think_on|>`** (NEW for this catalog): when present, sets
   `enable_thinking=True`. Useful when the runtime defaults thinking
   off and the user wants to override per-request without
   reconfiguring the kwarg pipeline. Originated in froggeric's
   `Qwen-Fixed-Chat-Templates/qwen3.6/chat_template.jinja` (initial
   commit `e1eb965`, 2026-05-01).

Both sentinels override any `enable_thinking` kwarg — sentinels take
precedence as the more specific, per-request signal.

**Conflict policy: rightmost-in-text wins.** When BOTH sentinels
appear in the merged system text, the one whose rfind position is
greater wins. Matches "last write wins" intuition for an explicit
per-request override appended to an inherited default. Codex
adversarial review (2026-05-06, fix in commit `bbce429`) caught the
initial implementation, which processed `<|think_off|>` first then
`<|think_on|>` in code order — so `<|think_on|>` always won regardless
of textual position. Fixed by computing `rfind` for each and comparing
positions before applying. Regression covered by
`test_q36_5_conflicting_sentinels_rightmost_wins`.

**Fix.** Three coordinated changes:

1. Initialize a `ns_flags = namespace(enable_thinking=none)` and seed
   it from the kwarg if defined.
2. After the merged system message is built, compute
   `_think_off_pos` and `_think_on_pos` via `rfind`; if either
   sentinel is present, set `ns_flags.enable_thinking` per the
   rightmost position and strip both sentinels from `merged_system`.
3. In the generation prompt, replace
   `if enable_thinking is defined and enable_thinking is false` with
   `if ns_flags.enable_thinking is false`.

**Why delimited tokens.** P5's original `/no_thinking` substring sentinel
was vulnerable to false matches in documentation excerpts, file paths,
or quoted tool output. R3's hardening switched to Qwen's delimited
control-token convention (`<|...|>`). Q3.6-5 follows the same shape
with a matching companion-on form.

**Verification fixture.** `tests/fixtures/qwen36_think_toggle_sentinels.json`
— system message containing `<|think_off|>` plus surrounding text.
Harness asserts:

1. Upstream Qwen3.6 passes the sentinel through to rendered output and
   does NOT flip thinking off.
2. Patched template strips the sentinel AND emits the closed
   `<think>\\n\\n</think>\\n\\n` form in the generation prompt.
3. `<|think_on|>` overrides an explicit `enable_thinking=False` kwarg
   (sentinel-precedence verification).
4. Without any sentinel, the existing `enable_thinking=False` kwarg
   path still flips thinking off correctly (regression).

**Attribution.**
- *Reporter / R3 base author:* u/ex-arman68 (Reddit) — r/LocalLLaMA
  "The definitive Qwen 3.5 jinja template" (`1sis1vn`); proposed the
  `<|think_off|>` delimited-token form for Qwen3.5.
- *`<|think_on|>` companion author:* froggeric (HuggingFace) —
  `Qwen-Fixed-Chat-Templates`. **Snapshotted** at
  `docs/sources/hf-snapshots/froggeric-Qwen-Fixed-Chat-Templates-qwen36-e1eb965.jinja`.
- *Combined form (sentinel-overrides-kwarg precedence):* fakezeta
  merged template (gist `9e8e039c`, **snapshotted**).
- *Template author:* Alibaba Cloud / Qwen Team.
- *Provenance tier:* community-tracker (R3 base) +
  community-tracker (froggeric for `think_on`).

---

### Q3.6-6 — Qwen3.6 tool-definition envelope unwrap

**Target:** Qwen3.6-35B-A3B. **Stacks on Q3.6-1 … Q3.6-5.**

**Failure mode.** Harnesses speaking the OpenAI tool protocol send tool
*definitions* wrapped in an envelope:
`{"type": "function", "function": {"name": ..., "parameters": ...}}`.
Qwen3.6's `<tools>` loop (upstream line 63 / patched line 79) emits the
whole wrapper via `tool | tojson`:
```jinja
{%- for tool in tools %}
    {{- "\n" }}
    {{- tool | tojson }}
{%- endfor %}
```
The model therefore sees an extra `type`/`function` layer it must peel off,
and the envelope keys cost tokens on every tool declaration.

**Fix.** Unwrap the envelope to its inner function spec when the full
envelope **shape** is present:
```jinja
{%- if tool is mapping and tool.type is defined and tool.type == 'function' and tool.function is mapping %}
    {%- set tool = tool.function %}
{%- endif %}
{{- tool | tojson }}
```

**Shape-strict guard (adversarial-review fix, 2026-05-30).** The guard
requires BOTH `type == "function"` AND a mapping `function` member — not
merely `tool.function is defined`. The initial form used the loose
`tool.function is defined`, which Codex flagged: a tool object that carries
an *unrelated* top-level key named `function` (or a tool that isn't a mapping
at all) would be silently rewritten to that member, dropping the tool's real
name/parameters. The shape check makes the unwrap fire **only** on an actual
OpenAI envelope. Regressions covered by
`test_q36_6_patched_does_not_unwrap_toplevel_function_key` and
`test_q36_6_patched_handles_non_mapping_tool`.

**Why this is `derived`, not an external port.** The template *already*
performs an analogous unwrap at the tool-**call** site — both upstream
(lines 110-112) and patched do
`{%- if tool_call.function is defined %}{%- set tool_call = tool_call.function %}`.
Q3.6-6 makes the tool-**definition** rendering symmetric with the
tool-**call** rendering that ships in the same file (and is in fact *stricter*
than the call-site idiom, which uses the loose `is defined` form). The idiom
is in-tree, not imported. With the shape-strict guard, anything that is not an
actual envelope renders unchanged.

**Why the gist's `unwrap_tool_envelope` kwarg was dropped (deliberate).**
jscott3201 gates the unwrap behind `unwrap_tool_envelope` (default true) so it
can be turned off per request. We drop that escape hatch on purpose: a
shape-strict guard is already a no-op for anything that isn't an OpenAI
envelope, so there is no legitimate input for which the wrapped form is
intended yet the unwrap would still fire. A per-request opt-out would only
matter if some deployment *wanted* the redundant `type`/`function` layer fed
to the model, which contradicts the publisher (Qwen3-Coder-Next) convention
this patch follows. Flagged and accepted during Codex adversarial review.

**Prior art / corroboration.** The unwrap convention is canonical in Qwen's
own newer coder template (`Qwen/Qwen3-Coder-Next/chat_template.jinja`, which
does `{%- if tool.function is defined %}{%- set tool = tool.function %}`).
Independently surfaced for Qwen3.6 by jscott3201's public fork (gist
`e4b155885cc68c038d6ac8909a3bd9fe`, its patch "Q5"), **snapshotted** at
`docs/sources/gists/jscott3201-e4b15588-qwen36-custom.jinja`.

**Note on the gist's form.** Besides the tool-definition unwrap, the gist also
unwraps at the tool-call site — redundant here, because Qwen3.6 upstream
already does that (lines 110-112). So Q3.6-6 ports only the definition-site
half of the gist's "Q5".

**Verification fixture.** `tests/fixtures/qwen36_tool_envelope_wrap.json` — a
`tools` list with an envelope-wrapped definition. The harness asserts:

1. Upstream renders the `"function":` wrapper key inside `<tools>` (envelope
   present).
2. Patched renders no `"function":` wrapper and emits the inner spec
   (`"name": "get_weather"`) at top level.
3. A bare (already-unwrapped) tool still renders correctly — the guard is a
   no-op (`test_q36_6_patched_passes_through_unwrapped_tool`).
4. A non-envelope tool with an unrelated top-level `function` key is NOT
   unwrapped — name/body survive
   (`test_q36_6_patched_does_not_unwrap_toplevel_function_key`).
5. A non-mapping `tools` entry renders without raising
   (`test_q36_6_patched_handles_non_mapping_tool`).

**Attribution.**
- *Reporter / surfacer (Qwen3.6):* jscott3201 (GitHub gist).
- *Convention author:* Alibaba Cloud / Qwen Team (the `tool.function` unwrap
  is canonical in Qwen3-Coder-Next).
- *Fix author:* original to this repo — mechanical mirror of the template's
  own tool-call-site unwrap.
- *Template author:* Alibaba Cloud / Qwen Team (Qwen3.6 chat template).
- *Provenance tier:* derived (in-tree idiom; community-tracker + publisher
  corroboration).

---

### Q3.6-7 — Qwen3.6 strengthened `<IMPORTANT>` tool-call instructions

**Target:** Qwen3.6-35B-A3B. **Stacks on Q3.6-1 … Q3.6-6.**

**Status: opt-in.** Q3.6-7 edits the in-prompt instruction *text* rather than
fixing a render-level bug, so its effect cannot be verified by a render-diff
the way the active Q3.6-N patches are. The reference patch ships in
`patches/qwen3.6/Q3.6-7-strengthened-tool-instructions.patch` and is **not**
applied to the default `patched/35B-A3B.jinja`. Same treatment as Gemma 4's
G8 (opt-in) and the guidance-only G6. Apply it if you observe the documented
tool-call formatting failures.

**Promotion gate: needs eval before going active.** Do not promote Q3.6-7 to
the default `patched/` stack without a measured tool-call-accuracy eval
(before/after on the documented failure modes). Until that evidence exists it
stays opt-in by policy, not just by default — this guards against the entry
silently accreting into the active set as untestable instruction-text.

**Failure modes addressed.** Upstream's `<IMPORTANT>` reminder has four
bullets. Q3.6-7 adds three that target documented, reproducible Qwen-coder
tool-call formatting failures:

- **Omitted opening `<tool_call>` tag** — the model emits `<function=...>`
  without the wrapping `<tool_call>`. QwenLM/Qwen3-Coder#475.
- **Indented tool calls** — `<tool_call>` / `<function>` with leading
  whitespace miss XML/PEG parsers that anchor on line start. block/goose#6883.
- **Nested `<tool_call>` blocks** — for parallel calls the model nests
  blocks instead of emitting separate closed ones. block/goose#6883 +
  parallel-call nesting reports.

**Fix.** Replace the 4-bullet `<IMPORTANT>` string with a 7-bullet version
(existing four retained, terminal punctuation normalized). Purely additive
guidance to the model; the tool-call wire format for well-formed output is
unchanged.

**Why opt-in and not active.** Instruction-text changes are not falsifiable by
the render harness — we can assert the bullets are *present*, not that they
*reduce error rates*. Promoting Q3.6-7 to active would require a measured
tool-call-accuracy eval, which is out of scope for a render-diff suite. This
mirrors how G6 (Gemma 4 grab-bag) is documented as guidance rather than a
discrete patch.

**Verification.** Two tests pin the opt-in contract without claiming an
efficacy result:
- `test_q36_7_not_applied_to_shipped_patched_template` — the default
  `patched/` must NOT contain the new bullets (guards against accidental
  promotion).
- `test_q36_7_patch_applied_in_memory_adds_bullets_and_renders` — applies the
  patch's single-line replacement in-memory and asserts the three bullets
  appear and the template still renders (no Jinja breakage).

**Note on the gist's form.** jscott3201 gates the strengthened block behind a
`verbose_tool_instructions` kwarg (default true). This repo ships it as a flat
opt-in patch (apply = enable) rather than adding a kwarg gate, consistent with
how G8 ships.

**Attribution.**
- *Reporter / fix author:* jscott3201 (GitHub gist
  `e4b155885cc68c038d6ac8909a3bd9fe`, its patch "Q6"). **Snapshotted** at
  `docs/sources/gists/jscott3201-e4b15588-qwen36-custom.jinja`.
- *Cited failure-mode sources:* QwenLM/Qwen3-Coder#475 (omitted tag),
  block/goose#6883 (indentation + nesting).
- *Template author:* Alibaba Cloud / Qwen Team (Qwen3.6 chat template).
- *Provenance tier:* community-tracker (gist; cited bugs on durable GitHub
  trackers).

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

**Field signal — open upstream (not template-fixable).** HF discussion
[`google/gemma-4-26B-A4B-it/discussions/15`](https://huggingface.co/google/gemma-4-26B-A4B-it/discussions/15)
documents a related but distinct failure mode where 26B-A4B states it
will call a tool then doesn't actually emit one, deeper in agentic loops.
Reproduces across multiple frontends/backends with the latest official
chat template; Google requested a repro and one was provided. Awaiting
publisher triage. Tracked here because it's the same family of "26B-A4B
behaves worse than 31B at tool calling" pattern G6 collects, but is not
addressable from the template — leave G6 itself as runtime-recommendation
guidance.

---

### G7 — Empty-content tool-call assistant turn closure

**Target:** Gemma 4 26B-A4B-it, 31B-it, E2B-it, E4B-it.

**Failure mode.** When an assistant message contains tool calls (with
matching `tool_responses` flagged) AND `content` is empty (or post-strip
empty after Google's PR #86 `has_content` refactor), the template's
close-marker conditional evaluates:
```jinja
{%- elif not (ns_tr_out.flag and not has_content) -%}
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
Old: {%- elif not (ns_tr_out.flag and not has_content) -%}
New: {%- else -%}
```

This is stronger than dropping just the `and not has_content` clause —
testing showed that the narrower fix (`not ns_tr_out.flag`) still suppresses
the close marker when `ns_tr_out.flag` is true, which is the actual failure
path. The `else` form always emits the close on the content/tool-response
branch and leaves the upstream `<|tool_response>` emission on the
pure-tool-call branch unchanged.

**Interaction with PR #86.** Google's PR #86 (commit `145dc25`, merged
~2026-04-28) refactored the conditional from `not message.get('content')`
to `not has_content` (post-`strip_thinking` content length), but did
**not** fix the underlying suppression bug. For the empty-content
tool-call case, `has_content` is false for the same reason
`message.get('content')` was falsy → close marker still suppressed.
G7's `{%- else -%}` rewrite is required on top of PR #86. The
regenerated patch (anchored at line 341 of the post-#86 upstream)
ships in `patches/gemma4/G7-empty-content-tool-close.patch`.

**Verification fixture.**
`tests/fixtures/gemma4_empty_content_tool_call.json` — an assistant message
with `tool_calls` + matching `tool_responses` + empty `content`. Upstream
render is missing the `<turn|>` marker between this turn and the next
prompt; patched render contains it. Render harness asserts both
directions (`tests/test_render.py::test_g7_*`).

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

---

### G8 — Tool-declaration JSON Schema robustness (sigjhl)

**Target:** Gemma 4 26B-A4B-it, 31B-it, E2B-it, E4B-it.

**Status: opt-in.** Reference patch ships in
`patches/gemma4/G8-jsonschema-robustness.patch` and is **not** applied
to the default `patched/` set. Promote to active once
[HF discussion #91](https://huggingface.co/google/gemma-4-31B-it/discussions/91)
merges upstream (currently "ready to merge", 7 days old).

**Failure mode.** Google's `format_parameters` macro only branches on a
direct top-level `type` field. JSON Schema patterns that don't expose
their meaning through a top-level `type` collapse to empty `type:""`
declarations — the model never sees the actual parameter schema. Affected
patterns include:

- Nullable refs: `{"anyOf": [{"$ref": "#/$defs/X"}, {"type": "null"}]}`
  (very common output of Pydantic v2 / OpenAPI 3.1 codegen).
- Type unions written as arrays: `{"type": ["string", "null"]}`.
- Composition: `oneOf`, `allOf`, `enum`, `const`.
- Schema indirection: `$ref` / `$defs` (the entire `$defs` block was
  dropped silently).
- Item-schemas inside type-array params containing array or object.
- Python `None` rendered as bare `None` instead of JSON `null`.

Symptom: tool-call accuracy collapses on real-world MCP tools. The
sigjhl repro on llama-server showed Qwen3.5-27B and gpt-oss-20b
calling the same tool fine while Gemma 4-31B-it Q4_K_S could not —
the difference traced to `type:""` rendering for an `anyOf`-nullable
ref parameter.

**Fix.** Rewrites `format_parameters` to:
- Compute `type_names` once (string or list-of-strings) and branch on
  `'ARRAY' in type_names.names` / `'OBJECT' in type_names.names`
  rather than `value['type'] | upper == 'X'` (so type arrays match).
- Emit `anyOf` / `oneOf` / `allOf` / `$ref` / `enum` / `const`
  unconditionally when present, with `escape_keys=false` so nested
  object keys render unquoted (matching the rest of the format).
- Render the trailing `type:` field only when defined, supporting
  both string and list forms.
- Add `$defs` emission to `format_function_declaration`.
- Add `null` rendering for Python `None` to `format_argument`.
- Guard `value['nullable']` and `value['required']` accesses with
  `is defined`.

**Verification.** No fixture / test ships with G8 in this initial
opt-in entry. Recommended verification before promoting to active:
add `tests/fixtures/gemma4_anyof_ref_param.json` containing an
`anyOf: [$ref, null]` parameter and assert that the rendered prompt
preserves `anyOf:` (upstream renders `type:""`; G8-patched renders
the structure).

**Known limitation in the source pastebin.** When a parameter combines
`type: "object"` with one of the new combinators (`anyOf` / `oneOf` /
`allOf` / `$ref` / `$defs` / `enum` / `const`) AND has no explicit
`properties`, the patched macro emits the combinator twice — once from
the new top-level branch, once again from the existing OBJECT-fallback
which recurses into `value` itself with `filter_keys=true`. The fallback
is supposed to drop schema-meta keys, but `standard_keys` was not
expanded to include the new combinators, so they're treated as child
properties and reappear inside `properties:{ ... }`. Result is corrupted
output like `properties:{anyOf:{...}}` for object-typed combinator
schemas. The vast majority of real-world MCP tool params use combinators
at the leaf-property level rather than the type-object level, so most
schemas are unaffected — but this is worth flagging to sigjhl before
HF disc #91 merges, and worth fixing locally if you opt into G8 with
heavy combinator usage. The fix is a one-line addition to
`standard_keys`: `['description', 'type', 'properties', 'required',
'nullable', 'anyOf', 'oneOf', 'allOf', '$ref', 'enum', 'const']`.

**Attribution.**
- *Reporter / fix author:* sigjhl — Reddit
  [r/LocalLLaMA `1syps6i`](https://www.reddit.com/r/LocalLLaMA/comments/1syps6i/)
  ("I stumbled on a Gemma 4 chat template bug for tools and fixed it",
  ~Apr 2026). Diagnosis assisted by GPT-5.5-high reading
  llama-server verbose logs.
- *Upstream PR:*
  [`google/gemma-4-31B-it/discussions/91`](https://huggingface.co/google/gemma-4-31B-it/discussions/91)
  (commit `4238b5d`), 6 upvotes, ready-to-merge.
- *Reference template:* pastebin `tBAHN6FV` (sigjhl's iterated form
  superset of the HF PR), **snapshotted** at
  `docs/sources/pastebins/tBAHN6FV-sigjhl-gemma4-jsonschema-robustness.jinja`.
- *Template author:* Google LLC (Gemma 4 chat template, modified).
- *Provenance tier:* community-tracker (HF discussion + Reddit;
  pastebin has a host-side delete risk so explicitly snapshotted).

**Real-world repro (2026-05-30 sweep).** LM Studio bug-tracker **#1749**
(`Cannot apply filter upper to UndefinedValue`) is an independent reproduction
of exactly what G8 fixes: a tool param whose `type` is undefined (or a
non-string union) hits `value['type'] | upper` and crashes. G8 already ships
the `value['type'] is defined and value['type']` guards + array/list type
normalization that prevent this. Added as a corroborating citation only — G8
remains opt-in (promotion to active still wants a fixture + a re-verification
of the HF disc #91 repo/number pairing, which differs across mirrors).

---

### G9 — Gemma 4 consecutive-assistant turn open/close balance

**Target:** Gemma 4 26B-A4B-it, 31B-it, E2B-it, E4B-it. **Stacks on G7.**

**Failure mode.** Two back-to-back assistant messages (no intervening
user/tool) render an **orphaned `<turn|>` close with no matching `<|turn>`
open**. Gemma 4 intentionally suppresses the *second* assistant's
`<|turn>model` OPEN via `continue_same_model_turn` (a backward scan: "previous
non-tool message was also assistant → don't re-open the model turn"). But the
*first* assistant already emitted its `<turn|>` CLOSE at the end of its own
loop iteration. Net: one open, two closes for what should be one merged turn.
Reproduced on `templates/gemma4/upstream/31B-it.jinja` with messages
`[user, assistant, assistant, user]`:

```
<|turn>model
FIRST<turn|>      ← premature close
SECOND<turn|>     ← orphaned close (no matching open)
```
→ opens=3, closes=4. Breaks prefix/KV-cache symmetry and confuses parsers that
pair turn markers. This is the consecutive-assistant sibling of **G7** (which
fixes the empty-content tool-call case in the same close-marker logic).

**Fix.** Make the close mirror the open. The open is suppressed when the
PREVIOUS non-tool message is an assistant; G9 adds the symmetric FORWARD scan
and defers THIS message's close when the NEXT non-tool message is an assistant
whose open will be suppressed:
```jinja
{%- set next_nt = namespace(role=None, found=false) -%}
{%- for j in range(loop.index0 + 1, loop_messages | length) -%}
    {%- if not next_nt.found and loop_messages[j]['role'] != 'tool' -%}
        {%- set next_nt.role = loop_messages[j]['role'] -%}
        {%- set next_nt.found = true -%}
    {%- endif -%}
{%- endfor -%}
{%- set continued_by_model = (role == 'model' and next_nt.role == 'assistant') -%}
```
and in the close block:
```jinja
{%- elif continued_by_model and not ns_tr_out.flag -%}
    {{- '\n' -}}   {#- defer close; emit newline so merged contents don't glue -#}
```
Result: `<|turn>model\nFIRST\nSECOND<turn|>` — one open, one close, balanced.
Normal user/assistant alternation is byte-identical (next non-tool message is a
user, so the close fires exactly as before).

**Scope boundary (deliberate).** The defer is guarded with
`and not ns_tr_out.flag`, so G9 never touches G7's tool-response close path.
CONSEQUENCE: the rarer "assistant-with-`tool_responses` immediately followed by
a bare assistant" sequence retains the pre-existing open/close asymmetry — the
open-suppression fires but G9 does not defer that close. That sequence was
neither reported nor reproduced, and fixing it would entangle G9 with G7's
tool-response handling. Left as a documented boundary; covered indirectly by
`test_g9_patched_leaves_normal_alternation_unchanged` (G9 must not perturb
non-consecutive cases).

**Verification fixture.** `tests/fixtures/gemma4_consecutive_assistant.json` —
`[user, assistant, assistant, user]`. The harness asserts (per size):

1. Upstream renders `closes > opens` (orphaned close present) —
   `test_g9_upstream_imbalanced_on_consecutive_assistant`.
2. Patched renders `opens == closes`, both assistant bodies survive, and no
   `<turn|>` sits between them (one merged turn) —
   `test_g9_patched_balances_consecutive_assistant`.
3. Normal alternation is unperturbed —
   `test_g9_patched_leaves_normal_alternation_unchanged`.

**Attribution.**
- *Reporter:* Reithan (HuggingFace) — `google/gemma-4-31B-it` discussion
  **#62** ("Chat Template has a bug"); Google (`@pannaga10`) reproduced and
  escalated. Status **OPEN** as of the 2026-05-30 sweep. A fix gist
  (`Reithan/a7431dc0c0b239688a24087bb25c0002`) accompanies the thread.
- *Fix author:* original to this repo — symmetric forward-scan mirroring the
  template's own backward `continue_same_model_turn` open-suppression.
  **Independently reproduced locally** against `upstream/31B-it.jinja` before
  authoring (opens=3 vs closes=4 → balanced 3/3 after).
- *Template author:* Google LLC (Gemma 4 chat template).
- *Provenance tier:* upstream-tracker (the bug sits in a durable Google HF
  discussion with a publisher-side reproduction).
- *Upstream status:* OPEN; this patch predates any upstream resolution.

