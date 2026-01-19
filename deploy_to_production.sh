#!/bin/bash
#
# Safe Production Deployment Script
#
# This script safely deploys the latest code to the production
# trading system with health checks and rollback capability.
#

set -e

GCP_IP="34.133.16.230"
GCP_USER="root"
PROJECT_DIR="/opt/AlphaGenesis"
BACKUP_DIR="/opt/AlphaGenesis_backup"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================================================"
echo "  AlphaGenesis Safe Production Deployment"
echo "======================================================================${NC}"
echo ""
echo "Target: $GCP_USER@$GCP_IP:$PROJECT_DIR"
echo "Time: $(date)"
echo ""

# Confirmation
read -p "Deploy to production? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled"
    exit 0
fi
echo ""

# Test connection
echo -e "${BLUE}[1/9] Testing connection...${NC}"
if ! ssh -o ConnectTimeout=5 $GCP_USER@$GCP_IP 'echo "Connected"' 2>/dev/null; then
    echo -e "${RED}✗ Cannot connect to production${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Connected${NC}"
echo ""

# Get current status
echo -e "${BLUE}[2/9] Recording current state...${NC}"
CURRENT_COMMIT=$(ssh $GCP_USER@$GCP_IP "cd $PROJECT_DIR && git rev-parse HEAD" 2>/dev/null)
echo "Current commit: $CURRENT_COMMIT"
echo ""

# Backup current state
echo -e "${BLUE}[3/9] Creating backup...${NC}"
ssh $GCP_USER@$GCP_IP << ENDSSH
set -e
rm -rf $BACKUP_DIR 2>/dev/null || true
cp -r $PROJECT_DIR $BACKUP_DIR
echo "Backup created at $BACKUP_DIR"
ENDSSH
echo -e "${GREEN}✓ Backup complete${NC}"
echo ""

# Stop service
echo -e "${BLUE}[4/9] Stopping trading service...${NC}"
ssh $GCP_USER@$GCP_IP "systemctl stop sdm-trading.service"
sleep 2
echo -e "${GREEN}✓ Service stopped${NC}"
echo ""

# Pull latest code
echo -e "${BLUE}[5/9] Pulling latest code...${NC}"
BRANCH=$(git branch --show-current)
ssh $GCP_USER@$GCP_IP << ENDSSH
set -e
cd $PROJECT_DIR
git fetch origin
git checkout $BRANCH
git pull origin $BRANCH
echo "Updated to: \$(git log -1 --oneline)"
ENDSSH
echo -e "${GREEN}✓ Code updated${NC}"
echo ""

# Install dependencies
echo -e "${BLUE}[6/9] Checking dependencies...${NC}"
ssh $GCP_USER@$GCP_IP << 'ENDSSH'
set -e
cd /opt/AlphaGenesis
if [ -f requirements.txt ]; then
    pip3 install -q -r requirements.txt
    echo "Dependencies updated"
else
    echo "No requirements.txt found, skipping"
fi
ENDSSH
echo -e "${GREEN}✓ Dependencies checked${NC}"
echo ""

# Start service
echo -e "${BLUE}[7/9] Starting trading service...${NC}"
ssh $GCP_USER@$GCP_IP "systemctl start sdm-trading.service"
sleep 5
echo -e "${GREEN}✓ Service started${NC}"
echo ""

# Health check
echo -e "${BLUE}[8/9] Running health checks...${NC}"

# Check service is running
SERVICE_STATUS=$(ssh $GCP_USER@$GCP_IP "systemctl is-active sdm-trading.service" || echo "failed")
if [ "$SERVICE_STATUS" != "active" ]; then
    echo -e "${RED}✗ Service failed to start!${NC}"
    echo ""
    echo "Rolling back..."
    ssh $GCP_USER@$GCP_IP << ENDSSH
systemctl stop sdm-trading.service
rm -rf $PROJECT_DIR
mv $BACKUP_DIR $PROJECT_DIR
systemctl start sdm-trading.service
ENDSSH
    echo -e "${RED}Rollback complete. Check logs for errors.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Service is running${NC}"

# Check for immediate errors
sleep 10
ERROR_COUNT=$(ssh $GCP_USER@$GCP_IP "journalctl -u sdm-trading.service --since '30 seconds ago' --no-pager | grep -c -E 'ERROR|CRITICAL'" || echo "0")
if [ "$ERROR_COUNT" -gt 5 ]; then
    echo -e "${RED}✗ High error rate detected!${NC}"
    echo ""
    echo "Recent errors:"
    ssh $GCP_USER@$GCP_IP "journalctl -u sdm-trading.service --since '30 seconds ago' --no-pager | grep -E 'ERROR|CRITICAL' | tail -10"
    echo ""
    read -p "Continue with deployment? (yes/no): " CONTINUE
    if [ "$CONTINUE" != "yes" ]; then
        echo "Rolling back..."
        ssh $GCP_USER@$GCP_IP << ENDSSH
systemctl stop sdm-trading.service
rm -rf $PROJECT_DIR
mv $BACKUP_DIR $PROJECT_DIR
systemctl start sdm-trading.service
ENDSSH
        echo -e "${RED}Rollback complete${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✓ No critical errors${NC}"

# Show recent logs
echo ""
echo "Recent log output:"
ssh $GCP_USER@$GCP_IP "journalctl -u sdm-trading.service --since '30 seconds ago' --no-pager | tail -20"
echo ""

# Final verification
echo -e "${BLUE}[9/9] Final verification...${NC}"
NEW_COMMIT=$(ssh $GCP_USER@$GCP_IP "cd $PROJECT_DIR && git rev-parse HEAD" 2>/dev/null)
echo "Deployed commit: $NEW_COMMIT"
echo ""

# Cleanup old backup (keep it for manual rollback if needed)
echo "Backup kept at: $BACKUP_DIR (for manual rollback if needed)"
echo ""

# Summary
echo -e "${BLUE}======================================================================"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""
echo "Previous commit: $CURRENT_COMMIT"
echo "New commit: $NEW_COMMIT"
echo "Service status: active"
echo ""
echo "Monitor logs:"
echo "  ssh $GCP_USER@$GCP_IP"
echo "  journalctl -u sdm-trading.service -f"
echo ""
echo "Rollback if needed:"
echo "  ssh $GCP_USER@$GCP_IP"
echo "  systemctl stop sdm-trading.service"
echo "  rm -rf $PROJECT_DIR"
echo "  mv $BACKUP_DIR $PROJECT_DIR"
echo "  systemctl start sdm-trading.service"
echo ""
echo -e "${BLUE}======================================================================${NC}"
