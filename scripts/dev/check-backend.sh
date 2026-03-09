#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR/backend"

echo "Running backend validation..."
echo "Optional manual Python formatting step if Ruff is installed: ruff check . && ruff format ."

mypy .
pytest tests/
