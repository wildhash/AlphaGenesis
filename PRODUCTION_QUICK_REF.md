# PRODUCTION QUICK REFERENCE

**Environment:** GCP VM (Project ID: gemiadvan)
**Path:** `/opt/AlphaGenesis` (NOT /home/user/AlphaGenesis)
**Service:** `sdm-trading.service`
**SSH:** SINGLE SESSION ONLY (VM resource constrained)

## ONE-LINE HEALTH CHECKS

```bash
# Signal count (last 5 min) - should be > 0
sudo journalctl -u sdm-trading.service -o cat --since "5 minutes ago" | grep "DIAG_SIGNAL_GENERATED" | wc -l

# Recent errors
sudo journalctl -u sdm-trading.service -o cat --since "5 minutes ago" | grep -i error | tail -5

# Current regime
sudo journalctl -u sdm-trading.service -o cat --since "2 minutes ago" | grep -i "regime" | tail -5

# LOW_VOL override firing?
sudo journalctl -u sdm-trading.service -o cat --since "3 minutes ago" | grep "LOW_VOL OVERRIDE" | tail -10
```

## CRITICAL FILES

```bash
# Core engine (bandit + signal generation)
/opt/AlphaGenesis/alphagenesis/sdm/sdm_engine.py

# Signal thresholds (if tuning needed)
/opt/AlphaGenesis/alphagenesis/features/momentum_hybrid_engine.py

# Service control
sudo systemctl status sdm-trading.service
sudo systemctl restart sdm-trading.service

# Logs (live tail)
sudo journalctl -u sdm-trading.service -o cat -f
```

## RECENT CHANGES

1. **Forced momentum-only:** `strategies=['momentum']` in sdm_engine.py
2. **LOW_VOL override:** Force momentum strategy when `regime == MarketRegime.LOW_VOLATILITY`
   - Location: After bandit selection in sdm_engine.py
   - Backup: `sdm_engine.py.bak.low_vol_override.<timestamp>`

## STATE FILES

```bash
/tmp/bandit_state.json        # Strategy learning
/tmp/position_ledger.json     # Active positions
/tmp/trading_journal.db       # Trade history
```

## VM RESOURCE WARNING

- 2nd SSH session crashed the VM
- Use `tmux` or `screen` for multiple views
- Single terminal workflow only
- Monitor: `free -h` and `top -bn1 | head -20`

## EMERGENCY SCRIPTS

```bash
cd /opt/AlphaGenesis

# Service restart
sudo systemctl restart sdm-trading.service

# Account status
python3 scripts/check_weex_account.py

# Position closure (emergency only)
python3 scripts/close_all_positions.py
```

## CURRENT MISSION

**Status:** 2nd place (fell from 1st)
**Goal:** Reclaim 1st place
**Action:** Verify LOW_VOL override + tune thresholds if needed
**Guide:** See CODEX_NEXT_STEPS.md for decision tree

---

**Keep it simple. One change at a time. Monitor. Adjust.**
