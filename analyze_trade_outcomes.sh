#!/bin/bash
# P&L AND TRADE OUTCOME ANALYSIS
# Purpose: Extract and analyze realized trade performance
# Usage: Run in production to assess strategy effectiveness

set -e

HOURS="${1:-4}"  # Default: last 4 hours
LOG_SOURCE="journalctl -u sdm-trading.service -o cat"

echo "========================================"
echo "  TRADE OUTCOME ANALYSIS"
echo "  Period: Last ${HOURS} hours"
echo "  Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "========================================"
echo ""

# 1. TRADE SUMMARY
echo "📊 TRADE SUMMARY"
echo "---"
entries=$(sudo $LOG_SOURCE --since "${HOURS} hours ago" | grep -c "DIAG_ACTION.*LONG\|DIAG_ACTION.*SHORT" || echo "0")
exits=$(sudo $LOG_SOURCE --since "${HOURS} hours ago" | grep -c "AI_EXIT_LOG\|TIME STOP\|BREAKOUT" || echo "0")

echo "  Total Entries:  ${entries}"
echo "  Total Exits:    ${exits}"
echo "  Open Positions: $((entries - exits))"
echo ""

# 2. ENTRY ANALYSIS
echo "🎯 ENTRY BREAKDOWN"
echo "---"
longs=$(sudo $LOG_SOURCE --since "${HOURS} hours ago" | grep -c "DIAG_ACTION.*LONG" || echo "0")
shorts=$(sudo $LOG_SOURCE --since "${HOURS} hours ago" | grep -c "DIAG_ACTION.*SHORT" || echo "0")

echo "  LONG entries:  ${longs}"
echo "  SHORT entries: ${shorts}"
echo ""

if [ "$longs" -gt 0 ] || [ "$shorts" -gt 0 ]; then
    echo "  Entry Reasons (top 5):"
    sudo $LOG_SOURCE --since "${HOURS} hours ago" | \
        grep "DIAG_ACTION" | \
        grep -oE "reason='[^']+'" | \
        sed "s/reason='//" | sed "s/'$//" | \
        sort | uniq -c | sort -rn | head -5 | \
        awk '{printf "    %3d - %s\n", $1, substr($0, index($0,$2))}'
fi
echo ""

# 3. EXIT ANALYSIS
echo "🚪 EXIT BREAKDOWN"
echo "---"
time_stops=$(sudo $LOG_SOURCE --since "${HOURS} hours ago" | grep -c "TIME STOP" || echo "0")
breakouts=$(sudo $LOG_SOURCE --since "${HOURS} hours ago" | grep -c "BREAKOUT" || echo "0")
ai_exits=$(sudo $LOG_SOURCE --since "${HOURS} hours ago" | grep -c "AI_EXIT_LOG" || echo "0")

echo "  Time Stops:    ${time_stops}"
echo "  Breakouts:     ${breakouts}"
echo "  AI Exits:      ${ai_exits}"
echo ""

if [ "$time_stops" -gt "$breakouts" ]; then
    echo "  ⚠️  More time stops than breakouts - positions may be holding too long"
fi
echo ""

# 4. REGIME PERFORMANCE
echo "🌡️  REGIME ANALYSIS"
echo "---"
echo "  Signal distribution by regime:"
sudo $LOG_SOURCE --since "${HOURS} hours ago" | \
    grep "DIAG_ACTION" | \
    grep -oE "regime=[A-Z_]+" | \
    sort | uniq -c | sort -rn | \
    awk '{printf "    %-25s: %3d signals\n", $2, $1}'
echo ""

# 5. SYMBOL PERFORMANCE
echo "📈 SYMBOL ACTIVITY"
echo "---"
echo "  Signals by symbol:"
sudo $LOG_SOURCE --since "${HOURS} hours ago" | \
    grep "DIAG_ACTION" | \
    grep -oE "symbol=[a-z_]+" | \
    sort | uniq -c | sort -rn | \
    awk '{printf "    %-20s: %3d signals\n", $2, $1}'
echo ""

# 6. HOLDING TIME ANALYSIS
echo "⏱️  HOLDING TIME PATTERNS"
echo "---"
echo "  Recent exits with holding duration:"
sudo $LOG_SOURCE --since "${HOURS} hours ago" | \
    grep -E "TIME STOP|BREAKOUT|AI_EXIT" | \
    grep -oE "held_[0-9]+min|time=[0-9]+min" | \
    tail -10 | \
    awk '{print "    " $0}'

avg_holding=$(sudo $LOG_SOURCE --since "${HOURS} hours ago" | \
    grep -oE "held_[0-9]+|time=[0-9]+" | \
    grep -oE "[0-9]+" | \
    awk '{sum+=$1; count++} END {if(count>0) printf "%.1f", sum/count; else print "N/A"}')

echo ""
echo "  Average holding time: ${avg_holding} minutes"
echo ""

# 7. ERROR PATTERNS
echo "⚠️  CRITICAL ISSUES"
echo "---"
errors=$(sudo $LOG_SOURCE --since "${HOURS} hours ago" | grep -ciE "Exception|ERROR|failed.*order" || echo "0")
echo "  Total errors: ${errors}"

if [ "$errors" -gt 0 ]; then
    echo ""
    echo "  Recent critical errors:"
    sudo $LOG_SOURCE --since "${HOURS} hours ago" | \
        grep -iE "Exception|ERROR|failed.*order" | \
        tail -5 | \
        sed 's/^/    /'
fi
echo ""

# 8. CURRENT STATE
echo "💼 CURRENT STATE FILES"
echo "---"
if [ -f /tmp/position_ledger.json ]; then
    echo "  Position Ledger:"
    cat /tmp/position_ledger.json | jq '.' 2>/dev/null || cat /tmp/position_ledger.json
else
    echo "  ⚠️  No position ledger found"
fi
echo ""

if [ -f /tmp/bandit_state.json ]; then
    echo "  Bandit State:"
    cat /tmp/bandit_state.json | jq '.' 2>/dev/null || cat /tmp/bandit_state.json
else
    echo "  ⚠️  No bandit state found"
fi
echo ""

# 9. PERFORMANCE INDICATORS
echo "📊 PERFORMANCE INDICATORS"
echo "---"

if [ "$entries" -gt 0 ]; then
    exit_rate=$((exits * 100 / entries))
    echo "  Trade completion rate: ${exit_rate}%"

    if [ "$exit_rate" -lt 50 ]; then
        echo "  ⚠️  Many positions still open - may be normal if recently entered"
    fi
fi

if [ "$time_stops" -gt 0 ] && [ "$breakouts" -gt 0 ]; then
    win_rate=$((breakouts * 100 / (time_stops + breakouts)))
    echo "  Estimated win rate:    ${win_rate}% (breakouts vs stops)"

    if [ "$win_rate" -lt 40 ]; then
        echo "  ⚠️  Low win rate - consider strategy adjustment"
    elif [ "$win_rate" -gt 60 ]; then
        echo "  ✅ Good win rate - strategy working"
    fi
fi
echo ""

# 10. RECOMMENDATIONS
echo "💡 ANALYSIS & RECOMMENDATIONS"
echo "---"

if [ "$entries" -eq 0 ]; then
    echo "  ⚠️  CRITICAL: No trades in ${HOURS} hours"
    echo "      → Check signal generation logs"
    echo "      → Verify momentum thresholds"
    echo "      → Review LOW_VOL override settings"
elif [ "$exits" -eq 0 ] && [ "$entries" -gt 0 ]; then
    echo "  ⚠️  WARNING: Entries without exits"
    echo "      → Verify exit logic is functioning"
    echo "      → Check TIME STOP and BREAKOUT triggers"
elif [ "$time_stops" -gt $((breakouts * 2)) ]; then
    echo "  ⚠️  WARNING: High stop-out rate"
    echo "      → Stops may be too tight for current volatility"
    echo "      → Consider widening stops or improving entry timing"
    echo "      → Review regime detection accuracy"
elif [ "$breakouts" -gt $((time_stops * 2)) ]; then
    echo "  ✅ EXCELLENT: High breakout rate"
    echo "      → Strategy capturing good moves"
    echo "      → Consider increasing position size if risk allows"
else
    echo "  ℹ️  Performance appears balanced"
    echo "      → Continue monitoring for 1-2 more trade cycles"
    echo "      → Review WEEX account for realized P&L"
fi

echo ""
echo "  Next steps:"
echo "    1. Run: python3 scripts/check_weex_account.py  (if available)"
echo "    2. Check realized P&L from WEEX exchange"
echo "    3. If win rate < 40%, analyze entry quality"
echo "    4. If holding too long, review exit parameters"
echo ""

echo "========================================"
echo "  Analysis completed: $(date -u '+%H:%M:%S UTC')"
echo "========================================"
