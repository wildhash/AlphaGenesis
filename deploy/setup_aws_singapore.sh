#!/bin/bash
#
# AWS Singapore Production Setup Script
# AlphaGenesis Trading System
#
# Usage: sudo bash setup_aws_singapore.sh
#

set -e

echo "======================================================================"
echo "  AlphaGenesis - AWS Singapore Production Deployment"
echo "======================================================================"
echo ""
echo "Environment: PRODUCTION"
echo "Cloud Provider: Amazon Web Services (AWS)"
echo "Region: Singapore (ap-southeast-1)"
echo "Timestamp: $(date)"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
PROJECT_DIR="/opt/AlphaGenesis"
SERVICE_USER="alphagenesis"
PYTHON_VERSION="3.9"
ENVIRONMENT="production"
REGION="ap-southeast-1"

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 1: AWS Instance Verification${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo "Hostname: $(hostname)"
echo "IP Address (Private): $(hostname -I | awk '{print $1}')"
echo "OS: $(lsb_release -d | cut -f2)"
echo "Kernel: $(uname -r)"
echo "Architecture: $(uname -m)"
echo "Python: $(python3 --version 2>/dev/null || echo 'Not installed')"
echo ""

# Verify we're on AWS
if curl -s --connect-timeout 3 http://169.254.169.254/latest/meta-data/instance-id &>/dev/null; then
    INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
    INSTANCE_TYPE=$(curl -s http://169.254.169.254/latest/meta-data/instance-type)
    AVAILABILITY_ZONE=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

    echo -e "${GREEN}✓${NC} Verified: Running on AWS EC2"
    echo "  Instance ID: $INSTANCE_ID"
    echo "  Instance Type: $INSTANCE_TYPE"
    echo "  Availability Zone: $AVAILABILITY_ZONE"
    echo "  Public IP: $PUBLIC_IP"
else
    echo -e "${YELLOW}⚠${NC} Warning: Could not verify AWS metadata"
fi
echo ""

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 2: System Updates${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo "Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

echo "Installing system dependencies..."
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
    dnsutils \
    awscli

echo -e "${GREEN}✓${NC} System dependencies installed"
echo ""

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 3: Creating Service User${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -m -s /bin/bash $SERVICE_USER
    echo -e "${GREEN}✓${NC} User created: $SERVICE_USER"
else
    echo -e "${YELLOW}⚠${NC} User already exists: $SERVICE_USER"
fi
echo ""

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 4: Project Setup${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

mkdir -p $PROJECT_DIR
chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR
echo -e "${GREEN}✓${NC} Project directory ready: $PROJECT_DIR"
echo ""

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 5: Repository Clone${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ ! -d "$PROJECT_DIR/.git" ]; then
    echo "Cloning AlphaGenesis repository..."
    su - $SERVICE_USER -c "git clone https://github.com/wildhash/AlphaGenesis.git $PROJECT_DIR"
    su - $SERVICE_USER -c "cd $PROJECT_DIR && git checkout finals/alpha-genesis-clean"
    echo -e "${GREEN}✓${NC} Repository cloned (finals/alpha-genesis-clean branch)"
else
    echo "Repository exists, updating..."
    su - $SERVICE_USER -c "cd $PROJECT_DIR && git fetch origin && git checkout finals/alpha-genesis-clean && git pull"
    echo -e "${GREEN}✓${NC} Repository updated"
fi
echo ""

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 6: Python Environment Setup${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo "Upgrading pip and tools..."
python3 -m pip install --upgrade pip setuptools wheel

echo "Installing production dependencies..."
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
    statsmodels>=0.14.0 \
    boto3>=1.26.0

echo -e "${GREEN}✓${NC} Python dependencies installed (including AWS SDK)"
echo ""

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 7: Directory Structure${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

su - $SERVICE_USER -c "mkdir -p $PROJECT_DIR/{logs,reports/sdm,models/saved,data,backups}"
echo -e "${GREEN}✓${NC} Directory structure created"
echo ""

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 8: AWS Production Configuration${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ ! -f "$PROJECT_DIR/.env" ]; then
    cat > $PROJECT_DIR/.env << 'EOF'
# ═══════════════════════════════════════════════════════════════
#  AlphaGenesis Trading System - AWS SINGAPORE PRODUCTION
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
DEPLOYMENT_ENV=aws-singapore-production
REGION=ap-southeast-1
CLOUD_PROVIDER=aws
ENVIRONMENT=production
INSTANCE_NAME=alphagenesis-prod-aws-sg

# AWS Integration
AWS_REGION=ap-southeast-1
ENABLE_CLOUDWATCH=true
CLOUDWATCH_NAMESPACE=AlphaGenesis/Production

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

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 9: Systemd Service (AWS Optimized)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cat > /etc/systemd/system/sdm-trading.service << EOF
[Unit]
Description=AlphaGenesis SDM Trading System - PRODUCTION (AWS Singapore)
After=network-online.target cloud-init.service
Wants=network-online.target
Documentation=https://github.com/wildhash/AlphaGenesis

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="DEPLOYMENT_ENV=aws-singapore-production"
Environment="REGION=$REGION"
Environment="AWS_DEFAULT_REGION=$REGION"

# Start command
ExecStart=/usr/bin/python3 scripts/start_sdm_trading.py

# Pre-start validation
ExecStartPre=/bin/sh -c 'test -f $PROJECT_DIR/.env || (echo "ERROR: .env file missing" && exit 1)'

# Restart policy - AWS production
Restart=always
RestartSec=20
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
SyslogIdentifier=alphagenesis-aws-prod

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$PROJECT_DIR /tmp

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable sdm-trading.service

echo -e "${GREEN}✓${NC} AWS-optimized systemd service configured"
echo ""

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 10: Management Scripts${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# AWS production monitor
cat > $PROJECT_DIR/monitor_aws_production.sh << 'EOF'
#!/bin/bash
echo "═══════════════════════════════════════════════════════════════"
echo "  AlphaGenesis PRODUCTION - AWS Singapore Monitor"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""

# AWS Instance Info
if command -v curl &>/dev/null; then
    INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null || echo "N/A")
    INSTANCE_TYPE=$(curl -s http://169.254.169.254/latest/meta-data/instance-type 2>/dev/null || echo "N/A")
    AZ=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone 2>/dev/null || echo "N/A")

    echo "AWS Instance: $INSTANCE_ID ($INSTANCE_TYPE) in $AZ"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SERVICE STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
systemctl status sdm-trading.service --no-pager | head -15
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "RECENT ACTIVITY (Last 25 lines)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
journalctl -u sdm-trading.service -n 25 --no-pager
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SYSTEM RESOURCES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CPU Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "Memory: $(free -h | grep Mem | awk '{print $3 " / " $2 " (" int($3/$2*100) "%)"}')"
echo "Disk: $(df -h / | tail -1 | awk '{print $3 " / " $2 " (" $5 " used)"}')"
echo "Network Connections: $(ss -s | grep TCP | head -1)"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "RECENT ERRORS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
journalctl -u sdm-trading.service --since "10 minutes ago" | grep -i "error\|exception\|failed" | tail -10 || echo "✓ No recent errors"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TRADING SIGNALS (Last hour)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
journalctl -u sdm-trading.service --since "1 hour ago" | grep "DIAG_SIGNAL_GENERATED" | wc -l | awk '{print "Signals generated: " $1}'
echo ""

echo "═══════════════════════════════════════════════════════════════"
EOF

chmod +x $PROJECT_DIR/monitor_aws_production.sh
chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR/monitor_aws_production.sh

# CloudWatch integration script
cat > $PROJECT_DIR/send_metrics_to_cloudwatch.sh << 'EOF'
#!/bin/bash
# Send custom metrics to AWS CloudWatch

NAMESPACE="AlphaGenesis/Production"
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null || echo "unknown")

# Service uptime
if systemctl is-active --quiet sdm-trading.service; then
    aws cloudwatch put-metric-data \
        --namespace "$NAMESPACE" \
        --metric-name ServiceStatus \
        --value 1 \
        --dimensions InstanceId=$INSTANCE_ID \
        --region ap-southeast-1 2>/dev/null || true
else
    aws cloudwatch put-metric-data \
        --namespace "$NAMESPACE" \
        --metric-name ServiceStatus \
        --value 0 \
        --dimensions InstanceId=$INSTANCE_ID \
        --region ap-southeast-1 2>/dev/null || true
fi

# Trading signals count
SIGNALS=$(journalctl -u sdm-trading.service --since "5 minutes ago" | grep "DIAG_SIGNAL_GENERATED" | wc -l)
aws cloudwatch put-metric-data \
    --namespace "$NAMESPACE" \
    --metric-name TradingSignals \
    --value $SIGNALS \
    --dimensions InstanceId=$INSTANCE_ID \
    --region ap-southeast-1 2>/dev/null || true
EOF

chmod +x $PROJECT_DIR/send_metrics_to_cloudwatch.sh
chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR/send_metrics_to_cloudwatch.sh

# Backup script with S3 integration
cat > $PROJECT_DIR/backup_to_s3.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/AlphaGenesis/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/aws_production_backup_$TIMESTAMP.tar.gz"
S3_BUCKET="alphagenesis-backups"  # Change to your bucket name

mkdir -p $BACKUP_DIR

echo "Creating production backup: $BACKUP_FILE"
tar -czf $BACKUP_FILE \
    /opt/AlphaGenesis/.env \
    /opt/AlphaGenesis/logs \
    /opt/AlphaGenesis/reports \
    /tmp/bandit_state.json \
    /tmp/position_ledger.json \
    /tmp/trading_journal.db 2>/dev/null

# Upload to S3 if configured
if command -v aws &>/dev/null && aws s3 ls s3://$S3_BUCKET 2>/dev/null; then
    echo "Uploading to S3..."
    aws s3 cp $BACKUP_FILE s3://$S3_BUCKET/backups/ || echo "S3 upload failed"
fi

# Keep only last 7 days of local backups
find $BACKUP_DIR -name "aws_production_backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
ls -lh $BACKUP_FILE
EOF

chmod +x $PROJECT_DIR/backup_to_s3.sh
chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR/backup_to_s3.sh

# Add cron jobs
(crontab -u $SERVICE_USER -l 2>/dev/null; echo "0 */6 * * * $PROJECT_DIR/backup_to_s3.sh") | crontab -u $SERVICE_USER -
(crontab -u $SERVICE_USER -l 2>/dev/null; echo "*/5 * * * * $PROJECT_DIR/send_metrics_to_cloudwatch.sh") | crontab -u $SERVICE_USER -

echo -e "${GREEN}✓${NC} AWS management scripts created"
echo "  - monitor_aws_production.sh"
echo "  - send_metrics_to_cloudwatch.sh (runs every 5 min)"
echo "  - backup_to_s3.sh (runs every 6 hours)"
echo ""

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 11: CloudWatch Logs Integration${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Install CloudWatch agent (optional)
echo "Installing AWS CloudWatch agent..."
wget -q https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb || {
    echo -e "${YELLOW}⚠${NC} CloudWatch agent download failed, skipping"
}

if [ -f amazon-cloudwatch-agent.deb ]; then
    dpkg -i -E amazon-cloudwatch-agent.deb
    rm amazon-cloudwatch-agent.deb
    echo -e "${GREEN}✓${NC} CloudWatch agent installed"
else
    echo -e "${YELLOW}⚠${NC} CloudWatch agent not installed"
fi
echo ""

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 12: Security Group Verification${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Configure local firewall
ufw allow 22/tcp || true
ufw allow 443/tcp || true
echo -e "${GREEN}✓${NC} Local firewall configured"
echo -e "${YELLOW}⚠${NC} Ensure AWS Security Group allows inbound SSH (22) and HTTPS (443)"
echo ""

echo "======================================================================"
echo -e "${GREEN}  ✓ AWS Singapore Production Setup Complete!${NC}"
echo "======================================================================"
echo ""
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${RED}  CRITICAL: CONFIGURE PRODUCTION CREDENTIALS${NC}"
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "1. Edit production environment:"
echo "   ${BLUE}sudo nano $PROJECT_DIR/.env${NC}"
echo ""
echo "2. Set PRODUCTION WEEX credentials:"
echo "   - WEEX_API_KEY"
echo "   - WEEX_API_SECRET"
echo "   - WEEX_API_PASSPHRASE"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  START PRODUCTION SYSTEM${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "3. Start trading system:"
echo "   ${BLUE}sudo systemctl start sdm-trading.service${NC}"
echo ""
echo "4. Verify status:"
echo "   ${BLUE}sudo systemctl status sdm-trading.service${NC}"
echo ""
echo "5. Monitor logs:"
echo "   ${BLUE}sudo journalctl -u sdm-trading.service -f${NC}"
echo ""
echo "6. Run health check:"
echo "   ${BLUE}bash $PROJECT_DIR/monitor_aws_production.sh${NC}"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  AWS PRODUCTION COMMANDS${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Start:       ${BLUE}systemctl start sdm-trading.service${NC}"
echo "  Stop:        ${BLUE}systemctl stop sdm-trading.service${NC}"
echo "  Restart:     ${BLUE}systemctl restart sdm-trading.service${NC}"
echo "  Status:      ${BLUE}systemctl status sdm-trading.service${NC}"
echo "  Logs:        ${BLUE}journalctl -u sdm-trading.service -f${NC}"
echo "  Monitor:     ${BLUE}bash $PROJECT_DIR/monitor_aws_production.sh${NC}"
echo "  Backup:      ${BLUE}bash $PROJECT_DIR/backup_to_s3.sh${NC}"
echo "  CloudWatch:  ${BLUE}bash $PROJECT_DIR/send_metrics_to_cloudwatch.sh${NC}"
echo "  Account:     ${BLUE}python3 $PROJECT_DIR/scripts/check_weex_account.py${NC}"
echo ""
echo "======================================================================"
echo -e "${GREEN}Provider: AWS | Region: Singapore (ap-southeast-1) | Environment: PRODUCTION${NC}"
echo "======================================================================"
echo ""
