#!/usr/bin/env python3
"""
Test Position Ledger Conflict Prevention
Verifies that the ledger correctly prevents self-hedging
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, '/home/user/AlphaGenesis')

# Direct import to avoid torch dependency
from importlib.machinery import SourceFileLoader
position_ledger = SourceFileLoader(
    'position_ledger',
    '/home/user/AlphaGenesis/alphagenesis/execution/position_ledger.py'
).load_module()

PositionLedger = position_ledger.PositionLedger

from loguru import logger

def test_conflict_prevention():
    """Test that ledger prevents LONG + SHORT on same symbol."""
    print("="*70)
    print("TESTING POSITION LEDGER CONFLICT PREVENTION")
    print("="*70)

    # Create ledger with test path
    ledger = PositionLedger(ledger_path="/tmp/test_position_ledger.json")

    # Test 1: Open LONG position on BTC
    print("\n[TEST 1] Opening LONG position on cmt_btcusdt...")
    can_open, reason = ledger.can_open_position('cmt_btcusdt', 'LONG')
    assert can_open, f"Should allow first LONG: {reason}"

    success = ledger.open_position('cmt_btcusdt', 'LONG', size=0.1, entry_price=45000.0)
    assert success, "Should successfully open LONG position"
    print("✓ LONG position opened successfully")

    # Test 2: Try to open SHORT on same symbol (should be blocked)
    print("\n[TEST 2] Attempting to open SHORT on cmt_btcusdt (should be BLOCKED)...")
    can_open, reason = ledger.can_open_position('cmt_btcusdt', 'SHORT')
    assert not can_open, "Should BLOCK SHORT when LONG exists"
    assert "CONFLICT" in reason, f"Reason should mention conflict: {reason}"
    print(f"✓ SHORT correctly blocked: {reason}")

    # Test 3: Try to open another LONG on same symbol (should be blocked - no scaling)
    print("\n[TEST 3] Attempting to open another LONG on cmt_btcusdt (should be BLOCKED)...")
    can_open, reason = ledger.can_open_position('cmt_btcusdt', 'LONG')
    assert not can_open, "Should BLOCK second LONG (no position scaling)"
    print(f"✓ Second LONG correctly blocked: {reason}")

    # Test 4: Open position on different symbol (should be allowed)
    print("\n[TEST 4] Opening SHORT position on cmt_ethusdt (different symbol)...")
    can_open, reason = ledger.can_open_position('cmt_ethusdt', 'SHORT')
    assert can_open, f"Should allow position on different symbol: {reason}"

    success = ledger.open_position('cmt_ethusdt', 'SHORT', size=1.0, entry_price=2500.0)
    assert success, "Should successfully open SHORT on different symbol"
    print("✓ SHORT on ETH opened successfully (different symbol)")

    # Test 5: Close BTC position and verify cooldown
    print("\n[TEST 5] Closing BTC LONG position...")
    ledger.close_position('cmt_btcusdt', close_price=46000.0, realized_pnl=100.0)

    pos = ledger.get_position('cmt_btcusdt')
    assert pos.side == 'FLAT', "Position should be FLAT after close"
    print("✓ BTC position closed, now FLAT")

    # Test 6: Try to open new position during cooldown
    print("\n[TEST 6] Attempting to open SHORT on cmt_btcusdt (in cooldown)...")
    can_open, reason = ledger.can_open_position('cmt_btcusdt', 'SHORT')
    assert not can_open, "Should BLOCK during cooldown period"
    assert "Cooldown" in reason, f"Reason should mention cooldown: {reason}"
    print(f"✓ Trade correctly blocked during cooldown: {reason}")

    # Test 7: Verify open positions
    print("\n[TEST 7] Checking all open positions...")
    open_positions = ledger.get_all_positions()
    assert len(open_positions) == 1, f"Should have 1 open position, got {len(open_positions)}"
    assert 'cmt_ethusdt' in open_positions, "ETH position should still be open"
    print(f"✓ Correctly tracking {len(open_positions)} open position(s)")

    print("\n" + "="*70)
    print("ALL TESTS PASSED ✓")
    print("="*70)
    print("\n🎯 Position Ledger is working correctly!")
    print("✓ Prevents LONG + SHORT on same symbol")
    print("✓ Prevents position scaling (multiple same-side positions)")
    print("✓ Enforces cooldown periods")
    print("✓ Allows positions on different symbols")
    print("\n🔒 Self-hedging bug is FIXED - system can now trade safely")

    return True

def test_reconciliation():
    """Test reconciliation with mock exchange data."""
    print("\n" + "="*70)
    print("TESTING LEDGER RECONCILIATION")
    print("="*70)

    ledger = PositionLedger(ledger_path="/tmp/test_reconcile_ledger.json")

    # Open position in ledger
    ledger.open_position('cmt_btcusdt', 'LONG', size=0.5, entry_price=45000.0)

    # Test matching exchange state
    print("\n[TEST 1] Reconciling with matching exchange state...")
    exchange_positions = [
        {'symbol': 'cmt_btcusdt', 'side': 'LONG', 'size': 0.5}
    ]
    is_consistent = ledger.reconcile_with_exchange(exchange_positions)
    assert is_consistent, "Should match when exchange state is consistent"
    print("✓ Reconciliation successful with matching state")

    # Test mismatched side
    print("\n[TEST 2] Reconciling with mismatched side (should fail)...")
    exchange_positions = [
        {'symbol': 'cmt_btcusdt', 'side': 'SHORT', 'size': 0.5}
    ]
    is_consistent = ledger.reconcile_with_exchange(exchange_positions)
    assert not is_consistent, "Should detect side mismatch"
    print("✓ Correctly detected side mismatch")

    # Test mismatched size
    print("\n[TEST 3] Reconciling with mismatched size (should fail)...")
    exchange_positions = [
        {'symbol': 'cmt_btcusdt', 'side': 'LONG', 'size': 1.0}
    ]
    is_consistent = ledger.reconcile_with_exchange(exchange_positions)
    assert not is_consistent, "Should detect size mismatch"
    print("✓ Correctly detected size mismatch")

    print("\n" + "="*70)
    print("RECONCILIATION TESTS PASSED ✓")
    print("="*70)

    return True

if __name__ == "__main__":
    try:
        test_conflict_prevention()
        test_reconciliation()

        print("\n" + "="*70)
        print("🎉 ALL POSITION LEDGER TESTS PASSED")
        print("="*70)
        print("\n✓ System is ready for dry-run testing")
        print("✓ Conflict prevention is fully functional")
        print("✓ Self-hedging bug is fixed")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during testing: {e}", exc_info=True)
        sys.exit(1)
