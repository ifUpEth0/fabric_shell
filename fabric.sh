#!/bin/bash
# AI Fabric Shell - Unix/Linux Shell Script

# Change to script directory
cd "$(dirname "$0")"

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

# Check if fabric_shell directory exists
if [ ! -d "fabric_shell" ]; then
    echo "Error: fabric_shell directory not found"
    echo "Please ensure you have the correct directory structure"
    exit 1
fi

# Run the application
echo "Starting AI Fabric Shell..."
$PYTHON_CMD run.py