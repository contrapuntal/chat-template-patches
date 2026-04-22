#!/usr/bin/env bash
# Refresh upstream chat templates from canonical sources.
#
# Usage:
#   fetch-upstream.sh [<family> ...]
#
# With no args, refreshes all families. With one or more family names
# (qwen3.5, qwen3.6, gemma4), refreshes only those.
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
    "gemma4|26B-A4B-it|https://huggingface.co/google/gemma-4-26B-A4B-it/raw/main/chat_template.jinja"
    "gemma4|31B-it|https://huggingface.co/google/gemma-4-31B-it/raw/main/chat_template.jinja"
    "gemma4|E2B-it|https://huggingface.co/google/gemma-4-E2B-it/raw/main/chat_template.jinja"
    "gemma4|E4B-it|https://huggingface.co/google/gemma-4-E4B-it/raw/main/chat_template.jinja"
)

want_families=("$@")

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

echo
echo "Done. $changed changed, $failed failed."
if [[ $changed -gt 0 ]]; then
    echo "Remember to update PROVENANCE.md and re-run pytest."
fi
# Exit nonzero only on fetch failures. A clean no-op (changed=0, failed=0)
# exits 0; partial failure with later successes still exits nonzero.
if [[ $failed -gt 0 ]]; then
    exit 1
fi
exit 0
