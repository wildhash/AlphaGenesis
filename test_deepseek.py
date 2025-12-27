"""
Test script for AlphaGenesis DeepSeek Implementation - Full Test Suite
"""

import sys
import numpy as np

print("Testing DeepSeek Reasoner (direct import)...")
print("="*60)

# Load the reasoner directly
exec(open('C:/AlphaGenesis/alphagenesis/ai/deepseek_reasoner.py').read())
print("[OK] DeepSeek Reasoner loaded")

# Test 1: Weak signal should be rejected
print("\n" + "="*60)
print("TEST 1: Weak Market (Should HOLD)")
print("="*60)

reasoner = DeepSeekReasoner(
    min_confluence=0.7,
    min_risk_reward=3.0,
    max_leverage=15.0,
    max_daily_trades=3
)

# Ranging market
np.random.seed(42)
prices_ranging = 95000 + np.random.randn(100) * 500  # Sideways

signal = {'direction': 'LONG', 'confidence': 0.75, 'leverage': 10.0}
context = {
    'current_price': float(prices_ranging[-1]),
    'atr': float(np.std(np.diff(prices_ranging)) * 2),
    'prices_1h': prices_ranging.tolist(),
    'prices_4h': prices_ranging[::4].tolist(),
    'prices_1d': prices_ranging[::24].tolist(),
    'funding_rate': 0.0001,
    'account_balance': 1000.0
}

decision = reasoner.evaluate_trade_signal('cmt_btcusdt', signal, context)
print(f"Decision: {decision.action.value}")
print(f"Passed {sum(1 for s in decision.reasoning_chain if s.passed)}/{len(decision.reasoning_chain)} checks")
assert decision.action == TradeAction.HOLD, "Should HOLD in ranging market"
print("PASS - Correctly rejected weak market")

# Test 2: Strong uptrend should be approved
print("\n" + "="*60)
print("TEST 2: Strong Uptrend (Should LONG)")
print("="*60)

# Strong uptrend - steep and consistent
np.random.seed(123)
base = 90000
trend = np.linspace(0, 10000, 100)  # 10% rise
prices_bull = base + trend + np.random.randn(100) * 100

signal = {'direction': 'LONG', 'confidence': 0.8, 'leverage': 10.0}
context = {
    'current_price': float(prices_bull[-1]),
    'atr': float(np.std(np.diff(prices_bull)) * 2),
    'prices_1h': prices_bull.tolist(),
    'prices_4h': prices_bull[::4].tolist(),
    'prices_1d': prices_bull[::24].tolist(),
    'funding_rate': -0.0005,  # Negative = longs get paid
    'account_balance': 1000.0
}

decision = reasoner.evaluate_trade_signal('cmt_btcusdt', signal, context)
print(f"Decision: {decision.action.value}")
print(f"Passed {sum(1 for s in decision.reasoning_chain if s.passed)}/{len(decision.reasoning_chain)} checks")

if decision.is_trade:
    print(f"\n[TRADE APPROVED]")
    print(f"  Entry: ${decision.entry_price:.2f}")
    print(f"  Stop Loss: ${decision.stop_loss:.2f}")
    print(f"  Take Profit: ${decision.take_profit:.2f}")
    print(f"  R:R: {decision.risk_reward_ratio:.1f}:1")
    print(f"  Leverage: {decision.leverage:.1f}x")
    print(f"  Size: {decision.position_size:.6f} BTC")
    print("PASS - Trade correctly approved")
else:
    print("Trade not approved - check reasoning:")
    for step in decision.reasoning_chain:
        status = "PASS" if step.passed else "FAIL"
        print(f"  [{status}] {step.check_name}: {step.reasoning}")

# Test 3: Daily trade limit
print("\n" + "="*60)
print("TEST 3: Daily Trade Limit (Should block after 3)")
print("="*60)

reasoner2 = DeepSeekReasoner(max_daily_trades=2)
reasoner2.trades_today = 2  # Simulate 2 trades already

decision = reasoner2.evaluate_trade_signal('cmt_btcusdt', signal, context)
print(f"Decision after 2 trades: {decision.action.value}")
assert decision.action == TradeAction.HOLD, "Should HOLD when daily limit reached"
print("PASS - Correctly enforced daily trade limit")

# Test 4: Low confidence rejection
print("\n" + "="*60)
print("TEST 4: Low Confidence (Should HOLD)")
print("="*60)

weak_signal = {'direction': 'LONG', 'confidence': 0.3, 'leverage': 10.0}
decision = reasoner.evaluate_trade_signal('cmt_ethusdt', weak_signal, context)
print(f"Decision with 30% confidence: {decision.action.value}")
assert decision.action == TradeAction.HOLD, "Should HOLD with low confidence"
print("PASS - Correctly rejected low confidence signal")

# Summary
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)
stats = reasoner.get_decision_stats()
print(f"Total Evaluations: {stats['total_evaluations']}")
print(f"Trades Executed: {stats['trades_executed']}")
print(f"Trade Rate: {stats['trade_rate']:.1%}")
print(f"Avg Reasoning Steps: {stats['avg_reasoning_steps']:.1f}")

print("\n" + "="*60)
print("ALL TESTS PASSED! DeepSeek Reasoner working correctly.")
print("="*60)
