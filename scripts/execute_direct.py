#!/usr/bin/env python3
"""Direct WEEX Order Execution - No IP Check"""

import time, hmac, hashlib, base64, requests, json, uuid, sys
from datetime import datetime

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

def main():
    print("=" * 80)
    print("WEEX ORDER EXECUTION - 10 USDT BTCUSDT")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    # Step 1: Check balance
    print("[1/4] Checking account balance...")
    try:
        r = request("GET", "/capi/v2/account/assets")
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print("✅ Balance retrieved")
        else:
            print(f"Response: {r.text}")
            if r.status_code == 521:
                print("\n⚠️  ERROR 521: Request blocked - not from whitelisted IP")
                print("Required IP: 34.133.16.230")
                sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    # Step 2: Set leverage
    print("\n[2/4] Setting leverage (2x)...")
    try:
        payload = {
            "symbol": "cmt_btcusdt",
            "marginMode": 1,
            "longLeverage": "2",
            "shortLeverage": "2"
        }
        r = request("POST", "/capi/v2/account/leverage", payload=payload)
        print(f"Status: {r.status_code}")
        data = r.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        if r.status_code == 200:
            print("✅ Leverage set")
        else:
            print("⚠️  Leverage setting warning (continuing...)")
    except Exception as e:
        print(f"⚠️  Warning: {e}")

    # Step 3: Get market price
    print("\n[3/4] Getting current market price...")
    try:
        r = request("GET", "/capi/v2/market/ticker", params={"symbol": "cmt_btcusdt"})
        print(f"Status: {r.status_code}")
        data = r.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        if r.status_code == 200 and data.get("code") == "00000":
            price = data.get("data", {}).get("last", "unknown")
            print(f"✅ Current BTC Price: ${price}")
    except Exception as e:
        print(f"⚠️  Warning: {e}")

    # Step 4: Place order
    print("\n[4/4] 🎯 PLACING ORDER - 10 USDT MARKET ORDER...")
    try:
        order_payload = {
            "symbol": "cmt_btcusdt",
            "client_oid": uuid.uuid4().hex[:20],
            "size": "10",
            "type": "1",
            "order_type": "0",
            "match_price": "1",
            "price": "0",
            "marginMode": 1
        }

        print(f"Order Payload: {json.dumps(order_payload, indent=2)}")

        r = request("POST", "/capi/v2/order/placeOrder", payload=order_payload)
        print(f"\nStatus: {r.status_code}")
        data = r.json()
        print(f"Response: {json.dumps(data, indent=2)}")

        if r.status_code == 200 and data.get("code") == "00000":
            order_id = data.get("data", {}).get("order_id", "N/A")

            print("\n" + "=" * 80)
            print("✅ ORDER EXECUTED SUCCESSFULLY!")
            print("=" * 80)
            print(f"Order ID: {order_id}")
            print(f"Symbol: BTCUSDT")
            print(f"Notional Value: 10 USDT")
            print(f"Type: Market Order (Long)")
            print(f"Leverage: 2x Isolated")
            print(f"Timestamp: {datetime.now().isoformat()}")
            print("=" * 80)

            # Save result
            result = {
                "timestamp": datetime.now().isoformat(),
                "order_id": order_id,
                "symbol": "BTCUSDT",
                "notional_value": "10 USDT",
                "order_type": "market_long",
                "leverage": "2x",
                "margin_mode": "isolated",
                "status": "success",
                "response": data
            }

            result_file = "order_execution_result.json"
            with open(result_file, "w") as f:
                json.dump(result, f, indent=2)

            print(f"\n✅ Execution result saved to: {result_file}")
            print("\nOrder Details:")
            print(json.dumps(result, indent=2))

            return 0
        else:
            print("\n" + "=" * 80)
            print("❌ ORDER EXECUTION FAILED")
            print("=" * 80)
            print(f"Error Code: {data.get('code')}")
            print(f"Error Message: {data.get('msg', 'Unknown error')}")
            print("=" * 80)
            return 1

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
