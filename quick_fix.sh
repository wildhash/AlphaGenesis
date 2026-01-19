#!/bin/bash
#
# Quick Fix Script for VM Deployment
# This script applies the gymnasium migration and installs dependencies
#

set -e

echo "======================================================================"
echo "  Quick Fix: Gymnasium Migration & Dependencies"
echo "======================================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: Not in AlphaGenesis directory"
    echo "Please run: cd /opt/AlphaGenesis"
    exit 1
fi

echo "Step 1: Updating rl_agent.py to use Gymnasium..."
sed -i 's/^import gym$/import gymnasium as gym/' alphagenesis/models/rl_agent.py
sed -i 's/^from gym import/from gymnasium import/' alphagenesis/models/rl_agent.py
echo "✓ rl_agent.py updated"
echo ""

echo "Step 2: Installing Poetry dependencies..."
export PATH="/home/alphagenesis/.local/bin:$PATH"

# Try different poetry commands based on version
if poetry install --only main &>/dev/null; then
    echo "✓ Dependencies installed with --only main"
elif poetry install --no-dev &>/dev/null; then
    echo "✓ Dependencies installed with --no-dev"
else
    echo "Installing with pip fallback..."
    pip3 install gymnasium matplotlib plotly arch seaborn
    echo "✓ Critical packages installed via pip"
fi
echo ""

echo "Step 3: Verifying critical packages..."
python3 -c "import gymnasium; print('✓ gymnasium')"
python3 -c "import matplotlib; print('✓ matplotlib')"
python3 -c "import plotly; print('✓ plotly')"
python3 -c "import arch; print('✓ arch')"
echo ""

echo "======================================================================"
echo "  Fix Complete!"
echo "======================================================================"
echo ""
echo "Now run the test:"
echo "  set -a && source .env && set +a && DRY_RUN=true timeout 30s python3 -m alphagenesis.sdm.sdm_engine 2>&1 | head -20"
echo ""
