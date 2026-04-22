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
3. **Regression tests** — any unchanged fixtures render byte-identical
   between upstream and patched (except within the documented patch
   region).

The third class isn't implemented in this initial scaffold beyond the
bug-fix tests — the fixtures exposing the bugs are load-bearing; broader
golden-file coverage is a follow-up.
"""

from __future__ import annotations

import pytest

from conftest import TemplatePair, load_fixture, render


# ---------------------------------------------------------------------------
# Smoke tests — every template renders basic chat without raising
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("variant", ["upstream", "patched"])
def test_basic_chat_renders(template_pairs: list[TemplatePair], variant: str) -> None:
    fixture = load_fixture("basic_chat")
    rendered_any = False
    for pair in template_pairs:
        path = pair.upstream if variant == "upstream" else pair.patched
        if not path.is_file():
            continue  # e.g. qwen3.5 patched/ is empty in initial release
        try:
            out = render(path, fixture)
        except Exception as e:  # noqa: BLE001
            pytest.fail(f"{pair.family}/{variant}/{pair.size} failed: {e}")
        assert out, f"{pair.family}/{variant}/{pair.size} rendered empty string"
        rendered_any = True
    assert rendered_any, f"No {variant} templates were exercised"


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
