# WEEX AI Wars Competition Configuration

## ✅ Competition Compliance Updates

### Trading Pairs (All 8 Approved Pairs)

The system now trades all approved WEEX AI Wars pairs:

1. ✅ `cmt_btcusdt` - Bitcoin
2. ✅ `cmt_ethusdt` - Ethereum
3. ✅ `cmt_solusdt` - Solana
4. ✅ `cmt_dogeusdt` - Dogecoin
5. ✅ `cmt_xrpusdt` - Ripple
6. ✅ `cmt_adausdt` - Cardano
7. ✅ `cmt_bnbusdt` - Binance Coin
8. ✅ `cmt_ltcusdt` - Litecoin

**Updated in:** `alphagenesis/sdm/sdm_engine.py` line 131

---

## 💰 Initial Capital Configuration

### If Your Account Has 1,000 USDT:
```env
INITIAL_CAPITAL=1000.0
```

### If Your Account Has 1,000,000 USDT:
```env
INITIAL_CAPITAL=1000000.0
```

**Update this in:** `/opt/AlphaGenesis/.env` on your VM

---

## 📋 Competition Rules Compliance

### ✅ What We're Doing Right:

1. **Automated AI Trading** ✅
   - SDM is fully autonomous
   - No manual intervention
   - Genuine AI technology (multi-model + continuous learning)

2. **Approved Trading Pairs Only** ✅
   - Trading all 8 approved pairs
   - No unauthorized pairs

3. **No Prohibited Activities** ✅
   - No HFT/latency arbitrage (low frequency: 1-3 trades/day)
   - No wash trading (genuine market orders)
   - No market manipulation (ML-based decisions)
   - No data falsification (complete audit trail)

4. **API Key Security** ✅
   - Keys stored securely in .env
   - No sharing or transferring
   - Protected file permissions (chmod 600)

5. **Risk Controls** ✅
   - 20x max leverage (hard limit)
   - Position size controls
   - Order frequency limits (max 5/day via ethics engine)
   - Circuit breakers active

---

## 🎯 Trading Strategy Per Pair

The SDM will automatically:

1. **Monitor all 8 pairs** simultaneously
2. **Detect market regime** for each pair (trend/sideways/volatile)
3. **Select best model** per pair via semantic binding:
   - LSTM for trending markets (BTC, ETH typically)
   - Scalper for sideways markets (altcoins in range)
   - RL agents for high volatility (DOGE, meme coins)
4. **Execute high-confidence trades** when criteria align
5. **Adapt based on performance** per pair

---

## 📊 Expected Trading Distribution

With 8 pairs and 1-3 trades/day total:

- **High activity pairs**: BTC, ETH (most liquidity)
- **Medium activity**: SOL, BNB (good volatility)
- **Opportunistic**: DOGE, XRP, ADA, LTC (when signals strong)

The SDM will naturally favor pairs with:
- Higher liquidity (BTC/ETH)
- Stronger trends
- Better model performance
- Lower risk

---

## ⚠️ Important: Verify Your Capital Amount

**Action Required on VM:**

```bash
# Check what your account balance actually is
# You'll see this when the system starts

# If it's 1M (not 1K), update .env:
sudo nano /opt/AlphaGenesis/.env

# Change this line:
INITIAL_CAPITAL=1000000.0

# Save: Ctrl+X, Y, Enter

# Restart the service:
sudo systemctl restart sdm-trading.service
```

---

## 🔄 After Capital Verification

The system will automatically:

1. **Query account balance** on startup
2. **Compare to INITIAL_CAPITAL** setting
3. **Use actual balance** for calculations
4. **Log any discrepancy**

**Check logs to confirm:**
```bash
sudo journalctl -u sdm-trading.service -n 50 | grep -i capital
```

---

## 🚀 System Status

| Component | Status |
|-----------|--------|
| Trading Pairs | ✅ All 8 pairs configured |
| AI/Automation | ✅ Fully automated SDM |
| Risk Controls | ✅ 20x max, circuit breakers |
| Compliance | ✅ All rules followed |
| API Integration | ✅ Official WEEX API |
| Monitoring | ✅ Complete logging |

---

## 📞 Quick Commands

### Check which pairs are being monitored:
```bash
sudo journalctl -u sdm-trading.service | grep "symbols"
```

### See trades per pair:
```bash
sudo journalctl -u sdm-trading.service | grep "EXECUTING ACTION"
```

### Monitor account balance:
```bash
sudo journalctl -u sdm-trading.service | grep -i "balance\|capital"
```

---

## ✅ Pre-Competition Checklist

- [x] All 8 trading pairs configured
- [ ] Capital amount verified (1K or 1M?)
- [ ] .env file configured with API keys
- [ ] Service running: `sudo systemctl status sdm-trading.service`
- [ ] Logs showing market monitoring
- [ ] No errors in startup
- [ ] Ready for 8 PM UTC+8 start!

---

**Competition starts TODAY at 8 PM UTC+8!** ⏰

**The SDM is ready to trade all 8 approved pairs with full compliance!** 🚀
