#!/bin/bash
#
# Fix corrupted systemd service file
#

echo "Recreating sdm-trading.service..."

sudo tee /etc/systemd/system/sdm-trading.service > /dev/null << 'EOF'
[Unit]
Description=SDM Trading System for WEEX AI Wars
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=alphagenesis
WorkingDirectory=/opt/AlphaGenesis
Environment="PATH=/home/alphagenesis/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/opt/AlphaGenesis:/usr/local/lib/python3.11/dist-packages"
ExecStart=/usr/bin/python3 -u /opt/AlphaGenesis/scripts/start_sdm_trading.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Service file recreated"
echo ""
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "✓ Daemon reloaded"
echo ""
echo "Service file is now ready. To start the service, run:"
echo "  sudo systemctl start sdm-trading.service"
