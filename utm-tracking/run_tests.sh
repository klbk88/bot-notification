#!/bin/bash

# Script to run tests for UTM tracking ML models

set -e

echo "🧪 UTM Tracking Tests Runner"
echo "=============================="
echo ""

# Check if we're in the right directory
if [ ! -d "tests" ]; then
    echo "❌ Error: tests directory not found"
    echo "Please run this script from utm-tracking directory"
    exit 1
fi

# Check Python version
echo "📦 Checking Python..."
python3 --version || { echo "❌ Python 3 not found"; exit 1; }
echo "✅ Python OK"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q -r requirements-test.txt
echo "✅ Dependencies installed"
echo ""

# Run tests
echo "🧪 Running tests..."
echo ""

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run unit tests
echo "▶️  Unit tests..."
python3 -m pytest tests/unit/ -v --tb=short || true
echo ""

# Run integration tests (may fail due to auth requirements)
echo "▶️  Integration tests..."
python3 -m pytest tests/integration/ -v --tb=short || true
echo ""

# Run with coverage
echo "▶️  Coverage report..."
python3 -m pytest tests/ --cov=utils --cov=api --cov-report=term-missing --cov-report=html || true
echo ""

# Results
if [ -f "htmlcov/index.html" ]; then
    echo "✅ Coverage report generated: htmlcov/index.html"
    echo ""
    echo "To view coverage report:"
    echo "  open htmlcov/index.html"
fi

echo ""
echo "🎉 Tests completed!"
echo ""
echo "Quick commands:"
echo "  Run all tests:        pytest"
echo "  Run unit tests:       pytest tests/unit/"
echo "  Run with coverage:    pytest --cov=utils --cov=api"
echo "  Run single file:      pytest tests/unit/test_markov_chain.py"
echo ""
