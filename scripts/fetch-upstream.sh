#!/usr/bin/env bash
# Refresh upstream chat templates from canonical sources.
#
# Usage:
#   fetch-upstream.sh [--check] [<family> ...]
#
# With no args, refreshes all families. With one or more family names
# (qwen3.5, qwen3.6, gemma4), refreshes only those.
#
#   --check   READ-ONLY drift detection: fetch and compare, but never write
#             to upstream/. Exits 1 if any tracked template has drifted or
#             could not be fetched. This is the mode to run on a schedule —
#             it turns "someone happens to notice" into "the repo tells you".
#             Google's 2026-07-09 Gemma 4 rewrite went undetected for 11 days,
#             during which the shipped Qwen3.6 template was separately broken
#             on llama.cpp; both were found only because someone asked.
#
# Reports any SHA-256 changes vs the current upstream/ files. Does NOT
# auto-update PROVENANCE.md — review the diff and update by hand.

set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

# (family, size, source-url) records. Edit when adding new sizes/families.
sources=(
    "qwen3.5|0.8B|https://huggingface.co/Qwen/Qwen3.5-0.8B/raw/main/chat_template.jinja"
    "qwen3.5|2B|https://huggingface.co/Qwen/Qwen3.5-2B/raw/main/chat_template.jinja"
    "qwen3.5|4B|https://huggingface.co/Qwen/Qwen3.5-4B/raw/main/chat_template.jinja"
    "qwen3.5|9B|https://huggingface.co/Qwen/Qwen3.5-9B/raw/main/chat_template.jinja"
    "qwen3.5|27B|https://huggingface.co/Qwen/Qwen3.5-27B/raw/main/chat_template.jinja"
    "qwen3.5|35B-A3B|https://huggingface.co/Qwen/Qwen3.5-35B-A3B/raw/main/chat_template.jinja"
    "qwen3.5|122B-A10B|https://huggingface.co/Qwen/Qwen3.5-122B-A10B/raw/main/chat_template.jinja"
    "qwen3.6|35B-A3B|https://huggingface.co/unsloth/Qwen3.6-35B-A3B-MLX-8bit/raw/main/chat_template.jinja"
    "gemma4|12B-it|https://huggingface.co/google/gemma-4-12B-it/raw/main/chat_template.jinja"
    "gemma4|26B-A4B-it|https://huggingface.co/google/gemma-4-26B-A4B-it/raw/main/chat_template.jinja"
    "gemma4|31B-it|https://huggingface.co/google/gemma-4-31B-it/raw/main/chat_template.jinja"
    "gemma4|E2B-it|https://huggingface.co/google/gemma-4-E2B-it/raw/main/chat_template.jinja"
    "gemma4|E4B-it|https://huggingface.co/google/gemma-4-E4B-it/raw/main/chat_template.jinja"
)

check_only=false
args=()
for a in "$@"; do
    if [[ "$a" == "--check" ]]; then
        check_only=true
    else
        args+=("$a")
    fi
done
want_families=("${args[@]+"${args[@]}"}")

if $check_only; then
    echo "Upstream drift check (read-only) — $(date -u +%Y-%m-%dT%H:%MZ)"
    echo
fi

changed=0
failed=0
for record in "${sources[@]}"; do
    IFS='|' read -r family size url <<<"$record"

    if [[ ${#want_families[@]} -gt 0 ]]; then
        match=false
        for f in "${want_families[@]}"; do
            [[ "$f" == "$family" ]] && match=true && break
        done
        $match || continue
    fi

    target="templates/$family/upstream/$size.jinja"
    mkdir -p "$(dirname "$target")"

    old_sha=""
    if [[ -f "$target" ]]; then
        old_sha=$(shasum -a 256 "$target" | cut -c1-12)
    fi

    tmp=$(mktemp)
    if curl -sSLf "$url" -o "$tmp"; then
        new_sha=$(shasum -a 256 "$tmp" | cut -c1-12)
        if [[ "$old_sha" == "$new_sha" ]]; then
            echo "  $family/$size  unchanged  ($new_sha)"
            rm -f "$tmp"
        elif $check_only; then
            rm -f "$tmp"
            echo "* $family/$size  DRIFTED    ($old_sha -> $new_sha)"
            changed=$((changed + 1))
        else
            mv "$tmp" "$target"
            echo "* $family/$size  CHANGED    ($old_sha -> $new_sha)"
            changed=$((changed + 1))
        fi
    else
        rm -f "$tmp"
        echo "! $family/$size  FETCH FAILED  $url" >&2
        failed=$((failed + 1))
    fi
done

# Community template trackers: not vendored into upstream/, but their version
# drives catalog entries, so a bump is a signal to run a source sweep.
if [[ ${#want_families[@]} -eq 0 ]]; then
    echo
    echo "Community trackers:"
    frog_snap="docs/sources/hf-snapshots/froggeric-Qwen-Fixed-Chat-Templates-v21.3.jinja"
    frog_url="https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates/raw/main/chat_template.jinja"
    tmp=$(mktemp)
    if curl -sSLf "$frog_url" -o "$tmp"; then
        live=$(shasum -a 256 "$tmp" | cut -c1-12)
        have=$(shasum -a 256 "$frog_snap" 2>/dev/null | cut -c1-12)
        ver=$(grep -m1 -oE 'template_version = "[^"]+"' "$tmp" | sed 's/.*"\(.*\)"/\1/')
        if [[ "$live" == "$have" ]]; then
            echo "  froggeric  unchanged  ($live${ver:+, $ver})"
        else
            echo "* froggeric  DRIFTED    ($have -> $live${ver:+, now $ver}) — run a source sweep"
            changed=$((changed + 1))
        fi
    else
        echo "! froggeric  FETCH FAILED  $frog_url" >&2
        failed=$((failed + 1))
    fi
    rm -f "$tmp"
fi

echo
if $check_only; then
    echo "Drift check: $changed drifted, $failed unreachable."
    if [[ $changed -gt 0 ]]; then
        echo "Run without --check to pull the new templates, then update"
        echo "PROVENANCE.md, re-run pytest, and re-verify retired patches:"
        echo "an upstream rewrite can silently FIX a carry (retire it) or"
        echo "silently BREAK one. Both happened on 2026-07-09."
    fi
else
    echo "Done. $changed changed, $failed failed."
    if [[ $changed -gt 0 ]]; then
        echo "Remember to update PROVENANCE.md and re-run pytest."
    fi
fi
# Exit nonzero only on fetch failures. A clean no-op (changed=0, failed=0)
# exits 0; partial failure with later successes still exits nonzero.
# --check exits nonzero on drift OR unreachable (it is a gate).
# Refresh mode exits nonzero only on fetch failure.
if $check_only; then
    if [[ $changed -gt 0 || $failed -gt 0 ]]; then
        exit 1
    fi
elif [[ $failed -gt 0 ]]; then
    exit 1
fi
exit 0
