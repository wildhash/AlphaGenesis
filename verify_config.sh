#!/bin/bash
# Verify WEEX API configuration

echo "========================================================================"
echo "WEEX API CONFIGURATION CHECK"
echo "========================================================================"
echo ""

ENV_FILE="/opt/AlphaGenesis/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ ERROR: .env file not found at $ENV_FILE"
    exit 1
fi

echo "=== ENVIRONMENT VARIABLES ==="
echo ""

# Check each required variable (mask sensitive data)
for var in WEEX_API_KEY WEEX_API_SECRET WEEX_API_PASSPHRASE INITIAL_CAPITAL UPDATE_INTERVAL_SECONDS; do
    value=$(grep "^${var}=" "$ENV_FILE" | cut -d'=' -f2-)
    if [ -z "$value" ]; then
        echo "❌ $var: NOT SET"
    else
        if [[ "$var" == *"SECRET"* ]] || [[ "$var" == *"KEY"* ]] || [[ "$var" == *"PASSPHRASE"* ]]; then
            # Mask sensitive data - show first 4 and last 4 chars
            masked="${value:0:4}...${value: -4}"
            echo "✓ $var: $masked"
        else
            echo "✓ $var: $value"
        fi
    fi
done

echo ""
echo "=== TESTING API CONNECTION ==="
echo ""

# Test if we can reach WEEX API
if command -v curl &> /dev/null; then
    response=$(curl -s -o /dev/null -w "%{http_code}" "https://api-contract.weex.com/capi/v2/market/ticker?symbol=cmt_btcusdt")
    if [ "$response" = "200" ]; then
        echo "✓ WEEX API is reachable (HTTP $response)"
    else
        echo "❌ WEEX API unreachable (HTTP $response)"
    fi
else
    echo "⚠ curl not found, skipping API test"
fi

echo ""
echo "=== CURRENT BALANCE FROM API ==="
echo ""

# Try to get balance using Python
cd /opt/AlphaGenesis
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv('.env')
from alphagenesis.data.weex_client import WEEXClient

try:
    client = WEEXClient()
    account = client.get_account()

    if 'data' in account and account['data']:
        data = account['data']
        if 'collateral' in data:
            for c in data['collateral']:
                if c.get('coin_id') == 2:  # USDT
                    balance = float(c.get('available', 0))
                    print(f'✓ Current Balance: \${balance:,.2f} USDT')
                    break
        else:
            print('⚠ No collateral data found')
    elif 'collateral' in account:
        for c in account['collateral']:
            if c.get('coin_id') == 2:  # USDT
                balance = float(c.get('available', 0))
                print(f'✓ Current Balance: \${balance:,.2f} USDT')
                break
    else:
        print(f'❌ API Error: {account}')
except Exception as e:
    print(f'❌ Error getting balance: {e}')
" 2>&1

echo ""
echo "========================================================================"
echo "If everything shows ✓, your config is correct!"
echo "========================================================================"
