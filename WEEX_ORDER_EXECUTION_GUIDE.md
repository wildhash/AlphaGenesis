# WEEX API Order Execution Guide

## 🎯 Objective
Execute a **10 USDT notional value** order on the **BTCUSDT** trading pair through the WEEX API.

## 📋 Current Status

### ✅ Completed
- **Execution script created**: `scripts/execute_btcusdt_order.py`
- **API connectivity verified**: WEEX API requires whitelisted IP
- **IP requirement identified**: Must execute from `34.133.16.230`

### 🔍 Diagnostics Results
- **Current environment IP**: `34.122.60.222`
- **Required whitelisted IP**: `34.133.16.230`
- **API response from current IP**: `521 (Blocked)`
- **Root cause**: IP whitelisting - requests must originate from `34.133.16.230`

## 🚀 Execution Options

### Option 1: Manual Execution on GCP VM (Recommended)

#### Prerequisites
- GCP Project: `gemiadvan`
- Whitelisted IP: `34.133.16.230` (already reserved)
- gcloud CLI installed on your local machine

#### Steps

**1. Create/Access GCP VM with Static IP**

```bash
# Set variables
PROJECT_ID="gemiadvan"
ZONE="us-central1-a"
REGION="us-central1"
VM_NAME="weex-order-executor"
STATIC_IP="34.133.16.230"

# Reserve static IP (if not already reserved)
gcloud compute addresses create weex-static-ip \
    --region=$REGION \
    --project=$PROJECT_ID \
    --addresses=$STATIC_IP

# Create VM with static IP
gcloud compute instances create $VM_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=e2-micro \
    --network-interface=address=weex-static-ip,network-tier=PREMIUM \
    --image-family=debian-12 \
    --image-project=debian-cloud \
    --boot-disk-size=10GB \
    --metadata=startup-script='#!/bin/bash
apt-get update
apt-get install -y python3-pip
pip3 install requests --break-system-packages
'
```

**2. Upload and Execute the Script**

```bash
# Wait for VM to initialize (30 seconds)
sleep 30

# Copy execution script to VM
gcloud compute scp \
    scripts/execute_btcusdt_order.py \
    $VM_NAME:~/execute_btcusdt_order.py \
    --project=$PROJECT_ID \
    --zone=$ZONE

# SSH into VM
gcloud compute ssh $VM_NAME --project=$PROJECT_ID --zone=$ZONE

# Inside the VM: Verify IP
curl -s ifconfig.me
# Should output: 34.133.16.230

# Install dependencies (if not already installed)
pip3 install requests --break-system-packages

# Execute the order
python3 ~/execute_btcusdt_order.py

# Exit SSH
exit
```

**3. Download Results**

```bash
# Download execution result
gcloud compute scp \
    $VM_NAME:~/order_execution_result.json \
    ./order_execution_result.json \
    --project=$PROJECT_ID \
    --zone=$ZONE

# View results
cat order_execution_result.json
```

**4. Cleanup (Optional)**

```bash
# Delete VM after execution
gcloud compute instances delete $VM_NAME \
    --zone=$ZONE \
    --project=$PROJECT_ID \
    --quiet
```

### Option 2: Using Provided Setup Scripts

We've created automated setup scripts for you:

```bash
# Step 1: Set up GCP VM with correct IP
./scripts/setup_gcp_vm.sh

# Step 2: Execute order on VM
./scripts/run_on_gcp.sh
```

**Note**: These scripts require gcloud CLI with proper authentication.

### Option 3: Direct Python Execution (If Already on Whitelisted IP)

If you're already on a machine with IP `34.133.16.230`:

```bash
# Install dependencies
pip install requests

# Execute directly
python3 scripts/execute_btcusdt_order.py
```

## 📄 Order Details

The execution script (`scripts/execute_btcusdt_order.py`) will:

1. **Check Account Balance** - Verify sufficient funds
2. **Set Leverage** - Configure 2x leverage for BTCUSDT
3. **Get Market Price** - Fetch current BTC/USDT price
4. **Place Order** - Execute market order with:
   - Symbol: `cmt_btcusdt`
   - Size: `10` (10 USDT notional value)
   - Type: `1` (Open long)
   - Order Type: `0` (Market order)
   - Margin Mode: `1` (Isolated margin)

## 🔑 API Configuration

**Endpoint**: `https://api-contract.weex.com`

**Credentials** (embedded in script):
- API Key: `weex_acb0afbb09f81c7ed746e19b66873807`
- Secret: `664d98a2a14769995d05c7449ec8bf6e67e3572dc255045b3c25f7d409ceb1c7`
- Passphrase: `weex783219649164`

## ✅ Expected Success Output

```
================================================================================
WEEX API - BTCUSDT ORDER EXECUTION (10 USDT Notional)
================================================================================

[1/4] Fetching Account Balance...
Status Code: 200
✅ Balance retrieved successfully

[2/4] Setting Leverage (2x for BTCUSDT)...
Status Code: 200
✅ Leverage set successfully

[3/4] Fetching Current Market Price...
Status Code: 200
✅ Current BTC Price: $86639.8

[4/4] 🎯 PLACING ORDER - 10 USDT NOTIONAL VALUE...
Status Code: 200

================================================================================
✅ ORDER EXECUTED SUCCESSFULLY!
================================================================================
Order ID: [order_id_here]
Symbol: BTCUSDT
Notional Value: 10 USDT
Order Type: Market Order (Long)
================================================================================

✅ Execution result saved to: order_execution_result.json
```

## 🔧 Troubleshooting

### Issue: 521 Error (Origin Server Down)
**Cause**: Request not from whitelisted IP
**Solution**: Ensure execution from `34.133.16.230`

### Issue: Authentication Failed
**Cause**: Incorrect signature or credentials
**Solution**: Verify API credentials haven't expired

### Issue: Insufficient Balance
**Cause**: Account doesn't have enough USDT
**Solution**: Deposit funds or reduce order size

### Issue: VM IP doesn't match
**Cause**: Static IP not properly assigned
**Solution**:
1. Check static IP reservation
2. Contact WEEX Labs to whitelist the new IP
3. Or recreate VM with correct IP assignment

## 📝 Files Created

- `scripts/execute_btcusdt_order.py` - Main execution script
- `scripts/setup_gcp_vm.sh` - Automated GCP VM setup
- `scripts/run_on_gcp.sh` - Execute order on VM
- `scripts/test_weex_api.py` - API connectivity test
- `WEEX_ORDER_EXECUTION_GUIDE.md` - This guide

## 🎯 Next Steps

1. Choose an execution option above
2. Follow the steps for your chosen option
3. Verify order execution in the output
4. Check `order_execution_result.json` for details
5. Verify order on WEEX platform

## 📞 Support

If you encounter issues:
- Verify IP is `34.133.16.230` using: `curl ifconfig.me`
- Check WEEX API status
- Ensure API credentials are active
- Review error messages in the output

---

**Status**: Ready for execution
**Created**: 2025-12-26
**Required IP**: 34.133.16.230 (Whitelisted)
