#!/usr/bin/env python3
"""
Fetch Trade History from WEEX API
Retrieves executed orders and trade logs
"""

import time, hmac, hashlib, base64, requests, json, sys
from datetime import datetime, timedelta

# WEEX API Configuration
API_KEY = "weex_acb0afbb09f81c7ed746e19b66873807"
SECRET = "664d98a2a14769995d05c7449ec8bf6e67e3572dc255045b3c25f7d409ceb1c7"
PASSPHRASE = "weex783219649164"
BASE_URL = "https://api-contract.weex.com"

def sign(timestamp, method, path, query="", body=""):
    """Generate HMAC SHA256 signature"""
    message = timestamp + method.upper() + path + query + str(body)
    return base64.b64encode(
        hmac.new(SECRET.encode(), message.encode(), hashlib.sha256).digest()
    ).decode()

def request(method, endpoint, params=None, payload=None):
    """Make authenticated API request"""
    timestamp = str(int(time.time() * 1000))
    query = ""
    body = ""

    if params and method == "GET":
        query = "?" + "&".join([f"{k}={v}" for k, v in params.items()])

    if payload:
        body = json.dumps(payload, separators=(",", ":"))

    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": sign(timestamp, method, endpoint, query, body),
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json",
        "locale": "en-US"
    }

    url = BASE_URL + endpoint + query

    try:
        if method == "GET":
            return requests.get(url, headers=headers, timeout=30)
        else:
            return requests.post(url, headers=headers, data=body, timeout=30)
    except Exception as e:
        print(f"Request error: {e}")
        raise

def get_order_history(symbol="cmt_btcusdt", limit=100):
    """Fetch order history"""
    print("=" * 80)
    print("WEEX API - TRADE HISTORY")
    print("=" * 80)
    print(f"Symbol: {symbol}")
    print(f"Fetching last {limit} orders...")
    print("=" * 80)

    try:
        # Get historical orders
        params = {
            "symbol": symbol,
            "limit": str(limit)
        }

        r = request("GET", "/capi/v2/order/history", params=params)

        print(f"\nStatus: {r.status_code}")

        if r.status_code == 200:
            data = r.json()

            if data.get("code") == "00000":
                orders = data.get("data", {}).get("orderList", [])

                print(f"\n✅ Found {len(orders)} orders")
                print("=" * 80)

                if orders:
                    # Save full response
                    with open("trade_history_full.json", "w") as f:
                        json.dump(data, f, indent=2)
                    print("✅ Full history saved to: trade_history_full.json")

                    # Create formatted log
                    trade_log = []

                    print("\n📊 TRADE LOG:")
                    print("-" * 80)

                    for i, order in enumerate(orders, 1):
                        trade_entry = {
                            "order_number": i,
                            "order_id": order.get("order_id"),
                            "client_oid": order.get("client_oid"),
                            "symbol": order.get("symbol"),
                            "side": "LONG" if order.get("type") == "1" else "SHORT",
                            "order_type": "MARKET" if order.get("order_type") == "0" else "LIMIT",
                            "size": order.get("size"),
                            "filled_size": order.get("filled_size"),
                            "avg_price": order.get("avg_price"),
                            "state": order.get("state"),
                            "created_at": order.get("created_at"),
                            "updated_at": order.get("updated_at")
                        }

                        trade_log.append(trade_entry)

                        # Print formatted
                        print(f"\n[Order #{i}]")
                        print(f"  Order ID: {trade_entry['order_id']}")
                        print(f"  Symbol: {trade_entry['symbol']}")
                        print(f"  Side: {trade_entry['side']}")
                        print(f"  Type: {trade_entry['order_type']}")
                        print(f"  Size: {trade_entry['size']} USDT")
                        print(f"  Filled: {trade_entry['filled_size']}")
                        print(f"  Avg Price: ${trade_entry['avg_price']}")
                        print(f"  Status: {trade_entry['state']}")
                        print(f"  Created: {trade_entry['created_at']}")
                        print(f"  Updated: {trade_entry['updated_at']}")

                    # Save formatted log
                    with open("trade_log.json", "w") as f:
                        json.dump(trade_log, f, indent=2)

                    print("\n" + "=" * 80)
                    print("✅ Formatted trade log saved to: trade_log.json")
                    print("=" * 80)

                    # Summary
                    print("\n📈 SUMMARY:")
                    print(f"  Total Orders: {len(orders)}")
                    filled_orders = [o for o in orders if o.get("state") == "filled"]
                    print(f"  Filled Orders: {len(filled_orders)}")
                    pending_orders = [o for o in orders if o.get("state") in ["pending", "partial_filled"]]
                    print(f"  Pending Orders: {len(pending_orders)}")

                else:
                    print("\nℹ️  No orders found in history")

            else:
                print(f"\n❌ API Error: {data.get('code')} - {data.get('msg')}")

        elif r.status_code == 521:
            print("\n⚠️  ERROR 521: Request blocked - not from whitelisted IP")
            print("Required IP: 34.133.16.230")
            print("\nCurrent IP check:")
            try:
                ip_resp = requests.get("https://api.ipify.org?format=json", timeout=5)
                current_ip = ip_resp.json().get("ip")
                print(f"Your IP: {current_ip}")
            except:
                print("Could not determine current IP")
            return 1

        else:
            print(f"\n❌ HTTP Error: {r.status_code}")
            print(f"Response: {r.text}")
            return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

def get_current_positions():
    """Fetch current open positions"""
    print("\n" + "=" * 80)
    print("CURRENT POSITIONS")
    print("=" * 80)

    try:
        r = request("GET", "/capi/v2/position/allPosition")

        if r.status_code == 200:
            data = r.json()

            if data.get("code") == "00000":
                positions = data.get("data", [])

                if positions:
                    print(f"\n✅ Found {len(positions)} open positions\n")

                    for pos in positions:
                        print(f"Symbol: {pos.get('symbol')}")
                        print(f"  Size: {pos.get('total')}")
                        print(f"  Avg Entry: ${pos.get('avg_cost')}")
                        print(f"  Unrealized PNL: ${pos.get('unrealized_profit')}")
                        print(f"  Leverage: {pos.get('leverage')}x")
                        print()

                    # Save positions
                    with open("current_positions.json", "w") as f:
                        json.dump(positions, f, indent=2)
                    print("✅ Positions saved to: current_positions.json")
                else:
                    print("\nℹ️  No open positions")
            else:
                print(f"\n❌ API Error: {data.get('code')} - {data.get('msg')}")
        else:
            print(f"\n❌ HTTP Error: {r.status_code}")

    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    # Get order history
    exit_code = get_order_history(symbol="cmt_btcusdt", limit=100)

    # Get current positions
    if exit_code == 0:
        get_current_positions()

    sys.exit(exit_code)
