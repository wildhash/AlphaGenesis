#!/bin/bash
#
# GCP Instance Setup Script for SDM Trading System
# Run this script ON your GCP instance at 34.133.16.230
#
# Usage: bash setup_gcp_instance.sh
#

set -e  # Exit on error

echo "======================================================================"
echo "  SDM Trading System - GCP Instance Setup"
echo "======================================================================"
echo ""
echo "GCP IP: 34.133.16.230"
echo "Timestamp: $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/opt/AlphaGenesis"
SERVICE_USER="alphagenesis"
PYTHON_VERSION="3.9"

echo -e "${GREEN}Step 1: System Information${NC}"
echo "----------------------------------------------------------------------"
echo "Hostname: $(hostname)"
echo "IP Address: $(hostname -I)"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "Python: $(python3 --version 2>/dev/null || echo 'Not installed')"
echo ""

echo -e "${GREEN}Step 2: Installing System Dependencies${NC}"
echo "----------------------------------------------------------------------"

# Update system
echo "Updating system packages..."
apt-get update -qq

# Install required packages
echo "Installing required packages..."
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    htop \
    tmux \
    vim \
    jq

echo -e "${GREEN}✓${NC} System dependencies installed"
echo ""

echo -e "${GREEN}Step 3: Creating Service User${NC}"
echo "----------------------------------------------------------------------"

# Create service user if doesn't exist
if ! id "$SERVICE_USER" &>/dev/null; then
    echo "Creating user: $SERVICE_USER"
    useradd -m -s /bin/bash $SERVICE_USER
    echo -e "${GREEN}✓${NC} User created: $SERVICE_USER"
else
    echo -e "${YELLOW}⚠${NC} User already exists: $SERVICE_USER"
fi
echo ""

echo -e "${GREEN}Step 4: Creating Project Directory${NC}"
echo "----------------------------------------------------------------------"

# Create project directory
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Creating directory: $PROJECT_DIR"
    mkdir -p $PROJECT_DIR
    chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR
    echo -e "${GREEN}✓${NC} Directory created: $PROJECT_DIR"
else
    echo -e "${YELLOW}⚠${NC} Directory already exists: $PROJECT_DIR"
    chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR
fi
echo ""

echo -e "${GREEN}Step 5: Installing Poetry${NC}"
echo "----------------------------------------------------------------------"

# Install Poetry as service user
if ! su - $SERVICE_USER -c "command -v poetry" &>/dev/null; then
    echo "Installing Poetry..."
    su - $SERVICE_USER -c "curl -sSL https://install.python-poetry.org | python3 -"

    # Add Poetry to PATH
    echo 'export PATH="/home/alphagenesis/.local/bin:$PATH"' >> /home/$SERVICE_USER/.bashrc

    echo -e "${GREEN}✓${NC} Poetry installed"
else
    echo -e "${YELLOW}⚠${NC} Poetry already installed"
fi
echo ""

echo -e "${GREEN}Step 6: Cloning Repository${NC}"
echo "----------------------------------------------------------------------"

if [ ! -d "$PROJECT_DIR/.git" ]; then
    echo "Cloning AlphaGenesis repository..."
    su - $SERVICE_USER -c "git clone https://github.com/wildhash/AlphaGenesis.git $PROJECT_DIR"
    echo -e "${GREEN}✓${NC} Repository cloned"
else
    echo -e "${YELLOW}⚠${NC} Repository already exists, pulling latest changes..."
    su - $SERVICE_USER -c "cd $PROJECT_DIR && git fetch origin && git checkout claude/weex-trading-system-JjDSY && git pull"
fi
echo ""

echo -e "${GREEN}Step 7: Installing Python Dependencies${NC}"
echo "----------------------------------------------------------------------"

echo "This may take a few minutes..."
su - $SERVICE_USER -c "cd $PROJECT_DIR && export PATH='/home/alphagenesis/.local/bin:$PATH' && poetry install --no-dev" || {
    echo -e "${YELLOW}⚠${NC} Poetry install failed, trying pip install..."
    su - $SERVICE_USER -c "cd $PROJECT_DIR && pip3 install -r requirements.txt" || {
        echo -e "${RED}✗${NC} Dependency installation failed"
        echo "Installing critical dependencies manually..."
        pip3 install numpy pandas loguru python-dotenv requests scikit-learn
    }
}
echo -e "${GREEN}✓${NC} Dependencies installed"
echo ""

echo -e "${GREEN}Step 8: Creating Required Directories${NC}"
echo "----------------------------------------------------------------------"

# Create necessary directories
su - $SERVICE_USER -c "mkdir -p $PROJECT_DIR/logs"
su - $SERVICE_USER -c "mkdir -p $PROJECT_DIR/reports/sdm"
su - $SERVICE_USER -c "mkdir -p $PROJECT_DIR/models/saved"

echo -e "${GREEN}✓${NC} Directories created"
echo ""

echo -e "${GREEN}Step 9: Setting Up Environment File${NC}"
echo "----------------------------------------------------------------------"

# Create .env template if doesn't exist
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cat > $PROJECT_DIR/.env << 'EOF'
# WEEX API Configuration
WEEX_API_KEY=your_api_key_here
WEEX_API_SECRET=your_api_secret_here
WEEX_API_PASSPHRASE=your_passphrase_here
WEEX_BASE_URL=https://api-contract.weex.com

# Trading Configuration
INITIAL_CAPITAL=1000.0
UPDATE_INTERVAL=300

# Model Configuration
MODEL_DEVICE=cpu

# Risk Management
MAX_LEVERAGE=20

# Logging
LOG_LEVEL=INFO

# Feature Flags
ENABLE_LIVE_TRADING=true
EOF

    chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR/.env
    echo -e "${GREEN}✓${NC} .env template created"
    echo -e "${YELLOW}⚠${NC} IMPORTANT: Edit $PROJECT_DIR/.env with your actual API credentials!"
else
    echo -e "${YELLOW}⚠${NC} .env file already exists"
fi
echo ""

echo -e "${GREEN}Step 10: Creating Systemd Service${NC}"
echo "----------------------------------------------------------------------"

# Create systemd service file
cat > /etc/systemd/system/sdm-trading.service << EOF
[Unit]
Description=SDM Trading System for WEEX AI Wars
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=/home/$SERVICE_USER/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/$SERVICE_USER/.local/bin/poetry run python scripts/start_sdm_trading.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

# Resource limits
LimitNOFILE=65536
MemoryLimit=2G

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

# Enable service (but don't start yet)
systemctl enable sdm-trading.service

echo -e "${GREEN}✓${NC} Systemd service created and enabled"
echo ""

echo -e "${GREEN}Step 11: Configuring Firewall${NC}"
echo "----------------------------------------------------------------------"

# Check if ufw is installed and configure
if command -v ufw &>/dev/null; then
    echo "Configuring UFW firewall..."
    ufw allow 22/tcp  # SSH
    ufw allow 80/tcp  # HTTP (if needed)
    ufw allow 443/tcp # HTTPS (if needed)
    echo -e "${GREEN}✓${NC} Firewall configured"
else
    echo -e "${YELLOW}⚠${NC} UFW not installed, skipping firewall configuration"
fi
echo ""

echo -e "${GREEN}Step 12: Setting Up Monitoring${NC}"
echo "----------------------------------------------------------------------"

# Create monitoring script
cat > $PROJECT_DIR/monitor.sh << 'EOF'
#!/bin/bash
# Quick monitoring script for SDM Trading System

echo "======================================================================="
echo "  SDM Trading System - Status Monitor"
echo "======================================================================="
echo ""

echo "Service Status:"
systemctl status sdm-trading.service --no-pager | head -20
echo ""

echo "Recent Logs (last 20 lines):"
journalctl -u sdm-trading.service -n 20 --no-pager
echo ""

echo "System Resources:"
echo "  Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
echo "  Disk: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 " used)"}')"
echo "  Load: $(uptime | awk -F'load average:' '{print $2}')"
echo ""

if [ -d "/opt/AlphaGenesis/reports/sdm" ]; then
    echo "Recent Reports:"
    ls -lht /opt/AlphaGenesis/reports/sdm/ | head -5
fi

echo ""
echo "======================================================================="
EOF

chmod +x $PROJECT_DIR/monitor.sh
chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR/monitor.sh

echo -e "${GREEN}✓${NC} Monitoring script created: $PROJECT_DIR/monitor.sh"
echo ""

echo "======================================================================"
echo -e "${GREEN}  Setup Complete!${NC}"
echo "======================================================================"
echo ""
echo "Next Steps:"
echo ""
echo "1. Edit the .env file with your WEEX API credentials:"
echo "   nano $PROJECT_DIR/.env"
echo ""
echo "2. Start the SDM trading system:"
echo "   systemctl start sdm-trading.service"
echo ""
echo "3. Check the status:"
echo "   systemctl status sdm-trading.service"
echo ""
echo "4. View live logs:"
echo "   journalctl -u sdm-trading.service -f"
echo ""
echo "5. Run monitor script:"
echo "   bash $PROJECT_DIR/monitor.sh"
echo ""
echo "Useful Commands:"
echo "  Start:   systemctl start sdm-trading.service"
echo "  Stop:    systemctl stop sdm-trading.service"
echo "  Restart: systemctl restart sdm-trading.service"
echo "  Status:  systemctl status sdm-trading.service"
echo "  Logs:    journalctl -u sdm-trading.service -f"
echo ""
echo "======================================================================"
