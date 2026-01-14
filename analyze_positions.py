#!/usr/bin/env python3
"""
Check current market conditions and position P&L before closing
"""
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, '/opt/AlphaGenesis')
load_dotenv('/opt/AlphaGenesis/.env')

from alphagenesis.data.weex_client import WEEXClient
from alphagenesis.sdm.simple_momentum import SimpleMomentumStrategy
import numpy as np

def main():
    print("=" * 70)
    print("MARKET ANALYSIS & POSITION P&L CHECK")
    print("=" * 70)

    client = WEEXClient()
    strategy = SimpleMomentumStrategy()

    # Get account with positions
    account = client.get_account()

    if 'position' not in account:
        print("\nNo positions to analyze")
        return

    positions = account['position']
    total_pnl = 0.0
    total_pnl_pct = 0.0

    print(f"\n{'='*70}")
    print(f"ANALYZING {len(positions)} OPEN POSITIONS")
    print(f"{'='*70}\n")

    for pos in positions:
        symbol = pos['symbol']
        side = pos['side']
        size = float(pos['size'])
        entry_price = float(pos['open_value']) / size
        open_fee = float(pos['open_fee'])

        print(f"\n{'='*70}")
        print(f"📊 {symbol} {side} POSITION")
        print(f"{'='*70}")

        # Get current price
        ticker = client.get_ticker(symbol)
        current_price = float(ticker.get('last', 0))

        # Get candles for RSI
        candles_resp = client.get_candles(symbol, '15m', 50)

        # Calculate RSI
        rsi = 50.0  # Default
        if 'data' in candles_resp:
            candles = candles_resp['data']
            closes = [float(c[4]) for c in candles if len(c) >= 5]
            if len(closes) >= 20:
                prices = np.array(closes)
                rsi = strategy.calculate_rsi(prices)

        # Calculate P&L
        if side == 'LONG':
            pnl_dollars = (current_price - entry_price) * size - open_fee
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # SHORT
            pnl_dollars = (entry_price - current_price) * size - open_fee
            pnl_pct = ((entry_price - current_price) / entry_price) * 100

        total_pnl += pnl_dollars
        total_pnl_pct += pnl_pct

        print(f"\n  Position Details:")
        print(f"    Size: {size}")
        print(f"    Entry Price: ${entry_price:,.2f}")
        print(f"    Current Price: ${current_price:,.2f}")
        print(f"    Entry Fee: ${open_fee:.2f}")

        print(f"\n  Market Conditions:")
        print(f"    Current RSI: {rsi:.1f}")

        # Reversal assessment
        if side == 'SHORT':
            if rsi < 50:
                print(f"    ✅ RSI cooled down from overbought - reversal played out!")
            elif rsi > 70:
                print(f"    ⚠️  Still overbought (RSI {rsi:.1f}) - might continue down")
            else:
                print(f"    📊 Neutral RSI - reversal partially played out")
        else:  # LONG
            if rsi > 50:
                print(f"    ✅ RSI recovered from oversold - reversal played out!")
            elif rsi < 30:
                print(f"    ⚠️  Still oversold (RSI {rsi:.1f}) - might continue up")
            else:
                print(f"    📊 Neutral RSI - reversal partially played out")

        print(f"\n  Position P&L:")
        if pnl_dollars > 0:
            print(f"    💰 PROFIT: ${pnl_dollars:,.2f} ({pnl_pct:+.2f}%)")
        else:
            print(f"    ❌ LOSS: ${pnl_dollars:,.2f} ({pnl_pct:+.2f}%)")

        # Recommendation
        print(f"\n  Recommendation:")
        if side == 'SHORT':
            if rsi < 50 and pnl_dollars > 0:
                print(f"    ✅ CLOSE - Reversal successful, take profit")
            elif pnl_dollars < -50:
                print(f"    ⚠️  CONSIDER CLOSING - Cut losses")
            else:
                print(f"    📊 HOLD or CLOSE - Market is neutral")
        else:  # LONG
            if rsi > 50 and pnl_dollars > 0:
                print(f"    ✅ CLOSE - Reversal successful, take profit")
            elif pnl_dollars < -50:
                print(f"    ⚠️  CONSIDER CLOSING - Cut losses")
            else:
                print(f"    📊 HOLD or CLOSE - Market is neutral")

    print(f"\n{'='*70}")
    print(f"PORTFOLIO SUMMARY")
    print(f"{'='*70}")
    print(f"  Total Unrealized P&L: ${total_pnl:,.2f}")
    print(f"  Average P&L per position: {total_pnl_pct / len(positions):.2f}%")

    if total_pnl > 100:
        print(f"\n  ✅ Overall profitable - good time to close and free up margin!")
    elif total_pnl > 0:
        print(f"\n  📊 Slightly profitable - acceptable to close")
    else:
        print(f"\n  ⚠️  Currently at loss - consider waiting for better exit")

    print(f"\n{'='*70}")

if __name__ == "__main__":
    main()
