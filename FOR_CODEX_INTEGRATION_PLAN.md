# Trade Logger Integration Plan for Codex

**Status:** Trade logger created, needs integration into sdm_engine.py
**Latest Commit:** `d091ed8` (includes trade logger + user script)
**Your Environment:** `/home/woakwild/` (no repo access)
**My Environment:** `/home/user/AlphaGenesis` (has full repo)

---

## What's Already Done

**File:** `alphagenesis/learning/trade_logger.py` ✅ Created
**Import:** Added to `alphagenesis/learning/__init__.py` ✅
**Methods:** 12 event logging methods implemented ✅

**Events Covered:**
- `log_signal_generated()` - When strategy generates signal
- `log_risk_gate_decision()` - Ledger/Gross/Risk/Ethics gates
- `log_order_created()` - Order sent to exchange
- `log_order_acknowledged()` - Exchange confirms
- `log_order_filled()` - Full or partial fill
- `log_position_opened()` - Position established
- `log_position_closed()` - Position closed with P&L
- `log_stop_loss_triggered()` - SL hit
- `log_take_profit_triggered()` - TP hit
- `log_account_snapshot()` - Periodic state capture
- `log_daily_summary()` - EOD statistics
- `log_error()` - Trading errors

---

## Integration Points in sdm_engine.py

### 1. Import at Top of File (after line 47)

```python
from alphagenesis.learning import DecisionJournal, DecisionTick, TradeEvent, ContextualBanditAllocator, get_trade_logger
```

### 2. Initialize in __init__ (around line 80-100)

```python
# Initialize trade logger
self.trade_logger = get_trade_logger()
```

### 3. Log Signal Generation (around line 659-720)

In `_generate_action()` method, after signal is generated:

```python
# After generating action dict (around line 780)
# TRADE LOGGING: Log signal generated
self.trade_logger.log_signal_generated(
    symbol=symbol,
    direction=signal['direction'],
    confidence=signal['confidence'],
    strategy=chosen_strategy,
    regime=regime_str,
    entry_price=price,
    position_size=size,
    stop_loss=stop_loss,
    take_profit=take_profit,
    features=features
)
```

### 4. Log Risk Gate Decisions (around line 852-915)

In `_execute_action()` method, after each gate:

```python
# After ledger gate (around line 853)
self.trade_logger.log_risk_gate_decision(
    symbol=symbol,
    direction=action['direction'],
    gate_type='ledger',
    approved=ledger_approved,
    reason=ledger_reason
)

# After gross exposure check (around line 877)
if gross_exposure_blocked:
    self.trade_logger.log_risk_gate_decision(
        symbol=symbol,
        direction=action['direction'],
        gate_type='gross_exposure',
        approved=False,
        reason=gross_exposure_reason
    )

# After risk manager (around line 915)
self.trade_logger.log_risk_gate_decision(
    symbol=symbol,
    direction=action['direction'],
    gate_type='risk_manager',
    approved=risk_approved,
    reason=str([v.message for v in veto_reasons])
)
```

### 5. Log Order Creation (around line 980-1050)

When placing order with exchange:

```python
# Before calling weex.place_order (around line 1030)
self.trade_logger.log_order_created(
    symbol=symbol,
    side='LONG' if side == 1 else 'SHORT',
    order_type='MARKET',
    quantity=action['position_size'],
    price=action['entry_price'],
    stop_loss=action.get('stop_loss'),
    take_profit=action.get('take_profit'),
    strategy=action.get('strategy'),
    regime=action.get('regime')
)

# After exchange responds (around line 1040)
self.trade_logger.log_order_acknowledged(
    symbol=symbol,
    order_id=str(time.time()),  # or extract from response
    exchange_order_id=str(order_response.get('orderId', 'unknown')),
    status='acknowledged',
    response=order_response
)
```

### 6. Log Account Snapshots (in run() loop)

Add periodic account state logging every N iterations:

```python
# In run() loop, after getting market_state (around line 330-340)
# Log account snapshot every 10 iterations (every ~50 minutes at 5min intervals)
if self.iteration_count % 10 == 0:
    self.trade_logger.log_account_snapshot(
        balance=market_state['account']['balance'],
        equity=market_state['account']['equity'],
        unrealized_pnl=market_state['account']['unrealized_pnl'],
        margin_used=market_state['account']['margin_used'],
        total_notional=market_state['account']['total_notional'],
        daily_pnl=market_state['account']['daily_pnl'],
        daily_pnl_percent=market_state['account']['daily_pnl_percent'],
        open_positions=len([p for p in self.position_ledger.get_all_positions().values() if p.side != 'FLAT'])
    )
```

### 7. Log Position Closures (position monitor callback)

This might require integration in position_monitor.py or wherever positions are closed.

---

## Missing Fields to Consider

Based on the schema, you might want to add:

1. **Fees tracking** - Extract from exchange responses
2. **Order IDs** - Track exchange order IDs properly
3. **Position IDs** - Link orders to positions
4. **Holding time** - Calculate duration for position_closed events
5. **Close reason** - Track why position closed (SL/TP/manual/liquidation)

---

## Verification After Integration

After deploying integrated version:

```bash
# Check logs are being created
ssh root@34.133.16.230
ls -lh /opt/AlphaGenesis/logs/trades/

# Check content
tail -20 /opt/AlphaGenesis/logs/trades/$(date +%Y-%m-%d).jsonl

# Count events
grep -c '"event_type"' /opt/AlphaGenesis/logs/trades/$(date +%Y-%m-%d).jsonl

# Check event types
grep -o '"event_type":"[^"]*"' /opt/AlphaGenesis/logs/trades/$(date +%Y-%m-%d).jsonl | sort | uniq -c
```

Expected output after a few hours:
```
  24 "event_type":"account_snapshot"
  15 "event_type":"signal_generated"
  12 "event_type":"risk_gate_decision"
   5 "event_type":"order_created"
   5 "event_type":"order_acknowledged"
   5 "event_type":"position_opened"
   3 "event_type":"position_closed"
```

---

## Deployment Plan

**Minimal steps:**

1. Integrate trade_logger calls in sdm_engine.py
2. Test locally (optional, but recommended)
3. Commit: "FEAT: Integrate trade logger into trading engine"
4. Push to GitHub
5. SSH to production:
   ```bash
   ssh root@34.133.16.230
   cd /opt/AlphaGenesis
   systemctl stop sdm-trading.service
   git pull origin claude/weex-trading-system-JjDSY
   systemctl start sdm-trading.service
   ```
6. Monitor logs:
   ```bash
   journalctl -u sdm-trading.service -f
   tail -f logs/trades/$(date +%Y-%m-%d).jsonl
   ```

---

## Questions for You (Codex)

1. Do you want me to do the integration from my environment?
2. Or should user copy the repo to `/home/woakwild/` for you?
3. Should we add position_monitor integration too?
4. Any other fields you want in the event schema?

---

## Current Production Status: UNKNOWN

**User needs to run:**
```bash
ssh root@34.133.16.230 "cd /opt/AlphaGenesis && git log -1 --oneline"
```

**Expected:** `d091ed8` or earlier
**Minimum safe:** `aacb1c2`

**If behind:** Deploy immediately (all fixes + validation logging critical)

---

**Status:** Ready for integration. Awaiting:
1. Production version check from user
2. Decision on who does integration (me or you)
3. Deployment coordination

**Risk:** Production might be running old unsafe code
**Urgency:** High - need to verify and update production ASAP
