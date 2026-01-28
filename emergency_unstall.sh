#!/bin/bash
# Emergency script to unstall the trading system
# Issue: Bandit learned that 'flat' (no trading) is better than 'momentum'
# This caused complete signal stall (no DIAG_ACTION, no orders)

set -e

echo "=========================================="
echo "EMERGENCY UNSTALL PROCEDURE"
echo "=========================================="
echo ""
echo "Problem diagnosed:"
echo "  - Bandit learned 'flat' strategy > 'momentum' strategy"
echo "  - System always choosing 'flat' = HOLD"
echo "  - Result: Zero signals for 4+ hours"
echo ""
echo "Solution applied:"
echo "  1. Removed 'flat' from bandit strategies (force momentum-only)"
echo "  2. Added DIAG_* logging to track signal generation"
echo "  3. Will reset bandit state to clear learned preferences"
echo ""
echo "=========================================="

# Stop the service
echo "1. Stopping sdm-trading.service..."
sudo systemctl stop sdm-trading.service || true
sleep 2

# Backup and delete bandit state (contains learned 'flat' preference)
echo "2. Resetting bandit state..."
if [ -f /tmp/bandit_state.json ]; then
    sudo cp /tmp/bandit_state.json /tmp/bandit_state.json.backup_$(date +%Y%m%d_%H%M%S)
    sudo rm /tmp/bandit_state.json
    echo "   ✓ Bandit state reset (backup saved)"
else
    echo "   ℹ No bandit state file found (already clean)"
fi

# Optional: Also reset position ledger if needed
if [ "$1" == "--full-reset" ]; then
    echo "3. Full reset: clearing position ledger and journal..."
    sudo rm -f /tmp/position_ledger.json
    sudo rm -f /tmp/trading_journal.db
    echo "   ✓ Ledger and journal cleared"
fi

# Restart the service
echo "4. Starting sdm-trading.service..."
sudo systemctl start sdm-trading.service
sleep 3

# Show status
echo ""
echo "5. Service status:"
sudo systemctl status sdm-trading.service --no-pager -l | head -20

echo ""
echo "=========================================="
echo "VERIFICATION"
echo "=========================================="
echo ""
echo "Monitor for signal generation (should see these logs now):"
echo ""
echo "sudo journalctl -u sdm-trading.service -o cat -f | egrep -i 'DIAG_STRATEGY_SELECT|DIAG_SIGNAL_GENERATED|DIAG_NO_SIGNAL|DIAG_FLAT_SELECTED|Placing order|WEEX_ORDER_RESPONSE'"
echo ""
echo "Expected in next 5-10 minutes:"
echo "  ✓ DIAG_STRATEGY_SELECT logs (shows bandit choosing momentum)"
echo "  ✓ DIAG_SIGNAL_GENERATED logs (shows signals being created)"
echo "  ✓ 'Placing order' logs (shows execution)"
echo "  ✓ WEEX_ORDER_RESPONSE logs (shows order confirmation)"
echo ""
echo "If you STILL see zero signals after 15 minutes:"
echo "  - Check if momentum_strategy.generate_signal() is returning None"
echo "  - Run: sudo journalctl -u sdm-trading.service -o cat --since '10 minutes ago' | grep DIAG_NO_SIGNAL"
echo "  - This indicates momentum engine itself is failing to generate signals"
echo ""
echo "=========================================="
