#!/usr/bin/env python3
"""Render every (template, fixture) pair and report drift vs golden files.

Quick smoke check that's lighter than the full pytest harness — useful for
CI quick-feedback or local development.

Usage:
    scripts/verify.py [--write-goldens]

With --write-goldens, captures current renderings as the new golden files
(use after intentional template changes; commit the diff explicitly).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))

from conftest import (  # noqa: E402
    FIXTURES,
    GOLDEN,
    TemplatePair,
    all_template_pairs,
    fixture_applies_to,
    load_fixture,
    render,
)


def golden_path(pair: TemplatePair, variant: str, fixture_name: str) -> Path:
    return GOLDEN / f"{pair.family}-{pair.size}-{variant}-{fixture_name}.txt"


def fixture_names() -> list[str]:
    return sorted(p.stem for p in FIXTURES.glob("*.json"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-goldens", action="store_true")
    args = parser.parse_args()

    GOLDEN.mkdir(exist_ok=True)
    drift = 0
    written = 0
    skipped = 0
    for pair in all_template_pairs():
        for variant in ("upstream", "patched"):
            template_path = pair.upstream if variant == "upstream" else pair.patched
            if not template_path.is_file():
                continue
            for fname in fixture_names():
                payload = load_fixture(fname)
                # Filter by `_applies_to` so a Qwen-only fixture isn't
                # rendered against Gemma 4 templates and vice versa.
                if not fixture_applies_to(payload, pair.family):
                    skipped += 1
                    continue
                try:
                    out = render(template_path, payload)
                except Exception as e:  # noqa: BLE001
                    print(f"  ERROR {pair.family}/{variant}/{pair.size}/{fname}: {e}")
                    drift += 1
                    continue

                gpath = golden_path(pair, variant, fname)
                if args.write_goldens:
                    gpath.write_text(out)
                    written += 1
                    continue

                if not gpath.exists():
                    print(f"  MISSING golden: {gpath.name}")
                    drift += 1
                    continue

                expected = gpath.read_text()
                if out != expected:
                    print(f"  DRIFT {pair.family}/{variant}/{pair.size}/{fname}")
                    drift += 1

    if args.write_goldens:
        print(f"\nWrote {written} golden files.")
        return 0

    if drift:
        print(f"\n{drift} drift(s) found. Re-run with --write-goldens to accept.")
        return 1
    print("All renders match goldens.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
