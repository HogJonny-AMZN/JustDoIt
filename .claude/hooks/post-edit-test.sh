#!/usr/bin/env bash
# post-edit-test.sh
# Run the test suite when core or effects files are modified.
# Claude Code hook: triggers after file edits matching justdoit/ or tests/

set -euo pipefail

CHANGED_FILE="${1:-}"

# Only trigger for source code changes
if [[ "$CHANGED_FILE" == justdoit/* ]] || [[ "$CHANGED_FILE" == tests/* ]]; then
    echo "→ Running tests after edit to $CHANGED_FILE..."
    .venv/bin/pytest tests/ -q --tb=short 2>&1 | tail -20
fi
