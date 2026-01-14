#!/usr/bin/env python3
"""
Check WEEX account status - positions, margin, and balance
"""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, '/opt/AlphaGenesis')

load_dotenv('/opt/AlphaGenesis/.env')

from alphagenesis.data.weex_client import WEEXClient

def main():
    print("=" * 70)
    print("WEEX ACCOUNT STATUS CHECK")
    print("=" * 70)

    client = WEEXClient()

    # Get account info
    print("\n=== ACCOUNT BALANCE ===")
    account = client.get_account()

    if 'data' in account:
        data = account['data']
        print(f"Raw response: {data}")

        if 'collateral' in data:
            for c in data['collateral']:
                if c.get('coin_id') == 2:  # USDT
                    print(f"  Total Balance: ${float(c.get('amount', 0)):,.2f}")
                    print(f"  Available: ${float(c.get('available', 0)):,.2f}")
                    print(f"  Frozen: ${float(c.get('frozen', 0)):,.2f}")
    elif 'collateral' in account:
        for c in account['collateral']:
            if c.get('coin_id') == 2:  # USDT
                print(f"  Total Balance: ${float(c.get('amount', 0)):,.2f}")
                print(f"  Available: ${float(c.get('available', 0)):,.2f}")
                print(f"  Frozen: ${float(c.get('frozen', 0)):,.2f}")
    else:
        print(f"  Error: {account}")

    # Check positions on all symbols
    print("\n=== OPEN POSITIONS ===")
    symbols = [
        'cmt_btcusdt', 'cmt_ethusdt', 'cmt_solusdt', 'cmt_dogeusdt',
        'cmt_xrpusdt', 'cmt_adausdt', 'cmt_bnbusdt', 'cmt_ltcusdt'
    ]

    total_positions = 0
    for symbol in symbols:
        pos = client.get_position(symbol)
        if 'data' in pos and pos['data']:
            position_data = pos['data']
            if isinstance(position_data, list) and len(position_data) > 0:
                for p in position_data:
                    if float(p.get('total', 0)) != 0:
                        total_positions += 1
                        print(f"\n  {symbol}:")
                        print(f"    Size: {p.get('total', 0)}")
                        print(f"    Side: {p.get('hold_side', 'unknown')}")
                        print(f"    Entry Price: ${float(p.get('avg_open_price', 0)):,.2f}")
                        print(f"    Current Price: ${float(p.get('mark_price', 0)):,.2f}")
                        print(f"    Unrealized P&L: ${float(p.get('unrealized_profit', 0)):,.2f}")
                        print(f"    Margin Used: ${float(p.get('margin', 0)):,.2f}")

    if total_positions == 0:
        print("  No open positions")
    else:
        print(f"\n  Total open positions: {total_positions}")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
