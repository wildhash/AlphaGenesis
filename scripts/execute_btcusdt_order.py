#!/usr/bin/env python3
"""
WEEX API Order Execution Script
Execute a 10 USDT notional value order on BTCUSDT trading pair
"""

import time
import hmac
import hashlib
import base64
import requests
import json
import uuid
from datetime import datetime

# WEEX API Configuration
API_KEY = "weex_acb0afbb09f81c7ed746e19b66873807"
SECRET = "664d98a2a14769995d05c7449ec8bf6e67e3572dc255045b3c25f7d409ceb1c7"
PASSPHRASE = "weex783219649164"
BASE_URL = "https://api-contract.weex.com"

def generate_signature(secret: str, timestamp: str, method: str, path: str, query: str = "", body: str = "") -> str:
    """
    Generate HMAC SHA256 signature for WEEX API authentication.

    Args:
        secret: API secret key
        timestamp: Request timestamp in milliseconds
        method: HTTP method (GET, POST, etc.)
        path: API endpoint path
        query: Query string parameters
        body: Request body (JSON string for POST requests)

    Returns:
        Base64 encoded HMAC signature
    """
    message = timestamp + method.upper() + path + query + str(body)
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode()

def make_request(method: str, endpoint: str, params: dict = None, payload: dict = None) -> requests.Response:
    """
    Make authenticated request to WEEX API.

    Args:
        method: HTTP method (GET or POST)
        endpoint: API endpoint path
        params: Query parameters for GET requests
        payload: Request body for POST requests

    Returns:
        Response object
    """
    timestamp = str(int(time.time() * 1000))
    query = ""
    body = ""

    if params and method == "GET":
        query = "?" + "&".join([f"{k}={v}" for k, v in params.items()])

    if payload:
        body = json.dumps(payload, separators=(",", ":"))

    signature = generate_signature(SECRET, timestamp, method, endpoint, query, body)

    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json",
        "locale": "en-US"
    }

    url = BASE_URL + endpoint + query

    if method == "GET":
        return requests.get(url, headers=headers, timeout=30)
    else:
        return requests.post(url, headers=headers, data=body, timeout=30)

def main():
    """Execute WEEX API order placement workflow."""

    print("=" * 80)
    print("WEEX API - BTCUSDT ORDER EXECUTION (10 USDT Notional)")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)

    # Step 1: Check account balance
    print("\n[1/4] Fetching Account Balance...")
    try:
        response = make_request("GET", "/capi/v2/account/assets")
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")

        if response.status_code != 200:
            print(f"❌ Failed to fetch balance. Aborting.")
            return
        print("✅ Balance retrieved successfully")
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # Step 2: Set leverage for BTCUSDT
    print("\n[2/4] Setting Leverage (2x for BTCUSDT)...")
    try:
        payload = {
            "symbol": "cmt_btcusdt",
            "marginMode": 1,
            "longLeverage": "2",
            "shortLeverage": "2"
        }
        response = make_request("POST", "/capi/v2/account/leverage", payload=payload)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")

        if response.status_code != 200:
            print(f"⚠️  Leverage setting failed, but continuing...")
        else:
            print("✅ Leverage set successfully")
    except Exception as e:
        print(f"⚠️  Warning: {e}")

    # Step 3: Get current market price
    print("\n[3/4] Fetching Current Market Price...")
    try:
        response = make_request("GET", "/capi/v2/market/ticker", params={"symbol": "cmt_btcusdt"})
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")

        if response.status_code == 200 and data.get("code") == "00000":
            current_price = data.get("data", {}).get("last")
            print(f"✅ Current BTC Price: ${current_price}")
        else:
            print(f"⚠️  Could not fetch price, but continuing...")
    except Exception as e:
        print(f"⚠️  Warning: {e}")

    # Step 4: Place order - 10 USDT notional value
    print("\n[4/4] 🎯 PLACING ORDER - 10 USDT NOTIONAL VALUE...")
    try:
        order_payload = {
            "symbol": "cmt_btcusdt",
            "client_oid": uuid.uuid4().hex[:20],  # Unique client order ID
            "size": "10",  # 10 USDT notional value
            "type": "1",  # Open long position
            "order_type": "0",  # Market order
            "match_price": "1",  # Match at market price
            "price": "0",  # Not needed for market order
            "marginMode": 1  # Isolated margin
        }

        print(f"Order Payload: {json.dumps(order_payload, indent=2)}")

        response = make_request("POST", "/capi/v2/order/placeOrder", payload=order_payload)
        print(f"\nStatus Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")

        if response.status_code == 200 and data.get("code") == "00000":
            print("\n" + "=" * 80)
            print("✅ ORDER EXECUTED SUCCESSFULLY!")
            print("=" * 80)
            order_id = data.get("data", {}).get("order_id", "N/A")
            print(f"Order ID: {order_id}")
            print(f"Symbol: BTCUSDT")
            print(f"Notional Value: 10 USDT")
            print(f"Order Type: Market Order (Long)")
            print(f"Timestamp: {datetime.now().isoformat()}")
            print("=" * 80)

            # Save execution result
            result = {
                "timestamp": datetime.now().isoformat(),
                "order_id": order_id,
                "symbol": "BTCUSDT",
                "notional_value": "10 USDT",
                "status": "success",
                "response": data
            }

            with open("/home/user/AlphaGenesis/order_execution_result.json", "w") as f:
                json.dump(result, f, indent=2)
            print(f"\n✅ Execution result saved to: order_execution_result.json")

        else:
            print("\n" + "=" * 80)
            print("❌ ORDER EXECUTION FAILED")
            print("=" * 80)
            print(f"Error Code: {data.get('code')}")
            print(f"Error Message: {data.get('msg', 'Unknown error')}")
            print("=" * 80)

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
