#!/usr/bin/env python3
"""Test WEEX API connectivity and authentication"""

import requests
import json

BASE_URL = "https://api-contract.weex.com"

print("=" * 80)
print("WEEX API Connectivity Test")
print("=" * 80)

# Test 1: Basic connectivity
print("\n[Test 1] Testing basic connectivity to:", BASE_URL)
try:
    response = requests.get(BASE_URL + "/capi/v2/market/ticker?symbol=cmt_btcusdt", timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    else:
        print(f"Response Text: {response.text[:500]}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

# Test 2: Check if it's an IP issue
print("\n[Test 2] Checking our current IP address...")
try:
    ip_services = [
        "https://api.ipify.org?format=json",
        "https://ifconfig.me/ip",
        "https://icanhazip.com"
    ]

    for service in ip_services:
        try:
            resp = requests.get(service, timeout=5)
            if resp.status_code == 200:
                print(f"Current IP from {service}: {resp.text.strip()}")
                break
        except:
            continue
except Exception as e:
    print(f"Could not determine IP: {e}")

# Test 3: Try different API endpoints
print("\n[Test 3] Testing alternative endpoints...")
endpoints = [
    "/capi/v2/public/time",
    "/capi/v2/market/tickers",
    "/api/v1/public/time"
]

for endpoint in endpoints:
    try:
        response = requests.get(BASE_URL + endpoint, timeout=10)
        print(f"{endpoint}: Status {response.status_code}")
        if response.status_code == 200:
            print(f"  Success: {response.text[:200]}")
    except Exception as e:
        print(f"{endpoint}: Error - {e}")

print("\n" + "=" * 80)
print("Required IP for WEEX API: 34.133.16.230 (whitelisted)")
print("=" * 80)
