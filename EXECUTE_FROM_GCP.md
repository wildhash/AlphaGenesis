# 🎯 Execute WEEX Order from GCP - Final Instructions

## Current Status
- ✅ Scripts created and tested
- ✅ Code committed to `claude/execute-btcusdt-order-N8usg`
- ❌ Current environment IP (34.122.60.222) is blocked
- ✅ Required IP (34.133.16.230) is whitelisted

## 🚀 EXECUTE NOW - Copy-Paste Commands

### Option A: Using GCP Cloud Shell or VM with Whitelisted IP

**If you already have access to a machine with IP 34.133.16.230:**

```bash
# 1. Clone the repository
git clone https://github.com/wildhash/AlphaGenesis.git
cd AlphaGenesis
git checkout claude/execute-btcusdt-order-N8usg

# 2. Verify your IP (should show 34.133.16.230)
curl -s ifconfig.me
echo ""

# 3. Execute the order
python3 scripts/execute_direct.py

# 4. View results
cat order_execution_result.json
```

### Option B: Create New GCP VM with Specific Static IP

**Prerequisites:** You need the static IP `34.133.16.230` reserved in GCP

```bash
# Set project
gcloud config set project gemiadvan

# Create VM with your whitelisted static IP
gcloud compute instances create weex-order-executor \
  --project=gemiadvan \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --network-interface="address=weex-static-ip,network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default" \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --boot-disk-size=10GB

# Wait for VM to be ready
echo "Waiting 30 seconds for VM initialization..."
sleep 30

# Execute the order on the VM
gcloud compute ssh weex-order-executor \
  --zone=us-central1-a \
  --project=gemiadvan \
  --command="
    set -e
    echo 'Verifying IP...'
    curl -s ifconfig.me
    echo ''
    echo 'Installing dependencies...'
    sudo apt-get update > /dev/null 2>&1
    sudo apt-get install -y python3 python3-pip git > /dev/null 2>&1
    pip3 install requests --break-system-packages > /dev/null 2>&1
    echo 'Cloning repository...'
    git clone https://github.com/wildhash/AlphaGenesis.git
    cd AlphaGenesis
    git checkout claude/execute-btcusdt-order-N8usg
    echo 'Executing order...'
    python3 scripts/execute_direct.py
  "

# Download the result
gcloud compute scp \
  weex-order-executor:~/AlphaGenesis/order_execution_result.json \
  ./ \
  --zone=us-central1-a \
  --project=gemiadvan

echo ""
echo "================================================================================  "
echo "Order Execution Complete! Result:"
echo "================================================================================"
cat order_execution_result.json | python3 -m json.tool

# Optional: Clean up VM
read -p "Delete the VM? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    gcloud compute instances delete weex-order-executor \
      --zone=us-central1-a \
      --project=gemiadvan \
      --quiet
    echo "VM deleted"
fi
```

### Option C: Quick Test (Single Command)

```bash
# Execute everything in one command
gcloud compute ssh weex-order-executor --zone=us-central1-a --project=gemiadvan --command="curl -s ifconfig.me && git clone https://github.com/wildhash/AlphaGenesis.git && cd AlphaGenesis && git checkout claude/execute-btcusdt-order-N8usg && python3 scripts/execute_direct.py" && gcloud compute scp weex-order-executor:~/AlphaGenesis/order_execution_result.json ./ --zone=us-central1-a --project=gemiadvan
```

## 📋 What Will Happen

1. **Balance Check** - Verifies sufficient funds
2. **Set Leverage** - Configures 2x isolated margin
3. **Get Price** - Fetches current BTC/USDT price
4. **Place Order** - Executes 10 USDT market buy order

## ✅ Success Output

```json
{
  "timestamp": "2025-12-26T...",
  "order_id": "...",
  "symbol": "BTCUSDT",
  "notional_value": "10 USDT",
  "order_type": "market_long",
  "leverage": "2x",
  "margin_mode": "isolated",
  "status": "success",
  "response": { ... }
}
```

## 🔧 Troubleshooting

### If Static IP Name is Different

Check your reserved IP:
```bash
gcloud compute addresses list --project=gemiadvan --filter="address=34.133.16.230"
```

Use the NAME from output in `--network-interface=address=NAME`

### If IP Not Reserved Yet

Reserve it:
```bash
gcloud compute addresses create weex-static-ip \
  --region=us-central1 \
  --project=gemiadvan \
  --addresses=34.133.16.230
```

Or create new and whitelist:
```bash
gcloud compute addresses create weex-static-ip \
  --region=us-central1 \
  --project=gemiadvan

# Get the new IP
gcloud compute addresses describe weex-static-ip \
  --region=us-central1 \
  --project=gemiadvan \
  --format="get(address)"

# Contact WEEX to whitelist this new IP
```

## 🎯 Fastest Path

If you have a VM with IP `34.133.16.230` already running:

```bash
# SSH into it
ssh your-vm

# Then run:
curl -sL https://raw.githubusercontent.com/wildhash/AlphaGenesis/claude/execute-btcusdt-order-N8usg/scripts/execute_direct.py | python3 -
```

## 📞 Need Help?

Check the detailed guide: `WEEX_ORDER_EXECUTION_GUIDE.md`

Test your setup: `python3 scripts/test_weex_api.py`

---

**Ready to execute!** Choose the option that matches your GCP setup and run the commands.
