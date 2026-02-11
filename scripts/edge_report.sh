#!/usr/bin/env bash
set -euo pipefail
HOURS="${1:-4}"
python3 /opt/AlphaGenesis/scripts/edge_report.py --hours "$HOURS"
