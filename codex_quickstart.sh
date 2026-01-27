#!/bin/bash
# CODEX QUICKSTART - Execute this in your GCP SSH terminal

echo "=================================================="
echo "REGIME-AWARE SIZING VERIFICATION - STARTING NOW"
echo "=================================================="
echo ""

# Step 1: Verify the math
echo "🔍 STEP 1: Verifying size multiplier implementation..."
echo ""
echo "Searching for size_multiplier in code:"
grep -rn "size_multiplier" /home/wildhash/alphagenesis/ --include="*.py" | head -10
echo ""
echo "Searching for STRONG_UPTREND sizing logic:"
grep -rn "STRONG_UPTREND.*multiplier\|regime.*position" /home/wildhash/alphagenesis/ --include="*.py" | head -10
echo ""
echo "⚠️  CRITICAL CHECK: Multiplier should be 2.5 (not 1.67)"
echo "    1% base * 2.5 = 2.5% position size"
echo ""
read -p "Does the multiplier look correct? (y/n): " math_ok

if [ "$math_ok" != "y" ]; then
    echo "❌ MATH ERROR DETECTED - Manual fix required before proceeding"
    echo "   Find the size_multiplier line and ensure it's set to 2.5"
    exit 1
fi

echo ""
echo "✅ Math verified"
echo ""

# Step 2: Check service status
echo "🔍 STEP 2: Checking service status..."
sudo systemctl status sdm-trading.service | grep -A 3 "Active:"
echo ""

# Step 3: Check recent logs
echo "🔍 STEP 3: Checking last 20 lines for regime-aware sizing..."
sudo journalctl -u sdm-trading.service --since "10 minutes ago" -o cat | \
  grep -E "STRONG_UPTREND detected|size multiplier|Position sizing" | tail -20
echo ""

# Step 4: Start monitoring
echo "=================================================="
echo "✅ VERIFICATION COMPLETE"
echo "=================================================="
echo ""
echo "📊 NEXT STEP: Start live monitoring for 60-90 minutes"
echo ""
echo "Run this command in a persistent terminal (tmux/screen):"
echo ""
echo "sudo journalctl -u sdm-trading.service -o cat -f | \\"
echo "  egrep -i 'STRONG_UPTREND detected|Position sizing|size multiplier|DIAG_ACTION|WEEX_ORDER_RESPONSE|AI_EXIT_LOG|P&L' --line-buffered --color=always"
echo ""
echo "=================================================="
echo "DECISION GATE: After 60 minutes, assess:"
echo "=================================================="
echo ""
echo "1. Check leaderboard gap: Is it shrinking/stable/widening?"
echo "2. Count STRONG_UPTREND trades: How many executed?"
echo "3. Assess win rate: Are larger positions profitable?"
echo ""
echo "Then execute appropriate contingency from CODEX_PROMPT.md:"
echo "  - Gap shrinking → HOLD (do nothing)"
echo "  - Gap stable + low frequency → B1 (relax threshold to 0.25)"
echo "  - Gap stable + high wins → B2 (increase size to 3%)"
echo "  - Gap widening → REVERT (rollback to 1% sizing)"
echo ""
echo "📋 Full decision matrix in: /home/user/AlphaGenesis/CODEX_PROMPT.md"
echo ""
