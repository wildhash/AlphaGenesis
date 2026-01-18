#!/bin/bash
#
# Collect Logs from Production System for Hackathon Submission
#
# This script fetches all logs from the GCP production instance
# and creates a comprehensive log archive for review.
#
# Usage: bash collect_logs.sh
#

set -e

# Configuration
GCP_IP="34.133.16.230"
GCP_USER="root"
PROJECT_DIR="/opt/AlphaGenesis"
LOCAL_LOG_DIR="./hackathon_logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}======================================================================"
echo "  Collecting Logs for Hackathon Submission"
echo "======================================================================${NC}"
echo ""
echo "Source: $GCP_USER@$GCP_IP:$PROJECT_DIR"
echo "Target: $LOCAL_LOG_DIR"
echo "Timestamp: $TIMESTAMP"
echo ""

# Create local log directory
mkdir -p "$LOCAL_LOG_DIR"
echo -e "${GREEN}✓ Created local log directory${NC}"

# Test connection
echo -e "${BLUE}Testing connection to GCP instance...${NC}"
if ! ssh -o ConnectTimeout=5 $GCP_USER@$GCP_IP 'echo "Connected"' 2>/dev/null; then
    echo -e "${YELLOW}✗ Cannot connect to $GCP_IP${NC}"
    echo ""
    echo "Please ensure:"
    echo "  1. You have SSH access to the GCP instance"
    echo "  2. Your SSH key is configured"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ Connection successful${NC}"
echo ""

# Collect file-based logs
echo -e "${BLUE}Collecting file-based logs...${NC}"
echo "----------------------------------------------------------------------"

ssh $GCP_USER@$GCP_IP "ls -lh $PROJECT_DIR/logs/ 2>/dev/null || echo 'No log files found'"

# Create logs directory and copy
rsync -avz --progress \
    "$GCP_USER@$GCP_IP:$PROJECT_DIR/logs/" \
    "$LOCAL_LOG_DIR/file_logs/" 2>/dev/null || echo "No file logs to copy"

echo -e "${GREEN}✓ File-based logs collected${NC}"
echo ""

# Collect systemd journal logs
echo -e "${BLUE}Collecting systemd journal logs...${NC}"
echo "----------------------------------------------------------------------"

# Full journal (last 10000 lines)
ssh $GCP_USER@$GCP_IP 'journalctl -u sdm-trading.service -n 10000 --no-pager' \
    > "$LOCAL_LOG_DIR/journal_full.log" 2>/dev/null || echo "No journal logs found"

# Today's journal only
ssh $GCP_USER@$GCP_IP 'journalctl -u sdm-trading.service --since today --no-pager' \
    > "$LOCAL_LOG_DIR/journal_today.log" 2>/dev/null || echo "No today's journal logs"

# Last 24 hours
ssh $GCP_USER@$GCP_IP 'journalctl -u sdm-trading.service --since "24 hours ago" --no-pager' \
    > "$LOCAL_LOG_DIR/journal_24h.log" 2>/dev/null || echo "No 24h journal logs"

echo -e "${GREEN}✓ Systemd journal logs collected${NC}"
echo ""

# Collect system status
echo -e "${BLUE}Collecting system status...${NC}"
echo "----------------------------------------------------------------------"

ssh $GCP_USER@$GCP_IP << 'ENDSSH' > "$LOCAL_LOG_DIR/system_status.txt" 2>&1
echo "==================================================================="
echo "System Status Report"
echo "Generated: $(date)"
echo "==================================================================="
echo ""

echo "--- Service Status ---"
systemctl status sdm-trading.service --no-pager || echo "Service not running"
echo ""

echo "--- Running Processes ---"
ps aux | grep -E "python.*sdm|python.*trading|python.*alpha" | grep -v grep || echo "No trading processes found"
echo ""

echo "--- Disk Usage ---"
df -h /opt/AlphaGenesis
echo ""

echo "--- Memory Usage ---"
free -h
echo ""

echo "--- Recent System Logs ---"
journalctl -n 100 --no-pager
echo ""
ENDSSH

echo -e "${GREEN}✓ System status collected${NC}"
echo ""

# Collect account state
echo -e "${BLUE}Collecting account state...${NC}"
echo "----------------------------------------------------------------------"

ssh $GCP_USER@$GCP_IP << ENDSSH > "$LOCAL_LOG_DIR/account_state.txt" 2>&1
cd $PROJECT_DIR
python3 check_weex_account.py 2>&1 || echo "Could not fetch account state"
ENDSSH

echo -e "${GREEN}✓ Account state collected${NC}"
echo ""

# Collect position history
echo -e "${BLUE}Collecting position data...${NC}"
echo "----------------------------------------------------------------------"

ssh $GCP_USER@$GCP_IP << ENDSSH > "$LOCAL_LOG_DIR/position_data.txt" 2>&1
cd $PROJECT_DIR
python3 analyze_positions.py 2>&1 || echo "Could not fetch position data"
ENDSSH

echo -e "${GREEN}✓ Position data collected${NC}"
echo ""

# Collect config files
echo -e "${BLUE}Collecting configuration...${NC}"
echo "----------------------------------------------------------------------"

mkdir -p "$LOCAL_LOG_DIR/config"

scp "$GCP_USER@$GCP_IP:$PROJECT_DIR/config/*.yaml" "$LOCAL_LOG_DIR/config/" 2>/dev/null || echo "No config files found"

# Collect .env (without secrets)
ssh $GCP_USER@$GCP_IP "grep -v -E '(API_KEY|API_SECRET|PASSPHRASE)' $PROJECT_DIR/.env 2>/dev/null" \
    > "$LOCAL_LOG_DIR/config/env_sanitized.txt" || echo "No .env file"

echo -e "${GREEN}✓ Configuration collected${NC}"
echo ""

# Create metadata file
echo -e "${BLUE}Creating metadata...${NC}"
echo "----------------------------------------------------------------------"

cat > "$LOCAL_LOG_DIR/METADATA.txt" << EOF
Log Collection Metadata
=======================

Collection Time: $(date)
Collection Timestamp: $TIMESTAMP
Source: $GCP_USER@$GCP_IP:$PROJECT_DIR

Directory Structure:
- file_logs/          : File-based logs from logs/ directory
- journal_full.log    : Full systemd journal (last 10000 lines)
- journal_today.log   : Today's systemd journal
- journal_24h.log     : Last 24 hours systemd journal
- system_status.txt   : System status and diagnostics
- account_state.txt   : WEEX account state
- position_data.txt   : Position analysis
- config/             : Configuration files (sanitized)
- METADATA.txt        : This file

Log Analysis Commands:
----------------------

# Search for risk gate decisions
grep -E "LEDGER|GROSS EXPOSURE|RISK VETO|ETHICS" journal_full.log

# Search for metrics
grep -E "unrealized_pnl|total_notional|margin_used|daily_pnl" journal_full.log

# Search for errors
grep -E "ERROR|CRITICAL|WARNING" journal_full.log

# Search for trades
grep -E "ORDER|POSITION|TRADE" journal_full.log

# Search for SL/TP
grep -E "stop_loss|take_profit" journal_full.log

# Daily reset events
grep "Day changed (UTC)" journal_full.log

EOF

echo -e "${GREEN}✓ Metadata created${NC}"
echo ""

# Create archive
echo -e "${BLUE}Creating archive...${NC}"
echo "----------------------------------------------------------------------"

ARCHIVE_NAME="hackathon_logs_${TIMESTAMP}.tar.gz"
tar -czf "$ARCHIVE_NAME" "$LOCAL_LOG_DIR"

echo -e "${GREEN}✓ Archive created: $ARCHIVE_NAME${NC}"
echo ""

# Summary
echo -e "${BLUE}======================================================================"
echo -e "${GREEN}  Log Collection Complete!${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""
echo "Logs collected to: $LOCAL_LOG_DIR"
echo "Archive created: $ARCHIVE_NAME"
echo ""
echo "Archive size: $(du -h "$ARCHIVE_NAME" | cut -f1)"
echo "Total files: $(find "$LOCAL_LOG_DIR" -type f | wc -l)"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Review logs: cd $LOCAL_LOG_DIR"
echo "  2. Analyze with: bash analyze_logs.sh"
echo "  3. Submit archive for hackathon review"
echo ""
echo -e "${BLUE}======================================================================${NC}"
