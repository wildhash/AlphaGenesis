#!/bin/bash
# Quick health check script for the trading system
# Run this to diagnose the current state

echo "========================================="
echo "AlphaGenesis Trading System Health Check"
echo "========================================="
echo ""

echo "1. SERVICE STATUS"
echo "-----------------"
sudo systemctl status sdm-trading.service --no-pager -l | head -20
echo ""

echo "2. RECENT LOGS (Last 50 lines)"
echo "-------------------------------"
sudo journalctl -u sdm-trading.service -o cat -n 50
echo ""

echo "3. SIGNAL GENERATION (Last 10 minutes)"
echo "---------------------------------------"
SIGNAL_COUNT=$(sudo journalctl -u sdm-trading.service -o cat --since "10 minutes ago" | grep "DIAG_SIGNAL_GENERATED" | wc -l)
echo "Signals generated: $SIGNAL_COUNT"
sudo journalctl -u sdm-trading.service -o cat --since "10 minutes ago" | grep "DIAG_SIGNAL_GENERATED" | tail -5
echo ""

echo "4. ERRORS (Last 10 minutes)"
echo "---------------------------"
sudo journalctl -u sdm-trading.service -o cat --since "10 minutes ago" | grep -i "error\|exception\|traceback" | tail -10
echo ""

echo "5. ITERATION PROGRESS"
echo "---------------------"
sudo journalctl -u sdm-trading.service -o cat --since "10 minutes ago" | grep "SDM ITERATION"
echo ""

echo "6. STATE FILES"
echo "--------------"
ls -lh /tmp/bandit_state.json /tmp/position_ledger.json /tmp/trading_journal.db 2>&1
echo ""

echo "7. ACCOUNT BALANCE"
echo "------------------"
python3 /opt/AlphaGenesis/scripts/check_weex_account.py 2>/dev/null || echo "Could not check account"
echo ""

echo "========================================="
echo "Health check complete!"
echo "========================================="
