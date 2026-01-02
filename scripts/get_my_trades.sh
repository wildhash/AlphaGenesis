#!/bin/bash
# Quick Trade History Retrieval
# Run this on your GCP VM with whitelisted IP

set -e

echo "================================================================================"
echo "WEEX TRADE HISTORY RETRIEVAL"
echo "================================================================================"

# Verify IP
echo "Verifying IP address..."
CURRENT_IP=$(curl -s ifconfig.me)
echo "Current IP: $CURRENT_IP"

if [ "$CURRENT_IP" = "34.133.16.230" ]; then
    echo "✅ IP matches whitelisted IP!"
else
    echo "⚠️  Warning: IP is $CURRENT_IP (expected 34.133.16.230)"
fi

# Check if repo exists
if [ -d "AlphaGenesis" ]; then
    echo "✅ Repository found, updating..."
    cd AlphaGenesis
    git fetch origin
    git checkout claude/execute-btcusdt-order-N8usg
    git pull origin claude/execute-btcusdt-order-N8usg
else
    echo "Cloning repository..."
    git clone https://github.com/wildhash/AlphaGenesis.git
    cd AlphaGenesis
    git checkout claude/execute-btcusdt-order-N8usg
fi

# Install dependencies if needed
echo "Checking dependencies..."
python3 -c "import requests" 2>/dev/null || {
    echo "Installing requests..."
    pip3 install requests --break-system-packages 2>/dev/null || pip3 install requests
}

# Fetch trade history
echo ""
echo "================================================================================"
echo "FETCHING YOUR TRADE HISTORY..."
echo "================================================================================"
python3 scripts/get_trade_history.py

# Show what files were created
echo ""
echo "================================================================================"
echo "FILES CREATED:"
echo "================================================================================"
ls -lh *.json 2>/dev/null || echo "No JSON files created"

echo ""
echo "================================================================================"
echo "QUICK VIEW - TRADE LOG:"
echo "================================================================================"
if [ -f "trade_log.json" ]; then
    cat trade_log.json | python3 -m json.tool 2>/dev/null || cat trade_log.json
else
    echo "No trade_log.json found"
fi

echo ""
echo "================================================================================"
echo "To download these files to your local machine, run:"
echo "gcloud compute scp [VM-NAME]:~/AlphaGenesis/*.json ./ --zone=us-central1-a"
echo "================================================================================"
