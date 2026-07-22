#!/usr/bin/env python3
"""Re-verify the community source snapshots in docs/sources/.

`docs/sources/README.md` records, for every snapshot, its SHA-256 prefix and
the original URL. Those hosts (pastebin, gists, Reddit, third-party HF and
GitHub repos) are exactly the ones that vanish, and the repo's own policy is:

    "Treat any 4xx on re-fetch as a finding to record in the catalog (e.g.
     update the patch's provenance tier from community-tracker to
     community-deleted)."

Nothing enforced that, so decay accrued silently. This script does the sweep.

Classification
--------------
  OK        re-fetched, bytes match the recorded SHA-256.
  MOVED     content changed at a URL that tracks a MOVING ref (`/raw/main/`,
            or a row whose URL cell says "as of <date>"). Expected — the
            snapshot is the point-in-time record. Informational.
  CHANGED   content changed at a URL that is supposed to be PINNED (a commit
            SHA in the path). A pinned artifact must never change: FINDING.
  GONE      404/410 — the source is DELETED. FINDING: downgrade the provenance
            tier in docs/PATCH-CATALOG.md (community-tracker -> deleted).
  BLOCKED   401/403/429 — the host now gates automated access. FINDING, but a
            different one: the content may well still exist for a human, and
            the local snapshot is now the only machine-readable copy — which
            raises its value rather than invalidating it. Do NOT downgrade the
            tier on this alone; verify by hand.
  ERROR     network/other failure. Not a finding by itself; re-run.

Exit status: 0 when there are no findings (GONE / CHANGED), 1 otherwise.

Usage:  scripts/check-sources.py [--timeout SECONDS] [--quiet]
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "docs" / "sources" / "README.md"
# Match the UA the manifest itself documents for re-fetching: Reddit (and
# others) gate bare/unknown agents with 403, which would otherwise be
# misreported as decay.
UA = "Mozilla/5.0 chat-template-patches archival"

ROW = re.compile(
    r"^\|\s*`(?P<file>[^`]+)`\s*\|\s*`(?P<sha>[0-9a-f]{6,})`\s*\|(?P<urlcell>[^|]*)\|"
)
URL_IN_CELL = re.compile(r"https?://\S+")
# a commit-pinned HF/GitHub raw path, e.g. /raw/e1eb965/ or /raw/<40-hex>/
PINNED = re.compile(r"/raw/(?:[0-9a-f]{7,40})/")


def raw_url(url: str) -> str | None:
    """Map a human-facing URL to the RAW artifact the snapshot actually holds.

    The manifest records the URL a human should visit, not the one we fetched.
    Comparing a gist landing page (HTML) against a snapshotted .jinja will
    always "differ", which is noise, not decay. Return None when the raw form
    cannot be derived — better to report NOCHECK than to invent a verdict.
    """
    # Reddit: snapshots are of the JSON API view
    if re.search(r"reddit\.com/r/[^/]+/comments/", url):
        return url.rstrip("/") + "/.json"
    # GitHub blob -> raw.githubusercontent
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/blob/(.+)$", url)
    if m:
        return f"https://raw.githubusercontent.com/{m.group(1)}/{m.group(2)}/{m.group(3)}"
    # Gist landing page -> /raw (single-file gists)
    m = re.match(r"https://gist\.github\.com/([^/]+)/([0-9a-f]+)/?$", url)
    if m:
        return url.rstrip("/") + "/raw"
    # Bare GitHub repo page: the file path is prose in the manifest, not derivable
    if re.match(r"https://github\.com/[^/]+/[^/]+/?$", url):
        return None
    return url


def parse_manifest(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        m = ROW.match(line.strip())
        if not m:
            continue
        cell = m.group("urlcell")
        u = URL_IN_CELL.search(cell)
        if not u:
            continue
        url = u.group(0).rstrip(").,`")
        rows.append({
            "file": m.group("file"),
            "sha": m.group("sha"),
            "url": url,
            # a row annotated "as of <date>" is knowingly tracking a moving ref
            "moving": bool(PINNED.search(url)) is False or "as of" in cell.lower(),
            "pinned": bool(PINNED.search(url)),
        })
    return rows


def fetch(url: str, timeout: int) -> tuple[str | None, str]:
    """Return (sha256_hex | None, status). status is '' on success."""
    r = subprocess.run(
        ["curl", "-sSL", "-A", UA, "--max-time", str(timeout),
         "-w", "\n%{http_code}", url],
        capture_output=True,
    )
    if r.returncode != 0:
        return None, (r.stderr.decode(errors="replace").strip().splitlines() or ["curl failed"])[-1]
    body, _, code = r.stdout.rpartition(b"\n")
    code_s = code.decode(errors="replace").strip()
    if code_s.startswith("4") or code_s.startswith("5"):
        return None, f"HTTP {code_s}"
    return hashlib.sha256(body).hexdigest(), ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--quiet", action="store_true", help="only print findings")
    args = ap.parse_args()

    rows = parse_manifest(MANIFEST.read_text())
    if not rows:
        print("no snapshot rows parsed from docs/sources/README.md", file=sys.stderr)
        return 1

    findings: list[str] = []
    counts = {"OK": 0, "MOVED": 0, "CHANGED": 0, "GONE": 0,
              "BLOCKED": 0, "ERROR": 0, "MISSING": 0, "NOCHECK": 0}
    print(f"Source snapshot check — {len(rows)} recorded snapshot(s)\n")

    for row in rows:
        local = REPO / "docs" / "sources" / row["file"]
        label = row["file"]
        if not local.is_file():
            counts["MISSING"] += 1
            findings.append(f"MISSING  {label} — recorded in README but not on disk")
            print(f"  MISSING  {label}")
            continue

        target = raw_url(row["url"])
        if target is None:
            counts["NOCHECK"] += 1
            if not args.quiet:
                print(f"  NOCHECK  {label}  (raw URL not derivable from the recorded page URL)")
            continue
        digest, err = fetch(target, args.timeout)
        if digest is None:
            if err.startswith(("HTTP 404", "HTTP 410")):
                counts["GONE"] += 1
                findings.append(
                    f"GONE     {label} — {err} at {target}\n"
                    f"           -> source DELETED; downgrade its provenance tier in"
                    f" docs/PATCH-CATALOG.md"
                )
                print(f"  GONE     {label}  ({err})")
            elif err.startswith(("HTTP 401", "HTTP 403", "HTTP 429")):
                counts["BLOCKED"] += 1
                findings.append(
                    f"BLOCKED  {label} — {err} at {target}\n"
                    f"           -> host gates automated access; verify by hand. The local"
                    f" snapshot may now be the only machine-readable copy."
                )
                print(f"  BLOCKED  {label}  ({err})")
            else:
                counts["ERROR"] += 1
                print(f"  ERROR    {label}  ({err})")
            continue

        if digest.startswith(row["sha"]):
            counts["OK"] += 1
            if not args.quiet:
                print(f"  OK       {label}")
        elif row["pinned"] and "as of" not in row["url"]:
            counts["CHANGED"] += 1
            findings.append(
                f"CHANGED  {label} — PINNED url changed content\n"
                f"           recorded {row['sha']}  live {digest[:12]}\n"
                f"           -> a commit-pinned artifact must not change; investigate"
            )
            print(f"  CHANGED  {label}  ({row['sha']} -> {digest[:12]})  PINNED")
        else:
            counts["MOVED"] += 1
            if not args.quiet:
                print(f"  MOVED    {label}  ({row['sha']} -> {digest[:12]})  moving ref, expected")

    print("\n" + "  ".join(f"{k}={v}" for k, v in counts.items() if v))
    if findings:
        print("\nFINDINGS:")
        for f in findings:
            print("  " + f)
        return 1
    print("\nNo findings — every snapshot still resolves and pinned content is intact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
