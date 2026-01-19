#!/bin/bash
#
# Production Status Check - Verify what version is running
#
# This script checks the production system to ensure it's running
# the latest code and trading correctly.
#

set -e

GCP_IP="34.133.16.230"
GCP_USER="root"
PROJECT_DIR="/opt/AlphaGenesis"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================================================"
echo "  AlphaGenesis Production Status Check"
echo "======================================================================${NC}"
echo ""
echo "Checking: $GCP_USER@$GCP_IP:$PROJECT_DIR"
echo "Time: $(date)"
echo ""

# Test connection
echo -e "${BLUE}[1/7] Testing connection...${NC}"
if ! ssh -o ConnectTimeout=5 $GCP_USER@$GCP_IP 'echo "Connected"' 2>/dev/null; then
    echo -e "${RED}✗ Cannot connect to production${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Connected${NC}"
echo ""

# Check git version
echo -e "${BLUE}[2/7] Checking deployed version...${NC}"
PROD_COMMIT=$(ssh $GCP_USER@$GCP_IP "cd $PROJECT_DIR && git rev-parse HEAD" 2>/dev/null)
PROD_BRANCH=$(ssh $GCP_USER@$GCP_IP "cd $PROJECT_DIR && git branch --show-current" 2>/dev/null)
PROD_COMMIT_MSG=$(ssh $GCP_USER@$GCP_IP "cd $PROJECT_DIR && git log -1 --oneline" 2>/dev/null)

echo "Branch: $PROD_BRANCH"
echo "Commit: $PROD_COMMIT_MSG"
echo ""

# Check local version
LOCAL_COMMIT=$(git rev-parse HEAD)
LOCAL_BRANCH=$(git branch --show-current)
LOCAL_COMMIT_MSG=$(git log -1 --oneline)

echo "Local branch: $LOCAL_BRANCH"
echo "Local commit: $LOCAL_COMMIT_MSG"
echo ""

if [ "$PROD_COMMIT" = "$LOCAL_COMMIT" ]; then
    echo -e "${GREEN}✓ Production is up to date with local${NC}"
else
    echo -e "${YELLOW}⚠ Production is OUT OF SYNC${NC}"
    echo ""
    echo "Commits on local that are NOT on production:"
    ssh $GCP_USER@$GCP_IP "cd $PROJECT_DIR && git fetch origin $LOCAL_BRANCH:$LOCAL_BRANCH 2>/dev/null || true"
    ssh $GCP_USER@$GCP_IP "cd $PROJECT_DIR && git log --oneline $PROD_COMMIT..$LOCAL_COMMIT" 2>/dev/null || echo "Unable to compare"
fi
echo ""

# Check service status
echo -e "${BLUE}[3/7] Checking service status...${NC}"
SERVICE_STATUS=$(ssh $GCP_USER@$GCP_IP "systemctl is-active sdm-trading.service 2>/dev/null" || echo "unknown")

if [ "$SERVICE_STATUS" = "active" ]; then
    echo -e "${GREEN}✓ Service is running${NC}"

    # Get uptime
    UPTIME=$(ssh $GCP_USER@$GCP_IP "systemctl show sdm-trading.service --property=ActiveEnterTimestamp --value 2>/dev/null" || echo "unknown")
    echo "Started: $UPTIME"
else
    echo -e "${RED}✗ Service is NOT running (status: $SERVICE_STATUS)${NC}"
fi
echo ""

# Check recent logs
echo -e "${BLUE}[4/7] Checking recent activity...${NC}"
LAST_LOG_LINE=$(ssh $GCP_USER@$GCP_IP "journalctl -u sdm-trading.service -n 1 --no-pager 2>/dev/null" || echo "No logs")
echo "Last log entry:"
echo "$LAST_LOG_LINE" | tail -1
echo ""

# Check for errors in last 100 lines
ERROR_COUNT=$(ssh $GCP_USER@$GCP_IP "journalctl -u sdm-trading.service -n 100 --no-pager 2>/dev/null | grep -c -E 'ERROR|CRITICAL'" || echo "0")
echo "Errors in last 100 log lines: $ERROR_COUNT"

if [ "$ERROR_COUNT" -gt 10 ]; then
    echo -e "${RED}⚠ High error count - review required${NC}"
elif [ "$ERROR_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Some errors present${NC}"
else
    echo -e "${GREEN}✓ No errors${NC}"
fi
echo ""

# Check account status
echo -e "${BLUE}[5/7] Checking WEEX account...${NC}"
ssh $GCP_USER@$GCP_IP "cd $PROJECT_DIR && timeout 10 python3 check_weex_account.py 2>&1" || echo "Could not fetch account"
echo ""

# Check if critical fixes are present
echo -e "${BLUE}[6/7] Verifying critical fixes in deployed code...${NC}"

# Check for P&L fallback
if ssh $GCP_USER@$GCP_IP "grep -q 'unrealized_pnl.*unrealised_pnl' $PROJECT_DIR/alphagenesis/sdm/sdm_engine.py 2>/dev/null"; then
    echo -e "${GREEN}✓ Fix #1: P&L fallback present${NC}"
else
    echo -e "${RED}✗ Fix #1: P&L fallback MISSING${NC}"
fi

# Check for SL/TP conversion
if ssh $GCP_USER@$GCP_IP "grep -q 'stop_loss_pct.*take_profit_pct' $PROJECT_DIR/alphagenesis/sdm/sdm_engine.py 2>/dev/null"; then
    echo -e "${GREEN}✓ Fix #4: SL/TP conversion present${NC}"
else
    echo -e "${RED}✗ Fix #4: SL/TP conversion MISSING${NC}"
fi

# Check for gross exposure cap
if ssh $GCP_USER@$GCP_IP "grep -q 'MAX_GROSS_EXPOSURE_PCT.*0.30' $PROJECT_DIR/alphagenesis/sdm/sdm_engine.py 2>/dev/null"; then
    echo -e "${GREEN}✓ Risk: 30% gross exposure cap present${NC}"
else
    echo -e "${RED}✗ Risk: 30% gross exposure cap MISSING${NC}"
fi

# Check for UTC timezone
if ssh $GCP_USER@$GCP_IP "grep -q 'timezone.utc' $PROJECT_DIR/alphagenesis/sdm/sdm_engine.py 2>/dev/null"; then
    echo -e "${GREEN}✓ Fix #6: UTC timezone present${NC}"
else
    echo -e "${RED}✗ Fix #6: UTC timezone MISSING${NC}"
fi

echo ""

# Check continuous learning status
echo -e "${BLUE}[7/7] Checking continuous learning...${NC}"

# Check for bandit state file
if ssh $GCP_USER@$GCP_IP "test -f $PROJECT_DIR/bandit_state.json 2>/dev/null"; then
    echo -e "${GREEN}✓ Bandit state file exists${NC}"

    # Get state info
    STATE_SIZE=$(ssh $GCP_USER@$GCP_IP "stat -f%z $PROJECT_DIR/bandit_state.json 2>/dev/null || stat -c%s $PROJECT_DIR/bandit_state.json 2>/dev/null")
    echo "State file size: $STATE_SIZE bytes"

    # Count strategies being tracked
    STRATEGY_COUNT=$(ssh $GCP_USER@$GCP_IP "cat $PROJECT_DIR/bandit_state.json 2>/dev/null | grep -c 'total_reward' || echo '0'")
    echo "Strategies tracked: $STRATEGY_COUNT"
else
    echo -e "${YELLOW}⚠ No bandit state file (fresh start)${NC}"
fi

echo ""

# Summary
echo -e "${BLUE}======================================================================"
echo "  Summary"
echo "======================================================================${NC}"
echo ""

if [ "$SERVICE_STATUS" = "active" ] && [ "$ERROR_COUNT" -lt 10 ]; then
    echo -e "${GREEN}✓ System is operational${NC}"
else
    echo -e "${YELLOW}⚠ System needs attention${NC}"
fi

if [ "$PROD_COMMIT" != "$LOCAL_COMMIT" ]; then
    echo -e "${YELLOW}⚠ Production needs update${NC}"
    echo ""
    echo "To update production:"
    echo "  ssh $GCP_USER@$GCP_IP"
    echo "  cd $PROJECT_DIR"
    echo "  git pull origin $LOCAL_BRANCH"
    echo "  systemctl restart sdm-trading.service"
fi

echo ""
echo -e "${BLUE}======================================================================${NC}"
