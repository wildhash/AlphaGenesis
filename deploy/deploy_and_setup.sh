#!/bin/bash
#
# Complete Deployment Script
# Copies files to GCP and runs setup
#
# Usage: bash deploy_and_setup.sh
#

set -e

# Configuration
GCP_IP="34.133.16.230"
GCP_USER="root"  # Change if needed
PROJECT_DIR="/opt/AlphaGenesis"
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================================================"
echo "  SDM Trading System - Complete Deployment"
echo "======================================================================${NC}"
echo ""
echo "Source: $LOCAL_DIR"
echo "Target: $GCP_USER@$GCP_IP:$PROJECT_DIR"
echo ""

# Check if we can connect
echo -e "${GREEN}Testing connection to GCP instance...${NC}"
if ! ssh -o ConnectTimeout=5 $GCP_USER@$GCP_IP 'echo "Connection successful"' 2>/dev/null; then
    echo -e "${RED}✗ Cannot connect to $GCP_IP${NC}"
    echo ""
    echo "Please ensure:"
    echo "  1. You have SSH access to the GCP instance"
    echo "  2. Your SSH key is configured"
    echo "  3. The IP address 34.133.16.230 is correct"
    echo ""
    echo "To set up SSH access, run:"
    echo "  ssh-keygen -t ed25519 (if you don't have a key)"
    echo "  ssh-copy-id $GCP_USER@$GCP_IP"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ Connection successful${NC}"
echo ""

# Check for .env file
if [ ! -f "$LOCAL_DIR/.env" ]; then
    echo -e "${YELLOW}⚠ Warning: .env file not found${NC}"
    echo ""
    echo "Creating .env template..."
    cp "$LOCAL_DIR/.env.example" "$LOCAL_DIR/.env"
    echo ""
    echo -e "${YELLOW}IMPORTANT: Edit .env with your WEEX API credentials before continuing!${NC}"
    echo ""
    read -p "Press Enter after you've edited .env, or Ctrl+C to cancel..."
fi

# Confirm deployment
echo -e "${YELLOW}This will:${NC}"
echo "  1. Copy all code to $GCP_IP"
echo "  2. Run complete setup on GCP instance"
echo "  3. Install dependencies"
echo "  4. Configure systemd service"
echo "  5. Start the SDM trading system"
echo ""
read -p "Continue with deployment? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi
echo ""

echo -e "${GREEN}Step 1: Creating temporary deployment package${NC}"
echo "----------------------------------------------------------------------"

# Create deployment package
TEMP_DIR=$(mktemp -d)
echo "Temporary directory: $TEMP_DIR"

# Copy necessary files
rsync -a --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='logs/' \
    --exclude='reports/' \
    --exclude='models/saved/' \
    "$LOCAL_DIR/" "$TEMP_DIR/AlphaGenesis/"

echo -e "${GREEN}✓ Deployment package created${NC}"
echo ""

echo -e "${GREEN}Step 2: Copying files to GCP instance${NC}"
echo "----------------------------------------------------------------------"

# Create project directory on GCP
ssh $GCP_USER@$GCP_IP "mkdir -p $PROJECT_DIR"

# Copy files
rsync -avz --delete \
    "$TEMP_DIR/AlphaGenesis/" \
    "$GCP_USER@$GCP_IP:$PROJECT_DIR/"

# Copy .env file
echo "Copying .env file..."
scp "$LOCAL_DIR/.env" "$GCP_USER@$GCP_IP:$PROJECT_DIR/.env"

echo -e "${GREEN}✓ Files copied to GCP${NC}"
echo ""

echo -e "${GREEN}Step 3: Running setup script on GCP${NC}"
echo "----------------------------------------------------------------------"

# Make setup script executable and run it
ssh $GCP_USER@$GCP_IP << 'ENDSSH'
chmod +x /opt/AlphaGenesis/deploy/setup_gcp_instance.sh
bash /opt/AlphaGenesis/deploy/setup_gcp_instance.sh
ENDSSH

echo ""

echo -e "${GREEN}Step 4: Verifying .env configuration${NC}"
echo "----------------------------------------------------------------------"

# Check if .env has actual credentials
ssh $GCP_USER@$GCP_IP << 'ENDSSH'
if grep -q "your_api_key_here" /opt/AlphaGenesis/.env; then
    echo ""
    echo "⚠️  WARNING: .env file still contains placeholder values!"
    echo ""
    echo "Please edit /opt/AlphaGenesis/.env with your actual WEEX API credentials:"
    echo "  nano /opt/AlphaGenesis/.env"
    echo ""
    echo "After editing, start the service:"
    echo "  systemctl start sdm-trading.service"
    echo ""
    exit 1
fi
ENDSSH

if [ $? -eq 1 ]; then
    echo -e "${YELLOW}⚠ Please configure .env file on GCP instance${NC}"
    echo ""
    echo "Run this command to edit it:"
    echo "  ssh $GCP_USER@$GCP_IP 'nano $PROJECT_DIR/.env'"
    echo ""
    read -p "Press Enter after you've configured .env to start the service..."
fi
echo ""

echo -e "${GREEN}Step 5: Starting SDM Trading System${NC}"
echo "----------------------------------------------------------------------"

ssh $GCP_USER@$GCP_IP << 'ENDSSH'
echo "Starting service..."
systemctl start sdm-trading.service
sleep 3
echo ""
echo "Service status:"
systemctl status sdm-trading.service --no-pager
ENDSSH

echo ""

echo -e "${GREEN}Step 6: Showing initial logs${NC}"
echo "----------------------------------------------------------------------"

ssh $GCP_USER@$GCP_IP 'journalctl -u sdm-trading.service -n 50 --no-pager'

echo ""

# Cleanup
rm -rf "$TEMP_DIR"

echo -e "${BLUE}======================================================================"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""
echo "Your SDM Trading System is now running on GCP at $GCP_IP"
echo ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo ""
echo "View live logs:"
echo "  ssh $GCP_USER@$GCP_IP 'journalctl -u sdm-trading.service -f'"
echo ""
echo "Check status:"
echo "  ssh $GCP_USER@$GCP_IP 'systemctl status sdm-trading.service'"
echo ""
echo "Stop system:"
echo "  ssh $GCP_USER@$GCP_IP 'systemctl stop sdm-trading.service'"
echo ""
echo "Restart system:"
echo "  ssh $GCP_USER@$GCP_IP 'systemctl restart sdm-trading.service'"
echo ""
echo "Run monitor:"
echo "  ssh $GCP_USER@$GCP_IP 'bash $PROJECT_DIR/monitor.sh'"
echo ""
echo "View reports:"
echo "  ssh $GCP_USER@$GCP_IP 'ls -lh $PROJECT_DIR/reports/sdm/'"
echo ""
echo -e "${BLUE}======================================================================${NC}"
