# STATUS_FOR_CODEX

## Current Focus
- Finalize Gym -> Gymnasium migration in venv and rerun validation.
- Prep for machine move: n2-standard-8 (8 vCPU, 32 GB RAM), 150 GB Balanced PD.

## Key Context
- Hackathon bot validated with regime adaptation; contest equity uses `legacy_amount`.
- Regime detection active (e.g., weak_uptrend) and profile application logged.
- Feedback loop logs active (reports no trades in last 4h during dry-run).

## Recent Changes
- sdm_engine.py:
  - Position fetch uses `get_position()`; account balance uses `legacy_amount`.
  - Added regime detection via MarketRegimeDetector (1h/4h), regime profiles, and feedback loop.
  - Added info-level logs for regime detection, profile application, balances, and feedback loop.
  - Startup banner exists but only prints when a signal is generated.
  - Log formatting fixed to Loguru `{}` style.
- position_monitor.py:
  - Uses market price for unrealized/close price.
  - Added `unrealizePnl` field support.
- sdm_engine.py:
  - Added `unrealizePnl` key support for PnL.
- rl_agent.py:
  - Switched `import gym` -> `import gymnasium as gym`.
  - Updated `reset` and `step` signatures to gymnasium API.
- venv created at `/opt/AlphaGenesis/.venv`.
  - `gymnasium` installed.
  - `requirements.txt` installed (loguru, pandas, etc.).

## Blockers
- Installing CPU-only PyTorch in venv failed: `No space left on device`.
  - Command attempted:
    `/opt/AlphaGenesis/.venv/bin/pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu`
  - Needs more disk or cleanup. New machine will have 150 GB disk.

## Last Validation Attempt
- 30s dry-run with system Python (not venv) shows regime detection and balances.
- 30s dry-run with venv failed due to missing `torch`.

## Next Steps (for next session)
1. On new machine, recreate venv and install dependencies:
   - `python3 -m venv /opt/AlphaGenesis/.venv`
   - `/opt/AlphaGenesis/.venv/bin/pip install -r /opt/AlphaGenesis/requirements.txt`
   - `/opt/AlphaGenesis/.venv/bin/pip install gymnasium`
   - `/opt/AlphaGenesis/.venv/bin/pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu`
2. Run final validation (30s):
   - `set -a && source /opt/AlphaGenesis/.env && set +a && DRY_RUN=true timeout 30s /opt/AlphaGenesis/.venv/bin/python -m alphagenesis.sdm.sdm_engine 2>&1`
3. If clean (no Gym warning), remove `DRY_RUN=true` and go live.
4. Optional: move startup banner earlier (user chose Option B earlier; may revisit).

## Machine Provisioning
- New machine type: n2-standard-8 (8 vCPU, 32 GB RAM).
- Boot disk: 150 GB Balanced Persistent Disk.

