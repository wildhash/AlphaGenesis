#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 0 ] && [ "$#" -ne 3 ]; then
  echo "Usage: sudo bash scripts/swap_to_finals.sh [<WEEX_API_KEY> <WEEX_API_SECRET> <WEEX_API_PASSPHRASE>]" >&2
  exit 1
fi

WEEX_API_KEY="${1:-}"
WEEX_API_SECRET="${2:-}"
WEEX_API_PASSPHRASE="${3:-}"

ENV_PATH="/opt/AlphaGenesis/.env"
FINALS_ENV="/opt/AlphaGenesis/finals_config.env"
BACKUP="/opt/AlphaGenesis/.env.prelims.bak.$(date +%Y%m%d_%H%M%S)"

if [ ! -f "$FINALS_ENV" ]; then
  echo "Missing finals_config.env at $FINALS_ENV" >&2
  exit 1
fi

cp "$ENV_PATH" "$BACKUP"

python3 - <<PY
import re
from pathlib import Path

env_path = Path("$ENV_PATH")
finals_path = Path("$FINALS_ENV")

current = env_path.read_text().splitlines()
finals = finals_path.read_text().splitlines()

def parse(lines):
    out = {}
    for line in lines:
        m = re.match(r"^([A-Z0-9_]+)=(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out

current_map = parse(current)
finals_map = parse(finals)

# Preserve credentials if not provided
if "$WEEX_API_KEY" and "$WEEX_API_SECRET" and "$WEEX_API_PASSPHRASE":
    current_map["WEEX_API_KEY"] = "$WEEX_API_KEY"
    current_map["WEEX_API_SECRET"] = "$WEEX_API_SECRET"
    current_map["WEEX_API_PASSPHRASE"] = "$WEEX_API_PASSPHRASE"

# Apply all finals config values to current map
for k, v in finals_map.items():
    current_map[k] = v

lines = []
seen = set()
for line in current:
    m = re.match(r"^([A-Z0-9_]+)=(.*)$", line)
    if m and m.group(1) in current_map:
        key = m.group(1)
        lines.append(f"{key}={current_map[key]}")
        seen.add(key)
    else:
        lines.append(line)
for key, val in current_map.items():
    if key not in seen:
        lines.append(f"{key}={val}")

env_path.write_text("\n".join(lines) + "\n")
PY

systemctl restart sdm-trading.service
sleep 2
journalctl -u sdm-trading.service -n 200 -o cat --no-pager | tail -30

echo "Finals env swapped. Backup saved to: $BACKUP"
