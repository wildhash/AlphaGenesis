# GCP Instance Quick Reference
## IP: 34.133.16.230

---

## 🚀 Quick Deploy (One Command)

From your local machine:

```bash
cd /home/user/AlphaGenesis
bash deploy/deploy_and_setup.sh
```

This does everything automatically!

---

## 📝 Before You Deploy

### 1. Set up SSH access (if not already done)

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy key to GCP
ssh-copy-id root@34.133.16.230

# Test connection
ssh root@34.133.16.230 'echo "Connected!"'
```

### 2. Configure .env file

```bash
cd /home/user/AlphaGenesis
nano .env
```

Add your WEEX API credentials:
```env
WEEX_API_KEY=your_actual_key
WEEX_API_SECRET=your_actual_secret
WEEX_API_PASSPHRASE=your_actual_passphrase
```

---

## 🔌 Connect to GCP

```bash
ssh root@34.133.16.230
```

---

## 📊 Monitor the System

### View Live Logs
```bash
ssh root@34.133.16.230 'journalctl -u sdm-trading.service -f'
```

### Check Status
```bash
ssh root@34.133.16.230 'systemctl status sdm-trading.service'
```

### Run Health Check
```bash
ssh root@34.133.16.230 'bash /opt/AlphaGenesis/monitor.sh'
```

### View Recent Trades
```bash
ssh root@34.133.16.230 'journalctl -u sdm-trading.service | grep "EXECUTING ACTION"'
```

---

## 🎮 Control Commands

### Start
```bash
ssh root@34.133.16.230 'systemctl start sdm-trading.service'
```

### Stop
```bash
ssh root@34.133.16.230 'systemctl stop sdm-trading.service'
```

### Restart
```bash
ssh root@34.133.16.230 'systemctl restart sdm-trading.service'
```

---

## 📈 Performance Reports

### List Reports
```bash
ssh root@34.133.16.230 'ls -lh /opt/AlphaGenesis/reports/sdm/'
```

### View Learning Metrics
```bash
ssh root@34.133.16.230 'cat /opt/AlphaGenesis/reports/sdm/learning_*.json | jq ".strategy_performance"'
```

### View Ethics Violations
```bash
ssh root@34.133.16.230 'cat /opt/AlphaGenesis/reports/sdm/ethics_*.json | jq ".summary"'
```

---

## 🔧 Troubleshooting

### Check if Service is Running
```bash
ssh root@34.133.16.230 'systemctl is-active sdm-trading.service'
```

### View Last 50 Log Lines
```bash
ssh root@34.133.16.230 'journalctl -u sdm-trading.service -n 50'
```

### Check for Errors
```bash
ssh root@34.133.16.230 'journalctl -u sdm-trading.service -p err -n 20'
```

### View .env Configuration
```bash
ssh root@34.133.16.230 'cat /opt/AlphaGenesis/.env'
```

### Test API Connection
```bash
ssh root@34.133.16.230 << 'EOF'
cd /opt/AlphaGenesis
su - alphagenesis -c "cd /opt/AlphaGenesis && python3 -c 'from alphagenesis.data import WEEXClient; import os; from dotenv import load_dotenv; load_dotenv(); c = WEEXClient(os.getenv(\"WEEX_API_KEY\"), os.getenv(\"WEEX_API_SECRET\"), os.getenv(\"WEEX_API_PASSPHRASE\")); print(c.get_ticker(\"cmt_btcusdt\"))'"
EOF
```

---

## 💾 Backup & Update

### Backup .env
```bash
ssh root@34.133.16.230 'cp /opt/AlphaGenesis/.env /opt/AlphaGenesis/.env.backup'
```

### Pull Latest Code
```bash
ssh root@34.133.16.230 << 'EOF'
cd /opt/AlphaGenesis
git pull origin claude/weex-trading-system-JjDSY
systemctl restart sdm-trading.service
EOF
```

### View Git Status
```bash
ssh root@34.133.16.230 'cd /opt/AlphaGenesis && git status'
```

---

## 📱 One-Liner Monitoring

### Complete System Status
```bash
ssh root@34.133.16.230 << 'EOF'
echo "=== Service Status ===" && systemctl status sdm-trading.service --no-pager | head -10 && \
echo -e "\n=== Recent Logs ===" && journalctl -u sdm-trading.service -n 5 --no-pager && \
echo -e "\n=== System Resources ===" && free -h | grep Mem && df -h / | tail -1 && \
echo -e "\n=== Recent Reports ===" && ls -lt /opt/AlphaGenesis/reports/sdm/ 2>/dev/null | head -3 || echo "No reports yet"
EOF
```

---

## 🚨 Emergency Procedures

### Emergency Stop
```bash
ssh root@34.133.16.230 'systemctl stop sdm-trading.service && echo "System stopped"'
```

### Force Kill
```bash
ssh root@34.133.16.230 'pkill -9 -f start_sdm_trading && echo "Process killed"'
```

### Restart After Crash
```bash
ssh root@34.133.16.230 'systemctl restart sdm-trading.service && sleep 3 && systemctl status sdm-trading.service'
```

---

## 📋 Daily Monitoring Routine

Run this once per day during competition:

```bash
# Save as check_daily.sh
cat > check_daily.sh << 'EOF'
#!/bin/bash
GCP_IP="34.133.16.230"

echo "Daily SDM Trading System Check - $(date)"
echo "======================================================================"

echo -e "\n1. Service Status:"
ssh root@$GCP_IP 'systemctl is-active sdm-trading.service' && echo "✓ Running" || echo "✗ Stopped"

echo -e "\n2. Recent Activity (last 10 lines):"
ssh root@$GCP_IP 'journalctl -u sdm-trading.service -n 10 --no-pager'

echo -e "\n3. Trade Count:"
ssh root@$GCP_IP 'journalctl -u sdm-trading.service | grep -c "EXECUTING ACTION"'

echo -e "\n4. Latest Reports:"
ssh root@$GCP_IP 'ls -lt /opt/AlphaGenesis/reports/sdm/ | head -5'

echo -e "\n5. System Resources:"
ssh root@$GCP_IP 'free -h | grep Mem && df -h / | tail -1'

echo "======================================================================"
EOF

chmod +x check_daily.sh
./check_daily.sh
```

---

## 📞 Support Contacts

- **Telegram Group**: https://t.me/+6OlzxYh52lc1YTg9
- **WEEX Event Page**: https://www.weex.com/events/ai-trading
- **API Documentation**: https://www.weex.com/api-doc/ai/

---

## 🎯 Competition Timeline

- **Start**: Jan 12, 2026 8:00 PM (UTC+8)
- **End**: Feb 2, 2026 11:59 PM (UTC+8)
- **Goal**: Top 2 in BUIDL group by account balance

---

## ✅ Pre-Launch Checklist

- [ ] SSH access working to 34.133.16.230
- [ ] .env configured with WEEX API credentials
- [ ] Deployment script run successfully
- [ ] Service status shows "active (running)"
- [ ] Logs show "SDM TRADING ENGINE INITIALIZED"
- [ ] No critical errors in recent logs
- [ ] Can view monitoring dashboard
- [ ] Joined Telegram group
- [ ] BUIDL group confirmed on event page

---

## 🎬 Launch Commands

When competition starts:

```bash
# Final verification
ssh root@34.133.16.230 << 'EOF'
echo "Pre-competition verification..."
systemctl status sdm-trading.service --no-pager | head -10
echo ""
echo "Recent logs:"
journalctl -u sdm-trading.service -n 20 --no-pager
echo ""
echo "System is ready for competition!"
EOF
```

---

**Good luck! 🚀 May your intents propagate favorably!**
