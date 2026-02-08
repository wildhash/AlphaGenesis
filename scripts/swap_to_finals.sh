#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "Usage: sudo bash scripts/swap_to_finals.sh <WEEX_API_KEY> <WEEX_API_SECRET> <WEEX_API_PASSPHRASE>" >&2
  exit 1
fi

WEEX_API_KEY="$1"
WEEX_API_SECRET="$2"
WEEX_API_PASSPHRASE="$3"

ENV_PATH="/opt/AlphaGenesis/.env"
FINALS_ENV="/opt/AlphaGenesis/finals_config.env"
BACKUP="/opt/AlphaGenesis/.env.prelims.bak.$(date +%Y%m%d_%H%M%S)"

if [ ! -f "$FINALS_ENV" ]; then
  echo "Missing finals_config.env at $FINALS_ENV" >&2
  exit 1
fi

cp "$ENV_PATH" "$BACKUP"
cp "$FINALS_ENV" "$ENV_PATH"

python3 - <<PY
import re
path = "$ENV_PATH"
updates = {
    "WEEX_API_KEY": "$WEEX_API_KEY",
    "WEEX_API_SECRET": "$WEEX_API_SECRET",
    "WEEX_API_PASSPHRASE": "$WEEX_API_PASSPHRASE",
}
lines = open(path).read().splitlines()
out = []
seen = set()
for line in lines:
    m = re.match(r"^([A-Z0-9_]+)=(.*)$", line)
    if m and m.group(1) in updates:
        key = m.group(1)
        out.append(f"{key}={updates[key]}")
        seen.add(key)
    else:
        out.append(line)
for key, val in updates.items():
    if key not in seen:
        out.append(f"{key}={val}")
open(path, "w").write("\n".join(out) + "\n")
PY

systemctl restart sdm-trading.service
sleep 2
journalctl -u sdm-trading.service -n 200 -o cat --no-pager | tail -30

echo "Finals env swapped. Backup saved to: $BACKUP"
