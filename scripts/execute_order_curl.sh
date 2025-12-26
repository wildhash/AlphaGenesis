#!/bin/bash
# WEEX API Order Execution using curl
# Execute 10 USDT order on BTCUSDT pair

set -e

API_KEY="weex_acb0afbb09f81c7ed746e19b66873807"
SECRET="664d98a2a14769995d05c7449ec8bf6e67e3572dc255045b3c25f7d409ceb1c7"
PASSPHRASE="weex783219649164"
BASE_URL="https://api-contract.weex.com"

# Function to generate HMAC signature
generate_signature() {
    local timestamp=$1
    local method=$2
    local path=$3
    local query=$4
    local body=$5

    local message="${timestamp}${method}${path}${query}${body}"
    echo -n "$message" | openssl dgst -sha256 -hmac "$SECRET" -binary | base64
}

# Function to generate UUID (client_oid)
generate_uuid() {
    cat /dev/urandom | tr -dc 'a-f0-9' | fold -w 20 | head -n 1
}

echo "================================================================================"
echo "WEEX API - BTCUSDT ORDER EXECUTION (10 USDT) - CURL VERSION"
echo "================================================================================"
echo "Timestamp: $(date -Iseconds)"
echo "================================================================================"

# Check current IP
echo -e "\n[0/4] Checking current IP address..."
CURRENT_IP=$(curl -s ifconfig.me || echo "unknown")
echo "Current IP: $CURRENT_IP"
if [ "$CURRENT_IP" != "34.133.16.230" ]; then
    echo "⚠️  WARNING: IP does not match whitelisted IP (34.133.16.230)"
    echo "This execution may fail due to IP whitelisting"
fi

# Step 1: Get account balance
echo -e "\n[1/4] Fetching Account Balance..."
TIMESTAMP=$(date +%s%3N)
PATH="/capi/v2/account/assets"
SIGNATURE=$(generate_signature "$TIMESTAMP" "GET" "$PATH" "" "")

curl -s -X GET "${BASE_URL}${PATH}" \
    -H "ACCESS-KEY: $API_KEY" \
    -H "ACCESS-SIGN: $SIGNATURE" \
    -H "ACCESS-TIMESTAMP: $TIMESTAMP" \
    -H "ACCESS-PASSPHRASE: $PASSPHRASE" \
    -H "Content-Type: application/json" \
    -H "locale: en-US" | jq '.' || echo "Failed to fetch balance"

# Step 2: Set leverage
echo -e "\n[2/4] Setting Leverage (2x for BTCUSDT)..."
TIMESTAMP=$(date +%s%3N)
PATH="/capi/v2/account/leverage"
BODY='{"symbol":"cmt_btcusdt","marginMode":1,"longLeverage":"2","shortLeverage":"2"}'
SIGNATURE=$(generate_signature "$TIMESTAMP" "POST" "$PATH" "" "$BODY")

curl -s -X POST "${BASE_URL}${PATH}" \
    -H "ACCESS-KEY: $API_KEY" \
    -H "ACCESS-SIGN: $SIGNATURE" \
    -H "ACCESS-TIMESTAMP: $TIMESTAMP" \
    -H "ACCESS-PASSPHRASE: $PASSPHRASE" \
    -H "Content-Type: application/json" \
    -H "locale: en-US" \
    -d "$BODY" | jq '.' || echo "Failed to set leverage"

# Step 3: Get market ticker
echo -e "\n[3/4] Fetching Current Market Price..."
TIMESTAMP=$(date +%s%3N)
PATH="/capi/v2/market/ticker"
QUERY="?symbol=cmt_btcusdt"
SIGNATURE=$(generate_signature "$TIMESTAMP" "GET" "$PATH" "$QUERY" "")

TICKER_RESPONSE=$(curl -s -X GET "${BASE_URL}${PATH}${QUERY}" \
    -H "ACCESS-KEY: $API_KEY" \
    -H "ACCESS-SIGN: $SIGNATURE" \
    -H "ACCESS-TIMESTAMP: $TIMESTAMP" \
    -H "ACCESS-PASSPHRASE: $PASSPHRASE" \
    -H "Content-Type: application/json" \
    -H "locale: en-US")

echo "$TICKER_RESPONSE" | jq '.'
CURRENT_PRICE=$(echo "$TICKER_RESPONSE" | jq -r '.data.last // "unknown"')
echo "✅ Current BTC Price: \$$CURRENT_PRICE"

# Step 4: Place order
echo -e "\n[4/4] 🎯 PLACING ORDER - 10 USDT NOTIONAL VALUE..."
TIMESTAMP=$(date +%s%3N)
PATH="/capi/v2/order/placeOrder"
CLIENT_OID=$(generate_uuid)
BODY='{"symbol":"cmt_btcusdt","client_oid":"'$CLIENT_OID'","size":"10","type":"1","order_type":"0","match_price":"1","price":"0","marginMode":1}'

echo "Order Payload: $BODY"

SIGNATURE=$(generate_signature "$TIMESTAMP" "POST" "$PATH" "" "$BODY")

ORDER_RESPONSE=$(curl -s -X POST "${BASE_URL}${PATH}" \
    -H "ACCESS-KEY: $API_KEY" \
    -H "ACCESS-SIGN: $SIGNATURE" \
    -H "ACCESS-TIMESTAMP: $TIMESTAMP" \
    -H "ACCESS-PASSPHRASE: $PASSPHRASE" \
    -H "Content-Type: application/json" \
    -H "locale: en-US" \
    -d "$BODY")

echo -e "\nResponse:"
echo "$ORDER_RESPONSE" | jq '.'

# Check if successful
if echo "$ORDER_RESPONSE" | jq -e '.code == "00000"' > /dev/null; then
    ORDER_ID=$(echo "$ORDER_RESPONSE" | jq -r '.data.order_id // "N/A"')

    echo ""
    echo "================================================================================"
    echo "✅ ORDER EXECUTED SUCCESSFULLY!"
    echo "================================================================================"
    echo "Order ID: $ORDER_ID"
    echo "Symbol: BTCUSDT"
    echo "Notional Value: 10 USDT"
    echo "Order Type: Market Order (Long)"
    echo "Timestamp: $(date -Iseconds)"
    echo "================================================================================"

    # Save result
    cat > order_execution_result.json <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "order_id": "$ORDER_ID",
  "symbol": "BTCUSDT",
  "notional_value": "10 USDT",
  "status": "success",
  "response": $ORDER_RESPONSE
}
EOF
    echo "✅ Execution result saved to: order_execution_result.json"
else
    echo ""
    echo "================================================================================"
    echo "❌ ORDER EXECUTION FAILED"
    echo "================================================================================"
    ERROR_CODE=$(echo "$ORDER_RESPONSE" | jq -r '.code // "unknown"')
    ERROR_MSG=$(echo "$ORDER_RESPONSE" | jq -r '.msg // "Unknown error"')
    echo "Error Code: $ERROR_CODE"
    echo "Error Message: $ERROR_MSG"
    echo "================================================================================"
    exit 1
fi
