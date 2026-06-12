"""Render harness: verifies that every template in `templates/` renders
correctly against canonical fixtures, and that each patched template
addresses the failure mode it targets.

Test taxonomy
-------------

1. **Smoke tests** — every (template, basic-chat) pair renders without
   raising and produces non-empty output.
2. **Bug-fix tests** — for each patch, a fixture exposes the bug and we
   assert:
     - `upstream` template exhibits the bug (fails the fix invariant).
     - `patched` template satisfies the fix invariant.
3. **Coverage assertions** — every family declared in scope (see
   `DECLARED_FAMILIES` in `conftest.py`) must ship at least one patched
   template, or be explicitly listed in `CATALOG_ONLY_FAMILIES`. This
   prevents an empty `patched/` directory from letting the suite go green
   via skips.

Optional byte-equal regression coverage against shipped golden files is
out of scope for the pytest suite — it's an opt-in workflow via
`scripts/verify.py --write-goldens` that a downstream user can bootstrap
locally if they want. `tests/golden/` is intentionally empty in this repo.
"""

from __future__ import annotations

import pytest

from conftest import (
    CATALOG_ONLY_FAMILIES,
    DECLARED_FAMILIES,
    REPO_ROOT,
    TemplatePair,
    fixture_applies_to,
    load_fixture,
    render,
)


# ---------------------------------------------------------------------------
# Coverage assertions — surface missing patched templates instead of
# silently letting them skip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("family", DECLARED_FAMILIES)
def test_declared_families_ship_patched_templates(
    template_pairs: list[TemplatePair], family: str
) -> None:
    """Every declared family must ship at least one patched template, OR
    be explicitly listed in CATALOG_ONLY_FAMILIES.

    Without this, a family with empty `patched/` would let the suite go
    green via skips even though the family is presented as in-scope in
    the README and PATCH-CATALOG.
    """
    if family in CATALOG_ONLY_FAMILIES:
        pytest.skip(
            f"{family} is intentionally catalog-only; remove from "
            f"CATALOG_ONLY_FAMILIES once the first patched template lands"
        )
    family_pairs = [p for p in template_pairs if p.family == family]
    assert family_pairs, f"no upstream templates for declared family {family}"
    patched_present = [p for p in family_pairs if p.patched_exists]
    assert patched_present, (
        f"family {family} ships no patched templates but is not in "
        f"CATALOG_ONLY_FAMILIES — either add a patched template or "
        f"explicitly mark it catalog-only"
    )


# ---------------------------------------------------------------------------
# Smoke tests — every template renders applicable fixtures without raising
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("variant", ["upstream", "patched"])
def test_basic_chat_renders(template_pairs: list[TemplatePair], variant: str) -> None:
    fixture = load_fixture("basic_chat")
    rendered_per_family: dict[str, int] = {}
    for pair in template_pairs:
        if not fixture_applies_to(fixture, pair.family):
            continue
        path = pair.upstream if variant == "upstream" else pair.patched
        if not path.is_file():
            continue  # e.g. qwen3.5 patched/ is empty in initial release
        try:
            out = render(path, fixture)
        except Exception as e:  # noqa: BLE001
            pytest.fail(f"{pair.family}/{variant}/{pair.size} failed: {e}")
        assert out, f"{pair.family}/{variant}/{pair.size} rendered empty string"
        rendered_per_family[pair.family] = rendered_per_family.get(pair.family, 0) + 1

    # Per-family coverage: every declared family with applicable templates
    # for this variant must have rendered at least once. This is what
    # protects against a silently-empty patched/ dir.
    for family in DECLARED_FAMILIES:
        family_has_pairs = any(p.family == family for p in template_pairs)
        if not family_has_pairs:
            continue
        if variant == "patched" and family in CATALOG_ONLY_FAMILIES:
            continue  # documented exemption
        assert rendered_per_family.get(family, 0) > 0, (
            f"variant={variant}: declared family {family} did not render "
            f"any basic_chat fixtures — check templates/{family}/{variant}/"
        )


# ---------------------------------------------------------------------------
# G7 — Gemma 4 empty-content tool-call assistant turn closure
# ---------------------------------------------------------------------------

GEMMA4_SIZES = ["26B-A4B-it", "31B-it", "E2B-it", "E4B-it"]


def _find_pair(pairs: list[TemplatePair], family: str, size: str) -> TemplatePair:
    for p in pairs:
        if p.family == family and p.size == size:
            return p
    pytest.skip(f"template pair {family}/{size} not present")


def _gap_after_last_tool_response(out: str) -> str:
    """Return the substring between the LAST `<tool_response|>` and the
    NEXT `<|turn>` opener that follows it. The G7 bug manifests as
    *missing* `<turn|>` in this gap.
    """
    end_close = "<tool_response|>"
    end_idx = out.rfind(end_close)
    if end_idx < 0:
        return ""  # caller can pytest.skip
    after = out[end_idx + len(end_close) :]
    # Find the next turn opener.
    next_idx_user = after.find("<|turn>user")
    next_idx_model = after.find("<|turn>model")
    candidates = [i for i in (next_idx_user, next_idx_model) if i >= 0]
    if not candidates:
        return after  # everything after the tool_response is the "gap"
    return after[: min(candidates)]


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g7_upstream_exhibits_bug(template_pairs, size: str) -> None:
    """Upstream Gemma 4 templates MUST drop `<turn|>` after an assistant
    tool-call turn with empty content — this is the bug G7 fixes.

    If this test ever fails on upstream, it means upstream has shipped a
    fix and G7 can be retired (move catalog entry to `upstream`).
    """
    pair = _find_pair(template_pairs, "gemma4", size)
    fixture = load_fixture("gemma4_empty_content_tool_call")
    out = render(pair.upstream, fixture)
    if "<tool_response|>" not in out:
        pytest.skip(f"{size} upstream rendered no <tool_response|> — fixture mismatch")
    gap = _gap_after_last_tool_response(out)
    assert "<turn|>" not in gap, (
        f"upstream {size} unexpectedly emitted <turn|> close in the gap "
        f"after the final <tool_response|> — G7 may already be fixed "
        f"upstream; update catalog status. Gap was: {gap!r}"
    )


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g7_patched_fixes_bug(template_pairs, size: str) -> None:
    """Patched Gemma 4 templates MUST emit `<turn|>` after an assistant
    tool-call turn with empty content."""
    pair = _find_pair(template_pairs, "gemma4", size)
    if not pair.patched_exists:
        pytest.skip(f"{size} patched not present")
    fixture = load_fixture("gemma4_empty_content_tool_call")
    out = render(pair.patched, fixture)
    if "<tool_response|>" not in out:
        pytest.skip(f"{size} patched rendered no <tool_response|>")
    gap = _gap_after_last_tool_response(out)
    assert "<turn|>" in gap, (
        f"patched {size} is missing the <turn|> close marker in the gap "
        f"after the final <tool_response|> — G7 patch did not take effect. "
        f"Gap was: {gap!r}"
    )


# ---------------------------------------------------------------------------
# G9 — Gemma 4 consecutive-assistant turn open/close balance
# ---------------------------------------------------------------------------


def _turn_counts(out: str) -> tuple[int, int]:
    """Return (opens, closes) for Gemma 4 turn markers: `<|turn>` opens a turn,
    `<turn|>` closes it. A balanced render has opens == closes."""
    return out.count("<|turn>"), out.count("<turn|>")


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g9_upstream_imbalanced_on_consecutive_assistant(template_pairs, size: str) -> None:
    """Upstream Gemma 4 leaves an ORPHANED `<turn|>` close on two back-to-back
    assistant messages: the second's `<|turn>model` open is suppressed
    (continue_same_model_turn) but the first already closed → closes > opens.

    If this ever balances on upstream, upstream fixed it and G9 can retire."""
    pair = _find_pair(template_pairs, "gemma4", size)
    fixture = load_fixture("gemma4_consecutive_assistant")
    out = render(pair.upstream, fixture)
    opens, closes = _turn_counts(out)
    assert closes > opens, (
        f"upstream {size} unexpectedly balanced turn markers "
        f"(opens={opens}, closes={closes}) — G9 may already be fixed upstream; "
        f"update catalog status.\n{out!r}"
    )


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g9_patched_balances_consecutive_assistant(template_pairs, size: str) -> None:
    """With G9, two consecutive assistant messages share ONE balanced
    open/close pair: opens == closes, both message bodies survive, and there is
    no orphaned `<turn|>`."""
    pair = _find_pair(template_pairs, "gemma4", size)
    if not pair.patched_exists:
        pytest.skip(f"{size} patched not present")
    fixture = load_fixture("gemma4_consecutive_assistant")
    out = render(pair.patched, fixture)
    opens, closes = _turn_counts(out)
    assert opens == closes, (
        f"G9 broken — patched {size} turn markers still imbalanced "
        f"(opens={opens}, closes={closes}).\n{out!r}"
    )
    assert "FIRST_ASSISTANT_MARKER" in out and "SECOND_ASSISTANT_MARKER" in out, (
        f"G9 dropped assistant content on {size}.\n{out!r}"
    )
    # The merged model turn must hold BOTH bodies between a single open/close:
    # i.e. no `<turn|>` appears between the two markers.
    a = out.find("FIRST_ASSISTANT_MARKER")
    b = out.find("SECOND_ASSISTANT_MARKER")
    assert 0 <= a < b, f"unexpected ordering on {size}\n{out!r}"
    assert "<turn|>" not in out[a:b], (
        f"G9 broken — a `<turn|>` close still sits between the two assistant "
        f"messages on {size} (they were not merged into one turn).\n{out!r}"
    )


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g9_patched_leaves_normal_alternation_unchanged(template_pairs, size: str) -> None:
    """Regression: G9's forward-scan must NOT change normal user/assistant
    alternation — the next non-tool message there is a user, so the close fires
    exactly as before. Patched render must equal upstream-shape balance."""
    pair = _find_pair(template_pairs, "gemma4", size)
    if not pair.patched_exists:
        pytest.skip(f"{size} patched not present")
    normal = {
        "_applies_to": ["gemma4"],
        "messages": [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"},
            {"role": "user", "content": "More"},
            {"role": "assistant", "content": "Sure"},
        ],
        "add_generation_prompt": False,
    }
    out = render(pair.patched, normal)
    opens, closes = _turn_counts(out)
    assert opens == closes and opens >= 4, (
        f"G9 regressed normal alternation on {size} "
        f"(opens={opens}, closes={closes}).\n{out!r}"
    )


# ---------------------------------------------------------------------------
# G10 — Gemma 4 preserve_thinking (default-OFF kwarg, keeps historical reasoning)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g10_default_drops_historical_tool_reasoning(template_pairs, size: str) -> None:
    """By default (no kwarg) Gemma 4 renders a tool-call turn's reasoning only
    for the current-turn region, so the HISTORICAL turn's reasoning is dropped.
    Patched default behaviour must match this (G10 is gated off by default)."""
    pair = _find_pair(template_pairs, "gemma4", size)
    if not pair.patched_exists:
        pytest.skip(f"{size} patched not present")
    fixture = load_fixture("gemma4_history_tool_call_reasoning")
    out = render(pair.patched, fixture)
    assert "CUR_REASONING_MARKER" in out, (
        f"current-turn reasoning unexpectedly dropped on {size}:\n{out!r}"
    )
    assert "HIST_REASONING_MARKER" not in out, (
        f"patched {size} preserved historical reasoning WITHOUT the kwarg — "
        f"G10 must be off by default.\n{out!r}"
    )


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g10_preserve_thinking_keeps_historical_reasoning(template_pairs, size: str) -> None:
    """With preserve_thinking=true, the historical tool-call turn's reasoning
    is rendered too (the fix for multi-step agentic arguments-collapse)."""
    pair = _find_pair(template_pairs, "gemma4", size)
    if not pair.patched_exists:
        pytest.skip(f"{size} patched not present")
    fixture = load_fixture("gemma4_history_tool_call_reasoning")
    payload = {**fixture, "preserve_thinking": True}
    out = render(pair.patched, payload)
    assert "HIST_REASONING_MARKER" in out and "CUR_REASONING_MARKER" in out, (
        f"G10 broken — preserve_thinking=True did not retain historical "
        f"reasoning on {size}.\n{out!r}"
    )


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g10_default_byte_identical_to_pre_g10(template_pairs, size: str) -> None:
    """G10 is a default-OFF kwarg gate. Synthesize the pre-G10 (G7+G9) state by
    reverting just the guard expression in-memory, then assert that with no
    kwarg (and with preserve_thinking=false) the shipped template renders
    byte-identical to that pre-G10 state — proving zero default-behaviour
    change. (Comparing to `upstream` would be wrong here: this fixture's
    empty-content tool-call turns are exactly G7's domain, so patched != upstream
    by design.)"""
    pair = _find_pair(template_pairs, "gemma4", size)
    if not pair.patched_exists:
        pytest.skip(f"{size} patched not present")
    src = pair.patched.read_text()
    g10_guard = (
        "((preserve_thinking is defined and preserve_thinking) "
        "or loop.index0 > ns_turn.last_user_idx)"
    )
    assert g10_guard in src, f"G10 guard missing from patched {size}"
    pre_g10 = src.replace(g10_guard, "loop.index0 > ns_turn.last_user_idx")

    import jinja2  # noqa: F401  (local, matches other synthetic-state tests)
    from conftest import make_env

    fixture = load_fixture("gemma4_history_tool_call_reasoning")
    env = make_env()
    ctx_base = {
        "bos_token": "", "eos_token": "", "pad_token": "",
        "add_generation_prompt": True, "add_vision_id": False, "tools": None,
    }
    pre_t = env.from_string(pre_g10)
    cur_t = env.from_string(src)
    for extra in ({}, {"preserve_thinking": False}):
        ctx = {**ctx_base, **fixture, **extra}
        assert pre_t.render(**ctx) == cur_t.render(**ctx), (
            f"G10 changed default render on {size} (kwarg unset/false must be "
            f"byte-identical to the pre-G10 state)."
        )


# ---------------------------------------------------------------------------
# Q3.6-1 — Qwen3.6 preserve_thinking default-on flip
# ---------------------------------------------------------------------------


def test_q36_1_upstream_drops_history_think_by_default(template_pairs) -> None:
    """Without `preserve_thinking=true`, upstream Qwen3.6 drops the
    `<think>` block from historical assistant turns. This is the
    cache-thrashing behaviour Q3.6-1 fixes by flipping the default."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    fixture = load_fixture("qwen36_history_with_reasoning")
    out = render(pair.upstream, fixture)
    # The fixture contains an assistant turn with `reasoning_content`
    # BEFORE the last user message (i.e., true history). With
    # preserve_thinking undefined, that history entry should NOT have
    # a `<think>...</think>` block in the rendered prompt.
    # Count how many <think>...</think> pairs appear in the prompt —
    # upstream should have zero in the history position.
    think_count = out.count("<think>")
    # Generation prompt emits `<think>\n` at the end, so total of 1 is
    # expected from upstream. > 1 would mean history was preserved.
    assert think_count == 1, (
        f"upstream Qwen3.6 unexpectedly emitted {think_count} <think> blocks; "
        f"expected 1 (only the generation prompt). If this is >1, the "
        f"upstream default may have been fixed and Q3.6-1 can be retired."
    )


def test_q36_1_patched_keeps_history_think_by_default(template_pairs) -> None:
    """With the Q3.6-1 patch, Qwen3.6 preserves historical `<think>`
    blocks when `preserve_thinking` is undefined."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    fixture = load_fixture("qwen36_history_with_reasoning")
    out = render(pair.patched, fixture)
    # Patched should now have BOTH the historical <think> AND the
    # generation-prompt <think> — i.e., > 1.
    think_count = out.count("<think>")
    assert think_count > 1, (
        f"patched Qwen3.6 emitted only {think_count} <think> blocks; "
        f"Q3.6-1 should preserve the historical one. Got:\n{out[:500]}"
    )
    # And the historical reasoning content should be present verbatim.
    assert "HISTORICAL_REASONING_MARKER" in out, (
        "patched Qwen3.6 did not render the historical reasoning_content"
    )


def test_q36_1_patched_respects_explicit_false(template_pairs) -> None:
    """Critical: even after flipping the default, passing
    `preserve_thinking=False` explicitly must still disable preservation.
    This protects the opt-out path."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    fixture = load_fixture("qwen36_history_with_reasoning")
    payload = {**fixture, "preserve_thinking": False}
    out = render(pair.patched, payload)
    assert "HISTORICAL_REASONING_MARKER" not in out, (
        "patched Qwen3.6 with preserve_thinking=False leaked historical "
        "reasoning — the opt-out escape hatch is broken"
    )


# ---------------------------------------------------------------------------
# Q3.6-2 — Qwen3.6 empty-`<think>` history guard (R1 port)
# ---------------------------------------------------------------------------

# Q3.6-1 + Q3.6-2 stack on each other: Q3.6-1 flips preserve_thinking
# default-on, which exposes the empty-`<think>` wrapper bug on history turns
# with no reasoning_content. Q3.6-2 adds `and reasoning_content` so the
# wrapper only fires when there is content to preserve. The "buggy" baseline
# for Q3.6-2 is therefore the Q3.6-1-only state, not raw upstream — but we
# capture both directions explicitly via the test names.


def test_q36_2_q36_1_alone_emits_empty_think_wrapper(template_pairs) -> None:
    """**Synthetic regression**: confirms that the Q3.6-1 patch alone
    (without Q3.6-2) introduces the empty-`<think>` wrapper on history turns.
    We synthesize the Q3.6-1-only state by reading the upstream and applying
    just the Q3.6-1 polarity flip in-memory, so this test stays meaningful
    even after Q3.6-2 is shipped on top."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    upstream_src = pair.upstream.read_text()
    # Synthesize Q3.6-1-only state by inverse-of-Q3.6-2 substitution. Match
    # against the upstream form (Q3.6-1 NOT applied) and apply just Q3.6-1.
    q36_1_only = upstream_src.replace(
        "(preserve_thinking is defined and preserve_thinking is true)",
        "(preserve_thinking is not defined or preserve_thinking is not false)",
    )
    assert q36_1_only != upstream_src, (
        "synthetic Q3.6-1-only construction failed — upstream template "
        "shape changed; rewrite this test"
    )
    import jinja2  # local import keeps top-of-file imports stable
    from conftest import make_env

    env = make_env()
    template = env.from_string(q36_1_only)
    fixture = load_fixture("qwen36_empty_history_reasoning")
    ctx = {
        "bos_token": "",
        "eos_token": "",
        "pad_token": "",
        "add_generation_prompt": True,
        "add_vision_id": False,
        "tools": None,
    }
    ctx.update(fixture)
    out = template.render(**ctx)
    assert "<think>\n\n</think>" in out, (
        "Q3.6-1-only state should emit empty `<think>\\n\\n</think>` wrapper "
        "on history turns — if it doesn't, the bug Q3.6-2 fixes was already "
        f"absent and Q3.6-2 may be redundant. Output:\n{out!r}"
    )


def test_q36_2_patched_suppresses_empty_history_wrapper(template_pairs) -> None:
    """With Q3.6-2 applied (current patched template), an assistant history
    turn with empty reasoning_content must NOT emit the `<think>\\n\\n</think>`
    wrapper. The exact assertion: there is exactly ONE `<think>` tag in the
    output (the one belonging to the generation prompt at the end)."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    fixture = load_fixture("qwen36_empty_history_reasoning")
    out = render(pair.patched, fixture)
    think_count = out.count("<think>")
    assert think_count == 1, (
        f"patched Qwen3.6 emitted {think_count} <think> blocks for an empty "
        f"history reasoning fixture; expected 1 (generation prompt only). "
        f"Q3.6-2's `and reasoning_content` guard is not taking effect.\n"
        f"Output:\n{out!r}"
    )
    assert "<think>\n\n</think>" not in out, (
        "patched Qwen3.6 still emits empty `<think>\\n\\n</think>` wrapper "
        "on history turns with empty reasoning_content — Q3.6-2 broken."
    )


# ---------------------------------------------------------------------------
# Q3.6-3 — Qwen3.6 auto-close <think> + </thinking> recognition
# ---------------------------------------------------------------------------


def _assistant_turn(out: str) -> str:
    """Return the substring of `out` belonging to the (first) assistant
    history turn — between `<|im_start|>assistant` and the matching
    `<|im_end|>`."""
    start = out.find("<|im_start|>assistant")
    if start < 0:
        return ""
    end = out.find("<|im_end|>", start)
    if end < 0:
        return out[start:]
    return out[start:end]


def test_q36_3_upstream_leaves_think_unclosed_before_tool_call(template_pairs) -> None:
    """Confirm the failure mode: when the assistant content carries
    `<think>...<tool_call>` with no closing tag, upstream Qwen3.6 renders
    that content verbatim — the `<tool_call>` ends up wrapped inside the
    unclosed `<think>` block."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    fixture = load_fixture("qwen36_unclosed_think_before_tool_call")
    out = render(pair.upstream, fixture)
    asst = _assistant_turn(out)
    # In upstream, no auto-close runs and the existing `</think>`-split
    # extraction does nothing because there is no `</think>` in content.
    # The literal `<think>` and `<tool_call>` both appear, with no
    # `</think>` between them.
    assert "<think>" in asst, "fixture didn't render the <think> tag"
    assert "<tool_call>" in asst, "fixture didn't render the <tool_call> tag"
    close_pos = asst.find("</think>")
    tool_pos = asst.find("<tool_call>")
    assert close_pos < 0 or close_pos > tool_pos, (
        "upstream Qwen3.6 unexpectedly closed the <think> before the "
        "<tool_call> — the bug Q3.6-3 fixes appears already absent. "
        f"Assistant turn:\n{asst!r}"
    )


def test_q36_3_patched_auto_closes_think_before_tool_call(template_pairs) -> None:
    """With Q3.6-3 applied, the assistant turn must contain `</think>`
    BEFORE `<tool_call>` so downstream parsers see a closed reasoning
    block."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    fixture = load_fixture("qwen36_unclosed_think_before_tool_call")
    out = render(pair.patched, fixture)
    asst = _assistant_turn(out)
    think_pos = asst.find("<think>")
    close_pos = asst.find("</think>", think_pos + 1)
    tool_pos = asst.find("<tool_call>")
    assert think_pos >= 0 and tool_pos >= 0, (
        f"fixture rendering missing <think> or <tool_call>:\n{asst!r}"
    )
    assert 0 <= close_pos < tool_pos, (
        f"Q3.6-3 broken — patched template did not inject </think> "
        f"before <tool_call>. Positions: <think>@{think_pos} "
        f"</think>@{close_pos} <tool_call>@{tool_pos}\n"
        f"Assistant turn:\n{asst!r}"
    )


def test_q36_3_patched_handles_earlier_completed_tool_call(template_pairs) -> None:
    """Adversarial fixture (from Codex review 2026-05-06): when an assistant
    turn contains an EARLIER completed `<tool_call>` followed by a LATER
    unclosed `<think>...<tool_call>` block, the auto-close must inject
    `</think>` before the LATER tool_call (the one wrapped by the unclosed
    think), not get confused by the earlier completed tool_call.

    Original Q3.6-3 used `content.find('<tool_call>')` which returns the
    FIRST tool_call regardless of position. The fix scopes the search to
    `content.find('<tool_call>', last_think)`."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    fixture = load_fixture("qwen36_unclosed_think_after_earlier_tool_call")
    out = render(pair.patched, fixture)
    asst = _assistant_turn(out)
    # Locate the LAST <think> (the unclosed one) and assert that </think>
    # appears before the SECOND <tool_call> in the assistant turn.
    last_think = asst.rfind("<think>")
    close_after_think = asst.find("</think>", last_think + 1)
    second_tool_call = asst.find("<tool_call>", last_think + 1)
    assert last_think >= 0 and second_tool_call >= 0, (
        f"fixture didn't render the expected shape:\n{asst!r}"
    )
    assert 0 <= close_after_think < second_tool_call, (
        f"Q3.6-3 broken — </think> at {close_after_think} did not close "
        f"BEFORE the wrapped <tool_call> at {second_tool_call} "
        f"(last_think at {last_think}). The auto-close picked the wrong "
        f"tool_call position.\nAssistant turn:\n{asst!r}"
    )
    # The marker payload of the wrapped tool_call must end up OUTSIDE the
    # think block — i.e., after the injected </think>.
    marker_pos = asst.find("NYC_AFTER_UNCLOSED_THINK_MARKER")
    assert close_after_think < marker_pos, (
        f"wrapped tool_call's payload landed inside the think block — "
        f"</think>@{close_after_think} marker@{marker_pos}\n{asst!r}"
    )


def test_q36_3_patched_recognizes_thinking_close_hallucination(template_pairs) -> None:
    """Q3.6-3 also adds an `elif '</thinking>' in content` branch to the
    reasoning_content extraction. When the model emits `</thinking>`
    instead of `</think>`, the patched template must extract the
    reasoning correctly — i.e., the literal `</thinking>` token must NOT
    leak into the rendered output."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    # Synthesize the </thinking> hallucination case by editing the fixture
    # in-memory rather than authoring a second JSON file. The base fixture's
    # _description already covers this scenario.
    base = load_fixture("qwen36_unclosed_think_before_tool_call")
    payload = {
        **base,
        "messages": [
            {"role": "user", "content": "Hi"},
            {
                "role": "assistant",
                "content": "<think>some reasoning</thinking>final answer",
            },
            {"role": "user", "content": "Continue"},
        ],
    }
    out = render(pair.patched, payload)
    # The literal `</thinking>` token must not appear in the rendered output —
    # the extractor should consume it and emit `</think>` (the canonical
    # close form Qwen3.6 uses everywhere else).
    assert "</thinking>" not in out, (
        f"Q3.6-3 broken — `</thinking>` hallucination leaked into the "
        f"rendered prompt. Output:\n{out!r}"
    )
    # And the canonical close form must appear (the template wrapping
    # always emits `</think>` for history with reasoning_content).
    assert "</think>" in out, (
        f"Q3.6-3 broken — no canonical `</think>` close in output:\n{out!r}"
    )


# ---------------------------------------------------------------------------
# Q3.6-4 — Qwen3.6 tool-call string-argument passthrough (R2 port)
# ---------------------------------------------------------------------------


def test_q36_4_upstream_drops_string_arguments(template_pairs) -> None:
    """Confirm the failure mode: upstream Qwen3.6 template only handles
    `tool_call.arguments is mapping`, so when arguments arrive as a JSON
    string the entire parameter body is dropped from the rendered prompt."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    fixture = load_fixture("qwen36_string_args_tool_call")
    out = render(pair.upstream, fixture)
    # The tool call block itself renders (function name + wrapper) but
    # the marker embedded in the JSON-string arguments is dropped.
    assert "<function=get_weather>" in out, (
        "fixture didn't trigger the tool_calls branch at all — fixture"
        " or template shape changed; review test"
    )
    assert "SF_STRING_ARG_MARKER" not in out, (
        "upstream Qwen3.6 unexpectedly preserved string-form tool-call "
        "arguments — Q3.6-4 may already be fixed upstream; update catalog "
        f"status. Output:\n{out!r}"
    )


def test_q36_4_patched_emits_string_arguments_verbatim(template_pairs) -> None:
    """With Q3.6-4 applied, JSON-string-form `arguments` must be emitted
    verbatim inside the `<function=...>` … `</function>` block."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    fixture = load_fixture("qwen36_string_args_tool_call")
    out = render(pair.patched, fixture)
    assert "SF_STRING_ARG_MARKER" in out, (
        "Q3.6-4 broken — string-form tool-call arguments are still being "
        f"dropped. Output:\n{out!r}"
    )
    # Must appear inside the tool-call block, not somewhere stray.
    tc_idx = out.find("<tool_call>")
    end_idx = out.find("</tool_call>", tc_idx)
    assert tc_idx >= 0 and end_idx > tc_idx, (
        f"could not locate <tool_call>...</tool_call> bounds in output:\n{out!r}"
    )
    assert "SF_STRING_ARG_MARKER" in out[tc_idx:end_idx], (
        "Q3.6-4 broken — string-form arguments emitted, but outside the "
        f"tool_call block. Output:\n{out!r}"
    )


def test_q36_4_patched_pins_raw_json_grammar_for_string_args(template_pairs) -> None:
    """Pinned-format regression (from Codex review 2026-05-06): when
    arguments arrive as a JSON string, Q3.6-4 emits them as RAW JSON
    inside `<function=...>` rather than re-wrapping in `<parameter>`
    blocks. This is intentional: pure Jinja2 has no portable `from_json`
    filter, so the trade-off is "raw JSON alternate grammar over silent
    drop." This test pins the exact rendered shape so any future change
    that reverses this decision is caught explicitly.

    Documented in PATCH-CATALOG § Q3.6-4 — see "Why two grammars" note."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    fixture = load_fixture("qwen36_string_args_tool_call")
    out = render(pair.patched, fixture)
    # The raw JSON string must appear verbatim inside <function=...>.
    expected_block = (
        '<function=get_weather>\n'
        '{"city": "SF_STRING_ARG_MARKER"}\n'
        '</function>'
    )
    assert expected_block in out, (
        "Q3.6-4 raw-JSON grammar drifted. Expected the literal block:\n"
        f"{expected_block!r}\n"
        "Got output (assistant turn shown):\n"
        f"{_assistant_turn(out)!r}"
    )
    # And explicitly NOT wrapped in <parameter=...>:
    assert "<parameter=city>" not in out, (
        "Q3.6-4 unexpectedly wrapped string-form arguments in "
        "<parameter=...>; this is the mapping-path grammar. If this "
        "change is intentional (e.g., the template now parses JSON via "
        "an extension filter), update PATCH-CATALOG § Q3.6-4 'Why two "
        "grammars' AND remove this pinned test."
    )


def test_q36_4_patched_preserves_mapping_arguments_path(template_pairs) -> None:
    """Regression: the mapping-form `arguments` path (the dominant one)
    must still wrap each key in `<parameter=NAME>` blocks. We synthesize
    a mapping-args variant of the Q3.6-4 fixture in-memory."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    base = load_fixture("qwen36_string_args_tool_call")
    mapping_variant = {
        **base,
        "messages": [
            *base["messages"][:1],
            {
                "role": "assistant",
                "content": "",
                "reasoning_content": "Need to call get_weather.",
                "tool_calls": [
                    {
                        "function": {
                            "name": "get_weather",
                            "arguments": {"city": "NYC_DICT_MARKER"},
                        }
                    }
                ],
            },
            *base["messages"][2:],
        ],
    }
    out = render(pair.patched, mapping_variant)
    assert "NYC_DICT_MARKER" in out, (
        f"Q3.6-4 broken the mapping-args path. Output:\n{out!r}"
    )
    assert "<parameter=city>" in out, (
        f"Q3.6-4 broken — mapping args no longer render `<parameter=...>`:\n{out!r}"
    )


# ---------------------------------------------------------------------------
# Q3.6-5 — Qwen3.6 <|think_off|> / <|think_on|> system-message sentinels
# ---------------------------------------------------------------------------


def _generation_prompt(out: str) -> str:
    """Return the substring of `out` from the LAST `<|im_start|>assistant`
    onward — the generation prompt, where the post-Q3.6-5 thinking-mode
    decision is observable as `<think>\\n` (open) vs
    `<think>\\n\\n</think>\\n\\n` (closed)."""
    idx = out.rfind("<|im_start|>assistant")
    if idx < 0:
        return ""
    return out[idx:]


def test_q36_5_upstream_passes_sentinels_through(template_pairs) -> None:
    """Confirm the failure mode: upstream Qwen3.6 has no sentinel
    awareness, so a `<|think_off|>` token in the system message renders
    verbatim AND does not flip thinking off."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    fixture = load_fixture("qwen36_think_toggle_sentinels")
    out = render(pair.upstream, fixture)
    assert "<|think_off|>" in out, (
        "fixture didn't emit the sentinel into upstream output — fixture "
        "shape changed; review test"
    )
    gen = _generation_prompt(out)
    # Default-on thinking → upstream emits `<think>\n` (open)
    assert gen.endswith("<think>\n"), (
        "upstream Qwen3.6 unexpectedly closed thinking by default — "
        f"check enable_thinking handling. Generation prompt:\n{gen!r}"
    )


def test_q36_5_patched_strips_think_off_and_closes_thinking(template_pairs) -> None:
    """With Q3.6-5, `<|think_off|>` in the system message must:
    1. Be stripped from the rendered system block.
    2. Force the generation prompt to emit the closed `<think>\\n\\n</think>\\n\\n`
       form."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    fixture = load_fixture("qwen36_think_toggle_sentinels")
    out = render(pair.patched, fixture)
    assert "<|think_off|>" not in out, (
        f"Q3.6-5 broken — `<|think_off|>` sentinel leaked into output:\n{out!r}"
    )
    gen = _generation_prompt(out)
    assert gen.endswith("<think>\n\n</think>\n\n"), (
        "Q3.6-5 broken — `<|think_off|>` sentinel did not flip thinking "
        f"off in the generation prompt. Got:\n{gen!r}"
    )


def test_q36_5_think_on_sentinel_overrides_explicit_kwarg(template_pairs) -> None:
    """`<|think_on|>` must take precedence over an explicit
    `enable_thinking=False` kwarg — the sentinel is the more specific,
    per-request control path."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    payload = {
        "messages": [
            {"role": "system", "content": "You are helpful.<|think_on|>"},
            {"role": "user", "content": "Hi"},
        ],
        "add_generation_prompt": True,
        "enable_thinking": False,
    }
    out = render(pair.patched, payload)
    assert "<|think_on|>" not in out, (
        f"Q3.6-5 broken — `<|think_on|>` sentinel leaked:\n{out!r}"
    )
    gen = _generation_prompt(out)
    assert gen.endswith("<think>\n"), (
        "Q3.6-5 broken — `<|think_on|>` did not override "
        f"enable_thinking=False kwarg. Got:\n{gen!r}"
    )


def test_q36_5_conflicting_sentinels_rightmost_wins(template_pairs) -> None:
    """Adversarial fixture (from Codex review 2026-05-06): when BOTH
    `<|think_on|>` and `<|think_off|>` appear in the merged system message,
    the rightmost-in-text sentinel wins. The original Q3.6-5 stripped them
    in code order (think_off first, think_on second), so think_on always
    won regardless of textual order — making per-request off-overrides
    appended to a default-on prompt silently ineffective."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    fixture = load_fixture("qwen36_conflicting_think_sentinels")
    # Fixture has think_on first, think_off later → think_off must win
    out = render(pair.patched, fixture)
    gen = _generation_prompt(out)
    assert gen.endswith("<think>\n\n</think>\n\n"), (
        "Q3.6-5 broken — think_on (earlier in text) won over think_off "
        f"(later in text). Generation prompt:\n{gen!r}"
    )
    assert "<|think_on|>" not in out and "<|think_off|>" not in out, (
        f"Q3.6-5 broken — sentinels not stripped:\n{out!r}"
    )

    # Reverse order: think_off first, think_on later → think_on must win
    payload = {
        **fixture,
        "messages": [
            {
                "role": "system",
                "content": "Default <|think_off|> but use <|think_on|> for this",
            },
            {"role": "user", "content": "Hi"},
        ],
    }
    out = render(pair.patched, payload)
    gen = _generation_prompt(out)
    assert gen.endswith("<think>\n"), (
        "Q3.6-5 broken — think_off (earlier in text) won over think_on "
        f"(later in text). Generation prompt:\n{gen!r}"
    )


def test_q36_5_kwarg_path_still_works_without_sentinel(template_pairs) -> None:
    """Regression: when no sentinel is present, the existing
    `enable_thinking=False` kwarg must still flip the generation prompt to
    closed thinking."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    payload = {
        "messages": [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"},
        ],
        "add_generation_prompt": True,
        "enable_thinking": False,
    }
    out = render(pair.patched, payload)
    gen = _generation_prompt(out)
    assert gen.endswith("<think>\n\n</think>\n\n"), (
        "Q3.6-5 regression — enable_thinking=False kwarg no longer flips "
        f"thinking off. Got:\n{gen!r}"
    )


def test_q36_5_sentinel_strip_is_minja_safe(template_pairs) -> None:
    """Static guard: Q3.6-5 strips sentinels with split|join, NOT `.replace()`.
    llama.cpp's minja silently drops the ENTIRE string when the replaced target
    is at index 0 (a system prompt starting with `<|think_off|>`), erasing the
    whole system block on C++ engines. split|join is byte-identical under
    jinja2. This guards against a regression back to `.replace()`."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    src = pair.patched.read_text()
    assert "merged_system.split('<|think_off|>')" in src, (
        "Q3.6-5 sentinel strip no longer uses split|join — minja index-0 "
        "payload-drop regression risk."
    )
    assert ".replace('<|think_off|>'" not in src and ".replace('<|think_on|>'" not in src, (
        "Q3.6-5 reverted to `.replace()` for sentinel stripping — unsafe on "
        "llama.cpp minja when the sentinel sits at index 0 of the system message."
    )


def test_q36_5_think_off_at_string_start(template_pairs) -> None:
    """Behavioral pin for the minja-bug trigger: a system message that STARTS
    with `<|think_off|>`. Under jinja2 both forms render the same; this fixes
    the expected behavior (sentinel stripped, content kept, thinking flipped
    off) for the index-0 case so the split|join form stays correct."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    payload = {
        "messages": [
            {"role": "system", "content": "<|think_off|>You are helpful."},
            {"role": "user", "content": "Hi"},
        ],
        "add_generation_prompt": True,
    }
    out = render(pair.patched, payload)
    assert "<|think_off|>" not in out, f"index-0 sentinel not stripped:\n{out!r}"
    assert "You are helpful." in out, f"system content lost on index-0 strip:\n{out!r}"
    gen = _generation_prompt(out)
    assert gen.endswith("<think>\n\n</think>\n\n"), (
        f"index-0 `<|think_off|>` did not flip thinking off:\n{gen!r}"
    )


# ---------------------------------------------------------------------------
# Q3.6-6 — Qwen3.6 tool-definition envelope unwrap
# ---------------------------------------------------------------------------


def _tools_block(out: str) -> str:
    """Return the `<tools>` … `</tools>` region of the rendered system
    prompt, where tool definitions are serialized."""
    start = out.find("<tools>")
    end = out.find("</tools>", start)
    if start < 0 or end < 0:
        return ""
    return out[start : end + len("</tools>")]


def test_q36_6_upstream_keeps_tool_envelope(template_pairs) -> None:
    """Confirm the failure mode: upstream Qwen3.6 serializes the whole
    OpenAI tool-definition envelope, so the `"function":` wrapper key
    appears inside the rendered <tools> block."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    fixture = load_fixture("qwen36_tool_envelope_wrap")
    out = render(pair.upstream, fixture)
    block = _tools_block(out)
    assert "ENVELOPE_DESC_MARKER" in block, (
        "fixture didn't render the tool definition at all — fixture or "
        f"template shape changed; review test. <tools> block:\n{block!r}"
    )
    assert '"function":' in block, (
        "upstream Qwen3.6 unexpectedly dropped the OpenAI envelope wrapper "
        '("function": key absent) — Q3.6-6 may already be present upstream; '
        f"update catalog status. <tools> block:\n{block!r}"
    )


def test_q36_6_patched_unwraps_tool_envelope(template_pairs) -> None:
    """With Q3.6-6 applied, the envelope is unwrapped to the inner function
    spec: the `"function":` wrapper key is gone, the inner spec (name,
    description) is emitted at top level."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    fixture = load_fixture("qwen36_tool_envelope_wrap")
    out = render(pair.patched, fixture)
    block = _tools_block(out)
    assert "ENVELOPE_DESC_MARKER" in block, (
        f"Q3.6-6 dropped the tool definition entirely. <tools> block:\n{block!r}"
    )
    assert '"function":' not in block, (
        "Q3.6-6 broken — the `\"function\":` envelope wrapper key is still "
        f"present; the tool definition was not unwrapped. <tools> block:\n{block!r}"
    )
    assert '"name": "get_weather"' in block, (
        "Q3.6-6 broken — inner function spec not emitted at top level. "
        f"<tools> block:\n{block!r}"
    )


def test_q36_6_patched_passes_through_unwrapped_tool(template_pairs) -> None:
    """Regression: a tool sent WITHOUT the envelope (bare function spec,
    no `.function` attribute) must render unchanged — the unwrap guard is
    a no-op for it."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    base = load_fixture("qwen36_tool_envelope_wrap")
    bare_variant = {
        **base,
        "tools": [base["tools"][0]["function"]],  # strip the envelope
    }
    out = render(pair.patched, bare_variant)
    block = _tools_block(out)
    assert "ENVELOPE_DESC_MARKER" in block and '"name": "get_weather"' in block, (
        f"Q3.6-6 mangled a bare (already-unwrapped) tool definition. "
        f"<tools> block:\n{block!r}"
    )


def test_q36_6_patched_does_not_unwrap_toplevel_function_key(template_pairs) -> None:
    """Adversarial (Codex review): a tool that is NOT an OpenAI envelope but
    happens to carry an unrelated top-level `function` key must NOT be
    unwrapped. The shape-strict guard requires `type == "function"` AND a
    mapping `function`; this tool has neither `type == "function"` nor a
    mapping `function`, so the whole definition must survive verbatim.

    A loose `tool.function is defined` guard (the gist's form) would rewrite
    `tool` to the string value and silently drop the tool's name/params."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    base = load_fixture("qwen36_tool_envelope_wrap")
    collision_variant = {
        **base,
        "tools": [
            {
                "name": "weird_tool",
                "description": "TOPLEVEL_FUNCTION_KEY_MARKER",
                "function": "this_string_must_not_replace_the_tool",
                "parameters": {"type": "object", "properties": {}},
            }
        ],
    }
    out = render(pair.patched, collision_variant)
    block = _tools_block(out)
    assert '"name": "weird_tool"' in block, (
        "Q3.6-6 over-unwrapped a non-envelope tool that merely has a "
        f"top-level `function` key — the tool name was lost. <tools>:\n{block!r}"
    )
    assert "TOPLEVEL_FUNCTION_KEY_MARKER" in block, (
        f"Q3.6-6 dropped the non-envelope tool's body. <tools>:\n{block!r}"
    )


def test_q36_6_patched_handles_non_mapping_tool(template_pairs) -> None:
    """Defensive (Codex review): if a `tools` entry is not a mapping, the
    `tool is mapping` guard must short-circuit so `tool.type` / `tool.function`
    are never evaluated against a non-mapping. The entry should render via
    `tojson` without raising."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    base = load_fixture("qwen36_tool_envelope_wrap")
    non_mapping_variant = {**base, "tools": ["NON_MAPPING_TOOL_MARKER"]}
    out = render(pair.patched, non_mapping_variant)  # must not raise
    assert "NON_MAPPING_TOOL_MARKER" in out, (
        f"Q3.6-6 mishandled a non-mapping tool entry. Output:\n{out!r}"
    )


# ---------------------------------------------------------------------------
# Q3.6-7 — Qwen3.6 strengthened <IMPORTANT> tool instructions (OPT-IN)
# ---------------------------------------------------------------------------

# Q3.6-7 is opt-in: the .patch ships but is NOT applied to patched/35B-A3B.jinja
# (it edits in-prompt instruction text, not render-level behavior — same
# treatment as Gemma 4's G8/G6). These tests pin (a) that the shipped template
# does NOT carry it, and (b) that the patch file, applied in-memory, injects the
# three new bullets and the template still renders.

Q36_7_PATCH = (
    REPO_ROOT / "patches" / "qwen3.6" / "Q3.6-7-strengthened-tool-instructions.patch"
)

Q36_7_NEW_BULLETS = (
    "Do NOT omit the opening <tool_call> tag",
    "with NO leading spaces or indentation",
    "Do NOT nest <tool_call> blocks inside one another",
)


def test_q36_7_not_applied_to_shipped_patched_template(template_pairs) -> None:
    """Opt-in invariant: the default patched/35B-A3B.jinja must NOT contain
    the Q3.6-7 bullets. If this fails, Q3.6-7 leaked into the active stack —
    either intentional (then promote it in the catalog and delete this test)
    or accidental (then revert)."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    src = pair.patched.read_text()
    for bullet in Q36_7_NEW_BULLETS:
        assert bullet not in src, (
            f"Q3.6-7 bullet {bullet!r} found in the shipped patched template, "
            "but Q3.6-7 is documented as opt-in (not applied)."
        )


def test_q36_7_patch_applied_in_memory_adds_bullets_and_renders(template_pairs) -> None:
    """Apply the Q3.6-7 patch's single-line replacement in-memory against the
    shipped (Q3.6-6) patched template, then render with a tools fixture and
    assert: the three new bullets appear, and the template still renders
    without raising (no Jinja syntax breakage)."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    assert Q36_7_PATCH.is_file(), f"Q3.6-7 patch missing at {Q36_7_PATCH}"

    patch_lines = Q36_7_PATCH.read_text().splitlines()
    # The patch changes exactly one content line: extract the old (`-`) and
    # new (`+`) forms of the `{{- '...IMPORTANT...' }}` instruction line.
    old_line = next(
        l[1:] for l in patch_lines if l.startswith("-") and "<IMPORTANT>" in l
    )
    new_line = next(
        l[1:] for l in patch_lines if l.startswith("+") and "<IMPORTANT>" in l
    )

    src = pair.patched.read_text()
    assert old_line in src, (
        "Q3.6-7 patch's `-` line does not match the shipped patched template — "
        "the patch is stale relative to patched/35B-A3B.jinja. Regenerate it."
    )
    applied = src.replace(old_line, new_line)
    assert applied != src

    import jinja2  # noqa: F401  (kept local; matches Q3.6-2 synthetic test)
    from conftest import make_env

    env = make_env()
    template = env.from_string(applied)
    fixture = load_fixture("qwen36_tool_envelope_wrap")
    ctx = {
        "bos_token": "",
        "eos_token": "",
        "pad_token": "",
        "add_generation_prompt": True,
        "add_vision_id": False,
        "tools": None,
    }
    ctx.update(fixture)
    out = template.render(**ctx)
    for bullet in Q36_7_NEW_BULLETS:
        assert bullet in out, (
            f"Q3.6-7 applied in-memory but bullet {bullet!r} is missing from "
            f"the rendered output. Output:\n{out!r}"
        )


# ---------------------------------------------------------------------------
# Q3.6-8 — tool-error escalation counter (WATCH / promotion-gate eval)
# ---------------------------------------------------------------------------

# Q3.6-8 is watch-listed and NOT implemented. This scaffold encodes the
# promotion gate from docs/evals/Q3.6-8-error-escalation.md and self-activates:
# it SKIPS while no qwen3.6 patched template implements the counter
# (`consecutive_failures`), and runs the full true-positive / false-positive
# matrix the moment a candidate does. The candidate must emit the fixture's
# `_escalation_signal` wherever it injects a correction directive.

Q36_8_IMPL_MARKER = "consecutive_failures"


def _q36_8_candidate_or_skip(template_pairs):
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("qwen3.6 patched template not present")
    if Q36_8_IMPL_MARKER not in pair.patched.read_text():
        pytest.skip(
            "Q3.6-8 not implemented (no `consecutive_failures` counter in the "
            "patched template). Eval scaffold ready — see "
            "docs/evals/Q3.6-8-error-escalation.md"
        )
    return pair


def test_q36_8_eval_fixture_is_well_formed() -> None:
    """Always-on guard: the eval fixture stays loadable and keeps its
    true-positive AND false-positive cases (the FP cases are the hard gate —
    losing them would silently weaken the eval)."""
    fx = load_fixture("qwen36_repeated_tool_failures")
    cases = {c["name"]: c for c in fx["_eval_cases"]}
    assert fx.get("_escalation_signal"), "fixture lost its _escalation_signal"
    tiers = {c["name"]: c["expect_tier"] for c in fx["_eval_cases"]}
    assert any(t == 2 for t in tiers.values()), "no tier-2 (consecutive) TP case"
    assert any(t == 1 for t in tiers.values()), "no tier-1 (first-failure) TP case"
    fp = [n for n, t in tiers.items() if t == 0]
    assert len(fp) >= 3, (
        f"eval weakened: expected >=3 false-positive bait cases, found {fp}"
    )


@pytest.mark.parametrize(
    "case_name",
    [
        "tp_two_consecutive_genuine_failures",
        "tp_first_failure_only",
        "reset_after_success",
        "fp_legitimate_error_count_data",
        "fp_identifier_and_path",
        "fp_negated_keyword",
    ],
)
def test_q36_8_eval_matrix(template_pairs, case_name: str) -> None:
    """Promotion gate (self-activating). For a candidate Q3.6-8 template:
    the escalation signal must be PRESENT for true-positive cases (tier >= 1)
    and ABSENT for the false-positive bait (tier 0)."""
    pair = _q36_8_candidate_or_skip(template_pairs)
    fx = load_fixture("qwen36_repeated_tool_failures")
    signal = fx["_escalation_signal"]
    case = next(c for c in fx["_eval_cases"] if c["name"] == case_name)
    payload = {"messages": case["messages"], "add_generation_prompt": True}
    out = render(pair.patched, payload)
    present = signal in out
    if case["expect_tier"] == 0:
        assert not present, (
            f"Q3.6-8 FALSE POSITIVE on {case_name}: a correction directive "
            f"fired on a non-failure. {case['why']}\nOutput:\n{out!r}"
        )
    else:
        assert present, (
            f"Q3.6-8 missed a genuine failure on {case_name} "
            f"(expected tier {case['expect_tier']}). {case['why']}\n"
            f"Output:\n{out!r}"
        )


# ---------------------------------------------------------------------------
# Q3.6-9 — loop.previtem -> array-indexing (minija portability, OPT-IN)
# Q3.6-10 — auto_disable_thinking_with_tools kwarg (OPT-IN)
# Both ship a .patch but are NOT applied to the shipped patched/35B-A3B.jinja.
# ---------------------------------------------------------------------------

Q36_9_PATCH = REPO_ROOT / "patches" / "qwen3.6" / "Q3.6-9-loop-previtem-portability.patch"
Q36_10_PATCH = REPO_ROOT / "patches" / "qwen3.6" / "Q3.6-10-auto-disable-thinking-with-tools.patch"


def _render_str(source: str, payload: dict) -> str:
    from conftest import make_env

    ctx = {
        "bos_token": "", "eos_token": "", "pad_token": "",
        "add_generation_prompt": True, "add_vision_id": False, "tools": None,
    }
    ctx.update(payload)
    return make_env().from_string(source).render(**ctx)


def _gen_tail(out: str) -> str:
    idx = out.rfind("<|im_start|>assistant")
    return out[idx:] if idx >= 0 else ""


def test_q36_9_not_applied_to_shipped_template(template_pairs) -> None:
    """Opt-in invariant: the shipped patched template keeps the idiomatic
    loop.previtem/nextitem form (Q3.6-9 is opt-in minija portability)."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    src = pair.patched.read_text()
    assert "loop.previtem" in src and "loop.nextitem" in src, (
        "shipped patched no longer uses loop.previtem/nextitem — if Q3.6-9 was "
        "promoted to active, update the catalog and this test."
    )
    assert "messages[loop.index0 - 1]" not in src


def test_q36_9_portability_rewrite_is_byte_identical(template_pairs) -> None:
    """Applying Q3.6-9's loop.previtem->indexing rewrite in-memory renders
    byte-identical to the shipped template under jinja2 (across single-tool,
    consecutive-tool and tool-last conversations) — it's a pure portability
    rewrite. Drift guard: the patch file must carry the new indexing form."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    assert Q36_9_PATCH.is_file()
    ptext = Q36_9_PATCH.read_text()
    assert "messages[loop.index0 - 1]" in ptext and "messages[loop.index0 + 1]" in ptext, (
        "Q3.6-9 patch no longer carries the array-indexing rewrite."
    )
    src = pair.patched.read_text()
    applied = src.replace(
        '{%- if loop.previtem and loop.previtem.role != "tool" %}',
        '{%- if loop.index0 > 0 and messages[loop.index0 - 1].role != "tool" %}',
    ).replace(
        '{%- if not loop.last and loop.nextitem.role != "tool" %}',
        '{%- if not loop.last and messages[loop.index0 + 1].role != "tool" %}',
    )
    assert applied != src, "Q3.6-9 in-memory rewrite matched nothing"
    convs = {
        "multi-tool": [
            {"role": "user", "content": "SF and NYC?"},
            {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "w", "arguments": {"c": "SF"}}},
                {"function": {"name": "w", "arguments": {"c": "NYC"}}}]},
            {"role": "tool", "content": "SF sunny"},
            {"role": "tool", "content": "NYC rain"},
            {"role": "user", "content": "thanks"},
        ],
        "tool-last": [
            {"role": "user", "content": "SF?"},
            {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "w", "arguments": {"c": "SF"}}}]},
            {"role": "tool", "content": "SF sunny"},
        ],
    }
    for name, msgs in convs.items():
        assert _render_str(src, {"messages": msgs}) == _render_str(applied, {"messages": msgs}), (
            f"Q3.6-9 rewrite changed output under jinja2 for {name}"
        )


def test_q36_10_not_applied_to_shipped_template(template_pairs) -> None:
    """Opt-in invariant: auto_disable_thinking_with_tools must NOT be in the
    shipped patched template (default behaviour keeps Q3.6-3 recovery)."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    assert "auto_disable_thinking_with_tools" not in pair.patched.read_text()


def test_q36_10_when_applied_disables_thinking_with_tools(template_pairs) -> None:
    """Applying Q3.6-10 in-memory: with the kwarg AND tools, the generation
    prompt closes thinking; without tools or without the kwarg it stays open;
    and a `<|think_on|>` sentinel still overrides (precedence)."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    assert Q36_10_PATCH.is_file()
    assert "auto_disable_thinking_with_tools" in Q36_10_PATCH.read_text()
    src = pair.patched.read_text()
    anchor = (
        "{%- set ns_flags = namespace(enable_thinking=none) %}\n"
        "{%- if enable_thinking is defined %}\n"
        "    {%- set ns_flags.enable_thinking = enable_thinking %}\n"
        "{%- endif %}\n"
    )
    assert src.count(anchor) == 1, "Q3.6-10 anchor not found in patched template"
    applied = src.replace(anchor, anchor + (
        "{#- Q3.6-10 -#}\n"
        "{%- if auto_disable_thinking_with_tools is defined and auto_disable_thinking_with_tools and tools and tools is iterable and tools is not mapping %}\n"
        "    {%- set ns_flags.enable_thinking = false %}\n"
        "{%- endif %}\n"
    ))
    assert applied != src
    TOOLS = [{"type": "function", "function": {"name": "w", "parameters": {"type": "object", "properties": {}}}}]
    base = [{"role": "user", "content": "hi"}]
    closed = "<think>\n\n</think>\n\n"
    # kwarg + tools -> thinking OFF
    out = _render_str(applied, {"messages": base, "tools": TOOLS, "auto_disable_thinking_with_tools": True})
    assert _gen_tail(out).endswith(closed), f"auto_disable+tools should close thinking:\n{out!r}"
    # kwarg but no tools -> unchanged (open)
    out = _render_str(applied, {"messages": base, "auto_disable_thinking_with_tools": True})
    assert _gen_tail(out).endswith("<think>\n") and not _gen_tail(out).endswith(closed)
    # sentinel <|think_on|> overrides auto_disable
    out = _render_str(applied, {
        "messages": [{"role": "system", "content": "x<|think_on|>"}, {"role": "user", "content": "hi"}],
        "tools": TOOLS, "auto_disable_thinking_with_tools": True})
    assert _gen_tail(out).endswith("<think>\n"), f"<|think_on|> should override auto_disable:\n{out!r}"
