#!/bin/bash
#
# Alibaba Cloud Production Setup Script
# AlphaGenesis Trading System
#
# Usage: sudo bash setup_alibaba_cloud.sh
#

set -e

echo "======================================================================"
echo "  AlphaGenesis - Alibaba Cloud Production Deployment"
echo "======================================================================"
echo ""
echo "Environment: PRODUCTION"
echo "Cloud Provider: Alibaba Cloud (阿里云)"
echo "Region: Hong Kong (cn-hongkong)"
echo "Timestamp: $(date)"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Configuration
PROJECT_DIR="/opt/AlphaGenesis"
SERVICE_USER="alphagenesis"
PYTHON_VERSION="3.9"
ENVIRONMENT="production"
REGION="cn-hongkong"

echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 1: System Verification${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo "Hostname: $(hostname)"
echo "IP Address: $(hostname -I | awk '{print $1}')"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "Kernel: $(uname -r)"
echo "Architecture: $(uname -m)"
echo "Python: $(python3 --version 2>/dev/null || echo 'Not installed')"
echo ""

# Verify we're on Alibaba Cloud
if curl -s --connect-timeout 3 http://100.100.100.200/latest/meta-data/instance-id &>/dev/null; then
    INSTANCE_ID=$(curl -s http://100.100.100.200/latest/meta-data/instance-id)
    INSTANCE_TYPE=$(curl -s http://100.100.100.200/latest/meta-data/instance/instance-type)
    echo -e "${GREEN}✓${NC} Verified: Running on Alibaba Cloud ECS"
    echo "  Instance ID: $INSTANCE_ID"
    echo "  Instance Type: $INSTANCE_TYPE"
else
    echo -e "${YELLOW}⚠${NC} Warning: Could not verify Alibaba Cloud metadata"
fi
echo ""

echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 2: System Updates and Dependencies${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if using apt or yum
if command -v apt-get &>/dev/null; then
    PKG_MANAGER="apt-get"
    UPDATE_CMD="apt-get update -qq"
    INSTALL_CMD="DEBIAN_FRONTEND=noninteractive apt-get install -y -qq"
elif command -v yum &>/dev/null; then
    PKG_MANAGER="yum"
    UPDATE_CMD="yum makecache fast"
    INSTALL_CMD="yum install -y -q"
else
    echo -e "${RED}✗${NC} Unsupported package manager"
    exit 1
fi

echo "Package Manager: $PKG_MANAGER"
echo "Updating package lists..."
$UPDATE_CMD

echo "Installing system dependencies..."
$INSTALL_CMD \
    python3 \
    python3-pip \
    python3-devel \
    git \
    curl \
    wget \
    gcc \
    gcc-c++ \
    make \
    openssl-devel \
    libffi-devel \
    htop \
    tmux \
    vim \
    nano \
    jq \
    net-tools \
    bind-utils || {
        echo "Trying alternate package names..."
        $INSTALL_CMD python3-dev build-essential || true
    }

echo -e "${GREEN}✓${NC} System dependencies installed"
echo ""

echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 3: Creating Service User${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -m -s /bin/bash $SERVICE_USER
    echo -e "${GREEN}✓${NC} User created: $SERVICE_USER"
else
    echo -e "${YELLOW}⚠${NC} User already exists: $SERVICE_USER"
fi
echo ""

echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 4: Project Directory Setup${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

mkdir -p $PROJECT_DIR
chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR
echo -e "${GREEN}✓${NC} Project directory ready: $PROJECT_DIR"
echo ""

echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 5: Cloning Repository${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ ! -d "$PROJECT_DIR/.git" ]; then
    echo "Cloning AlphaGenesis repository..."
    su - $SERVICE_USER -c "git clone https://github.com/wildhash/AlphaGenesis.git $PROJECT_DIR"
    su - $SERVICE_USER -c "cd $PROJECT_DIR && git checkout finals/alpha-genesis-clean"
    echo -e "${GREEN}✓${NC} Repository cloned (finals/alpha-genesis-clean branch)"
else
    echo "Repository exists, pulling latest..."
    su - $SERVICE_USER -c "cd $PROJECT_DIR && git fetch origin && git checkout finals/alpha-genesis-clean && git pull"
    echo -e "${GREEN}✓${NC} Repository updated"
fi
echo ""

echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 6: Python Dependencies Installation${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo "Upgrading pip, setuptools, wheel..."
python3 -m pip install --upgrade pip setuptools wheel

echo "Installing production dependencies (this may take 5-10 minutes)..."
pip3 install --no-cache-dir \
    numpy>=1.24.0 \
    pandas>=2.0.0 \
    scipy>=1.10.0 \
    scikit-learn>=1.3.0 \
    torch>=2.0.0 \
    requests>=2.31.0 \
    websocket-client>=1.6.0 \
    aiohttp>=3.8.0 \
    python-dotenv>=1.0.0 \
    pyyaml>=6.0 \
    loguru>=0.7.0 \
    ccxt>=4.0.0 \
    arch>=6.2.0 \
    statsmodels>=0.14.0

echo -e "${GREEN}✓${NC} Python dependencies installed"
echo ""

echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 7: Directory Structure${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

su - $SERVICE_USER -c "mkdir -p $PROJECT_DIR/{logs,reports/sdm,models/saved,data,backups}"
echo -e "${GREEN}✓${NC} Directory structure created"
echo ""

echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 8: Production Environment Configuration${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ ! -f "$PROJECT_DIR/.env" ]; then
    cat > $PROJECT_DIR/.env << 'EOF'
# ═══════════════════════════════════════════════════════════════
#  AlphaGenesis Trading System - ALIBABA CLOUD PRODUCTION
# ═══════════════════════════════════════════════════════════════

# WEEX API Configuration - PRODUCTION
WEEX_API_KEY=YOUR_PRODUCTION_API_KEY
WEEX_API_SECRET=YOUR_PRODUCTION_API_SECRET
WEEX_API_PASSPHRASE=YOUR_PRODUCTION_PASSPHRASE
WEEX_BASE_URL=https://api-contract.weex.com

# Trading Configuration - PRODUCTION MODE
INITIAL_CAPITAL=10000.0
UPDATE_INTERVAL=60
MAX_LEVERAGE=10
ENABLE_LIVE_TRADING=true
ENABLE_PAPER_TRADING=false

# Trading Symbols (8 pairs for competition)
TRADING_SYMBOLS=BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,XRP/USDT,ADA/USDT,DOGE/USDT,MATIC/USDT

# Risk Management - PRODUCTION
MAX_POSITION_SIZE=0.15
STOP_LOSS_PERCENT=0.025
TAKE_PROFIT_PERCENT=0.06
MAX_DRAWDOWN_LIMIT=0.15
VAR_CONFIDENCE_LEVEL=0.95

# Strategy Configuration
STRATEGY_MODE=momentum
ENABLE_MULTI_STRATEGY=true
MOMENTUM_THRESHOLD=0.02
VOLATILITY_THRESHOLD=0.03

# Model Configuration
MODEL_DEVICE=cpu
MODEL_CHECKPOINT_DIR=./models/saved
ENABLE_ML_MODELS=true

# Logging - PRODUCTION
LOG_LEVEL=INFO
LOG_FILE=./logs/alphagenesis_production.log
ENABLE_DETAILED_LOGGING=true
LOG_ROTATION=100 MB
LOG_RETENTION=30 days

# Environment Tags
DEPLOYMENT_ENV=alibaba-cloud-production
REGION=cn-hongkong
CLOUD_PROVIDER=alibaba
ENVIRONMENT=production
INSTANCE_NAME=alphagenesis-prod-alibaba

# Performance Monitoring
ENABLE_METRICS=true
ENABLE_MONITORING=true
METRICS_INTERVAL=60
HEALTH_CHECK_INTERVAL=30

# Feature Flags
ENABLE_BACKTESTING=false
ENABLE_AI_REASONING=true
ENABLE_ORDER_BOOK_ANALYSIS=true
ENABLE_SENTIMENT_ANALYSIS=false

# Alert Configuration
ENABLE_ALERTS=true
ALERT_ON_ERROR=true
ALERT_ON_LARGE_LOSS=true
LARGE_LOSS_THRESHOLD=500.0

# Competition Settings
COMPETITION_MODE=true
COMPETITION_NAME=WEEX_AI_WARS
EOF

    chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR/.env
    chmod 600 $PROJECT_DIR/.env
    echo -e "${GREEN}✓${NC} Production environment file created"
    echo -e "${RED}⚠ CRITICAL: Edit $PROJECT_DIR/.env with PRODUCTION API credentials!${NC}"
else
    echo -e "${YELLOW}⚠${NC} .env file exists, keeping existing configuration"
fi
echo ""

echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 9: Systemd Service Configuration${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cat > /etc/systemd/system/sdm-trading.service << EOF
[Unit]
Description=AlphaGenesis SDM Trading System - PRODUCTION (Alibaba Cloud)
After=network-online.target
Wants=network-online.target
Documentation=https://github.com/wildhash/AlphaGenesis

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="DEPLOYMENT_ENV=alibaba-cloud-production"
Environment="REGION=$REGION"

# Start command
ExecStart=/usr/bin/python3 scripts/start_sdm_trading.py

# Pre-start checks
ExecStartPre=/bin/sh -c 'test -f $PROJECT_DIR/.env || (echo "ERROR: .env file missing" && exit 1)'

# Restart policy - aggressive for production
Restart=always
RestartSec=15
StartLimitInterval=600
StartLimitBurst=10

# Resource limits - production
LimitNOFILE=131072
MemoryLimit=6G
CPUQuota=300%

# Watchdog
WatchdogSec=300

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=alphagenesis-prod

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable sdm-trading.service

echo -e "${GREEN}✓${NC} Production systemd service configured"
echo ""

echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 10: Management and Monitoring Scripts${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Production monitor script
cat > $PROJECT_DIR/monitor_production.sh << 'EOF'
#!/bin/bash
echo "═══════════════════════════════════════════════════════════════"
echo "  AlphaGenesis PRODUCTION - Alibaba Cloud Monitor"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SERVICE STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
systemctl status sdm-trading.service --no-pager | head -15
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "RECENT ACTIVITY (Last 20 lines)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
journalctl -u sdm-trading.service -n 20 --no-pager
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SYSTEM RESOURCES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CPU Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "Memory: $(free -h | grep Mem | awk '{print $3 " / " $2 " (" int($3/$2*100) "%)"}')"
echo "Disk: $(df -h / | tail -1 | awk '{print $3 " / " $2 " (" $5 " used)"}')"
echo "Network: $(ip -s link show | grep -A1 "state UP" | tail -1 | awk '{print "RX: " $1 " TX: " $9}')"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "RECENT ERRORS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
journalctl -u sdm-trading.service --since "10 minutes ago" | grep -i "error\|exception\|failed" | tail -10 || echo "No recent errors"
echo ""
echo "═══════════════════════════════════════════════════════════════"
EOF

chmod +x $PROJECT_DIR/monitor_production.sh
chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR/monitor_production.sh

# Backup script
cat > $PROJECT_DIR/backup_production.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/AlphaGenesis/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/production_backup_$TIMESTAMP.tar.gz"

mkdir -p $BACKUP_DIR

echo "Creating production backup: $BACKUP_FILE"
tar -czf $BACKUP_FILE \
    /opt/AlphaGenesis/.env \
    /opt/AlphaGenesis/logs \
    /opt/AlphaGenesis/reports \
    /tmp/bandit_state.json \
    /tmp/position_ledger.json \
    /tmp/trading_journal.db 2>/dev/null

# Keep only last 7 days of backups
find $BACKUP_DIR -name "production_backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
ls -lh $BACKUP_FILE
EOF

chmod +x $PROJECT_DIR/backup_production.sh
chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR/backup_production.sh

# Add backup cron job
(crontab -u $SERVICE_USER -l 2>/dev/null; echo "0 */6 * * * $PROJECT_DIR/backup_production.sh") | crontab -u $SERVICE_USER -

echo -e "${GREEN}✓${NC} Management scripts created"
echo "  - monitor_production.sh (health check)"
echo "  - backup_production.sh (automated backups every 6 hours)"
echo ""

echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 11: Firewall Configuration${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if command -v firewalld &>/dev/null; then
    systemctl start firewalld || true
    firewall-cmd --permanent --add-service=ssh || true
    firewall-cmd --permanent --add-service=https || true
    firewall-cmd --reload || true
    echo -e "${GREEN}✓${NC} Firewall configured (firewalld)"
elif command -v ufw &>/dev/null; then
    ufw allow 22/tcp || true
    ufw allow 443/tcp || true
    echo -e "${GREEN}✓${NC} Firewall configured (ufw)"
else
    echo -e "${YELLOW}⚠${NC} No firewall detected, skipping"
fi
echo ""

echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 12: System Optimization${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Network optimizations
cat >> /etc/sysctl.conf << 'EOF'
# AlphaGenesis Production Optimizations
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864
net.ipv4.tcp_congestion_control = bbr
EOF

sysctl -p >/dev/null 2>&1

echo -e "${GREEN}✓${NC} System optimizations applied"
echo ""

echo "======================================================================"
echo -e "${GREEN}  ✓ Alibaba Cloud Production Setup Complete!${NC}"
echo "======================================================================"
echo ""
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${RED}  CRITICAL: CONFIGURE PRODUCTION API CREDENTIALS${NC}"
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "1. Edit the production .env file:"
echo "   ${BLUE}nano $PROJECT_DIR/.env${NC}"
echo ""
echo "2. Replace these with PRODUCTION credentials:"
echo "   - WEEX_API_KEY"
echo "   - WEEX_API_SECRET"
echo "   - WEEX_API_PASSPHRASE"
echo ""
echo "3. Verify configuration:"
echo "   ${BLUE}cat $PROJECT_DIR/.env | grep WEEX_${NC}"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  START PRODUCTION SYSTEM${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "4. Start the trading system:"
echo "   ${BLUE}systemctl start sdm-trading.service${NC}"
echo ""
echo "5. Verify it's running:"
echo "   ${BLUE}systemctl status sdm-trading.service${NC}"
echo ""
echo "6. Monitor live logs:"
echo "   ${BLUE}journalctl -u sdm-trading.service -f${NC}"
echo ""
echo "7. Run health check:"
echo "   ${BLUE}bash $PROJECT_DIR/monitor_production.sh${NC}"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  PRODUCTION COMMANDS${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Start:     ${BLUE}systemctl start sdm-trading.service${NC}"
echo "  Stop:      ${BLUE}systemctl stop sdm-trading.service${NC}"
echo "  Restart:   ${BLUE}systemctl restart sdm-trading.service${NC}"
echo "  Status:    ${BLUE}systemctl status sdm-trading.service${NC}"
echo "  Logs:      ${BLUE}journalctl -u sdm-trading.service -f${NC}"
echo "  Monitor:   ${BLUE}bash $PROJECT_DIR/monitor_production.sh${NC}"
echo "  Backup:    ${BLUE}bash $PROJECT_DIR/backup_production.sh${NC}"
echo "  Account:   ${BLUE}python3 $PROJECT_DIR/scripts/check_weex_account.py${NC}"
echo ""
echo "======================================================================"
echo -e "${GREEN}Environment: PRODUCTION | Provider: Alibaba Cloud | Region: HK${NC}"
echo "======================================================================"
echo ""
