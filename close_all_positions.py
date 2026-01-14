#!/usr/bin/env python3
"""
Emergency: Close all positions to free up margin
"""
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, '/opt/AlphaGenesis')
load_dotenv('/opt/AlphaGenesis/.env')

from alphagenesis.data.weex_client import WEEXClient

def main():
    print("=" * 70)
    print("EMERGENCY: CLOSING ALL POSITIONS")
    print("=" * 70)

    client = WEEXClient()

    # Get account with positions
    account = client.get_account()

    if 'position' not in account:
        print("No positions found")
        return

    positions = account['position']
    print(f"\nFound {len(positions)} open positions")

    for pos in positions:
        symbol = pos['symbol']
        side = pos['side']
        size = float(pos['size'])
        open_value = float(pos['open_value'])

        print(f"\n{symbol} {side}:")
        print(f"  Size: {size}")
        print(f"  Value: ${open_value:,.2f}")

        # Determine close side
        if side == 'LONG':
            close_side = 3  # Close long
        else:
            close_side = 4  # Close short

        print(f"  Closing position...")

        # Close the position
        result = client.place_order(
            symbol=symbol,
            side=close_side,
            size=size,
            is_market=True
        )

        if 'order_id' in result or 'client_oid' in result:
            print(f"  ✅ Position closed successfully")
        else:
            print(f"  ❌ Failed to close: {result}")

    print("\n" + "=" * 70)
    print("Position closure complete!")
    print("Check balance again to verify margin is freed up")
    print("=" * 70)

if __name__ == "__main__":
    main()
