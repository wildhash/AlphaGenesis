#!/bin/bash
# Quick status check for Alpha Genesis trading system

echo "========================================================================"
echo "ALPHA GENESIS - CURRENT STATUS"
echo "========================================================================"
echo ""

echo "=== SERVICE STATUS ==="
systemctl is-active sdm-trading.service
echo ""

echo "=== RECENT TRADES (Last 10) ==="
journalctl -u sdm-trading.service --since '30 minutes ago' | grep "✓ Order placed successfully" | tail -10
echo ""

echo "=== RECENT ERRORS (Last 5) ==="
journalctl -u sdm-trading.service --since '30 minutes ago' | grep "ERROR" | tail -5
echo ""

echo "=== REVERSAL SIGNALS (Last 10) ==="
journalctl -u sdm-trading.service --since '30 minutes ago' | grep "REVERSAL" | tail -10
echo ""

echo "=== LATEST SYSTEM STATUS ==="
journalctl -u sdm-trading.service --since '10 minutes ago' | grep -A 10 "SDM SYSTEM STATUS" | tail -15
echo ""

echo "=== CURRENT BALANCE ==="
journalctl -u sdm-trading.service --since '10 minutes ago' | grep "Capital:" | tail -1
echo ""

echo "========================================================================"
echo "Run this to watch live: sudo journalctl -u sdm-trading.service -f"
echo "========================================================================"
