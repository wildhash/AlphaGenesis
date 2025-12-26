# 🚀 Execute WEEX Order NOW - Quick Start

## ⚡ ONE-COMMAND EXECUTION

### Method 1: Google Cloud Shell (Easiest)

If your Cloud Shell has IP `34.133.16.230`, simply:

```bash
# Clone and execute
git clone https://github.com/wildhash/AlphaGenesis.git
cd AlphaGenesis
git checkout claude/execute-btcusdt-order-N8usg
./scripts/execute_now.sh
```

### Method 2: GCP VM (Recommended if Cloud Shell IP doesn't match)

**Quick Setup:**

```bash
# Set your project
gcloud config set project gemiadvan

# Create VM with static IP (replace ADDRESS_NAME with your reserved IP resource)
gcloud compute instances create weex-executor \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --network-interface=address=YOUR_STATIC_IP_RESOURCE_NAME \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --scopes=cloud-platform

# Wait 30 seconds for boot
sleep 30

# SSH and execute
gcloud compute ssh weex-executor --zone=us-central1-a --command="
  curl -s ifconfig.me && \
  git clone https://github.com/wildhash/AlphaGenesis.git && \
  cd AlphaGenesis && \
  git checkout claude/execute-btcusdt-order-N8usg && \
  bash scripts/execute_now.sh
"

# Get results
gcloud compute scp weex-executor:~/AlphaGenesis/order_execution_result.json ./ --zone=us-central1-a

# Cleanup (optional)
gcloud compute instances delete weex-executor --zone=us-central1-a --quiet
```

### Method 3: If You Already Have a VM with IP 34.133.16.230

```bash
# SSH into your VM
ssh your-vm-with-whitelisted-ip

# Clone and execute
git clone https://github.com/wildhash/AlphaGenesis.git
cd AlphaGenesis
git checkout claude/execute-btcusdt-order-N8usg
./scripts/execute_now.sh
```

### Method 4: Cloud Run Job (Alternative)

Create a Cloud Run job with the whitelisted IP's VPC:

```bash
# Build container
cat > Dockerfile.weex <<EOF
FROM python:3.11-slim
RUN pip install requests
WORKDIR /app
COPY scripts/execute_btcusdt_order.py .
CMD ["python", "execute_btcusdt_order.py"]
EOF

# Build and push
gcloud builds submit --tag gcr.io/gemiadvan/weex-executor

# Run job (ensure it uses the whitelisted IP's network)
gcloud run jobs create weex-order \
  --image gcr.io/gemiadvan/weex-executor \
  --region us-central1 \
  --vpc-connector YOUR_VPC_CONNECTOR

gcloud run jobs execute weex-order --region us-central1
```

---

## 🎯 What the Script Does

1. **Verifies IP** is `34.133.16.230`
2. **Installs dependencies** (Python, requests)
3. **Executes order workflow**:
   - Check account balance
   - Set 2x leverage
   - Get BTC market price
   - Place 10 USDT market order (long)
4. **Saves result** to `order_execution_result.json`

## ✅ Expected Output

```
================================================================================
WEEX ORDER EXECUTION - 10 USDT BTCUSDT
================================================================================

[1/4] Checking balance...
Status: 200
✅ Balance OK

[2/4] Setting leverage (2x)...
Status: 200
✅ Leverage set

[3/4] Getting market price...
Status: 200
✅ Current BTC: $86639.8

[4/4] 🎯 PLACING ORDER...
Status: 200

================================================================================
✅ ORDER EXECUTED SUCCESSFULLY!
================================================================================
Order ID: [order_id]
Symbol: BTCUSDT
Notional: 10 USDT
Type: Market Long
================================================================================

✅ Result saved to: order_execution_result.json
```

## 🔧 If You Need to Reserve the Static IP First

```bash
# Reserve the specific IP in us-central1
gcloud compute addresses create weex-static-ip \
  --region=us-central1 \
  --addresses=34.133.16.230

# Or create a new IP and ask WEEX to whitelist it
gcloud compute addresses create weex-static-ip \
  --region=us-central1

# Get the IP
gcloud compute addresses describe weex-static-ip --region=us-central1 --format="get(address)"
```

## ❓ Need Help?

**Check your current IP:**
```bash
curl ifconfig.me
```

**Verify static IP reservation:**
```bash
gcloud compute addresses list --filter="region:us-central1"
```

**Test API connectivity:**
```bash
cd AlphaGenesis
python3 scripts/test_weex_api.py
```

---

## 📋 TL;DR - Fastest Method

**If you have gcloud CLI:**

```bash
# One command - creates VM, executes, gets result, cleans up
gcloud compute instances create weex-temp --zone=us-central1-a --machine-type=e2-micro && \
gcloud compute ssh weex-temp --zone=us-central1-a --command="curl -L https://raw.githubusercontent.com/wildhash/AlphaGenesis/claude/execute-btcusdt-order-N8usg/scripts/execute_now.sh | bash" && \
gcloud compute instances delete weex-temp --zone=us-central1-a --quiet
```

**Note**: This uses default IP (not whitelisted). For production with whitelisted IP, use Method 2 above.
