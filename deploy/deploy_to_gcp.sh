#!/bin/bash
#
# Deploy SDM Trading System to GCP
#
# Reserved IP: 34.133.16.230
#

set -e  # Exit on error

# Configuration
GCP_IP="34.133.16.230"
GCP_USER="alphagenesis"  # Change to your GCP username
PROJECT_DIR="/home/${GCP_USER}/AlphaGenesis"
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "======================================================================"
echo "  SDM Trading System - GCP Deployment"
echo "======================================================================"
echo ""
echo "Target: ${GCP_USER}@${GCP_IP}:${PROJECT_DIR}"
echo "Source: ${LOCAL_DIR}"
echo ""

# Check if .env file exists
if [ ! -f "${LOCAL_DIR}/.env" ]; then
    echo "ERROR: .env file not found!"
    echo "Please create .env file with your WEEX API credentials"
    echo ""
    echo "Copy .env.example to .env and fill in your credentials:"
    echo "  cp .env.example .env"
    echo "  # Edit .env with your API keys"
    exit 1
fi

# Confirm deployment
read -p "Deploy to GCP? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo "Step 1: Syncing code to GCP..."
echo "----------------------------------------------------------------------"

rsync -avz --delete \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='logs/' \
    --exclude='reports/' \
    --exclude='models/saved/' \
    "${LOCAL_DIR}/" \
    "${GCP_USER}@${GCP_IP}:${PROJECT_DIR}/"

echo "✓ Code synced"
echo ""

echo "Step 2: Copying .env file..."
echo "----------------------------------------------------------------------"

scp "${LOCAL_DIR}/.env" "${GCP_USER}@${GCP_IP}:${PROJECT_DIR}/.env"

echo "✓ .env copied"
echo ""

echo "Step 3: Installing dependencies on GCP..."
echo "----------------------------------------------------------------------"

ssh "${GCP_USER}@${GCP_IP}" << 'ENDSSH'
cd /home/alphagenesis/AlphaGenesis

# Check if Python 3.9+ is installed
python3 --version

# Install Poetry if not installed
if ! command -v poetry &> /dev/null; then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="/home/alphagenesis/.local/bin:$PATH"
fi

# Install dependencies
echo "Installing dependencies..."
poetry install --no-dev

echo "✓ Dependencies installed"
ENDSSH

echo ""

echo "Step 4: Setting up systemd service..."
echo "----------------------------------------------------------------------"

# Create systemd service file
cat > /tmp/sdm-trading.service << EOF
[Unit]
Description=SDM Trading System for WEEX AI Wars
After=network.target

[Service]
Type=simple
User=${GCP_USER}
WorkingDirectory=${PROJECT_DIR}
ExecStart=/home/${GCP_USER}/.local/bin/poetry run python scripts/start_sdm_trading.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Copy service file to GCP
scp /tmp/sdm-trading.service "${GCP_USER}@${GCP_IP}:/tmp/sdm-trading.service"

# Install service
ssh "${GCP_USER}@${GCP_IP}" << 'ENDSSH'
sudo mv /tmp/sdm-trading.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sdm-trading.service
echo "✓ Systemd service installed"
ENDSSH

echo ""

echo "Step 5: Starting SDM Trading System..."
echo "----------------------------------------------------------------------"

ssh "${GCP_USER}@${GCP_IP}" << 'ENDSSH'
sudo systemctl restart sdm-trading.service
sleep 2
sudo systemctl status sdm-trading.service --no-pager
ENDSSH

echo ""
echo "======================================================================"
echo "  Deployment Complete!"
echo "======================================================================"
echo ""
echo "The SDM Trading System is now running on GCP at ${GCP_IP}"
echo ""
echo "Useful commands:"
echo "  View logs:    ssh ${GCP_USER}@${GCP_IP} 'sudo journalctl -u sdm-trading.service -f'"
echo "  Stop system:  ssh ${GCP_USER}@${GCP_IP} 'sudo systemctl stop sdm-trading.service'"
echo "  Start system: ssh ${GCP_USER}@${GCP_IP} 'sudo systemctl start sdm-trading.service'"
echo "  Check status: ssh ${GCP_USER}@${GCP_IP} 'sudo systemctl status sdm-trading.service'"
echo ""
echo "  View reports: ssh ${GCP_USER}@${GCP_IP} 'ls -lh ${PROJECT_DIR}/reports/sdm/'"
echo ""
echo "======================================================================"
