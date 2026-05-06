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
