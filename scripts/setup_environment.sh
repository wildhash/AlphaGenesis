#!/bin/bash

# AlphaGenesis Environment Setup Script
# Sets up the development environment for the WEEX AI Wars hackathon trading system

set -e

echo "========================================="
echo "AlphaGenesis Environment Setup"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

required_version="3.9"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.9 or higher is required"
    exit 1
fi

echo "✓ Python version OK"
echo ""

# Check if Poetry is installed
echo "Checking for Poetry..."
if ! command -v poetry &> /dev/null; then
    echo "Poetry not found. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    echo "Please add Poetry to your PATH and re-run this script"
    echo "Run: export PATH=\"\$HOME/.local/bin:\$PATH\""
    exit 1
fi

echo "✓ Poetry found: $(poetry --version)"
echo ""

# Install dependencies
echo "Installing dependencies with Poetry..."
poetry install

echo "✓ Dependencies installed"
echo ""

# Create necessary directories
echo "Creating directory structure..."
mkdir -p data/raw
mkdir -p data/processed
mkdir -p models/saved
mkdir -p logs
mkdir -p reports

echo "✓ Directories created"
echo ""

# Setup environment file
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✓ .env file created"
        echo ""
        echo "⚠️  IMPORTANT: Please edit .env and add your WEEX API credentials:"
        echo "   - WEEX_API_KEY"
        echo "   - WEEX_API_SECRET"
        echo "   - WEEX_API_PASSPHRASE"
        echo ""
    else
        echo "Warning: .env.example not found"
    fi
else
    echo "✓ .env file already exists"
    echo ""
fi

# Run tests to verify installation
echo "Running tests to verify installation..."
poetry run pytest tests/ -v --tb=short || echo "⚠️  Some tests failed, but installation is complete"

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   poetry shell"
echo ""
echo "2. Configure your WEEX API credentials in .env"
echo ""
echo "3. Run the example script:"
echo "   poetry run python scripts/example_usage.py"
echo ""
echo "4. Run a backtest:"
echo "   poetry run python scripts/run_backtest.py"
echo ""
echo "For WEEX AI Wars Hackathon participants:"
echo "- Remember to complete team registration (BUIDL) on WEEX portal"
echo "- Pass the mandatory API test (place 10 USDT live order)"
echo "- Review risk limits: Max leverage 20x, Max daily DD 10%, Max total DD 25%"
echo ""
echo "Good luck in the hackathon! 🚀"
