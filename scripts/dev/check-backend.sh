#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR/backend"

echo "Running backend validation (CI-equivalent)..."
echo ""
echo "Installing dependencies via uv..."
uv sync --extra dev

echo ""
echo "Running mypy type checks..."
uv run python -m mypy . --show-error-codes --pretty

echo ""
echo "Running pytest..."
uv run python -m pytest tests/

echo ""
echo "✓ All checks passed"
