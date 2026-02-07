#!/bin/bash
#
# GCP Test Environment Setup Script
# AlphaGenesis Trading System
#
# Usage: sudo bash setup_gcp_test.sh
#

set -e

echo "======================================================================"
echo "  AlphaGenesis - GCP Test Environment Setup"
echo "======================================================================"
echo ""
echo "Environment: TEST"
echo "Cloud Provider: Google Cloud Platform"
echo "Timestamp: $(date)"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_DIR="/opt/AlphaGenesis"
SERVICE_USER="alphagenesis"
PYTHON_VERSION="3.9"
ENVIRONMENT="test"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 1: System Information${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "Hostname: $(hostname)"
echo "IP Address: $(hostname -I | awk '{print $1}')"
echo "OS: $(lsb_release -d | cut -f2)"
echo "Kernel: $(uname -r)"
echo "Python: $(python3 --version 2>/dev/null || echo 'Not installed')"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 2: Installing System Dependencies${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Update system
echo "Updating package lists..."
apt-get update -qq

# Install dependencies
echo "Installing system packages..."
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    curl \
    wget \
    build-essential \
    libssl-dev \
    libffi-dev \
    htop \
    tmux \
    vim \
    nano \
    jq \
    net-tools \
    dnsutils

echo -e "${GREEN}✓${NC} System dependencies installed"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 3: Creating Service User${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if ! id "$SERVICE_USER" &>/dev/null; then
    echo "Creating user: $SERVICE_USER"
    useradd -m -s /bin/bash $SERVICE_USER
    echo -e "${GREEN}✓${NC} User created: $SERVICE_USER"
else
    echo -e "${YELLOW}⚠${NC} User already exists: $SERVICE_USER"
fi
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 4: Setting Up Project Directory${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "Creating directory: $PROJECT_DIR"
    mkdir -p $PROJECT_DIR
    chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR
    echo -e "${GREEN}✓${NC} Directory created"
else
    echo -e "${YELLOW}⚠${NC} Directory exists, updating permissions"
    chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR
fi
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 5: Installing Poetry${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if ! su - $SERVICE_USER -c "command -v poetry" &>/dev/null; then
    echo "Installing Poetry for $SERVICE_USER..."
    su - $SERVICE_USER -c "curl -sSL https://install.python-poetry.org | python3 -"
    echo 'export PATH="/home/alphagenesis/.local/bin:$PATH"' >> /home/$SERVICE_USER/.bashrc
    echo -e "${GREEN}✓${NC} Poetry installed"
else
    echo -e "${YELLOW}⚠${NC} Poetry already installed"
fi
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 6: Installing Python Dependencies${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo "Installing core Python packages..."
pip3 install --upgrade pip setuptools wheel

echo "Installing trading system dependencies..."
pip3 install -q \
    numpy>=1.24.0 \
    pandas>=2.0.0 \
    scipy>=1.10.0 \
    scikit-learn>=1.3.0 \
    requests>=2.31.0 \
    websocket-client>=1.6.0 \
    aiohttp>=3.8.0 \
    python-dotenv>=1.0.0 \
    pyyaml>=6.0 \
    loguru>=0.7.0 \
    ccxt>=4.0.0

echo -e "${GREEN}✓${NC} Python dependencies installed"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 7: Creating Required Directories${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

su - $SERVICE_USER -c "mkdir -p $PROJECT_DIR/logs"
su - $SERVICE_USER -c "mkdir -p $PROJECT_DIR/reports/sdm"
su - $SERVICE_USER -c "mkdir -p $PROJECT_DIR/models/saved"
su - $SERVICE_USER -c "mkdir -p $PROJECT_DIR/data"

echo -e "${GREEN}✓${NC} Directories created"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 8: Creating Environment Configuration${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ ! -f "$PROJECT_DIR/.env" ]; then
    cat > $PROJECT_DIR/.env << 'EOF'
# ═══════════════════════════════════════════════════════════════
#  AlphaGenesis Trading System - GCP TEST ENVIRONMENT
# ═══════════════════════════════════════════════════════════════

# WEEX API Configuration
WEEX_API_KEY=your_test_api_key_here
WEEX_API_SECRET=your_test_api_secret_here
WEEX_API_PASSPHRASE=your_test_passphrase_here
WEEX_BASE_URL=https://api-contract.weex.com

# Trading Configuration - TEST MODE
INITIAL_CAPITAL=1000.0
UPDATE_INTERVAL=300
MAX_LEVERAGE=5
ENABLE_LIVE_TRADING=false
ENABLE_PAPER_TRADING=true

# Trading Symbols
TRADING_SYMBOLS=BTC/USDT,ETH/USDT,SOL/USDT

# Risk Management
MAX_POSITION_SIZE=0.1
STOP_LOSS_PERCENT=0.02
TAKE_PROFIT_PERCENT=0.05

# Model Configuration
MODEL_DEVICE=cpu
MODEL_CHECKPOINT_DIR=./models/saved

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/alphagenesis.log

# Environment Tags
DEPLOYMENT_ENV=gcp-test
REGION=us-central1
CLOUD_PROVIDER=gcp
ENVIRONMENT=test

# Feature Flags
ENABLE_BACKTESTING=true
ENABLE_METRICS=true
ENABLE_MONITORING=true
EOF

    chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR/.env
    echo -e "${GREEN}✓${NC} Environment file created"
    echo -e "${YELLOW}⚠${NC} IMPORTANT: Edit $PROJECT_DIR/.env with your WEEX API credentials"
else
    echo -e "${YELLOW}⚠${NC} .env file already exists, skipping"
fi
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 9: Creating Systemd Service${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cat > /etc/systemd/system/sdm-trading.service << EOF
[Unit]
Description=AlphaGenesis SDM Trading System - TEST ENVIRONMENT
After=network-online.target
Wants=network-online.target
Documentation=https://github.com/wildhash/AlphaGenesis

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=/usr/local/bin:/usr/bin:/bin:/home/$SERVICE_USER/.local/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="DEPLOYMENT_ENV=gcp-test"

# Start command
ExecStart=/usr/bin/python3 scripts/start_sdm_trading.py

# Restart policy
Restart=on-failure
RestartSec=10
StartLimitInterval=300
StartLimitBurst=5

# Resource limits (test environment)
LimitNOFILE=65536
MemoryLimit=4G
CPUQuota=200%

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=alphagenesis-test

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable sdm-trading.service

echo -e "${GREEN}✓${NC} Systemd service created and enabled"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 10: Creating Management Scripts${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Monitor script
cat > $PROJECT_DIR/monitor.sh << 'EOF'
#!/bin/bash
echo "═══════════════════════════════════════════════════════════════"
echo "  AlphaGenesis Test Environment - Status Monitor"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Service Status:"
systemctl status sdm-trading.service --no-pager | head -20
echo ""
echo "Recent Logs:"
journalctl -u sdm-trading.service -n 30 --no-pager
echo ""
echo "System Resources:"
echo "  CPU Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "  Memory: $(free -h | grep Mem | awk '{print $3 " / " $2}')"
echo "  Disk: $(df -h / | tail -1 | awk '{print $3 " / " $2 " (" $5 " used)"}')"
echo ""
echo "═══════════════════════════════════════════════════════════════"
EOF

chmod +x $PROJECT_DIR/monitor.sh
chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR/monitor.sh

echo -e "${GREEN}✓${NC} Management scripts created"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 11: Installing Optional Monitoring Tools${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Install Google Cloud Monitoring agent (optional)
if command -v gcloud &>/dev/null; then
    echo "Google Cloud SDK detected, installing monitoring agent..."
    curl -sSO https://dl.google.com/cloudagents/add-monitoring-agent-repo.sh
    bash add-monitoring-agent-repo.sh --also-install || echo "Monitoring agent installation skipped"
    rm -f add-monitoring-agent-repo.sh
fi

echo -e "${GREEN}✓${NC} Optional tools configured"
echo ""

echo "======================================================================"
echo -e "${GREEN}  ✓ GCP Test Environment Setup Complete!${NC}"
echo "======================================================================"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Configure WEEX API credentials:"
echo "   ${BLUE}sudo nano $PROJECT_DIR/.env${NC}"
echo ""
echo "2. Start the trading system:"
echo "   ${BLUE}sudo systemctl start sdm-trading.service${NC}"
echo ""
echo "3. Check status:"
echo "   ${BLUE}sudo systemctl status sdm-trading.service${NC}"
echo ""
echo "4. View logs:"
echo "   ${BLUE}sudo journalctl -u sdm-trading.service -f${NC}"
echo ""
echo "5. Monitor system:"
echo "   ${BLUE}bash $PROJECT_DIR/monitor.sh${NC}"
echo ""
echo -e "${YELLOW}Management Commands:${NC}"
echo "  Start:   ${BLUE}systemctl start sdm-trading.service${NC}"
echo "  Stop:    ${BLUE}systemctl stop sdm-trading.service${NC}"
echo "  Restart: ${BLUE}systemctl restart sdm-trading.service${NC}"
echo "  Status:  ${BLUE}systemctl status sdm-trading.service${NC}"
echo "  Logs:    ${BLUE}journalctl -u sdm-trading.service -f${NC}"
echo ""
echo "======================================================================"
echo -e "${GREEN}Environment: TEST | Provider: GCP${NC}"
echo "======================================================================"
echo ""
