#!/bin/bash
# PRODUCTION MONITORING SCRIPT
# Purpose: Track trading performance during critical competition hours
# Usage: Run this in production environment to monitor 1-2 trade cycles

set -e

TIMEFRAME="${1:-60}"  # Default: last 60 minutes
LOG_SOURCE="journalctl -u sdm-trading.service -o cat"

echo "========================================"
echo "  TRADING PERFORMANCE MONITOR"
echo "  Timeframe: Last ${TIMEFRAME} minutes"
echo "  Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "========================================"
echo ""

# 1. SERVICE HEALTH
echo "📊 SERVICE STATUS"
echo "---"
if systemctl is-active --quiet sdm-trading.service 2>/dev/null; then
    echo "✅ sdm-trading.service: RUNNING"
    uptime_sec=$(systemctl show sdm-trading.service --property=ActiveEnterTimestamp --value | xargs -I{} date -d "{}" +%s 2>/dev/null || echo "0")
    current_sec=$(date +%s)
    uptime_min=$(( (current_sec - uptime_sec) / 60 ))
    echo "   Uptime: ${uptime_min} minutes"
else
    echo "❌ sdm-trading.service: NOT RUNNING"
fi
echo ""

# 2. SIGNAL GENERATION METRICS
echo "🎯 SIGNAL ACTIVITY (Last ${TIMEFRAME}min)"
echo "---"
signal_count=$(sudo $LOG_SOURCE --since "${TIMEFRAME} minutes ago" | grep -c "DIAG_ACTION" || echo "0")
momentum_results=$(sudo $LOG_SOURCE --since "${TIMEFRAME} minutes ago" | grep -c "DIAG_MOMENTUM_RESULT" || echo "0")
echo "  Signals Generated: ${signal_count}"
echo "  Momentum Checks:   ${momentum_results}"

if [ "$signal_count" -eq 0 ]; then
    echo "  ⚠️  WARNING: Zero signals in last ${TIMEFRAME} minutes"
fi
echo ""

# 3. ORDER EXECUTION
echo "📈 ORDER EXECUTION (Last ${TIMEFRAME}min)"
echo "---"
orders_placed=$(sudo $LOG_SOURCE --since "${TIMEFRAME} minutes ago" | grep -ci "Placing order:" || echo "0")
orders_confirmed=$(sudo $LOG_SOURCE --since "${TIMEFRAME} minutes ago" | grep -c "WEEX_ORDER_RESPONSE" || echo "0")
echo "  Orders Placed:    ${orders_placed}"
echo "  Orders Confirmed: ${orders_confirmed}"

if [ "$orders_placed" -gt 0 ]; then
    echo "  ✅ System executing trades"
else
    echo "  ⚠️  No orders placed (may be normal if no signals)"
fi
echo ""

# 4. EXIT EVENTS
echo "🚪 EXIT ACTIVITY (Last ${TIMEFRAME}min)"
echo "---"
exit_total=$(sudo $LOG_SOURCE --since "${TIMEFRAME} minutes ago" | grep -ciE "AI_EXIT_LOG|TIME STOP|BREAKOUT|RUNNER" || echo "0")
time_stops=$(sudo $LOG_SOURCE --since "${TIMEFRAME} minutes ago" | grep -c "TIME STOP" || echo "0")
breakouts=$(sudo $LOG_SOURCE --since "${TIMEFRAME} minutes ago" | grep -c "BREAKOUT" || echo "0")
ai_exits=$(sudo $LOG_SOURCE --since "${TIMEFRAME} minutes ago" | grep -c "AI_EXIT_LOG" || echo "0")

echo "  Total Exits:     ${exit_total}"
echo "  - Time Stops:    ${time_stops}"
echo "  - Breakouts:     ${breakouts}"
echo "  - AI Exits:      ${ai_exits}"

if [ "$orders_placed" -gt 0 ] && [ "$exit_total" -eq 0 ]; then
    echo "  ⚠️  WARNING: Entries without exits detected"
fi
echo ""

# 5. REGIME ANALYSIS
echo "🌡️  MARKET REGIME DISTRIBUTION (Last ${TIMEFRAME}min)"
echo "---"
sudo $LOG_SOURCE --since "${TIMEFRAME} minutes ago" | \
    grep -oE "regime=[A-Z_]+" | sort | uniq -c | \
    awk '{printf "  %-20s: %3d occurrences\n", $2, $1}'
echo ""

# 6. SIGNAL BREAKDOWN
echo "💡 SIGNAL DETAILS (Last ${TIMEFRAME}min)"
echo "---"
sudo $LOG_SOURCE --since "${TIMEFRAME} minutes ago" | \
    grep "DIAG_ACTION" | \
    grep -oE "direction=[A-Z]+" | sort | uniq -c | \
    awk '{printf "  %-10s: %3d signals\n", $2, $1}'
echo ""

# 7. ERROR CHECK
echo "⚠️  ERROR SCAN (Last ${TIMEFRAME}min)"
echo "---"
error_count=$(sudo $LOG_SOURCE --since "${TIMEFRAME} minutes ago" | grep -ciE "Traceback|Exception|ERROR" || echo "0")
echo "  Total Errors: ${error_count}"

if [ "$error_count" -gt 0 ]; then
    echo ""
    echo "  Recent Errors (last 5):"
    sudo $LOG_SOURCE --since "${TIMEFRAME} minutes ago" | \
        grep -iE "Traceback|Exception|ERROR" | tail -5 | \
        sed 's/^/    /'
fi
echo ""

# 8. CURRENT POSITIONS
echo "💼 CURRENT POSITIONS"
echo "---"
if [ -f /tmp/position_ledger.json ]; then
    position_count=$(cat /tmp/position_ledger.json | jq -r '.positions | length' 2>/dev/null || echo "0")
    echo "  Open Positions: ${position_count}"

    if [ "$position_count" -gt 0 ]; then
        echo ""
        echo "  Active Positions:"
        cat /tmp/position_ledger.json | jq -r '.positions | to_entries[] | "    \(.key): \(.value.direction) @ \(.value.entry_price)"' 2>/dev/null || echo "    (parsing error)"
    fi
else
    echo "  ⚠️  Position ledger not found"
fi
echo ""

# 9. TRADE LIFECYCLE SAMPLE
echo "📋 RECENT TRADE LIFECYCLE (Last 20 events)"
echo "---"
sudo $LOG_SOURCE --since "${TIMEFRAME} minutes ago" | \
    grep -E "DIAG_ACTION|Placing order:|WEEX_ORDER_RESPONSE|AI_EXIT_LOG|TIME STOP|BREAKOUT" | \
    tail -20 | \
    awk '{
        if (match($0, /symbol=[^ ]+/)) symbol = substr($0, RSTART, RLENGTH);
        if (match($0, /direction=[^ ]+/)) direction = substr($0, RSTART, RLENGTH);

        if ($0 ~ /DIAG_ACTION/) print "  ➤ ENTRY:  " symbol " " direction;
        else if ($0 ~ /Placing order:/) print "  ↗ ORDER:  " $0;
        else if ($0 ~ /WEEX_ORDER_RESPONSE/) print "  ✓ FILLED: " $0;
        else if ($0 ~ /AI_EXIT_LOG|TIME STOP|BREAKOUT/) print "  ✕ EXIT:  " $0;
    }'
echo ""

# 10. RECOMMENDATIONS
echo "💡 NEXT ACTIONS"
echo "---"

if [ "$signal_count" -eq 0 ]; then
    echo "  1. ⚠️  Investigate signal stall - check momentum thresholds"
elif [ "$orders_placed" -eq 0 ] && [ "$signal_count" -gt 0 ]; then
    echo "  1. ⚠️  Signals not converting to orders - check intent graph"
elif [ "$orders_placed" -gt 0 ] && [ "$exit_total" -eq 0 ]; then
    echo "  1. ⚠️  No exits detected - verify exit logic is functioning"
elif [ "$signal_count" -gt 5 ] && [ "$exit_total" -gt 3 ]; then
    echo "  1. ✅ System operating normally - monitor P&L"
else
    echo "  1. ℹ️  Continue monitoring - collect more data"
fi

echo "  2. Check WEEX account balance and P&L"
echo "  3. Review realized P&L from closed trades"
echo "  4. If performance suboptimal, analyze regime accuracy"
echo ""

echo "========================================"
echo "  Monitor completed: $(date -u '+%H:%M:%S UTC')"
echo "========================================"
