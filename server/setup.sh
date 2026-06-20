#!/bin/bash

# ===================================
# RackSorter - React Quick Start
# ===================================

echo "Starting RackSorter backend..."
echo ""

# Check if Python venv exists
if [ ! -d ".venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv .venv

echo ""
echo "=========================================="
echo "✅ Setup complete! Now run:"
echo "=========================================="
echo ""
echo "Terminal 1 (Backend):"
echo "  python -m uvicorn main:app --reload"
echo "
echo "=========================================="