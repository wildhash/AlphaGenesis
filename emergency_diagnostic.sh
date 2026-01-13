#!/bin/bash
#
# Emergency diagnostic - what just happened?
#

echo "======================================================================"
echo "EMERGENCY DIAGNOSTIC - WHAT HAPPENED?"
echo "======================================================================"
echo ""

echo "Last 20 trades/actions:"
sudo journalctl -u sdm-trading.service --since "30 minutes ago" --no-pager | grep -E "EXECUTING ACTION|Order placed|Order failed|Direction:|Size:|Price:" | tail -40

echo ""
echo "======================================================================"
echo "Current P&L Status:"
sudo journalctl -u sdm-trading.service -n 200 --no-pager | grep "Capital:" | tail -5

echo ""
echo "======================================================================"
echo "What regimes are we detecting?"
sudo journalctl -u sdm-trading.service --since "10 minutes ago" --no-pager | grep -E "Bound.*->" | tail -10

echo ""
echo "======================================================================"
echo "Any errors?"
sudo journalctl -u sdm-trading.service --since "30 minutes ago" --no-pager | grep "ERROR" | tail -10

echo ""
echo "======================================================================"
