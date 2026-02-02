# WEEX AI Log Upload - Deployment Guide

## CRITICAL: Competition Requirement

WEEX judging panel has rejected our previous logs for lacking "AI-driven decision logic". This deployment implements the required `uploadAiLog` API integration to prove AI involvement.

**Without valid AI logs, we will be disqualified from rankings.**

## What Was Changed

### 1. WEEXClient Enhancement (`alphagenesis/data/weex_client.py`)
- Added `UPLOAD_AI_LOG_ENDPOINT = "/capi/v2/order/uploadAiLog"`
- Added `upload_ai_log()` method with full API integration
- Validates explanation length (max 1000 chars)
- Returns proper API response handling

### 2. SDM Engine Integration (`alphagenesis/sdm/sdm_engine.py`)
- Added `_upload_ai_log_to_weex()` method to format and submit logs
- Integrated into execution pipeline after successful order placement
- Extracts features, indicators, and reasoning from signals
- Formats according to WEEX requirements:
  - **Stage**: "Strategy Generation"
  - **Model**: "AlphaGenesis-SDM-v2.0-Momentum"
  - **Input**: Market data + technical indicators + regime + strategy context
  - **Output**: Signal + confidence + risk management + reasoning
  - **Explanation**: Natural language summary (under 1000 chars)

### 3. Momentum Engine Features (`alphagenesis/features/momentum_hybrid_engine.py`)
- Added `features` dictionary to all signal returns
- Includes: RSI, EMA_fast, EMA_slow, momentum_pct, ATR, volatility
- Enables comprehensive AI reasoning documentation

## AI Log Format

Each order now submits a log with:

```json
{
  "orderId": "12345678",
  "stage": "Strategy Generation",
  "model": "AlphaGenesis-SDM-v2.0-Momentum",
  "input": {
    "symbol": "cmt_btcusdt",
    "market_regime": "WEAK_UPTREND",
    "technical_indicators": {
      "RSI_14": 62.3,
      "EMA_20": 68950.4,
      "EMA_50": 68820.2,
      "momentum_pct": 1.2,
      "ATR": 450.0,
      "volatility": 0.0065
    },
    "current_price": 68980.5,
    "strategy_context": {
      "chosen_strategy": "momentum",
      "bandit_algorithm": "UCB (Upper Confidence Bound)",
      "exploration_rate": 0.2
    }
  },
  "output": {
    "signal": "LONG",
    "confidence": 0.72,
    "entry_price": 68980.5,
    "position_size": 0.015,
    "stop_loss": 67944.09,
    "take_profit": 71052.91,
    "risk_reward_ratio": 2.0,
    "reasoning": "Uptrend momentum: RSI=62.3, EMA20>68820, Mom=1.2%",
    "technical_analysis": {
      "trend": "UPTREND",
      "rsi_state": "NEUTRAL",
      "momentum": "POSITIVE"
    }
  },
  "explanation": "AI Analysis for cmt_btcusdt in WEAK_UPTREND regime: Technical indicators show UPTREND (EMA20 68950.40 vs EMA50 68820.20), RSI at 62.3 (neutral), momentum +1.20%. Contextual bandit (UCB algorithm) selected momentum strategy based on historical performance. AI generated LONG signal with 72.00% confidence. Risk management: stop loss at $67944.09, take profit at $71052.91."
}
```

## Deployment Status

✅ **Code Changes**: Committed to `claude/weex-trading-system-JjDSY` branch
✅ **Git Push**: Successfully pushed to remote
✅ **Production Files**: Copied to `/opt/AlphaGenesis/` (timestamps: Feb 2 02:36)

## Next Steps (CRITICAL)

### On GCP Production VM (SSH-in-browser):

1. **Restart the Trading Service**:
   ```bash
   sudo systemctl restart sdm-trading.service
   sudo systemctl status sdm-trading.service
   ```

2. **Monitor AI Log Uploads**:
   ```bash
   sudo journalctl -u sdm-trading.service -f | grep "AI log"
   ```

   Look for:
   - `✓ AI log uploaded to WEEX for order [order_id]`
   - `✗ AI log upload failed` (investigate if seen)

3. **Verify Order + Log Flow**:
   ```bash
   sudo journalctl -u sdm-trading.service -f | egrep "Placing order|AI log|WEEX_ORDER" --color=always
   ```

4. **Check for Errors**:
   ```bash
   sudo journalctl -u sdm-trading.service --since "1 minute ago" | grep -i "error\|exception"
   ```

## Testing

A test script is provided:
```bash
cd /opt/AlphaGenesis
python3 scripts/test_ai_log_upload.py
```

**Note**: Test requires WEEX API credentials (already configured in production `.env`)

## Expected Behavior

After restart, **every successful order** will:
1. Place order via WEEX API
2. Extract AI reasoning data (features, signals, confidence)
3. Format according to WEEX requirements
4. Submit via `POST /capi/v2/order/uploadAiLog`
5. Log result: `✓ AI log uploaded` or `✗ AI log upload failed`

## Failure Handling

- AI log upload failures **do NOT** cancel the order
- Orders complete normally, but a warning is logged
- Manual log submission may be required if uploads consistently fail

## Monitoring Commands

```bash
# Real-time monitoring
sudo journalctl -u sdm-trading.service -f

# Recent AI log activity
sudo journalctl -u sdm-trading.service --since "10 minutes ago" | grep "AI log"

# Count successful uploads
sudo journalctl -u sdm-trading.service --since "1 hour ago" | grep "✓ AI log uploaded" | wc -l

# Check for upload failures
sudo journalctl -u sdm-trading.service --since "1 hour ago" | grep "✗ AI log upload failed"
```

## Rollback Plan

If issues arise:
```bash
cd /opt/AlphaGenesis
git log -2  # Note current commit
git checkout [previous-commit-hash]
sudo systemctl restart sdm-trading.service
```

## Verification Checklist

- [ ] Service restarted on GCP VM
- [ ] No errors in service logs
- [ ] First order placed successfully
- [ ] AI log uploaded for first order
- [ ] No "AI log upload failed" errors in logs
- [ ] System continues trading normally

## Contact WEEX Support

If logs continue to be rejected:
- Provide sample AI log JSON (from this document)
- Reference API docs: https://www.weex.com/api-doc/ai/UploadAiLog
- Emphasize: "We are uploading detailed AI reasoning with technical indicators, strategy selection via contextual bandit, and comprehensive explanations"

---

**Deployed by**: Claude Code CLI
**Branch**: claude/weex-trading-system-JjDSY
**Commit**: d32d785
**Date**: 2026-02-02 02:36 UTC
