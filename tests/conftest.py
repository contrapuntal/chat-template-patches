"""Shared pytest fixtures and helpers for the render harness.

The harness is deliberately small: it wraps a Jinja2 Environment with the
set of globals and filters that Hugging Face's `transformers.AutoTokenizer`
exposes during chat-template rendering. This lets us render the real
on-disk `chat_template.jinja` files the same way `apply_chat_template` does,
without pulling in the full `transformers` dependency tree.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jinja2
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = REPO_ROOT / "templates"
FIXTURES = Path(__file__).parent / "fixtures"
GOLDEN = Path(__file__).parent / "golden"


def _raise_exception(msg: str) -> None:  # noqa: D401
    """HF-compatible template helper."""
    raise RuntimeError(msg)


def _strftime_now(fmt: str) -> str:
    import datetime

    return datetime.datetime.now().strftime(fmt)


def make_env() -> jinja2.Environment:
    """A Jinja2 environment configured to match HF tokenizer rendering.

    Keep this in sync with what `transformers.utils.chat_template_utils`
    registers — currently just `raise_exception`, `strftime_now`, and the
    `tojson` filter (built in).
    """
    env = jinja2.Environment(
        trim_blocks=True,
        lstrip_blocks=False,
        keep_trailing_newline=True,
    )
    env.globals["raise_exception"] = _raise_exception
    env.globals["strftime_now"] = _strftime_now
    return env


def render(template_path: Path, payload: dict[str, Any]) -> str:
    env = make_env()
    source = template_path.read_text()
    template = env.from_string(source)
    # Most HF chat templates expect `bos_token`, `eos_token`, `add_generation_prompt`
    # to be accessible even when the fixture doesn't supply them.
    ctx = {
        "bos_token": "",
        "eos_token": "",
        "pad_token": "",
        "add_generation_prompt": True,
        "add_vision_id": False,
        "tools": None,
    }
    ctx.update(payload)
    return template.render(**ctx)


def load_fixture(name: str) -> dict[str, Any]:
    path = FIXTURES / f"{name}.json"
    return json.loads(path.read_text())


def fixture_applies_to(fixture: dict[str, Any], family: str) -> bool:
    """Return True if `fixture` is intended to render against `family` templates.

    Fixtures declare `_applies_to` as a list of family names (e.g.
    `["gemma4"]`, `["qwen3.6"]`) or `["*"]` for the universal/smoke case.
    Fixtures missing `_applies_to` are treated as universal so legacy
    fixtures continue to work, but adding the key is recommended.
    """
    declared = fixture.get("_applies_to") or ["*"]
    return "*" in declared or family in declared


# Families the repo declares are in scope. Used by tests to assert that
# every declared family ships at least one patched template (preventing
# silent "patched dir is empty so nothing runs" green-suite failures).
DECLARED_FAMILIES = ("gemma4", "qwen3.5", "qwen3.6")

# Families that are intentionally catalog-only as of this release. Listing
# a family here documents that the patched/ dir is expected empty and
# disables the "must ship at least one patched template" assertion. Move
# a family OUT of this set when its first patched template is added.
CATALOG_ONLY_FAMILIES = frozenset({"qwen3.5"})


@dataclass(frozen=True)
class TemplatePair:
    family: str
    size: str
    upstream: Path
    patched: Path

    @property
    def patched_exists(self) -> bool:
        return self.patched.is_file()


def all_template_pairs() -> list[TemplatePair]:
    pairs: list[TemplatePair] = []
    for family_dir in sorted(TEMPLATES.iterdir()):
        if not family_dir.is_dir():
            continue
        upstream_dir = family_dir / "upstream"
        patched_dir = family_dir / "patched"
        if not upstream_dir.is_dir():
            continue
        for upstream_file in sorted(upstream_dir.glob("*.jinja")):
            size = upstream_file.stem
            pairs.append(
                TemplatePair(
                    family=family_dir.name,
                    size=size,
                    upstream=upstream_file,
                    patched=patched_dir / f"{size}.jinja",
                )
            )
    return pairs


@pytest.fixture(scope="session")
def template_pairs() -> list[TemplatePair]:
    return all_template_pairs()
