#!/usr/bin/env bash
set -euo pipefail

FLAG="/tmp/clear_straddles.flag"

echo "Creating clear-straddles flag at $FLAG"
touch "$FLAG"

echo "Restarting service to clear in-memory straddle state..."
systemctl restart sdm-trading.service
sleep 2

journalctl -u sdm-trading.service -n 200 -o cat --no-pager | tail -30

echo "Note: Straddle state is stored in-memory. If live positions exist, the system may re-adopt them."
