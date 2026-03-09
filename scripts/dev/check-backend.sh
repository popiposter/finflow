#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

pre-commit run --all-files

if [[ -n "$(git status --porcelain)" ]]; then
  echo
  echo "pre-commit modified files or the git tree is not clean."
  echo "Review the diff, stage changes, amend/commit, and rerun this script."
  git status --short
  exit 1
fi

cd backend
mypy .
pytest tests/
