# WEEX AI Log Pipeline

This system uploads AI decision logs to WEEX AI Wars using:

- `POST /capi/v2/order/uploadAiLog`
- Required fields: `stage`, `model`, `input`, `output`, `explanation`
- Optional: `orderId`
- Success response: `{"code":"00000","data":"upload success"}`

## Storage

Logs are queued in SQLite for persistence:

- Default path: `/opt/AlphaGenesis/tmp/ai_logs.sqlite`
- Configurable via `AI_LOG_DB_PATH`

## How It Works

1. AI events are emitted to the local queue (non-blocking).
2. A background worker uploads events with retry and backoff.
3. Failures never block trading execution.

## Verification

Check queue size:

```bash
python3 - <<'PY'
from alphagenesis.omni.ai_logs import AILogStore
store = AILogStore('/opt/AlphaGenesis/tmp/ai_logs.sqlite')
print(store.pending_count())
PY
```

Run smoke upload (no orders):

```bash
python3 /opt/AlphaGenesis/scripts/weex_ai_log_smoke.py
```

See recent service logs:

```bash
sudo journalctl -u sdm-trading.service -n 120 --no-pager | grep -E "AI log"
```

## Curl Example (for reference only)

```bash
curl -X POST https://api-contract.weex.com/capi/v2/order/uploadAiLog \
  -H "ACCESS-KEY: <key>" \
  -H "ACCESS-SIGN: <signature>" \
  -H "ACCESS-TIMESTAMP: <timestamp>" \
  -H "ACCESS-PASSPHRASE: <passphrase>" \
  -H "Content-Type: application/json" \
  -d '{"stage":"Decision","model":"AlphaGenesis","input":{},"output":{},"explanation":"..."}'
```
