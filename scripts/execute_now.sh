#!/bin/bash
# One-Command WEEX Order Execution
# Run this script on a machine/VM with IP 34.133.16.230

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================================================"
echo "WEEX API - BTCUSDT ORDER EXECUTION (10 USDT)"
echo "================================================================================"

# Verify IP address
echo -e "\n${YELLOW}[Step 0]${NC} Verifying IP address..."
CURRENT_IP=$(curl -s --max-time 5 ifconfig.me || curl -s --max-time 5 api.ipify.org || echo "unknown")
echo "Current IP: $CURRENT_IP"

if [ "$CURRENT_IP" != "34.133.16.230" ]; then
    echo -e "${RED}❌ WARNING: IP ($CURRENT_IP) does not match whitelisted IP (34.133.16.230)${NC}"
    echo "The order may fail due to IP whitelisting."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Execution cancelled."
        exit 1
    fi
else
    echo -e "${GREEN}✅ IP matches whitelisted IP!${NC}"
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Installing...${NC}"
    apt-get update && apt-get install -y python3 python3-pip
fi

# Check for requests library
echo -e "\n${YELLOW}[Step 1]${NC} Installing dependencies..."
python3 -c "import requests" 2>/dev/null || {
    echo "Installing requests library..."
    pip3 install requests --break-system-packages 2>/dev/null || pip3 install requests
}
echo -e "${GREEN}✅ Dependencies ready${NC}"

# Create the execution script inline
echo -e "\n${YELLOW}[Step 2]${NC} Preparing execution script..."
cat > /tmp/weex_execute.py << 'EOFPYTHON'
import time, hmac, hashlib, base64, requests, json, uuid
from datetime import datetime

API_KEY = "weex_acb0afbb09f81c7ed746e19b66873807"
SECRET = "664d98a2a14769995d05c7449ec8bf6e67e3572dc255045b3c25f7d409ceb1c7"
PASSPHRASE = "weex783219649164"
BASE_URL = "https://api-contract.weex.com"

def sign(timestamp, method, path, query="", body=""):
    message = timestamp + method.upper() + path + query + str(body)
    return base64.b64encode(hmac.new(SECRET.encode(), message.encode(), hashlib.sha256).digest()).decode()

def request(method, endpoint, params=None, payload=None):
    timestamp = str(int(time.time() * 1000))
    query = "?" + "&".join([f"{k}={v}" for k, v in params.items()]) if params and method == "GET" else ""
    body = json.dumps(payload, separators=(",", ":")) if payload else ""
    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": sign(timestamp, method, endpoint, query, body),
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json",
        "locale": "en-US"
    }
    url = BASE_URL + endpoint + query
    return requests.get(url, headers=headers, timeout=30) if method == "GET" else requests.post(url, headers=headers, data=body, timeout=30)

print("="*80)
print("WEEX ORDER EXECUTION - 10 USDT BTCUSDT")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}\n")

# Step 1: Balance
print("[1/4] Checking balance...")
r = request("GET", "/capi/v2/account/assets")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print("✅ Balance OK")
else:
    print(f"⚠️  Response: {r.text}")

# Step 2: Leverage
print("\n[2/4] Setting leverage (2x)...")
r = request("POST", "/capi/v2/account/leverage", payload={"symbol":"cmt_btcusdt","marginMode":1,"longLeverage":"2","shortLeverage":"2"})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print("✅ Leverage set")
else:
    print(f"⚠️  Response: {r.text}")

# Step 3: Price
print("\n[3/4] Getting market price...")
r = request("GET", "/capi/v2/market/ticker", params={"symbol":"cmt_btcusdt"})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    price = data.get("data", {}).get("last", "unknown")
    print(f"✅ Current BTC: ${price}")

# Step 4: Order
print("\n[4/4] 🎯 PLACING ORDER...")
payload = {
    "symbol": "cmt_btcusdt",
    "client_oid": uuid.uuid4().hex[:20],
    "size": "10",
    "type": "1",
    "order_type": "0",
    "match_price": "1",
    "price": "0",
    "marginMode": 1
}
print(f"Payload: {json.dumps(payload, indent=2)}")

r = request("POST", "/capi/v2/order/placeOrder", payload=payload)
print(f"\nStatus: {r.status_code}")
data = r.json()
print(f"Response: {json.dumps(data, indent=2)}")

if r.status_code == 200 and data.get("code") == "00000":
    order_id = data.get("data", {}).get("order_id", "N/A")
    print("\n" + "="*80)
    print("✅ ORDER EXECUTED SUCCESSFULLY!")
    print("="*80)
    print(f"Order ID: {order_id}")
    print(f"Symbol: BTCUSDT")
    print(f"Notional: 10 USDT")
    print(f"Type: Market Long")
    print(f"Time: {datetime.now().isoformat()}")
    print("="*80)

    result = {
        "timestamp": datetime.now().isoformat(),
        "order_id": order_id,
        "symbol": "BTCUSDT",
        "notional_value": "10 USDT",
        "status": "success",
        "response": data
    }
    with open("order_execution_result.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\n✅ Result saved to: order_execution_result.json")
    exit(0)
else:
    print("\n" + "="*80)
    print("❌ ORDER FAILED")
    print("="*80)
    print(f"Code: {data.get('code')}")
    print(f"Message: {data.get('msg', 'Unknown')}")
    print("="*80)
    exit(1)
EOFPYTHON

echo -e "${GREEN}✅ Script ready${NC}"

# Execute the order
echo -e "\n${YELLOW}[Step 3]${NC} Executing order..."
echo "================================================================================"

python3 /tmp/weex_execute.py

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}================================================================================${NC}"
    echo -e "${GREEN}SUCCESS! Order executed and result saved.${NC}"
    echo -e "${GREEN}================================================================================${NC}"

    if [ -f "order_execution_result.json" ]; then
        echo -e "\n${YELLOW}Order Result:${NC}"
        cat order_execution_result.json | python3 -m json.tool || cat order_execution_result.json
    fi
else
    echo ""
    echo -e "${RED}================================================================================${NC}"
    echo -e "${RED}FAILED! Check output above for errors.${NC}"
    echo -e "${RED}================================================================================${NC}"
    exit 1
fi
