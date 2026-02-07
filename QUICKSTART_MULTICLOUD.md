# 🚀 AlphaGenesis Multi-Cloud Quick Start

**Get your trading system running in under 30 minutes across all three cloud providers!**

---

## 📑 What You'll Deploy

| Cloud Provider | Purpose | Region | Setup Time |
|----------------|---------|--------|------------|
| **GCP** | Testing | us-central1 | ~10 min |
| **Alibaba Cloud** | Production | cn-hongkong | ~10 min |
| **AWS Singapore** | Production | ap-southeast-1 | ~10 min |

---

## ⚡ Prerequisites Checklist

Before you begin, ensure you have:

- [ ] WEEX API credentials (Key, Secret, Passphrase)
- [ ] Access to GCP project (Project ID: gemiadvan)
- [ ] Alibaba Cloud account with ECS access
- [ ] AWS account with EC2 access in Singapore region
- [ ] SSH client or browser access to cloud consoles

---

## 🔵 Part 1: GCP Test Environment (10 minutes)

### Option A: Browser Console (Easiest)

1. **Open GCP Console**
   ```
   https://console.cloud.google.com
   ```

2. **Navigate to VM**
   - Click ☰ Menu → Compute Engine → VM instances
   - Find or create your test VM
   - Click **SSH** button

3. **Run Setup**
   ```bash
   cd /opt
   sudo mkdir -p AlphaGenesis
   cd AlphaGenesis
   sudo git clone https://github.com/wildhash/AlphaGenesis.git .
   sudo git checkout finals/alpha-genesis-clean
   sudo bash deploy/setup_gcp_test.sh
   ```

4. **Configure Credentials**
   ```bash
   sudo nano /opt/AlphaGenesis/.env
   ```

   Replace these lines:
   ```env
   WEEX_API_KEY=your_test_api_key_here
   WEEX_API_SECRET=your_test_api_secret_here
   WEEX_API_PASSPHRASE=your_test_passphrase_here
   ```

   Save: `Ctrl+X`, `Y`, `Enter`

5. **Start System**
   ```bash
   sudo systemctl start sdm-trading.service
   sudo systemctl status sdm-trading.service
   ```

6. **Verify Running**
   ```bash
   sudo journalctl -u sdm-trading.service -f
   ```

   You should see trading activity! Press `Ctrl+C` to exit.

### Option B: gcloud CLI

```bash
# Create VM
gcloud compute instances create alphagenesis-test \
  --project=gemiadvan \
  --zone=us-central1-a \
  --machine-type=e2-standard-4 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB

# SSH and setup
gcloud compute ssh alphagenesis-test --zone=us-central1-a

# Then follow steps 3-6 above
```

✅ **GCP Test Environment Complete!**

---

## 🟠 Part 2: Alibaba Cloud Production (10 minutes)

### 1. Create ECS Instance

**Via Console:**
- Login: https://ecs.console.aliyun.com
- Region: **Hong Kong** (cn-hongkong)
- Instance Type: **ecs.c6.xlarge** (4 vCPU, 8 GB)
- Image: **Ubuntu 22.04 64-bit**
- Storage: **50 GB SSD**
- Enable: **Public IP**

**Via CLI:**
```bash
aliyun ecs RunInstances \
  --RegionId cn-hongkong \
  --ImageId ubuntu_22_04_x64_20G \
  --InstanceType ecs.c6.xlarge \
  --InstanceName alphagenesis-prod-alibaba
```

### 2. Configure Security Group

Allow inbound:
- Port 22 (SSH)
- Port 443 (HTTPS)

### 3. SSH and Deploy

```bash
# SSH to instance
ssh root@<your-alibaba-instance-ip>

# Download and run setup
curl -o setup.sh https://raw.githubusercontent.com/wildhash/AlphaGenesis/finals/alpha-genesis-clean/deploy/setup_alibaba_cloud.sh
chmod +x setup.sh
sudo bash setup.sh
```

**Or clone first:**
```bash
cd /opt
mkdir -p AlphaGenesis
cd AlphaGenesis
git clone https://github.com/wildhash/AlphaGenesis.git .
git checkout finals/alpha-genesis-clean
sudo bash deploy/setup_alibaba_cloud.sh
```

### 4. Configure PRODUCTION Credentials

```bash
sudo nano /opt/AlphaGenesis/.env
```

**IMPORTANT: Use PRODUCTION credentials!**
```env
WEEX_API_KEY=YOUR_PRODUCTION_KEY
WEEX_API_SECRET=YOUR_PRODUCTION_SECRET
WEEX_API_PASSPHRASE=YOUR_PRODUCTION_PASSPHRASE
```

### 5. Start Production Trading

```bash
# Start service
sudo systemctl start sdm-trading.service

# Enable auto-restart
sudo systemctl enable sdm-trading.service

# Verify
sudo systemctl status sdm-trading.service
sudo journalctl -u sdm-trading.service -f
```

### 6. Monitor Production

```bash
bash /opt/AlphaGenesis/monitor_production.sh
```

✅ **Alibaba Cloud Production Running!**

---

## 🟢 Part 3: AWS Singapore Production (10 minutes)

### 1. Launch EC2 Instance

**Via Console:**
- Open: https://ap-southeast-1.console.aws.amazon.com/ec2
- Click: **Launch Instance**
- Name: `alphagenesis-prod-aws-singapore`
- AMI: **Ubuntu Server 22.04 LTS**
- Instance type: **c6i.xlarge** (4 vCPU, 8 GB)
- Key pair: Create or select existing
- Storage: **50 GB gp3**
- Security group:
  - SSH (22) - Your IP
  - HTTPS (443) - Anywhere

**Via AWS CLI:**
```bash
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type c6i.xlarge \
  --key-name your-key-name \
  --region ap-southeast-1 \
  --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=50,VolumeType=gp3}' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=alphagenesis-prod-aws}]'
```

### 2. SSH and Deploy

```bash
# SSH to instance
ssh -i your-key.pem ubuntu@<your-aws-public-ip>

# Download and run setup
curl -o setup.sh https://raw.githubusercontent.com/wildhash/AlphaGenesis/finals/alpha-genesis-clean/deploy/setup_aws_singapore.sh
chmod +x setup.sh
sudo bash setup.sh
```

**Or clone first:**
```bash
cd /opt
sudo mkdir -p AlphaGenesis
cd AlphaGenesis
sudo git clone https://github.com/wildhash/AlphaGenesis.git .
sudo git checkout finals/alpha-genesis-clean
sudo bash deploy/setup_aws_singapore.sh
```

### 3. Configure PRODUCTION Credentials

```bash
sudo nano /opt/AlphaGenesis/.env
```

**Set PRODUCTION credentials:**
```env
WEEX_API_KEY=YOUR_PRODUCTION_KEY
WEEX_API_SECRET=YOUR_PRODUCTION_SECRET
WEEX_API_PASSPHRASE=YOUR_PRODUCTION_PASSPHRASE
```

### 4. Start AWS Production

```bash
# Start service
sudo systemctl start sdm-trading.service

# Enable auto-restart
sudo systemctl enable sdm-trading.service

# Check status
sudo systemctl status sdm-trading.service

# Monitor
sudo journalctl -u sdm-trading.service -f
```

### 5. AWS-Specific Monitoring

```bash
# Health check
bash /opt/AlphaGenesis/monitor_aws_production.sh

# Send metrics to CloudWatch (if configured)
bash /opt/AlphaGenesis/send_metrics_to_cloudwatch.sh
```

✅ **AWS Singapore Production Running!**

---

## 🎯 Verification Checklist

### For Each Deployment:

```bash
# 1. Check service is running
sudo systemctl status sdm-trading.service
# Should show: "active (running)" in green

# 2. Verify logs show trading activity
sudo journalctl -u sdm-trading.service -n 50
# Should see: "SDM ITERATION", "Observing market", etc.

# 3. Check for signals
sudo journalctl -u sdm-trading.service | grep "DIAG_SIGNAL_GENERATED" | wc -l
# Should show: Number > 0

# 4. Verify WEEX connection
python3 /opt/AlphaGenesis/scripts/check_weex_account.py
# Should show: Your account balance and positions

# 5. No critical errors
sudo journalctl -u sdm-trading.service -n 100 | grep -i "error\|exception"
# Should show: Minimal or no errors
```

---

## 📊 Quick Management Commands

### All Environments (Same Commands)

```bash
# Start trading
sudo systemctl start sdm-trading.service

# Stop trading
sudo systemctl stop sdm-trading.service

# Restart
sudo systemctl restart sdm-trading.service

# Status check
sudo systemctl status sdm-trading.service

# Live logs
sudo journalctl -u sdm-trading.service -f

# Check account
python3 /opt/AlphaGenesis/scripts/check_weex_account.py

# Close all positions (EMERGENCY)
python3 /opt/AlphaGenesis/scripts/close_all_positions.py
```

### Environment-Specific Monitoring

**GCP Test:**
```bash
bash /opt/AlphaGenesis/monitor.sh
```

**Alibaba Cloud:**
```bash
bash /opt/AlphaGenesis/monitor_production.sh
bash /opt/AlphaGenesis/backup_production.sh  # Manual backup
```

**AWS Singapore:**
```bash
bash /opt/AlphaGenesis/monitor_aws_production.sh
bash /opt/AlphaGenesis/send_metrics_to_cloudwatch.sh
bash /opt/AlphaGenesis/backup_to_s3.sh  # Manual backup
```

---

## 🔄 Multi-Cloud Monitoring Script

Create a local script to monitor all deployments:

```bash
#!/bin/bash
# Save as: monitor_all.sh

echo "═══════════════════════════════════════════════════════════"
echo "  Multi-Cloud AlphaGenesis Status"
echo "═══════════════════════════════════════════════════════════"
echo ""

# GCP Test
echo "🔵 GCP Test:"
gcloud compute ssh alphagenesis-test --zone=us-central1-a --command="systemctl is-active sdm-trading.service" 2>/dev/null && echo "✓ Running" || echo "✗ Stopped"

# Alibaba Cloud
echo "🟠 Alibaba Cloud Production:"
ssh root@<alibaba-ip> "systemctl is-active sdm-trading.service" 2>/dev/null && echo "✓ Running" || echo "✗ Stopped"

# AWS Singapore
echo "🟢 AWS Singapore Production:"
ssh -i key.pem ubuntu@<aws-ip> "systemctl is-active sdm-trading.service" 2>/dev/null && echo "✓ Running" || echo "✗ Stopped"

echo ""
echo "═══════════════════════════════════════════════════════════"
```

---

## ⚠️ Important Notes

### Security

- **Test vs Production**: Use different API keys for test and production
- **Permissions**: .env file has restricted permissions (600)
- **Firewall**: Only required ports are open (22, 443)

### Trading Configuration

- **Test Environment**: Paper trading mode, low leverage
- **Production**: Live trading enabled, higher leverage

### Monitoring

- **Logs**: All environments use systemd journal
- **Backups**: Automated backups run every 6 hours
- **Metrics**: CloudWatch integration on AWS (optional)

### Resource Management

- **CPU**: 4 vCPU recommended for production
- **RAM**: 8 GB recommended for production
- **Storage**: 50 GB SSD recommended
- **Network**: High bandwidth for low latency

---

## 🚨 Troubleshooting

### Service Won't Start

```bash
# Check what's wrong
sudo journalctl -u sdm-trading.service -n 100 --no-pager

# Verify .env exists
ls -la /opt/AlphaGenesis/.env

# Check Python dependencies
pip3 list | grep -E 'numpy|pandas|loguru|ccxt'

# Reinstall if needed
pip3 install --upgrade numpy pandas loguru ccxt python-dotenv
```

### No Trading Signals

```bash
# Check signal generation
sudo journalctl -u sdm-trading.service | grep "DIAG_SIGNAL"

# Verify market data
sudo journalctl -u sdm-trading.service | grep "Observing market"

# Check API connection
python3 -c "from alphagenesis.data.weex_client import WEEXClient; client = WEEXClient(); print(client.get_server_time())"
```

### High CPU/Memory Usage

```bash
# Check resources
htop  # or top

# Restart service
sudo systemctl restart sdm-trading.service

# Check for memory leaks in logs
sudo journalctl -u sdm-trading.service | grep -i "memory"
```

---

## 📞 Getting Help

- **Documentation**: See `/deploy/MULTI_CLOUD_DEPLOYMENT.md` for detailed guide
- **Repository**: https://github.com/wildhash/AlphaGenesis
- **Issues**: https://github.com/wildhash/AlphaGenesis/issues

---

## ✅ Success Indicators

Your deployment is successful when you see:

1. ✓ Service status shows "active (running)"
2. ✓ Logs show "SDM ITERATION" messages
3. ✓ Signal generation count > 0
4. ✓ WEEX account check returns valid data
5. ✓ No critical errors in recent logs

---

## 🎉 You're Live!

Congratulations! You now have AlphaGenesis running across three cloud providers:

- 🔵 **GCP**: Testing new strategies safely
- 🟠 **Alibaba Cloud**: Primary production trading
- 🟢 **AWS Singapore**: Secondary/backup production

**Happy Trading! 🚀📈**

---

*For detailed configuration options and advanced features, see the complete documentation in `/deploy/MULTI_CLOUD_DEPLOYMENT.md`*
