# Finals Cutover Plan

## T-24h (Preparation + Verification)

- Verify service health and stability for 1-2 hours (no error spikes).
- Confirm WEEX API connectivity (ticker + account endpoints succeed).
- Verify AI log queue worker is processing (pending ~0).
- Confirm structured AI trace stages appear in live logs:
  - Strategy Evaluation
  - Risk & Constraints
  - Decision Making
  - Order Execution
  - Exit Decision
- Inspect active straddle states; plan how to clear them before finals start.
- Confirm open positions and balance after any account reset.

### F. Infrastructure Migration

- Provision Alibaba Cloud Singapore ECS: ecs.t6-c1m1.large (2 vCPU, 2 GB).
- Deploy bot to Singapore server (code + config + systemd service).
- Whitelist new Singapore IP with WEEX; keep GCP IP as backup.
- Verify latency from Singapore to WEEX (<20ms target).
- Set up AWS ap-southeast-1 failover instance (same code + config).

### G. Integration

- Integrate `alphagen_finals.py` (consolidated 1010-line bot) as alternative deployment option.
- Decide primary finals engine:
  - SDM engine (current)
  - `alphagen_finals.py` (new)
- If SDM: verify compliance traces flow end-to-end in live mode.
- If `alphagen_finals.py`: deploy to Singapore and test with paper trade.

### H. Monitoring

- Set up watchdog cron to restart on crash.
- Set up log rotation (17 days of logs can fill disk).
- Create a simple alert channel (Telegram/Discord webhook on errors).

## T-2h (Cutover + Dry Validation)

- Freeze code changes; tag current commit as finals candidate.
- Ensure ONLY one trading mode is enabled (live only for finals).
- Apply finals config at cutover time:
  - MAX_LEVERAGE=8
  - STOP_LOSS_PERCENT=0.03
  - TAKE_PROFIT_PERCENT=0.09
  - ENABLE_LIVE_TRADING=true
  - ENABLE_PAPER_TRADING=false
  - LOG_LEVEL=INFO
- Restart service and confirm it boots cleanly.
- Verify AI log pipeline still drains (pending ~0).
- Confirm no straddle runner states are blocking normal strategy evaluation.

## T-0 (Finals Start)

- Confirm live mode active and account reset state is correct.
- Verify first live signal produces all 4 AI trace stages.
- Capture a real AI decision log sample for compliance evidence.
- Keep GCP instance idle as hot backup if Singapore instance fails.

## Post-Start (First 2 Hours)

- Watch error logs and AI log queue status every 15 minutes.
- Ensure latency and order execution are normal.
- If issues arise, fail over to backup instance.
