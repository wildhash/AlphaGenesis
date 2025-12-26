#!/bin/bash
# Script to upload and execute the order script on GCP VM

set -e

PROJECT_ID="gemiadvan"
ZONE="us-central1-a"
VM_NAME="weex-hackathon-vm"

echo "=============================================================================="
echo "Uploading and Executing Order Script on GCP VM"
echo "=============================================================================="

# Step 1: Copy the execution script to VM
echo ""
echo "[1/3] Uploading execution script to VM..."
gcloud compute scp \
    /home/user/AlphaGenesis/scripts/execute_btcusdt_order.py \
    $VM_NAME:~/execute_btcusdt_order.py \
    --project=$PROJECT_ID \
    --zone=$ZONE

echo "✅ Script uploaded"

# Step 2: Verify IP address
echo ""
echo "[2/3] Verifying VM IP address..."
VM_IP=$(gcloud compute ssh $VM_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --command="curl -s ifconfig.me")

echo "VM IP Address: $VM_IP"

if [ "$VM_IP" = "34.133.16.230" ]; then
    echo "✅ IP matches whitelisted IP!"
else
    echo "⚠️  WARNING: IP ($VM_IP) does not match whitelisted IP (34.133.16.230)"
    echo "You may need to contact WEEX Labs to whitelist this IP"
fi

# Step 3: Execute the order script
echo ""
echo "[3/3] Executing order script on VM..."
echo "=============================================================================="

gcloud compute ssh $VM_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --command="python3 ~/execute_btcusdt_order.py"

echo ""
echo "=============================================================================="
echo "✅ EXECUTION COMPLETE"
echo "=============================================================================="

# Step 4: Download the result file if it exists
echo ""
echo "Downloading execution result..."
if gcloud compute scp \
    $VM_NAME:~/order_execution_result.json \
    /home/user/AlphaGenesis/order_execution_result.json \
    --project=$PROJECT_ID \
    --zone=$ZONE 2>/dev/null; then
    echo "✅ Result file downloaded"
    cat /home/user/AlphaGenesis/order_execution_result.json
else
    echo "⚠️  No result file found (execution may have failed)"
fi

echo ""
echo "=============================================================================="
