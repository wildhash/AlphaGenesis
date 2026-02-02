# Quick AI Log Monitoring Guide

## Restart Service (After Deployment)
```bash
sudo systemctl restart sdm-trading.service
sudo systemctl status sdm-trading.service
```

## Monitor AI Log Activity (Real-time)
```bash
sudo journalctl -u sdm-trading.service -f | grep --color=always "AI log"
```

## Complete Order Flow (Real-time)
```bash
sudo journalctl -u sdm-trading.service -f | egrep "Placing order|AI log|DIAG_SIGNAL|WEEX_ORDER" --line-buffered --color=always
```

## Check Recent Success/Failure
```bash
# Last 10 minutes
sudo journalctl -u sdm-trading.service --since "10 minutes ago" | grep "AI log"

# Success count (last hour)
sudo journalctl -u sdm-trading.service --since "1 hour ago" | grep "✓ AI log uploaded" | wc -l

# Failure check
sudo journalctl -u sdm-trading.service --since "1 hour ago" | grep "✗ AI log upload failed"
```

## Expected Log Pattern

For each order, you should see:
```
1. DIAG_SIGNAL_GENERATED symbol=cmt_btcusdt direction=LONG
2. Placing order: {'symbol': 'cmt_btcusdt', ...}
3. WEEX_ORDER_RESPONSE order_id=123456789
4. ✓ AI log uploaded to WEEX for order 123456789
```

## Troubleshooting

### No AI logs appearing
- Check if orders are being placed: `grep "Placing order"`
- Verify DRY_RUN mode is OFF: `grep DRY_RUN /opt/AlphaGenesis/.env`

### AI log upload fails
- Check WEEX API credentials: `grep WEEX_API /opt/AlphaGenesis/.env`
- Check error message in logs: `grep "AI log upload failed" -A 5`
- Verify API endpoint: https://www.weex.com/api-doc/ai/UploadAiLog

### Service not running
```bash
sudo systemctl status sdm-trading.service
sudo journalctl -u sdm-trading.service --since "5 minutes ago" | tail -50
```

## Quick Health Check
```bash
# One-liner to check everything
echo "=== Service Status ===" && \
sudo systemctl is-active sdm-trading.service && \
echo "=== Recent Orders ===" && \
sudo journalctl -u sdm-trading.service --since "10 minutes ago" | grep "Placing order" | wc -l && \
echo "=== AI Logs Uploaded ===" && \
sudo journalctl -u sdm-trading.service --since "10 minutes ago" | grep "✓ AI log uploaded" | wc -l && \
echo "=== Failures ===" && \
sudo journalctl -u sdm-trading.service --since "10 minutes ago" | grep "✗ AI log upload failed" | wc -l
```
