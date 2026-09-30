#!/bin/bash
set -e

echo "=== Markazi Database Setup for Linux Server ==="

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed. Run: sudo apt install python3 -y"
    exit 1
fi

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "Warning: psql command not found in PATH. Make sure postgresql-client is installed:"
    echo "sudo apt install postgresql postgresql-client -y"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

if [ -f "venv/bin/python" ]; then
    PYTHON_EXEC="venv/bin/python"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_EXEC=".venv/bin/python"
else
    PYTHON_EXEC="python3"
fi

echo "Running setup script using $PYTHON_EXEC..."
$PYTHON_EXEC scripts/setup_database.py
