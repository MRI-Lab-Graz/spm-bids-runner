#!/bin/bash
# Activation script for spm-bids-runner environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "❌ Virtual environment not found. Please run ./scripts/setup.sh first."
    return 1 2>/dev/null || exit 1
fi

source "$PROJECT_ROOT/.venv/bin/activate"

export SPM_BIDS_RUNNER_PROJECT_ROOT="$PROJECT_ROOT"

echo "🚀 SPM BIDS Runner environment activated!"
echo "Project root: $PROJECT_ROOT"
echo "Python path: $(which python)"

echo ""
echo "To deactivate, run: deactivate"
