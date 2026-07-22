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

import re
import shutil

import pytest

from conftest import (
    CATALOG_ONLY_FAMILIES,
    all_template_pairs,
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
# Gemma 4 — G7 / G9 / G10 RETIRED (fixed upstream 2026-07-09)
# ---------------------------------------------------------------------------

# Google's 2026-07-09 template rewrite ("Fixed tool-calling loops, turn
# closures, and thinking content-ordering") fixed all three:
#   G7  empty-content tool-call turn closure  -> close conditional gained
#       `and not next_nt.found`
#   G9  consecutive-assistant turn balance    -> upstream added the same
#       forward-scan + `continues_into_next` suppression G9 derived
#   G10 preserve_thinking                     -> upstream added a NATIVE
#       `preserve_thinking` kwarg with the same default-OFF contract
# The patches are retired and gemma4 ships no patched/ templates (it is now in
# CATALOG_ONLY_FAMILIES). These tests are INVERTED: they assert upstream STAYS
# fixed, so a future upstream regression re-surfaces the bug here rather than
# silently returning. See docs/PATCH-CATALOG.md §§ G7 / G9 / G10.

GEMMA4_SIZES = ["12B-it", "26B-A4B-it", "31B-it", "E2B-it", "E4B-it"]


def _find_pair(pairs: list[TemplatePair], family: str, size: str) -> TemplatePair:
    for p in pairs:
        if p.family == family and p.size == size:
            return p
    pytest.skip(f"template pair {family}/{size} not present")


def _gap_after_last_tool_response(out: str) -> str:
    """Return the substring between the LAST `<tool_response|>` and the
    NEXT `<|turn>` opener that follows it. The (now-fixed) G7 bug manifested
    as *missing* `<turn|>` in this gap."""
    end_close = "<tool_response|>"
    end_idx = out.rfind(end_close)
    if end_idx < 0:
        return ""
    after = out[end_idx + len(end_close):]
    next_idx_user = after.find("<|turn>user")
    next_idx_model = after.find("<|turn>model")
    candidates = [i for i in (next_idx_user, next_idx_model) if i >= 0]
    if not candidates:
        return after
    return after[: min(candidates)]


def _turn_counts(out: str) -> tuple[int, int]:
    """(opens, closes) for Gemma 4 turn markers: `<|turn>` opens, `<turn|>` closes."""
    return out.count("<|turn>"), out.count("<turn|>")


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g7_upstream_closes_empty_content_tool_call(template_pairs, size: str) -> None:
    """RETIRED-G7 sentinel: upstream MUST emit `<turn|>` after an assistant
    tool-call turn with empty content when the conversation continues. If this
    fails, upstream regressed and G7 must be un-retired."""
    pair = _find_pair(template_pairs, "gemma4", size)
    fixture = load_fixture("gemma4_empty_content_tool_call")
    out = render(pair.upstream, fixture)
    if "<tool_response|>" not in out:
        pytest.skip(f"{size} rendered no <tool_response|> — fixture mismatch")
    gap = _gap_after_last_tool_response(out)
    assert "<turn|>" in gap, (
        f"UPSTREAM REGRESSION on {size}: the `<turn|>` close after an "
        f"empty-content tool-call turn is missing again (the old G7 bug). "
        f"Un-retire G7 in docs/PATCH-CATALOG.md. Gap was: {gap!r}"
    )


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g9_upstream_balances_consecutive_assistant(template_pairs, size: str) -> None:
    """RETIRED-G9 sentinel: two back-to-back assistant messages must share ONE
    balanced open/close pair (upstream's `continues_into_next` suppression)."""
    pair = _find_pair(template_pairs, "gemma4", size)
    fixture = load_fixture("gemma4_consecutive_assistant")
    out = render(pair.upstream, fixture)
    opens, closes = _turn_counts(out)
    assert opens == closes, (
        f"UPSTREAM REGRESSION on {size}: turn markers imbalanced again "
        f"(opens={opens}, closes={closes}) — the old G9 orphaned-`<turn|>` bug. "
        f"Un-retire G9.\n{out!r}"
    )
    assert "FIRST_ASSISTANT_MARKER" in out and "SECOND_ASSISTANT_MARKER" in out, (
        f"upstream {size} dropped assistant content.\n{out!r}"
    )
    a = out.find("FIRST_ASSISTANT_MARKER")
    b = out.find("SECOND_ASSISTANT_MARKER")
    assert 0 <= a < b, f"unexpected ordering on {size}\n{out!r}"
    assert "<turn|>" not in out[a:b], (
        f"UPSTREAM REGRESSION on {size}: a `<turn|>` close sits between the two "
        f"assistant messages (they were not merged into one turn).\n{out!r}"
    )


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g10_upstream_honors_preserve_thinking(template_pairs, size: str) -> None:
    """RETIRED-G10 sentinel: upstream now ships a NATIVE `preserve_thinking`
    kwarg — default drops historical tool-call reasoning, `True` retains it."""
    pair = _find_pair(template_pairs, "gemma4", size)
    fixture = load_fixture("gemma4_history_tool_call_reasoning")
    out_default = render(pair.upstream, fixture)
    assert "CUR_REASONING_MARKER" in out_default, (
        f"upstream {size} dropped current-turn reasoning:\n{out_default!r}"
    )
    assert "HIST_REASONING_MARKER" not in out_default, (
        f"UPSTREAM CHANGE on {size}: historical reasoning is now retained WITHOUT "
        f"the kwarg — preserve_thinking is no longer default-OFF.\n{out_default!r}"
    )
    out_kwarg = render(pair.upstream, {**fixture, "preserve_thinking": True})
    assert "HIST_REASONING_MARKER" in out_kwarg and "CUR_REASONING_MARKER" in out_kwarg, (
        f"UPSTREAM REGRESSION on {size}: preserve_thinking=True no longer retains "
        f"historical tool-call reasoning (the old G10 bug). Un-retire G10.\n{out_kwarg!r}"
    )


# ---------------------------------------------------------------------------
# Gemma 4 — G1 / G8 (OPT-IN patches; gemma4 ships no patched/ stack)
# ---------------------------------------------------------------------------

G1_PATCH = REPO_ROOT / "patches" / "gemma4" / "G1-portable-iterable-check.patch"
G8_PATCH = REPO_ROOT / "patches" / "gemma4" / "G8-jsonschema-robustness.patch"


def _apply_gemma_patch(base_src: str, patch_path) -> str:
    """Apply a repo-relative unified-diff .patch to a single-file base in pure
    Python (no external `patch`), reusing the Q3.6-13 additive applier."""
    return _apply_additive_patch(base_src, patch_path)


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g1_upstream_still_uses_sequence_test(template_pairs, size: str) -> None:
    """G1 is still needed: upstream must still carry the non-portable
    `is sequence` test. If this fails, Google fixed it and G1 can retire."""
    pair = _find_pair(template_pairs, "gemma4", size)
    src = pair.upstream.read_text()
    assert "is sequence" in src, (
        f"upstream {size} no longer uses `is sequence` — G1 may be fixed "
        f"upstream; update docs/PATCH-CATALOG.md § G1."
    )


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g1_patch_removes_all_sequence_tests(template_pairs, size: str) -> None:
    """Applying G1 must eliminate every `is sequence` occurrence (the surface
    grew to 4 sites in Google's 2026-07-09 rewrite)."""
    pair = _find_pair(template_pairs, "gemma4", size)
    assert G1_PATCH.is_file(), f"G1 patch missing at {G1_PATCH}"
    applied = _apply_gemma_patch(pair.upstream.read_text(), G1_PATCH)
    assert "is sequence" not in applied, (
        f"G1 left an `is sequence` test behind on {size}"
    )
    assert applied.count("is not mapping") >= 4, (
        f"G1 did not add the mapping guard at every site on {size}"
    )


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g1_is_render_equivalent_under_jinja2(template_pairs, size: str) -> None:
    """G1 is a portability rewrite: under jinja2 it must render byte-identically
    to upstream for normal inputs (string / list content), across kwarg sets."""
    pair = _find_pair(template_pairs, "gemma4", size)
    src = pair.upstream.read_text()
    applied = _apply_gemma_patch(src, G1_PATCH)
    fixtures = [
        "gemma4_empty_content_tool_call",
        "gemma4_consecutive_assistant",
        "gemma4_history_tool_call_reasoning",
    ]
    for name in fixtures:
        fx = {k: v for k, v in load_fixture(name).items() if not k.startswith("_")}
        for extra in ({}, {"preserve_thinking": True}, {"enable_thinking": True}):
            payload = {**fx, **extra}
            assert _render_str(src, payload) == _render_str(applied, payload), (
                f"G1 changed the render on {size} ({name}, extra={extra}) — it "
                f"must be a pure portability rewrite for normal inputs."
            )


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g1_fixes_dict_content_crash(template_pairs, size: str) -> None:
    """Deliberate behaviour change: jinja2's `sequence` test is true for
    MAPPINGS, so a dict-valued `content` made upstream iterate the dict's
    string keys and raise. G1's `is not mapping` guard renders instead."""
    pair = _find_pair(template_pairs, "gemma4", size)
    src = pair.upstream.read_text()
    applied = _apply_gemma_patch(src, G1_PATCH)
    payload = {"messages": [{"role": "user", "content": {"type": "text", "text": "D"}}]}
    with pytest.raises(Exception):
        _render_str(src, payload)
    out = _render_str(applied, payload)  # must not raise
    assert "<|turn>user" in out, f"G1 dict-content render looks wrong on {size}:\n{out!r}"


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g8_restores_dropped_schema_constructs(template_pairs, size: str) -> None:
    """Upstream silently drops anyOf / $ref / const from tool declarations;
    G8 must restore them (Pydantic-v2 / MCP tool schemas depend on this)."""
    pair = _find_pair(template_pairs, "gemma4", size)
    assert G8_PATCH.is_file(), f"G8 patch missing at {G8_PATCH}"
    src = pair.upstream.read_text()
    applied = _apply_gemma_patch(src, G8_PATCH)
    tools = [{"type": "function", "function": {"name": "t", "parameters": {
        "type": "object", "properties": {
            "a": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "b": {"$ref": "#/$defs/Thing"},
            "c": {"type": "string", "const": "CONST_VAL"},
        }}}}]
    payload = {"messages": [{"role": "user", "content": "hi"}], "tools": tools}
    up_out = _render_str(src, payload)
    g8_out = _render_str(applied, payload)
    for token in ("anyOf", "$ref", "CONST_VAL"):
        assert token not in up_out, (
            f"upstream {size} unexpectedly emits {token!r} — G8 may be merged "
            f"upstream; update docs/PATCH-CATALOG.md § G8."
        )
        assert token in g8_out, f"G8 failed to restore {token!r} on {size}"


def _tool_decl(src: str, props: dict) -> str:
    """Render one tool declaration block for `properties`."""
    tools = [{"type": "function", "function": {
        "name": "f", "parameters": {"type": "object", "properties": props}}}]
    out = _render_str(src, {"messages": [{"role": "user", "content": "hi"}], "tools": tools})
    return out[out.find("<|tool>"):out.find("<tool|>")]


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g8_no_pseudo_properties_for_combinator_objects(template_pairs, size: str) -> None:
    """`{"type":"object","anyOf":[...]}` must emit the real `anyOf` and NOT a
    pseudo-property. Upstream's object fallback recurses with filter_keys=true
    over a `standard_keys` list that names none of the schema vocabulary, so
    stock renders `properties:{anyOf:{...}}` — losing the real anyOf and
    inventing a property. Asserting exact output, not just token presence:
    the earlier G8 passed a presence check while emitting both."""
    pair = _find_pair(template_pairs, "gemma4", size)
    src = pair.upstream.read_text()
    g8 = _apply_gemma_patch(src, G8_PATCH)
    props = {"x": {"type": "object", "anyOf": [{"type": "string"}, {"type": "number"}]}}
    up_out, g8_out = _tool_decl(src, props), _tool_decl(g8, props)
    assert "properties:{anyOf" in up_out, (
        f"upstream {size} no longer creates the pseudo-property — G8's "
        f"standard_keys fix may be redundant; re-check the catalog."
    )
    assert "properties:{anyOf" not in g8_out, (
        f"G8 still emits a pseudo-property on {size}:\n{g8_out!r}"
    )
    assert "properties:{}" not in g8_out, (
        f"G8 emits a hollow properties block on {size}:\n{g8_out!r}"
    )
    assert "anyOf:[" in g8_out, f"G8 lost the real anyOf on {size}:\n{g8_out!r}"


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g8_preserves_empty_constraints(template_pairs, size: str) -> None:
    """Empty `anyOf`/`oneOf`/`enum` and an empty `$ref` are meaningful and must
    survive — they were previously gated on truthiness and silently dropped."""
    pair = _find_pair(template_pairs, "gemma4", size)
    g8 = _apply_gemma_patch(pair.upstream.read_text(), G8_PATCH)
    for props, needle in (
        ({"y": {"anyOf": [], "description": "D"}}, "anyOf:[]"),
        ({"y": {"oneOf": [], "description": "D"}}, "oneOf:[]"),
        ({"z": {"$ref": "", "description": "D"}}, "$ref:"),
        ({"w": {"type": "string", "enum": []}}, "enum:[]"),
    ):
        out = _tool_decl(g8, props)
        assert needle in out, f"G8 dropped {needle} on {size}:\n{out!r}"


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g8_keeps_explicit_empty_properties(template_pairs, size: str) -> None:
    """Suppressing the hollow fallback must not suppress a schema's own
    explicitly-empty `properties: {}`."""
    pair = _find_pair(template_pairs, "gemma4", size)
    g8 = _apply_gemma_patch(pair.upstream.read_text(), G8_PATCH)
    out = _tool_decl(g8, {"p": {"type": "object", "properties": {}}})
    assert "properties:{}" in out, f"explicit empty properties lost on {size}:\n{out!r}"


# ---------------------------------------------------------------------------
# Gemma 4 — G4 thinking-toggle sentinels (OPT-IN; stacks on G1)
# ---------------------------------------------------------------------------

G4_PATCH = REPO_ROOT / "patches" / "gemma4" / "G4-thinking-toggle-sentinels.patch"


def _apply_g1_g4(upstream_src: str) -> str:
    """G4 diffs against the G1-applied state (G1 rewrites the `is sequence`
    line sitting between G4's two edited lines, so they overlap in context)."""
    return _apply_gemma_patch(_apply_gemma_patch(upstream_src, G1_PATCH), G4_PATCH)


def _g4_has_think(out: str) -> bool:
    return "<|think|>" in out


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g4_patch_stacks_on_g1_and_is_inert_without_sentinels(template_pairs, size: str) -> None:
    """G1 -> G4 must apply, and with no sentinel present the render must be
    byte-identical to the G1-only state (G4 is a pure escape hatch)."""
    pair = _find_pair(template_pairs, "gemma4", size)
    assert G4_PATCH.is_file(), f"G4 patch missing at {G4_PATCH}"
    src = pair.upstream.read_text()
    g1 = _apply_gemma_patch(src, G1_PATCH)
    g1g4 = _apply_g1_g4(src)
    assert "think_on" in g1g4, "G4 did not introduce the sentinel scan"
    convs = [
        [{"role": "user", "content": "hi"}],
        [{"role": "system", "content": "plain sys"}, {"role": "user", "content": "hi"}],
        [{"role": "system", "content": [{"type": "text", "text": "sys"}]},
         {"role": "user", "content": "hi"}],
    ]
    for msgs in convs:
        for extra in ({}, {"enable_thinking": True}, {"preserve_thinking": True}):
            payload = {"messages": msgs, **extra}
            assert _render_str(g1, payload) == _render_str(g1g4, payload), (
                f"G4 changed the no-sentinel render on {size} (extra={extra})"
            )


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g4_sentinels_toggle_and_are_stripped(template_pairs, size: str) -> None:
    """`<|think_on|>` enables thinking and `<|think_off|>` overrides an explicit
    enable_thinking=True kwarg; both are stripped from the rendered output and
    the surrounding system text survives."""
    pair = _find_pair(template_pairs, "gemma4", size)
    t = _apply_g1_g4(pair.upstream.read_text())
    on = _render_str(t, {"messages": [
        {"role": "system", "content": "You are helpful.<|think_on|>"},
        {"role": "user", "content": "hi"}]})
    assert _g4_has_think(on) and "<|think_on|>" not in on and "You are helpful." in on, on
    off = _render_str(t, {"messages": [
        {"role": "system", "content": "sys<|think_off|>"},
        {"role": "user", "content": "hi"}], "enable_thinking": True})
    assert not _g4_has_think(off) and "<|think_off|>" not in off, off


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g4_rightmost_sentinel_wins(template_pairs, size: str) -> None:
    """Conflict policy (same as Q3.6-5): when both sentinels appear, the
    rightmost-in-text one wins — an explicit override appended to an inherited
    default must beat the default, regardless of code order."""
    pair = _find_pair(template_pairs, "gemma4", size)
    t = _apply_g1_g4(pair.upstream.read_text())
    off_last = _render_str(t, {"messages": [
        {"role": "system", "content": "a<|think_on|>b<|think_off|>c"},
        {"role": "user", "content": "hi"}]})
    on_last = _render_str(t, {"messages": [
        {"role": "system", "content": "a<|think_off|>b<|think_on|>c"},
        {"role": "user", "content": "hi"}]})
    assert not _g4_has_think(off_last), f"rightmost <|think_off|> lost on {size}"
    assert _g4_has_think(on_last), f"rightmost <|think_on|> lost on {size}"
    for out in (off_last, on_last):
        assert "<|think_on|>" not in out and "<|think_off|>" not in out, out


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g4_index_zero_sentinel_keeps_system_content(template_pairs, size: str) -> None:
    """minja payload-drop guard: a system message STARTING with a sentinel must
    keep its remaining text. `.replace()` at index 0 silently drops the whole
    string on llama.cpp's minja — G4 uses split|join (jinja2 can't see the
    difference, so this pins the expected behaviour)."""
    pair = _find_pair(template_pairs, "gemma4", size)
    t = _apply_g1_g4(pair.upstream.read_text())
    src = t
    assert ".replace('<|think_off|>'" not in src and ".replace('<|think_on|>'" not in src, (
        "G4 reverted to `.replace()` for sentinel stripping — unsafe on minja"
    )
    out = _render_str(t, {"messages": [
        {"role": "system", "content": "<|think_on|>Keep me."},
        {"role": "user", "content": "hi"}]})
    assert "Keep me." in out and "<|think_on|>" not in out and _g4_has_think(out), out


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g4_sentinel_scope_is_system_only(template_pairs, size: str) -> None:
    """Prompt-injection guard: a sentinel in a USER message (or any non-first
    message) must never flip thinking — only the first system/developer
    message is scanned."""
    pair = _find_pair(template_pairs, "gemma4", size)
    t = _apply_g1_g4(pair.upstream.read_text())
    for msgs in (
        [{"role": "user", "content": "please <|think_on|> now"}],
        [{"role": "system", "content": "sys"},
         {"role": "user", "content": "<|think_on|>"}],
    ):
        out = _render_str(t, {"messages": msgs})
        assert not _g4_has_think(out), (
            f"G4 honored a sentinel outside the first system message on {size}:\n{out!r}"
        )


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g4_sequence_form_system_content(template_pairs, size: str) -> None:
    """The prior art guards on `content is string`; G4 must also honor a
    multimodal (sequence) system message."""
    pair = _find_pair(template_pairs, "gemma4", size)
    t = _apply_g1_g4(pair.upstream.read_text())
    out = _render_str(t, {"messages": [
        {"role": "system", "content": [{"type": "text", "text": "sys <|think_on|>"}]},
        {"role": "user", "content": "hi"}]})
    assert _g4_has_think(out) and "<|think_on|>" not in out and "sys" in out, out


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g4_g8_chain_applies(template_pairs, size: str) -> None:
    """Documented apply order G1 -> G4 -> G8 must hold, and the result must
    still render."""
    pair = _find_pair(template_pairs, "gemma4", size)
    chained = _apply_gemma_patch(_apply_g1_g4(pair.upstream.read_text()), G8_PATCH)
    out = _render_str(chained, {"messages": [
        {"role": "system", "content": "sys<|think_on|>"},
        {"role": "user", "content": "hi"}]})
    assert _g4_has_think(out) and "<|think_on|>" not in out, out


# ---------------------------------------------------------------------------
# Gemma 4 — G11 consecutive-assistant separator (OPT-IN)
# ---------------------------------------------------------------------------

G11_PATCH = REPO_ROOT / "patches" / "gemma4" / "G11-consecutive-assistant-separator.patch"


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g11_upstream_glues_consecutive_assistants(template_pairs, size: str) -> None:
    """Confirms the defect G11 fixes: upstream balances the turn markers (the G9
    fix, now upstream) but emits NO separator, so adjacent assistant bodies are
    concatenated. If this ever passes, upstream added a separator and G11 can
    retire."""
    pair = _find_pair(template_pairs, "gemma4", size)
    msgs = [{"role": "user", "content": "u"},
            {"role": "assistant", "content": "LEFT"},
            {"role": "assistant", "content": "RIGHT"},
            {"role": "user", "content": "v"}]
    out = _render_str(pair.upstream.read_text(),
                      {"messages": msgs, "add_generation_prompt": False})
    assert "LEFTRIGHT" in out, (
        f"upstream {size} no longer glues consecutive assistants — G11 may be "
        f"fixed upstream; update docs/PATCH-CATALOG.md § G11.\n{out!r}"
    )


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g11_separates_two_three_and_four_consecutive(template_pairs, size: str) -> None:
    """With G11 applied, runs of 2, 3 and 4 consecutive assistants are separated
    by exactly one newline and remain inside ONE balanced turn."""
    pair = _find_pair(template_pairs, "gemma4", size)
    assert G11_PATCH.is_file(), f"G11 patch missing at {G11_PATCH}"
    applied = _apply_gemma_patch(pair.upstream.read_text(), G11_PATCH)
    for k in (2, 3, 4):
        msgs = ([{"role": "user", "content": "u"}]
                + [{"role": "assistant", "content": f"A{i + 1}"} for i in range(k)]
                + [{"role": "user", "content": "v"}])
        out = _render_str(applied, {"messages": msgs, "add_generation_prompt": False})
        expected = "\n".join(f"A{i + 1}" for i in range(k))
        assert expected in out, f"{k} consecutive assistants not separated on {size}:\n{out!r}"
        assert "A1A2" not in out, f"{k} assistants still glued on {size}:\n{out!r}"
        opens, closes = _turn_counts(out)
        assert opens == closes, f"G11 unbalanced turns on {size} (k={k}): {opens}/{closes}"


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g11_empty_leading_message_adds_no_stray_separator(template_pairs, size: str) -> None:
    """G11 gates the separator on `has_content`, unlike the retired G9 which
    emitted it unconditionally. An empty FIRST message of the pair must render
    byte-identically to upstream (no stray blank line)."""
    pair = _find_pair(template_pairs, "gemma4", size)
    applied = _apply_gemma_patch(pair.upstream.read_text(), G11_PATCH)
    msgs = [{"role": "user", "content": "u"},
            {"role": "assistant", "content": ""},
            {"role": "assistant", "content": "A2"},
            {"role": "user", "content": "v"}]
    payload = {"messages": msgs, "add_generation_prompt": False}
    assert _render_str(pair.upstream.read_text(), payload) == _render_str(applied, payload), (
        f"G11 injected a stray separator for an empty leading message on {size}"
    )


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g11_inert_without_consecutive_assistants(template_pairs, size: str) -> None:
    """G11 must be byte-identical to upstream for any conversation that has no
    consecutive assistant messages."""
    pair = _find_pair(template_pairs, "gemma4", size)
    src = pair.upstream.read_text()
    applied = _apply_gemma_patch(src, G11_PATCH)
    convs = [
        [{"role": "user", "content": "u"}, {"role": "assistant", "content": "a"}],
        [{"role": "user", "content": "u"}, {"role": "assistant", "content": "a"},
         {"role": "user", "content": "v"}, {"role": "assistant", "content": "b"}],
        [{"role": "user", "content": "u"},
         {"role": "assistant", "content": "", "tool_calls": [
             {"function": {"name": "t", "arguments": {"a": "b"}}}]},
         {"role": "tool", "content": "R"}, {"role": "user", "content": "v"}],
    ]
    for msgs in convs:
        for extra in ({}, {"add_generation_prompt": False}, {"preserve_thinking": True}):
            payload = {"messages": msgs, **extra}
            assert _render_str(src, payload) == _render_str(applied, payload), (
                f"G11 changed a non-consecutive conversation on {size} (extra={extra})"
            )


@pytest.mark.parametrize("size", GEMMA4_SIZES)
def test_g5_upstream_rejects_string_tool_arguments(template_pairs, size: str) -> None:
    """Catalogued upstream behaviour change (2026-07-09): string-form
    `tool_calls[].function.arguments` — the shape the OpenAI API spec mandates —
    now raises instead of rendering. Pinned so a future upstream reversal is
    noticed. See docs/PATCH-CATALOG.md § "Gemma 4 — string-form tool arguments"."""
    pair = _find_pair(template_pairs, "gemma4", size)
    src = pair.upstream.read_text()
    msgs = [{"role": "user", "content": "u"},
            {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "t", "arguments": '{"city": "SF"}'}}]}]
    with pytest.raises(Exception) as exc:
        _render_str(src, {"messages": msgs})
    assert "JSON object" in str(exc.value) or "mapping" in str(exc.value), (
        f"upstream {size} raised something unexpected for string args: {exc.value}"
    )
    # the mapping form must still work
    ok = [{"role": "user", "content": "u"},
          {"role": "assistant", "content": "", "tool_calls": [
              {"function": {"name": "t", "arguments": {"city": "SF"}}}]}]
    assert "call:t" in _render_str(src, {"messages": ok})


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


# ---------------------------------------------------------------------------
# Q3.6-12 — Qwen3.6 Anthropic-style message.thinking reasoning support (ACTIVE)
# ---------------------------------------------------------------------------

# The Q3.6-12 elif branch, kept verbatim so the byte-identical regression test
# can synthesize the pre-Q3.6-12 state by removing it.
Q36_12_ELIF_BLOCK = (
    "        {#- Q3.6-12: accept Anthropic-style `message.thinking` reasoning "
    "payloads (Claude Code / Anthropic-compat clients) as an alternate reasoning "
    "source, but ONLY when it is a string. The Qwen-native string "
    "`reasoning_content` still wins (its branch is first). A non-string "
    "`message.thinking` (list / dict / Anthropic content-block) is deliberately "
    "ignored — coercing it with `| string` would emit a Python repr (leaking e.g. "
    "block `signature` metadata) and, for `[]`/`{}`, defeat the empty-reasoning "
    "guard by producing a truthy wrapper. Non-`thinking` and non-string-`thinking` "
    "inputs render byte-identically to the Q3.6-6 state. -#}\n"
    "        {%- elif message.thinking is string %}\n"
    "            {%- set reasoning_content = message.thinking %}\n"
)


def test_q36_12_upstream_drops_message_thinking(template_pairs) -> None:
    """Confirm the failure mode: upstream Qwen3.6 only reads
    `message.reasoning_content`, so a turn whose reasoning arrives in the
    Anthropic-shape `thinking` field is dropped. The fixture forces
    `preserve_thinking=true`, so upstream WOULD render a `<think>` wrapper if it
    had reasoning — the marker's absence isolates the non-handling of
    `message.thinking` (not history pruning)."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    fixture = load_fixture("qwen36_message_thinking_reasoning")
    out = render(pair.upstream, fixture)
    assert "ANTHROPIC_THINKING_MARKER" not in out, (
        "upstream Qwen3.6 unexpectedly rendered `message.thinking` reasoning — "
        "Q3.6-12 may already be present upstream; update catalog status.\n"
        f"Output:\n{out!r}"
    )


def test_q36_12_patched_renders_message_thinking(template_pairs) -> None:
    """With Q3.6-12, the assistant turn's `message.thinking` payload is sourced
    as reasoning_content and rendered inside a `<think>` block."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    fixture = load_fixture("qwen36_message_thinking_reasoning")
    out = render(pair.patched, fixture)
    assert "ANTHROPIC_THINKING_MARKER" in out, (
        f"Q3.6-12 broken — `message.thinking` reasoning was dropped.\n{out!r}"
    )
    asst = _assistant_turn(out)
    think_pos = asst.find("<think>")
    close_pos = asst.find("</think>", think_pos + 1)
    marker_pos = asst.find("ANTHROPIC_THINKING_MARKER")
    assert 0 <= think_pos < marker_pos < close_pos, (
        "Q3.6-12 broken — `message.thinking` marker not wrapped inside the "
        f"<think>...</think> block. Assistant turn:\n{asst!r}"
    )


def test_q36_12_reasoning_content_wins_over_thinking(template_pairs) -> None:
    """Precedence: when BOTH `reasoning_content` (Qwen-native) and `thinking`
    (Anthropic) are present on the same turn, the native field wins — the
    `thinking` marker must not appear."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    payload = {
        "messages": [
            {"role": "user", "content": "Hi"},
            {
                "role": "assistant",
                "content": "Hello",
                "reasoning_content": "NATIVE_REASONING_MARKER",
                "thinking": "ANTHROPIC_THINKING_MARKER",
            },
            {"role": "user", "content": "More"},
        ],
        "preserve_thinking": True,
        "add_generation_prompt": True,
    }
    out = render(pair.patched, payload)
    assert "NATIVE_REASONING_MARKER" in out, (
        f"Q3.6-12 broke the reasoning_content path.\n{out!r}"
    )
    assert "ANTHROPIC_THINKING_MARKER" not in out, (
        "Q3.6-12 broken — `message.thinking` overrode the Qwen-native "
        f"`reasoning_content`; native must win.\n{out!r}"
    )


def test_q36_12_empty_thinking_emits_no_wrapper(template_pairs) -> None:
    """Q3.6-2 interaction: a whitespace-only `thinking` payload must NOT emit an
    empty `<think>\\n\\n</think>` wrapper on the history turn (the reasoning is
    `| trim`-ed and gated by Q3.6-2's `and reasoning_content` guard)."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    payload = {
        "messages": [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello", "thinking": "   \n  "},
            {"role": "user", "content": "More"},
        ],
        "preserve_thinking": True,
        "add_generation_prompt": True,
    }
    out = render(pair.patched, payload)
    # Only the generation-prompt <think> should remain (history turn emits none).
    assert out.count("<think>") == 1, (
        f"Q3.6-12 broken — empty `thinking` emitted a stray <think> wrapper.\n{out!r}"
    )
    assert "<think>\n\n</think>" not in out, (
        f"Q3.6-12 broken — empty `thinking` emitted an empty wrapper.\n{out!r}"
    )


def test_q36_12_non_string_thinking_is_ignored(template_pairs) -> None:
    """Non-string `message.thinking` (list / dict / Anthropic content-block) must
    be IGNORED, not coerced: no Python repr leaks into the prompt and no
    `<think>` wrapper is emitted (an empty `[]`/`{}` must not become a truthy
    wrapper that defeats Q3.6-2's guard)."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    cases = [
        [],
        {},
        ["NONSTRING_THINKING_MARKER"],
        [{"type": "thinking", "thinking": "T", "signature": "SIG_MUST_NOT_LEAK"}],
    ]
    for thinking in cases:
        payload = {
            "messages": [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "ok", "thinking": thinking},
                {"role": "user", "content": "next"},
            ],
            "preserve_thinking": True,
            "add_generation_prompt": True,
        }
        out = render(pair.patched, payload)
        # Only the generation-prompt <think> should remain (history turn: none).
        assert out.count("<think>") == 1, (
            f"Q3.6-12 emitted a stray <think> for non-string thinking={thinking!r}\n{out!r}"
        )
        assert "<think>\n\n</think>" not in out, (
            f"Q3.6-12 emitted an empty wrapper for thinking={thinking!r}\n{out!r}"
        )
        for leak in ("NONSTRING_THINKING_MARKER", "SIG_MUST_NOT_LEAK", "'type':", "[]", "{}"):
            assert leak not in out, (
                f"Q3.6-12 leaked a coerced repr ({leak!r}) for thinking={thinking!r}\n{out!r}"
            )


def test_q36_12_default_byte_identical_for_non_thinking_inputs(template_pairs) -> None:
    """Regression: Q3.6-12 is additive. Synthesize the pre-Q3.6-12 state by
    removing the elif block, then assert byte-identical renders for
    conversations that carry NO `thinking` field (mapping-args, string-args,
    reasoning_content, and plain multi-turn). Proves zero behaviour change on
    every non-`thinking` input."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    src = pair.patched.read_text()
    assert Q36_12_ELIF_BLOCK in src, (
        "Q3.6-12 elif block not found verbatim in the shipped template — the "
        "byte-identical synthesis is stale; update Q36_12_ELIF_BLOCK."
    )
    pre_q36_12 = src.replace(Q36_12_ELIF_BLOCK, "")
    assert pre_q36_12 != src

    convs = {
        "reasoning_content": [
            {"role": "user", "content": "2+2?"},
            {"role": "assistant", "content": "4", "reasoning_content": "arith"},
            {"role": "user", "content": "3+3?"},
        ],
        "plain-multiturn": [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"},
            {"role": "user", "content": "More"},
        ],
        "tool-call": [
            {"role": "user", "content": "SF?"},
            {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "w", "arguments": {"c": "SF"}}}]},
            {"role": "tool", "content": "SF sunny"},
            {"role": "user", "content": "thanks"},
        ],
    }
    for name, msgs in convs.items():
        for extra in ({}, {"preserve_thinking": True}, {"preserve_thinking": False}):
            payload = {"messages": msgs, **extra}
            assert _render_str(src, payload) == _render_str(pre_q36_12, payload), (
                f"Q3.6-12 changed the render of a non-`thinking` input "
                f"({name}, extra={extra}) — it must be additive."
            )


# ---------------------------------------------------------------------------
# Q3.6-13 — tool_call_format="json" (Hermes JSON tool calls, OPT-IN)
# Ships a .patch but is NOT applied to the shipped patched/35B-A3B.jinja.
# ---------------------------------------------------------------------------

Q36_13_PATCH = REPO_ROOT / "patches" / "qwen3.6" / "Q3.6-13-tool-call-format-json.patch"


def _apply_additive_patch(base_src: str, patch_path) -> str:
    """Apply the SHIPPED unified-diff .patch to a single-file base in pure Python
    (no external `patch` binary, no temp dir — portable, and still validates the
    real patch file so staleness is caught). Q3.6-13 is purely additive, so each
    hunk's context block is reconstructed and the additions spliced in by a
    unique-context replace."""
    out = base_src
    lines = patch_path.read_text().splitlines(keepends=True)
    i = 0
    while i < len(lines) and not lines[i].startswith("@@"):
        i += 1
    while i < len(lines):
        i += 1  # skip the @@ header
        before, after = [], []
        while i < len(lines) and lines[i][:1] in (" ", "+", "-"):
            tag, body = lines[i][0], lines[i][1:]
            if tag in (" ", "-"):
                before.append(body)
            if tag in (" ", "+"):
                after.append(body)
            i += 1
        b, a = "".join(before), "".join(after)
        assert out.count(b) == 1, f"Q3.6-13 patch context not unique/found:\n{b!r}"
        out = out.replace(b, a, 1)
        while i < len(lines) and not lines[i].startswith("@@"):
            i += 1
    return out


def test_q36_13_not_applied_to_shipped_template(template_pairs) -> None:
    """Opt-in invariant: the shipped patched template must NOT carry the
    tool_call_format switch — the default stays native XML."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    src = pair.patched.read_text()
    assert "tool_call_format" not in src and "_tool_format" not in src, (
        "Q3.6-13 leaked into the shipped patched template — if it was promoted "
        "to active, update the catalog and this test; otherwise revert."
    )


def test_q36_13_patch_applies_and_default_is_byte_identical(template_pairs) -> None:
    """The shipped .patch must apply cleanly to the current default stack, and
    with the kwarg unset or 'xml' the applied template renders byte-identical
    to the shipped one (opt-in must not touch the default XML path)."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    assert Q36_13_PATCH.is_file(), f"Q3.6-13 patch missing at {Q36_13_PATCH}"
    src = pair.patched.read_text()
    applied = _apply_additive_patch(src, Q36_13_PATCH)
    assert "_tool_format" in applied, "Q3.6-13 patch did not introduce the kwarg"
    convs = {
        "single": [
            {"role": "user", "content": "SF?"},
            {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "get_weather", "arguments": {"city": "SF"}}}]},
            {"role": "tool", "content": "sunny"}, {"role": "user", "content": "thx"}],
        "parallel": [
            {"role": "user", "content": "SF and NYC?"},
            {"role": "assistant", "content": "on it", "tool_calls": [
                {"function": {"name": "w", "arguments": {"c": "SF"}}},
                {"function": {"name": "w", "arguments": {"c": "NYC"}}}]}],
    }
    for name, msgs in convs.items():
        for extra in ({}, {"tool_call_format": "xml"}):
            assert _render_str(src, {"messages": msgs, **extra}) == \
                   _render_str(applied, {"messages": msgs, **extra}), (
                f"Q3.6-13 changed the default XML render ({name}, extra={extra})"
            )


def test_q36_13_json_mode_emits_hermes_shape(template_pairs) -> None:
    """With tool_call_format='json' applied, tool calls serialize as a single
    JSON object inside <tool_call> and the XML <function=>/<parameter=> form is
    gone (both in the instruction block and the assistant turn)."""
    pair = _find_pair(template_pairs, "qwen3.6", "35B-A3B")
    if not pair.patched_exists:
        pytest.skip("patched 35B-A3B not present")
    applied = _apply_additive_patch(pair.patched.read_text(), Q36_13_PATCH)
    TOOLS = [{"type": "function", "function": {
        "name": "get_weather",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}}}}]
    msgs = [
        {"role": "user", "content": "SF?"},
        {"role": "assistant", "content": "", "tool_calls": [
            {"function": {"name": "get_weather", "arguments": {"city": "SF"}}}]},
    ]
    out = _render_str(applied, {"messages": msgs, "tools": TOOLS, "tool_call_format": "json"})
    assert '<tool_call>\n{"name": "get_weather", "arguments": {"city": "SF"}}\n</tool_call>' in out, out
    assert "<function=get_weather>" not in out, "json mode still emitted XML tool call"
    assert '{"name": "example_function_name"' in out, "json instruction example missing"
    assert "<function=example_function_name>" not in out, "XML instruction example leaked in json mode"
    # string-form arguments pass through verbatim in json mode
    msgs_s = [
        {"role": "user", "content": "SF?"},
        {"role": "assistant", "content": "", "tool_calls": [
            {"function": {"name": "w", "arguments": '{"c": "SF"}'}}]},
    ]
    out_s = _render_str(applied, {"messages": msgs_s, "tool_call_format": "json"})
    assert '"arguments": {"c": "SF"}}' in out_s, out_s
    # Every emitted tool_call body must be VALID JSON — in particular a
    # whitespace-only string `arguments` must fall back to {} (froggeric's form
    # emits it raw, producing invalid JSON).
    import json
    import re
    for args, expect in [
        ({"city": "SF"}, {"name": "w", "arguments": {"city": "SF"}}),
        ('{"c": "SF"}', {"name": "w", "arguments": {"c": "SF"}}),
        ("   \n\t ", {"name": "w", "arguments": {}}),
        (None, {"name": "w", "arguments": {}}),
    ]:
        msgs_v = [
            {"role": "user", "content": "x"},
            {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "w", "arguments": args}}]},
        ]
        out_v = _render_str(applied, {"messages": msgs_v, "tool_call_format": "json"})
        body = re.search(r"<tool_call>\n(.*?)\n</tool_call>", out_v, re.S).group(1)
        assert json.loads(body) == expect, (
            f"Q3.6-13 emitted invalid/wrong JSON for arguments={args!r}: {body!r}"
        )


# ---------------------------------------------------------------------------
# minja gate — every shipped/opt-in template must parse in llama.cpp's engine
# ---------------------------------------------------------------------------

# jinja2 and minja (the C++ engine in llama.cpp / LM Studio's GGUF path) diverge,
# and the divergence is INVISIBLE to a jinja2-only harness. This repo has now hit
# that class three times: P4 (`| safe`), Q3.6-5 (`.replace()` dropping the string
# at index 0), and Q3.6-14 — minja implements NO position-returning string method,
# so `rfind` / `find` / `index` are Undefined and abort the whole render. The
# shipped Qwen3.6 template used `rfind` and could not render on llama.cpp at all;
# `llama-template-analysis` reported `supports_tools: false` for it.
#
# This gate parses every shipped template, and every opt-in patch applied to its
# base, through the real minja binary. It SKIPS when the binary is absent so the
# suite stays runnable without llama.cpp installed.

MINJA_BIN = shutil.which("llama-template-analysis")
MINJA_FORBIDDEN = (".rfind(", ".find(", ".index(")


def _minja_parses(src: str) -> tuple[bool, str]:
    """Render `src` through llama.cpp's minja. Returns (ok, detail)."""
    import subprocess
    import tempfile
    from pathlib import Path as _P

    with tempfile.TemporaryDirectory() as d:
        f = _P(d) / "t.jinja"
        f.write_text(src)
        r = subprocess.run([MINJA_BIN, "--template-file", str(f)],
                           capture_output=True, text=True)
    out = r.stdout + r.stderr
    if "Analysis failed" in out:
        detail = ""
        for line in out.splitlines():
            if "Error:" in line:
                detail = line.strip()
                break
        return False, detail or "Analysis failed"
    return True, ""


def _shipped_and_optin_templates() -> list[tuple[str, str]]:
    """(label, source) for every shipped template and every opt-in patch applied
    to the base it targets."""
    cases: list[tuple[str, str]] = []
    for pair in all_template_pairs():
        if pair.patched_exists:
            cases.append((f"{pair.family}/patched/{pair.size}", pair.patched.read_text()))
    # Gemma opt-ins: G1 and G8 apply to bare upstream; G4 stacks on G1.
    gemma = [p for p in all_template_pairs() if p.family == "gemma4"]
    for pair in gemma:
        base = pair.upstream.read_text()
        g1 = _apply_additive_patch(base, G1_PATCH)
        cases.append((f"gemma4/{pair.size}+G1", g1))
        cases.append((f"gemma4/{pair.size}+G8", _apply_additive_patch(base, G8_PATCH)))
        cases.append((f"gemma4/{pair.size}+G11", _apply_additive_patch(base, G11_PATCH)))
        cases.append((f"gemma4/{pair.size}+G1+G4", _apply_additive_patch(g1, G4_PATCH)))
    return cases


_MINJA_CASES = [pytest.param(_lbl, _src, id=_lbl)
                for _lbl, _src in _shipped_and_optin_templates()]


def test_minja_binary_presence_is_reported() -> None:
    """Visibility: make it obvious in the run whether the minja gate is active."""
    if MINJA_BIN is None:
        pytest.skip(
            "llama-template-analysis not on PATH — the minja gate is INACTIVE. "
            "Install llama.cpp to enable it (this is the only check that can see "
            "jinja2/minja divergence)."
        )
    assert MINJA_BIN


@pytest.mark.parametrize("label,src", _MINJA_CASES)
def test_minja_renders_every_shipped_and_optin_template(label: str, src: str) -> None:
    """Hard gate: every template we ship (and every opt-in patch applied to its
    base) must parse and render under llama.cpp's minja."""
    if MINJA_BIN is None:
        pytest.skip("llama-template-analysis not on PATH")
    ok, detail = _minja_parses(src)
    assert ok, (
        f"{label} does not render under llama.cpp's minja: {detail}\n"
        f"minja implements no rfind/find/index and diverges from jinja2 in other "
        f"ways; reformulate with split/join/`in`/slicing."
    )


@pytest.mark.parametrize("label,src", _MINJA_CASES)
def test_no_position_returning_string_methods(label: str, src: str) -> None:
    """Static belt-and-braces companion to the minja gate: `rfind`/`find`/`index`
    must not reappear. Runs even when the minja binary is unavailable."""
    hits = [m for m in MINJA_FORBIDDEN if m in src]
    assert not hits, (
        f"{label} uses position-returning string method(s) {hits} — minja has "
        f"none of them and aborts the render. See PATCH-CATALOG § Q3.6-14."
    )


# ---------------------------------------------------------------------------
# jinja2 <-> minja CONSTRUCT DIFFERENTIAL
# ---------------------------------------------------------------------------

# The minja gate above proves our templates *parse* under llama.cpp's engine.
# It does NOT prove they render the SAME bytes — a construct can be valid in
# both engines and still behave differently. That gap is real: `| tojson`
# diverges in three ways, one of them security-relevant (see below).
#
# This suite renders a minimal probe of every construct the shipped templates
# rely on through BOTH engines and asserts agreement. Constructs that are known
# to diverge are pinned in KNOWN_DIVERGENCES with their exact current outputs,
# so the suite fails if minja's behaviour changes in EITHER direction — a new
# divergence, or an existing one being fixed (at which point delete the entry).

_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x1b\([A-Za-z]")

# construct -> (jinja2_output, minja_output) as measured on llama.cpp b9290
KNOWN_DIVERGENCES = {
    # jinja2 sorts object keys; minja preserves insertion order.
    "tojson_key_order": ('{"aa": 2, "zz": 1}', '{"zz": 1, "aa": 2}'),
    # SECURITY-RELEVANT: jinja2 escapes < > & (HTML-safety heritage); minja does
    # not. A tool name/description containing "</tools>" is therefore contained
    # under jinja2 but TERMINATES the <tools> envelope under minja, letting
    # attacker-controlled tool metadata inject prompt structure. The affected
    # `{{- tool | tojson }}` is UPSTREAM Qwen3.6 (line 63), not one of our
    # patches, and cannot be fixed portably from inside the template.
    # See docs/PATCH-CATALOG.md § "jinja2 / minja tojson divergence".
    "tojson_angle": ('{"k": "a\\u003cb\\u003ec"}', '{"k": "a<b>c"}'),
    "tojson_amp": ('{"k": "a\\u0026b"}', '{"k": "a&b"}'),
    # jinja2 escapes non-ASCII; minja emits it raw. Both valid JSON.
    "tojson_nonascii": ('{"k": "caf\\u00e9"}', '{"k": "caf\u00e9"}'),
    # jinja2's `sequence` test is true for mappings; minja's is not. This is why
    # G1's dict-content crash fix is a JINJA2-scoped concern (see § G1).
    "is_sequence_dict": ("Y", "N"),
}

CONSTRUCT_PROBES = {
    "tojson_key_order": "{%- set d={'zz':1,'aa':2} -%}{{- d|tojson -}}",
    "tojson_angle": "{{- {'k':'a<b>c'}|tojson -}}",
    "tojson_amp": "{{- {'k':'a&b'}|tojson -}}",
    "tojson_nonascii": "{{- {'k':'caf\u00e9'}|tojson -}}",
    "tojson_list": "{{- [1,'a',true]|tojson -}}",
    "split_join": "{%- set s='a<T>b' -%}{{- s.split('<T>')|join('|') -}}",
    "last_length": "{%- set s='a<T>b<T>c' -%}{{- s.split('<T>')|last|length -}}",
    "slice_head": "{%- set s='a<T>b<T>c' -%}{{- s.split('<T>')[:-1]|join('/') -}}",
    "slice_tail": "{%- set s='a<T>b<T>c' -%}{{- s.split('<T>')[1:]|join('/') -}}",
    "rstrip_arg": "{{- 'xaa'.rstrip('a') -}}",
    "lstrip_arg": "{{- 'aax'.lstrip('a') -}}",
    "startswith": "{{- 'abc'.startswith('ab') -}}",
    "endswith": "{{- 'abc'.endswith('bc') -}}",
    "reverse_slice": "{%- set l=[1,2,3] -%}{{- l[::-1]|join(',') -}}",
    "dictsort": "{%- set d={'b':1,'a':2} -%}{%- for k,v in d|dictsort -%}{{k}}{%- endfor -%}",
    "is_mapping": "{%- set d={'a':1} -%}{{- 'Y' if d is mapping else 'N' -}}",
    "is_iterable_str": "{{- 'Y' if 'ab' is iterable else 'N' -}}",
    "is_string": "{{- 'Y' if 'ab' is string else 'N' -}}",
    "is_sequence_dict": "{%- set d={'a':1} -%}{{- 'Y' if d is sequence else 'N' -}}",
    "tilde_concat": "{{- 'a' ~ 1 ~ 'b' -}}",
    "namespace_loop": "{%- set n=namespace(v=0) -%}{%- for i in [1,2] -%}{%- set n.v=n.v+i -%}{%- endfor -%}{{- n.v -}}",
    "trim": "{{- '  x  '|trim -}}",
    "default_filter": "{{- undef|default('D') -}}",
    "in_operator": "{{- 'Y' if 'b' in 'abc' else 'N' -}}",
    "bool_render": "{{- (1==1) -}}",
}


def _minja_render(source: str) -> str:
    """Render `source` under llama.cpp's minja and return its output.

    `llama-template-analysis` reports the rendered text as the "Common Prefix"
    of its probe diffs; for a message-independent template that is the whole
    output.
    """
    import subprocess
    import tempfile
    from pathlib import Path as _P

    with tempfile.TemporaryDirectory() as d:
        f = _P(d) / "probe.jinja"
        f.write_text(source)
        r = subprocess.run([MINJA_BIN, "--template-file", str(f)],
                           capture_output=True, text=True)
    out = _ANSI.sub("", r.stdout + r.stderr)
    if "Analysis failed" in out:
        return "<minja FAILED>"
    m = re.search(r"Common Prefix: '(.*?)'\s*\nCommon Suffix", out, re.S)
    return m.group(1) if m else "<unparsed>"


@pytest.mark.parametrize("name", sorted(CONSTRUCT_PROBES))
def test_jinja2_minja_construct_agreement(name: str) -> None:
    """Every Jinja construct our templates use must render identically under
    jinja2 and minja — or be pinned in KNOWN_DIVERGENCES with both outputs."""
    if MINJA_BIN is None:
        pytest.skip("llama-template-analysis not on PATH")
    from conftest import make_env

    source = CONSTRUCT_PROBES[name]
    j2 = make_env().from_string(source).render()
    mj = _minja_render(source)
    assert mj not in ("<unparsed>", "<minja FAILED>"), (
        f"could not obtain minja output for {name!r} — probe or extraction is "
        f"broken, not the engine. Got {mj!r}."
    )
    if name in KNOWN_DIVERGENCES:
        want_j2, want_mj = KNOWN_DIVERGENCES[name]
        assert (j2, mj) == (want_j2, want_mj), (
            f"KNOWN divergence {name!r} changed.\n"
            f"  expected jinja2={want_j2!r} minja={want_mj!r}\n"
            f"  actual   jinja2={j2!r} minja={mj!r}\n"
            f"If minja now AGREES with jinja2, delete the KNOWN_DIVERGENCES "
            f"entry and update docs/PATCH-CATALOG.md."
        )
    else:
        assert j2 == mj, (
            f"NEW jinja2/minja divergence in {name!r}:\n"
            f"  jinja2={j2!r}\n  minja ={mj!r}\n"
            f"Either avoid this construct in shipped templates, or pin it in "
            f"KNOWN_DIVERGENCES with a documented rationale."
        )


def test_tojson_escaping_divergence_is_an_injection_vector() -> None:
    """Pin the concrete consequence, not just the byte difference: a tool
    description containing `</tools>` is contained under jinja2 but breaks the
    `<tools>` envelope under minja. Upstream Qwen3.6 renders tool declarations
    with `{{- tool | tojson }}`, so this affects stock templates too — it is a
    RUNTIME caveat for llama.cpp users, not a defect introduced by our patches."""
    if MINJA_BIN is None:
        pytest.skip("llama-template-analysis not on PATH")
    from conftest import make_env

    probe = "{{- {'description':'x</tools>y'}|tojson -}}"
    j2 = make_env().from_string(probe).render()
    mj = _minja_render(probe)
    assert "</tools>" not in j2, f"jinja2 unexpectedly left the marker raw: {j2!r}"
    assert "</tools>" in mj, (
        f"minja now escapes the marker ({mj!r}) — the injection vector is gone; "
        f"update docs/PATCH-CATALOG.md and KNOWN_DIVERGENCES."
    )
