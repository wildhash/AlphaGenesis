#!/bin/bash
#
# Quick performance check for WEEX trading system
#

echo "======================================================================"
echo "WEEX AI WARS - PERFORMANCE CHECK"
echo "======================================================================"
echo ""

echo "Service Status:"
sudo systemctl status sdm-trading.service --no-pager | grep "Active:"
echo ""

echo "Recent Trading Activity (last 30 lines):"
sudo journalctl -u sdm-trading.service -n 30 --no-pager | grep -E "EXECUTING ACTION|Order placed|Order failed|Capital:|Daily Trades:|Learning:|Ethics:"
echo ""

echo "Current System Status:"
sudo journalctl -u sdm-trading.service -n 100 --no-pager | grep -A 10 "SDM SYSTEM STATUS" | tail -15
echo ""

echo "Trade Success Rate:"
sudo journalctl -u sdm-trading.service --since "1 hour ago" --no-pager | grep "Learning:" | tail -1
echo ""

echo "Recent Errors:"
sudo journalctl -u sdm-trading.service --since "30 minutes ago" --no-pager | grep "ERROR" | tail -5
echo ""

echo "======================================================================"
