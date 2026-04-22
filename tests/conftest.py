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
