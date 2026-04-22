#!/usr/bin/env bash
# Apply a patched chat template to a model directory.
#
# Usage:
#   apply.sh <family> <size> <model-dir> [--symlink|--copy] [--no-backup]
#
# Examples:
#   apply.sh gemma4 26B-A4B-it ~/models/gemma-4-26b-a4b-it-MLX-8bit --symlink
#   apply.sh qwen3.6 35B-A3B ~/models/Qwen3.6-35B-A3B-MLX-8bit
#
# By default, copies the patched file (a snapshot at apply time) and creates
# a backup of the existing chat_template.jinja next to it as
# chat_template.jinja.upstream.<sha>.bak.
#
# --symlink uses ln -sf instead of cp; the model directory then tracks future
# repo updates automatically.
# --no-backup skips the backup step (useful when scripting bulk applies).

set -euo pipefail

usage() {
    grep -E '^# ' "$0" | sed 's/^# \?//'
    exit "${1:-1}"
}

[[ $# -ge 3 ]] || usage

family="$1"
size="$2"
model_dir="$3"
shift 3

mode="copy"
backup=true
while [[ $# -gt 0 ]]; do
    case "$1" in
        --symlink) mode="symlink" ;;
        --copy) mode="copy" ;;
        --no-backup) backup=false ;;
        -h|--help) usage 0 ;;
        *) echo "Unknown option: $1" >&2; usage ;;
    esac
    shift
done

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
patched="$repo_root/templates/$family/patched/$size.jinja"
target="$model_dir/chat_template.jinja"

if [[ ! -f "$patched" ]]; then
    echo "ERROR: no patched template at $patched" >&2
    echo "       check templates/$family/patched/ for available sizes" >&2
    exit 2
fi

if [[ ! -d "$model_dir" ]]; then
    echo "ERROR: model directory does not exist: $model_dir" >&2
    exit 2
fi

if [[ -f "$target" && "$backup" == true ]]; then
    sha=$(shasum -a 256 "$target" | cut -c1-12)
    backup_path="$target.upstream.$sha.bak"
    if [[ ! -f "$backup_path" ]]; then
        cp "$target" "$backup_path"
        echo "Backed up existing template to $backup_path"
    else
        echo "Backup already exists at $backup_path (skipped)"
    fi
fi

if [[ "$mode" == "symlink" ]]; then
    ln -sf "$patched" "$target"
    echo "Symlinked $patched -> $target"
else
    cp "$patched" "$target"
    echo "Copied $patched -> $target"
fi

# Show patch identity
sha_new=$(shasum -a 256 "$patched" | cut -c1-12)
echo "Applied template sha: $sha_new ($family/$size)"
