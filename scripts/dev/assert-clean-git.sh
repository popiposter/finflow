#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

unstaged="$(git diff --name-only --ignore-cr-at-eol)"
staged="$(git diff --cached --name-only --ignore-cr-at-eol)"

if [[ -n "$unstaged" || -n "$staged" ]]; then
  echo "Advisory: working tree has local changes."
  echo "Unstaged:"
  echo "$unstaged"
  echo "Staged:"
  echo "$staged"
else
  echo "Working tree looks clean."
fi
