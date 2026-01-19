# Production Status & Version Control Guide

**Critical Information for WEEX AI Wars Competition**

---

## ❓ Your Questions Answered

### 1. What version is Codex running?

**Short Answer:** We don't know without checking the production server.

**How to Check:**
```bash
ssh root@34.133.16.230
cd /opt/AlphaGenesis
git log -1 --oneline
```

**Expected Output:**
- **If up to date:** `0af4016 DOCS: Add quick start guide for logging system`
- **If out of date:** An older commit hash

**Why It Matters:**
- The **trading logic fixes** (6 critical fixes) were deployed in commits `8d39baf` and `aacb1c2`
- The **enhanced logging** was added in commits `c33ffff` and `0af4016`
- If production is on `8d39baf` or later → Trading logic is correct
- If production is NOT on `c33ffff` or later → Enhanced validation logging is missing

---

### 2. Is the GitHub repo up to date?

**Yes!** ✅

**Local repo status:**
```
Branch: claude/weex-trading-system-JjDSY
Latest commit: 0af4016 DOCS: Add quick start guide for logging system
Status: Clean, all changes pushed to origin
```

**Recent commits (newest first):**
```
0af4016 - DOCS: Add quick start guide for logging system
c33ffff - FEAT: Add comprehensive validation logging for hackathon submission
3fc7a5b - DOCS: Add status report and validation report for Codex review
8d39baf - DOCS: Complete documentation of all critical risk management fixes
aacb1c2 - URGENT: Fix remaining critical risk management blockers
```

**GitHub is the source of truth.** Production may be behind.

---

### 3. Does it matter if production is out of sync?

**Short Answer:** Depends on which commit production is running.

**Critical Commits:**

| Commit | Description | Impact if Missing |
|--------|-------------|-------------------|
| `0abd4ec` | CRITICAL FIX: Restore risk management | 🔴 **CRITICAL** - System unsafe |
| `11dcf0a` | FIX: Robust field name handling | 🔴 **CRITICAL** - Metrics will be zero |
| `aacb1c2` | URGENT: Fix remaining risk blockers | 🔴 **CRITICAL** - Risk gates broken |
| `8d39baf` | DOCS: Risk management docs | 🟡 Documentation only |
| `c33ffff` | FEAT: Validation logging | 🟢 Nice to have - better logs |
| `0af4016` | DOCS: Logging quick start | 🟢 Documentation only |

**Minimum Safe Version:** Production MUST be on `aacb1c2` or later.

**Recommended Version:** Production SHOULD be on `c33ffff` or later for complete validation logging.

---

### 4. How do we check on the trading machine status?

**Method 1: Quick Status Check**
```bash
bash check_production_status.sh
```

This checks:
- Git version deployed
- Service status (running/stopped)
- Recent errors
- WEEX account balance
- Critical fixes presence

**Method 2: Manual SSH Check**
```bash
ssh root@34.133.16.230

# Check service
systemctl status sdm-trading.service

# Check recent logs
journalctl -u sdm-trading.service -n 50

# Check account
cd /opt/AlphaGenesis
python3 check_weex_account.py

# Check version
git log -1 --oneline
```

**Method 3: Automated Monitoring (Recommended)**

Set up daily health checks:
```bash
# On production server
crontab -e

# Add this line (runs daily at 9 AM UTC)
0 9 * * * /root/check_production_status.sh >> /var/log/alpha_status.log 2>&1
```

**What to Monitor:**

✅ **Critical Metrics (check daily):**
- Service is running (`systemctl status`)
- No high error rate (< 10 errors/hour)
- Account balance is growing
- Recent trades are executing

⚠️ **Warning Signs:**
- Service stopped unexpectedly
- High error rate (> 10 errors/hour)
- Account balance dropping rapidly
- No trades in last 6 hours

🚨 **Emergency Actions:**
- Service crashed → restart: `systemctl restart sdm-trading.service`
- High losses → check risk limits, consider stopping
- API errors → check WEEX API status

---

### 5. How do we make it aware of current/upcoming conditions?

**Current State:** ✅ System is **reactive** and **learning**

The system currently:
- ✅ Detects market regime changes (UPTREND, DOWNTREND, etc.)
- ✅ Learns which strategies work best automatically (bandit algorithm)
- ✅ Adapts position sizing based on account state
- ✅ Records all decisions for later analysis

**What It DOESN'T Do Yet:**
- ❌ Anticipate economic events (FOMC, NFP, etc.)
- ❌ Predict regime transitions before they happen
- ❌ Incorporate news/sentiment
- ❌ Forecast volatility spikes

**How to Add Event Awareness:**

**Phase 1: Economic Calendar (Easiest)**
```python
# Add to sdm_engine.py
import requests
from datetime import datetime, timedelta

def get_upcoming_events():
    """Fetch high-impact economic events in next 24h"""
    # Use API like tradingeconomics.com or econdb.com
    tomorrow = datetime.now() + timedelta(days=1)
    events = fetch_calendar_api(tomorrow)
    return [e for e in events if e['impact'] == 'HIGH']

def should_reduce_exposure():
    """Check if major event coming up"""
    events = get_upcoming_events()
    if events:
        logger.warning(f"High-impact event in 24h: {events[0]['name']}")
        return True
    return False

# In position sizing logic
if should_reduce_exposure():
    position_size *= 0.5  # Reduce size before major events
```

**Phase 2: Volatility Forecasting (Medium)**
```python
# Add GARCH model for volatility prediction
from arch import arch_model

def forecast_volatility(returns, horizon=1):
    """Predict volatility for next period"""
    model = arch_model(returns, vol='GARCH', p=1, q=1)
    fitted = model.fit(disp='off')
    forecast = fitted.forecast(horizon=horizon)
    return forecast.variance.values[-1, 0]

# In risk checks
expected_vol = forecast_volatility(recent_returns)
if expected_vol > current_vol * 1.5:
    # Volatility spike expected - reduce exposure
    max_position_size *= 0.7
```

**Phase 3: Regime Transition Prediction (Advanced)**
```python
# Use Hidden Markov Model or ML classifier
from hmmlearn import hmm

def predict_regime_transition(price_history):
    """Predict if regime about to change"""
    model = hmm.GaussianHMM(n_components=3)
    model.fit(price_history)

    # Predict next state
    current_state = model.predict(price_history[-1:])
    confidence = model.predict_proba(price_history[-1:])[0].max()

    if confidence < 0.6:
        return "UNCERTAIN"  # Wait for clearer signal
    return current_state
```

---

### 6. How does it get better/smarter in perpetuity?

**Built-in Learning (Already Active):**

**1. Multi-Armed Bandit Algorithm** 🎰
- **What:** Automatically discovers best strategies for each market regime
- **How:** Tries different strategies, measures results, prefers winners
- **Speed:** Learns over 2-4 weeks, improves continuously
- **Persistence:** Saves state to `bandit_state.json` - never forgets

**2. Decision Journal** 📔
- **What:** Records every decision with full context
- **How:** SQLite database of all trades, signals, outcomes
- **Use:** Analyze patterns, identify improvements
- **Location:** `/opt/AlphaGenesis/decision_journal.db`

**3. Regime Adaptation** 🌡️
- **What:** Detects market regime and adapts strategy
- **How:** Analyzes price action, volatility, trends
- **Benefit:** Different strategies for different conditions
- **Implementation:** `_detect_market_regime()` in sdm_engine.py

**Example of Automatic Learning:**

```
Week 1:
  ETHUSDT UPTREND:
    momentum: 3 trades, avg +$1.20
    mean_reversion: 2 trades, avg -$0.80

  → Bandit learns: Use momentum in uptrends

Week 2:
  ETHUSDT UPTREND:
    momentum: 8 trades (selected more), avg +$1.45
    mean_reversion: 1 trade (selected less), avg -$0.50

  → Bandit exploits momentum, avoids mean reversion

Week 4:
  ETHUSDT UPTREND:
    momentum: 24 trades, avg +$1.68
    mean_reversion: 2 trades (occasional exploration)

  → System is now optimized for this regime
```

**Manual Improvements (Periodic):**

**Weekly:**
- Review bandit statistics
- Check decision journal for patterns
- Verify no new error types

**Monthly:**
- Analyze overall performance
- Optimize risk limits based on data
- Consider adding new strategies

**Quarterly:**
- Add new features (indicators, data sources)
- Implement structural improvements
- Expand to new markets/pairs

**See `CONTINUOUS_IMPROVEMENT.md` for detailed guide.**

---

## 🔧 Action Items

### Immediate (Next 30 Minutes)

1. **Check what version is running on production:**
   ```bash
   ssh root@34.133.16.230
   cd /opt/AlphaGenesis
   git log -1 --oneline
   ```

2. **If production is behind `aacb1c2`:**
   ```bash
   bash deploy_to_production.sh
   ```
   This is CRITICAL - system may be unsafe.

3. **If production is on `aacb1c2` but behind `c33ffff`:**
   ```bash
   bash deploy_to_production.sh
   ```
   This is recommended - better logging for validation.

4. **If production is up to date (`0af4016`):**
   Nothing needed. Just monitor.

### Short Term (This Week)

1. **Set up monitoring:**
   ```bash
   # On production
   crontab -e
   # Add: 0 9 * * * /root/check_production_status.sh >> /var/log/alpha_status.log 2>&1
   ```

2. **Collect first logs:**
   ```bash
   bash collect_logs.sh
   bash analyze_logs.sh
   ```

3. **Review bandit learning:**
   ```bash
   ssh root@34.133.16.230
   cd /opt/AlphaGenesis
   cat bandit_state.json | jq .
   ```

### Medium Term (Before Hackathon Ends)

1. **Accumulate validation data:**
   - Let system trade for at least 48 hours
   - Collect comprehensive logs
   - Verify all 6 fixes are working

2. **Prepare final submission:**
   - Run `collect_logs.sh` 24 hours before deadline
   - Run `analyze_logs.sh` to generate report
   - Package logs and analysis

3. **Document results:**
   - Update STATUS_FOR_CODEX.md with final metrics
   - Include evidence of continuous learning
   - Show performance improvement over time

---

## 📊 Key Files & Commands

**Check Status:**
```bash
bash check_production_status.sh
```

**Deploy Updates:**
```bash
bash deploy_to_production.sh
```

**Collect Logs:**
```bash
bash collect_logs.sh
```

**Analyze Performance:**
```bash
bash analyze_logs.sh
```

**Monitor Live:**
```bash
ssh root@34.133.16.230
journalctl -u sdm-trading.service -f
```

---

## 🎯 Current Status Summary

**GitHub Repo:**
- ✅ Up to date
- ✅ Branch: `claude/weex-trading-system-JjDSY`
- ✅ Latest: `0af4016`

**Production Server:**
- ❓ Unknown (need to check)
- 📍 Location: `34.133.16.230:/opt/AlphaGenesis`
- 🔧 Service: `sdm-trading.service`

**Competition:**
- 🏆 Rank: 2nd place in Group1-3
- 💰 Balance: ~$1,221 (as of screenshot)
- 📈 ROI: +22.1%
- 🤖 Bot: Alpha Genesis

**Learning Status:**
- ✅ Bandit algorithm: Active
- ✅ Decision journal: Recording
- ✅ Regime detection: Active
- ⏳ Learning since: ~6 days

**Next Critical Step:**
Check production version and deploy if needed.

---

**Created:** 2026-01-19
**Author:** AlphaGenesis Team
**Status:** Ready for production deployment verification
