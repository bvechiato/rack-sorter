#!/bin/bash

# ===================================
# RackSorter - React Quick Start
# ===================================

echo "Starting RackSorter..."
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Check if Python venv exists
if [ ! -d ".venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv .venv
fi

echo ""
echo "=========================================="
echo "✅ Setup complete! Now run:"
echo "=========================================="
echo ""
echo "Terminal 1 (Backend):"
echo "  python -m uvicorn main:app --reload"
echo ""
echo "Terminal 2 (Frontend):"
echo "  npm run dev"
echo ""
echo "Then open: http://localhost:3000"
echo ""
echo "For production build:"
echo "  npm run build"
echo "=========================================="
