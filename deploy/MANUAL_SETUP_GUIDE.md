# Manual Setup Guide for GCP Instance (34.133.16.230)

This guide provides step-by-step instructions for manually setting up the SDM Trading System on your GCP instance.

---

## Prerequisites

- SSH access to 34.133.16.230
- Root or sudo privileges
- WEEX API credentials (from hackathon)

---

## Option 1: Automated Deployment (Recommended)

### Step 1: Configure Local Environment

```bash
cd /home/user/AlphaGenesis

# Edit .env with your WEEX API credentials
nano .env
```

Add your actual credentials:
```env
WEEX_API_KEY=your_actual_key_from_hackathon
WEEX_API_SECRET=your_actual_secret
WEEX_API_PASSPHRASE=your_actual_passphrase
```

### Step 2: Run Automated Deployment

```bash
# Make scripts executable
chmod +x deploy/deploy_and_setup.sh
chmod +x deploy/setup_gcp_instance.sh

# Run deployment
bash deploy/deploy_and_setup.sh
```

This will automatically:
- Copy all files to GCP
- Install dependencies
- Configure systemd service
- Start the trading system

### Step 3: Monitor

```bash
# View live logs
ssh root@34.133.16.230 'journalctl -u sdm-trading.service -f'
```

---

## Option 2: Manual Setup (Step-by-Step)

If automated deployment doesn't work, follow these manual steps:

### Step 1: Connect to GCP

```bash
ssh root@34.133.16.230
```

### Step 2: Install System Dependencies

```bash
# Update system
apt-get update && apt-get upgrade -y

# Install required packages
apt-get install -y \
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
```

### Step 3: Create Service User

```bash
# Create user for running the service
useradd -m -s /bin/bash alphagenesis
```

### Step 4: Create Project Directory

```bash
# Create directory
mkdir -p /opt/AlphaGenesis
chown -R alphagenesis:alphagenesis /opt/AlphaGenesis
```

### Step 5: Clone Repository

```bash
# Switch to service user
su - alphagenesis

# Clone repository
cd /opt
git clone https://github.com/wildhash/AlphaGenesis.git
cd AlphaGenesis

# Checkout the SDM branch
git checkout claude/weex-trading-system-JjDSY
```

### Step 6: Install Poetry

```bash
# Install Poetry (as alphagenesis user)
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH
echo 'export PATH="/home/alphagenesis/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Step 7: Install Python Dependencies

```bash
# Install dependencies
cd /opt/AlphaGenesis
poetry install --no-dev

# Or if Poetry fails, use pip
pip3 install numpy pandas loguru python-dotenv requests scikit-learn
```

### Step 8: Create Required Directories

```bash
# Create directories
mkdir -p /opt/AlphaGenesis/logs
mkdir -p /opt/AlphaGenesis/reports/sdm
mkdir -p /opt/AlphaGenesis/models/saved
```

### Step 9: Configure Environment

```bash
# Create .env file
cd /opt/AlphaGenesis
nano .env
```

Add your configuration:
```env
# WEEX API Configuration
WEEX_API_KEY=your_actual_api_key
WEEX_API_SECRET=your_actual_api_secret
WEEX_API_PASSPHRASE=your_actual_api_passphrase
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
```

Save and exit (Ctrl+X, Y, Enter)

### Step 10: Create Systemd Service

Exit from alphagenesis user back to root:
```bash
exit  # Back to root
```

Create service file:
```bash
nano /etc/systemd/system/sdm-trading.service
```

Add this content:
```ini
[Unit]
Description=SDM Trading System for WEEX AI Wars
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=alphagenesis
WorkingDirectory=/opt/AlphaGenesis
Environment="PATH=/home/alphagenesis/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/alphagenesis/.local/bin/poetry run python scripts/start_sdm_trading.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

# Resource limits
LimitNOFILE=65536
MemoryLimit=2G

[Install]
WantedBy=multi-user.target
```

Save and exit.

### Step 11: Enable and Start Service

```bash
# Reload systemd
systemctl daemon-reload

# Enable service (start on boot)
systemctl enable sdm-trading.service

# Start service
systemctl start sdm-trading.service

# Check status
systemctl status sdm-trading.service
```

### Step 12: Verify It's Running

```bash
# View logs
journalctl -u sdm-trading.service -f

# You should see:
# - "SDM TRADING ENGINE INITIALIZED"
# - "STARTING SDM TRADING ENGINE"
# - Market monitoring messages
```

---

## Monitoring Commands

### Check Service Status
```bash
systemctl status sdm-trading.service
```

### View Live Logs
```bash
journalctl -u sdm-trading.service -f
```

### View Last 100 Log Lines
```bash
journalctl -u sdm-trading.service -n 100 --no-pager
```

### Check if Trading
```bash
# Look for "EXECUTING ACTION" in logs
journalctl -u sdm-trading.service | grep "EXECUTING ACTION"
```

### View Performance Reports
```bash
ls -lh /opt/AlphaGenesis/reports/sdm/
cat /opt/AlphaGenesis/reports/sdm/learning_*.json | jq '.strategy_performance'
```

### Monitor System Resources
```bash
# CPU and memory
htop

# Or simpler
top

# Disk usage
df -h

# Network
netstat -tuln
```

---

## Control Commands

### Start Service
```bash
systemctl start sdm-trading.service
```

### Stop Service
```bash
systemctl stop sdm-trading.service
```

### Restart Service
```bash
systemctl restart sdm-trading.service
```

### Disable Service (won't start on boot)
```bash
systemctl disable sdm-trading.service
```

### Re-enable Service
```bash
systemctl enable sdm-trading.service
```

---

## Troubleshooting

### Service Won't Start

Check logs for errors:
```bash
journalctl -u sdm-trading.service -n 50
```

Common issues:
1. **Missing dependencies**: Run `pip3 install numpy pandas loguru python-dotenv requests scikit-learn`
2. **Wrong Python path**: Check ExecStart path in service file
3. **Permission issues**: Ensure alphagenesis user owns /opt/AlphaGenesis

### API Connection Errors

Check .env file:
```bash
cat /opt/AlphaGenesis/.env | grep WEEX_
```

Test API connection:
```bash
su - alphagenesis
cd /opt/AlphaGenesis
python3 << EOF
from alphagenesis.data import WEEXClient
import os
from dotenv import load_dotenv
load_dotenv()

client = WEEXClient(
    api_key=os.getenv('WEEX_API_KEY'),
    api_secret=os.getenv('WEEX_API_SECRET'),
    api_passphrase=os.getenv('WEEX_API_PASSPHRASE')
)

# Test connection
print("Testing connection...")
ticker = client.get_ticker('cmt_btcusdt')
print("Success! BTC Price:", ticker)
EOF
```

### High Memory Usage

Reduce update interval in .env:
```env
UPDATE_INTERVAL=600  # 10 minutes instead of 5
```

Then restart:
```bash
systemctl restart sdm-trading.service
```

### No Trades Happening

This is normal! The SDM is disciplined:
- Only trades high-confidence opportunities
- Expected 1-3 trades/day
- Check logs for "Resolving Intent" messages

If you see constraint violations, the system is working correctly (protecting capital).

---

## Quick Health Check Script

Create a monitoring script:

```bash
nano /opt/AlphaGenesis/health_check.sh
```

Add:
```bash
#!/bin/bash

echo "======================================================================"
echo "  SDM Trading System - Health Check"
echo "======================================================================"
echo ""

# Service status
echo "Service Status:"
systemctl is-active sdm-trading.service && echo "✓ Running" || echo "✗ Stopped"
echo ""

# Recent logs
echo "Recent Activity (last 5 lines):"
journalctl -u sdm-trading.service -n 5 --no-pager
echo ""

# System resources
echo "System Resources:"
echo "  Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
echo "  Disk: $(df -h / | tail -1 | awk '{print $3 "/" $2}')"
echo ""

# Reports
if [ -d "/opt/AlphaGenesis/reports/sdm" ]; then
    echo "Recent Reports:"
    ls -lt /opt/AlphaGenesis/reports/sdm/ | head -3
fi

echo ""
echo "======================================================================"
```

Make executable and run:
```bash
chmod +x /opt/AlphaGenesis/health_check.sh
bash /opt/AlphaGenesis/health_check.sh
```

---

## Security Recommendations

### 1. Configure Firewall

```bash
# Install ufw if not present
apt-get install -y ufw

# Allow SSH
ufw allow 22/tcp

# Enable firewall
ufw enable
```

### 2. Secure .env File

```bash
chmod 600 /opt/AlphaGenesis/.env
chown alphagenesis:alphagenesis /opt/AlphaGenesis/.env
```

### 3. Set Up Log Rotation

```bash
nano /etc/logrotate.d/sdm-trading
```

Add:
```
/opt/AlphaGenesis/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 alphagenesis alphagenesis
}
```

---

## Emergency Procedures

### Emergency Stop
```bash
systemctl stop sdm-trading.service
```

### Force Kill If Unresponsive
```bash
pkill -9 -f "start_sdm_trading"
```

### Backup Configuration Before Changes
```bash
cp /opt/AlphaGenesis/.env /opt/AlphaGenesis/.env.backup.$(date +%Y%m%d)
```

### Roll Back to Previous Version
```bash
cd /opt/AlphaGenesis
git fetch origin
git checkout <previous_commit_hash>
systemctl restart sdm-trading.service
```

---

## Post-Deployment Checklist

After setup, verify:

- [ ] Service is running: `systemctl status sdm-trading.service`
- [ ] Logs show initialization: `journalctl -u sdm-trading.service -n 20`
- [ ] No critical errors in logs
- [ ] .env has correct API credentials
- [ ] System can connect to WEEX API
- [ ] Directories created: logs/, reports/sdm/, models/saved/
- [ ] Service enabled for autostart: `systemctl is-enabled sdm-trading.service`

---

## Support

If you encounter issues:

1. Check logs: `journalctl -u sdm-trading.service -n 100`
2. Verify .env configuration
3. Test API connectivity
4. Check system resources (memory, disk)
5. Review error messages

---

## Competition Day Checklist

Before competition starts (Jan 12, 8 PM UTC+8):

- [ ] System deployed and running
- [ ] API credentials verified
- [ ] Monitoring working
- [ ] No errors in logs
- [ ] Joined Telegram group
- [ ] BUIDL group confirmed

During competition:

- [ ] Check daily: `bash /opt/AlphaGenesis/health_check.sh`
- [ ] Monitor account balance
- [ ] Review learning metrics weekly
- [ ] Let SDM adapt and learn (don't intervene unless critical)

---

**Good luck with the competition!** 🚀
