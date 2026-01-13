#!/bin/bash
#
# SDM Trading System Monitoring Script
# Run: bash /opt/AlphaGenesis/monitor_trading.sh
#

echo "======================================================================"
echo "  SDM Trading System - Real-Time Monitor"
echo "======================================================================"
echo ""
date
echo ""

# Service status
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SERVICE STATUS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
systemctl is-active sdm-trading.service >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Service is RUNNING"
    uptime_seconds=$(systemctl show sdm-trading.service --property=ActiveEnterTimestamp --value | xargs -I{} date -d {} +%s)
    current_seconds=$(date +%s)
    uptime=$((current_seconds - uptime_seconds))
    uptime_hours=$((uptime / 3600))
    uptime_minutes=$(((uptime % 3600) / 60))
    echo "  Uptime: ${uptime_hours}h ${uptime_minutes}m"
else
    echo "✗ Service is STOPPED"
fi
echo ""

# Recent activity
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "RECENT ACTIVITY (last 10 lines):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
journalctl -u sdm-trading.service -n 10 --no-pager | tail -10
echo ""

# Trade count
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TRADING STATISTICS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
trade_count=$(journalctl -u sdm-trading.service | grep -c "EXECUTING ACTION" || echo "0")
echo "  Total Trades: $trade_count"

if [ "$trade_count" -gt 0 ]; then
    echo ""
    echo "  Recent Trades:"
    journalctl -u sdm-trading.service | grep "EXECUTING ACTION" -A 5 | tail -20
fi
echo ""

# Error check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ERROR CHECK:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
error_count=$(journalctl -u sdm-trading.service --since "1 hour ago" | grep -ci "error" || echo "0")
if [ "$error_count" -eq 0 ]; then
    echo "✓ No errors in last hour"
else
    echo "⚠ $error_count errors in last hour"
    echo ""
    echo "Recent errors:"
    journalctl -u sdm-trading.service --since "1 hour ago" | grep -i "error" | tail -5
fi
echo ""

# System resources
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SYSTEM RESOURCES:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Memory: $(free -h | grep Mem | awk '{print $3 " / " $2}')"
echo "  Disk:   $(df -h / | tail -1 | awk '{print $3 " / " $2 " (" $5 " used)"}')"
echo "  Load:   $(uptime | awk -F'load average:' '{print $2}')"
echo ""

# Reports
if [ -d "/opt/AlphaGenesis/reports/sdm" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "RECENT REPORTS:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ls -lht /opt/AlphaGenesis/reports/sdm/ 2>/dev/null | head -5 || echo "  No reports yet"
    echo ""
fi

echo "======================================================================"
echo "  Use 'sudo journalctl -u sdm-trading.service -f' for live logs"
echo "======================================================================"
