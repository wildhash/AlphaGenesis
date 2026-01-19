#!/bin/bash
#
# USER: Run this from YOUR LOCAL MACHINE (not from container)
#
# This checks production status and gives you info to share with Codex
#

echo "======================================================================"
echo "  AlphaGenesis Production Status Check"
echo "  Run this from YOUR machine (not in container)"
echo "======================================================================"
echo ""

# Production details
PROD_HOST="root@34.133.16.230"
PROD_DIR="/opt/AlphaGenesis"

echo "Checking production at $PROD_HOST:$PROD_DIR"
echo ""

# Check 1: What version is deployed?
echo "[1/5] Production version:"
echo "----------------------------------------------------------------------"
ssh $PROD_HOST "cd $PROD_DIR && git log -1 --oneline"
PROD_COMMIT=$(ssh $PROD_HOST "cd $PROD_DIR && git rev-parse HEAD")
echo ""

# Check 2: What's the latest local version?
echo "[2/5] Latest local version:"
echo "----------------------------------------------------------------------"
git log -1 --oneline
LOCAL_COMMIT=$(git rev-parse HEAD)
echo ""

# Check 3: Are they in sync?
echo "[3/5] Version sync:"
echo "----------------------------------------------------------------------"
if [ "$PROD_COMMIT" = "$LOCAL_COMMIT" ]; then
    echo "✓ Production is UP TO DATE"
else
    echo "✗ Production is OUT OF SYNC"
    echo ""
    echo "Production commit: $PROD_COMMIT"
    echo "Local commit:      $LOCAL_COMMIT"
    echo ""
    echo "To update production, run:"
    echo "  ssh $PROD_HOST"
    echo "  cd $PROD_DIR"
    echo "  systemctl stop sdm-trading.service"
    echo "  git pull origin $(git branch --show-current)"
    echo "  systemctl start sdm-trading.service"
fi
echo ""

# Check 4: Is service running?
echo "[4/5] Service status:"
echo "----------------------------------------------------------------------"
ssh $PROD_HOST "systemctl is-active sdm-trading.service"
echo ""

# Check 5: Recent activity
echo "[5/5] Recent logs (last 10 lines):"
echo "----------------------------------------------------------------------"
ssh $PROD_HOST "journalctl -u sdm-trading.service -n 10 --no-pager"
echo ""

# Summary
echo "======================================================================"
echo "  Summary"
echo "======================================================================"
echo ""
echo "Production commit: $PROD_COMMIT"
echo "Local commit:      $LOCAL_COMMIT"
echo ""

if [ "$PROD_COMMIT" = "$LOCAL_COMMIT" ]; then
    echo "Status: ✓ Production is up to date"
else
    echo "Status: ✗ Production needs update"
fi
echo ""

# What to share with Codex
echo "======================================================================"
echo "  Share this with Codex:"
echo "======================================================================"
echo ""
echo "Production version: $(ssh $PROD_HOST \"cd $PROD_DIR && git log -1 --oneline\")"
echo "Local version: $(git log -1 --oneline)"
echo "Service status: $(ssh $PROD_HOST \"systemctl is-active sdm-trading.service\")"
echo ""
echo "Also share: SHARE_WITH_CODEX.md"
echo ""
