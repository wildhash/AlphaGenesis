# WEEX Evidence Pack

## Summary
- Service running: `sdm-trading.service`
- AI log smoke upload: `uploadAiLog` returned `00000` (see smoke_upload.txt)
- AI log queue: see ai_log_queue.txt
- Queue DB: `/opt/AlphaGenesis/tmp/ai_logs.sqlite`
- AI log code: `alphagenesis/omni/ai_logs/`

## Files
- `smoke_upload.txt` — AI log upload proof
- `service_status.txt` — systemd status
- `journal_last_500.txt` — last 500 service log lines
- `journal_errors.txt` — filtered errors/stop/suspend/drawdown/exception
- `ai_log_queue.txt` — queue snapshot
- `sanitized_env.txt` — config with secrets redacted
- `config_snapshot/` — safe config copies

## Reproduce (read-only)
```
sudo bash -lc 'set -a && source /opt/AlphaGenesis/.env && set +a && python3 /opt/AlphaGenesis/scripts/weex_ai_log_smoke.py'
sudo systemctl status sdm-trading.service --no-pager
sudo journalctl -u sdm-trading.service -n 500 --no-pager
PYTHONPATH=/opt/AlphaGenesis python3 - <<'PY'
from alphagenesis.omni.ai_logs import AILogStore
store = AILogStore('/opt/AlphaGenesis/tmp/ai_logs.sqlite')
print({'pending': store.pending_count(), 'db_path': '/opt/AlphaGenesis/tmp/ai_logs.sqlite'})
PY
```
