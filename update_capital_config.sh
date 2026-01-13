#!/bin/bash
#
# Update INITIAL_CAPITAL in .env to match actual WEEX account balance
#
# This prevents misleading P&L displays when the configured capital
# doesn't match the real account balance
#

echo "This script will help you set the correct INITIAL_CAPITAL in .env"
echo ""
echo "Your actual WEEX account balance appears to be around \$1,000 USDT"
echo "The .env currently has INITIAL_CAPITAL=1000000.0"
echo ""
echo "To fix the P&L calculation, we should update it to match reality."
echo ""
read -p "Enter your actual WEEX account balance in USDT (e.g., 1000): " ACTUAL_BALANCE

if [ -z "$ACTUAL_BALANCE" ]; then
    echo "No balance entered, exiting"
    exit 1
fi

echo "Updating .env to set INITIAL_CAPITAL=${ACTUAL_BALANCE}.0..."
sudo sed -i "s/^INITIAL_CAPITAL=.*/INITIAL_CAPITAL=${ACTUAL_BALANCE}.0/" /opt/AlphaGenesis/.env

echo "✓ Updated .env"
echo ""
echo "Restart the service to apply changes:"
echo "  sudo systemctl restart sdm-trading.service"
