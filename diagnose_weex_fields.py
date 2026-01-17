#!/usr/bin/env python3
"""
WEEX API Field Diagnostic Script

Run this to see the EXACT field names returned by the WEEX API.
This will help us fix any mismatches in our risk management code.
"""
import json
import os
from alphagenesis.data import WEEXClient
from loguru import logger

def diagnose_weex_api():
    """Fetch and display raw WEEX API responses."""

    print("="*80)
    print("WEEX API FIELD DIAGNOSTIC")
    print("="*80)

    # Initialize client
    client = WEEXClient(
        api_key=os.getenv('WEEX_API_KEY'),
        api_secret=os.getenv('WEEX_API_SECRET'),
        api_passphrase=os.getenv('WEEX_API_PASSPHRASE')
    )

    print("\n1. Testing get_account()...")
    print("-" * 80)
    try:
        account = client.get_account()
        print(json.dumps(account, indent=2, default=str))

        # Analyze position structure if exists
        if 'position' in account and len(account['position']) > 0:
            print("\n2. POSITION FIELD ANALYSIS")
            print("-" * 80)
            print(f"Found {len(account['position'])} position(s)")

            for i, pos in enumerate(account['position']):
                size = float(pos.get('size', 0))
                if size != 0:  # Only analyze active positions
                    print(f"\nACTIVE POSITION #{i+1}:")
                    print(f"  Symbol: {pos.get('symbol', 'N/A')}")
                    print(f"  Available fields in this position object:")
                    for key in sorted(pos.keys()):
                        value = pos[key]
                        print(f"    '{key}': {value} (type: {type(value).__name__})")

                    # Check for unrealized P&L variations
                    print(f"\n  Checking for unrealized P&L field:")
                    unrealized_pnl_fields = [
                        'unrealized_pnl', 'unrealised_pnl', 'unrealized_profit',
                        'unrealised_profit', 'unrealizedPnl', 'unrealizedProfit',
                        'upnl', 'floating_pl', 'floating_profit'
                    ]
                    found_pnl = False
                    for field in unrealized_pnl_fields:
                        if field in pos:
                            print(f"    ✓ FOUND: '{field}' = {pos[field]}")
                            found_pnl = True

                    if not found_pnl:
                        print(f"    ✗ No standard unrealized P&L field found!")
                        print(f"    Available keys: {list(pos.keys())}")
        else:
            print("\nNo active positions found. Cannot analyze position structure.")
            print("To see position fields, you need at least one open position.")

        # Analyze collateral structure
        if 'collateral' in account:
            print("\n3. COLLATERAL FIELD ANALYSIS")
            print("-" * 80)
            for i, coll in enumerate(account['collateral']):
                print(f"\nCOLLATERAL #{i+1}:")
                for key in sorted(coll.keys()):
                    print(f"  '{key}': {coll[key]}")

    except Exception as e:
        logger.error(f"Error calling get_account(): {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print("DIAGNOSTIC COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Review the field names above")
    print("2. Update sdm_engine.py to use the correct field names")
    print("3. Test with a live position to verify P&L calculations")
    print("="*80)

if __name__ == "__main__":
    diagnose_weex_api()
