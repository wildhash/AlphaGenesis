#!/bin/bash
# GCP VM Setup Script for WEEX API Execution
# This script creates a VM, reserves the whitelisted static IP, and prepares for order execution

set -e

echo "=============================================================================="
echo "GCP VM Setup for WEEX API Order Execution"
echo "=============================================================================="

PROJECT_ID="gemiadvan"
ZONE="us-central1-a"
REGION="us-central1"
VM_NAME="weex-hackathon-vm"
STATIC_IP_NAME="weex-api-static-ip"
TARGET_IP="34.133.16.230"

# Step 1: Check if static IP exists, if not try to reserve it
echo ""
echo "[1/5] Checking/Reserving Static IP: $TARGET_IP"
if gcloud compute addresses describe $STATIC_IP_NAME --region=$REGION --project=$PROJECT_ID &>/dev/null; then
    RESERVED_IP=$(gcloud compute addresses describe $STATIC_IP_NAME --region=$REGION --project=$PROJECT_ID --format="get(address)")
    echo "✅ Static IP already reserved: $RESERVED_IP"
else
    echo "Attempting to reserve static IP $TARGET_IP..."
    if gcloud compute addresses create $STATIC_IP_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --addresses=$TARGET_IP 2>&1; then
        echo "✅ Static IP reserved successfully"
    else
        echo "⚠️  Could not reserve exact IP $TARGET_IP, creating new static IP..."
        gcloud compute addresses create $STATIC_IP_NAME \
            --region=$REGION \
            --project=$PROJECT_ID
        RESERVED_IP=$(gcloud compute addresses describe $STATIC_IP_NAME --region=$REGION --project=$PROJECT_ID --format="get(address)")
        echo "⚠️  WARNING: New IP created: $RESERVED_IP"
        echo "⚠️  You must contact WEEX Labs to whitelist: $RESERVED_IP"
    fi
fi

# Step 2: Delete existing VM if it exists
echo ""
echo "[2/5] Cleaning up existing VM (if any)..."
if gcloud compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT_ID &>/dev/null; then
    echo "Deleting existing VM..."
    gcloud compute instances delete $VM_NAME \
        --zone=$ZONE \
        --project=$PROJECT_ID \
        --quiet
    echo "✅ Existing VM deleted"
else
    echo "✅ No existing VM to clean up"
fi

# Step 3: Create firewall rule if needed
echo ""
echo "[3/5] Setting up firewall rules..."
if ! gcloud compute firewall-rules describe allow-weex-api --project=$PROJECT_ID &>/dev/null; then
    gcloud compute firewall-rules create allow-weex-api \
        --project=$PROJECT_ID \
        --direction=EGRESS \
        --priority=1000 \
        --network=default \
        --action=ALLOW \
        --rules=all \
        --destination-ranges=0.0.0.0/0 \
        --target-tags=weex-api
    echo "✅ Firewall rule created"
else
    echo "✅ Firewall rule already exists"
fi

# Step 4: Create VM with static IP
echo ""
echo "[4/5] Creating VM with static IP..."
gcloud compute instances create $VM_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=e2-micro \
    --network-interface=address=$STATIC_IP_NAME,network-tier=PREMIUM,subnet=default \
    --image-family=debian-12 \
    --image-project=debian-cloud \
    --boot-disk-size=10GB \
    --boot-disk-type=pd-standard \
    --tags=weex-api \
    --metadata=startup-script='#!/bin/bash
apt-get update
apt-get install -y python3-pip curl
pip3 install requests --break-system-packages
'

echo "✅ VM created successfully"

# Step 5: Wait for VM to be ready
echo ""
echo "[5/5] Waiting for VM to initialize..."
sleep 30

# Get VM IP
VM_IP=$(gcloud compute instances describe $VM_NAME \
    --zone=$ZONE \
    --project=$PROJECT_ID \
    --format="get(networkInterfaces[0].accessConfigs[0].natIP)")

echo ""
echo "=============================================================================="
echo "✅ GCP VM SETUP COMPLETE"
echo "=============================================================================="
echo "VM Name: $VM_NAME"
echo "VM IP: $VM_IP"
echo "Zone: $ZONE"
echo ""

if [ "$VM_IP" = "$TARGET_IP" ]; then
    echo "✅ SUCCESS: IP matches whitelisted IP ($TARGET_IP)"
    echo ""
    echo "Next steps:"
    echo "1. SSH into VM:"
    echo "   gcloud compute ssh $VM_NAME --project=$PROJECT_ID --zone=$ZONE"
    echo ""
    echo "2. Upload and run the order execution script"
else
    echo "⚠️  WARNING: IP does not match target ($VM_IP != $TARGET_IP)"
    echo ""
    echo "Action required:"
    echo "1. Contact WEEX Labs to whitelist: $VM_IP"
    echo "2. Or investigate why static IP was not assigned correctly"
fi

echo "=============================================================================="
