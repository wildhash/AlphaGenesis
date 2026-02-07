# 🌐 AlphaGenesis Multi-Cloud Deployment Guide

**Production-Ready Trading System Deployment Across GCP, Alibaba Cloud, and AWS**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [GCP Test Deployment](#gcp-test-deployment)
5. [Alibaba Cloud Production](#alibaba-cloud-production)
6. [AWS Singapore Production](#aws-singapore-production)
7. [Monitoring & Management](#monitoring--management)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This guide will help you deploy the AlphaGenesis trading system across multiple cloud providers:

- **GCP (Google Cloud)**: Testing environment
- **Alibaba Cloud**: Production deployment (primary)
- **AWS Singapore**: Production deployment (secondary/backup)

### Key Benefits

✅ **Multi-region redundancy** - Geographic distribution
✅ **High availability** - Multiple cloud providers
✅ **Load distribution** - Spread trading across regions
✅ **Reduced latency** - Closer to exchange servers
✅ **Risk mitigation** - No single point of failure

---

## 🏗️ Architecture

```
                            ┌─────────────────┐
                            │  WEEX Exchange  │
                            └────────┬────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
              ┌─────▼─────┐    ┌────▼────┐    ┌─────▼─────┐
              │    GCP    │    │ Alibaba │    │    AWS    │
              │   (Test)  │    │  Cloud  │    │ Singapore │
              │           │    │  (Prod) │    │   (Prod)  │
              └───────────┘    └─────────┘    └───────────┘
                  Testing       Primary Prod   Secondary Prod
```

---

## 📦 Prerequisites

### Required for All Deployments

1. **WEEX API Credentials**
   - API Key
   - API Secret
   - API Passphrase
   - Obtained from WEEX AI Wars Hackathon

2. **Cloud Provider Access**
   - GCP: Project with Compute Engine enabled
   - Alibaba Cloud: Account with ECS access
   - AWS: Account with EC2 access

3. **SSH Access**
   - SSH key pair for each cloud provider
   - Terminal access to local machine

4. **Git Repository Access**
   - GitHub account
   - Access to wildhash/AlphaGenesis repository
   - Configured SSH keys or personal access tokens

### System Requirements (Per Instance)

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| vCPUs | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Storage | 20 GB | 50 GB SSD |
| Network | 1 Gbps | 5 Gbps |
| OS | Ubuntu 20.04 | Ubuntu 22.04 LTS |

---

## 🔵 GCP Test Deployment

### Step 1: Create GCP VM Instance

```bash
# Using gcloud CLI
gcloud compute instances create alphagenesis-test \
  --project=gemiadvan \
  --zone=us-central1-a \
  --machine-type=e2-standard-4 \
  --network-interface=network-tier=PREMIUM,subnet=default \
  --maintenance-policy=MIGRATE \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --boot-disk-type=pd-balanced \
  --tags=http-server,https-server
```

### Step 2: SSH into Instance

```bash
gcloud compute ssh alphagenesis-test --zone=us-central1-a
```

### Step 3: Run Automated Setup

```bash
# Clone repository
cd /opt
sudo mkdir -p AlphaGenesis
sudo chown $USER:$USER AlphaGenesis
cd AlphaGenesis
git clone https://github.com/wildhash/AlphaGenesis.git .

# Checkout the clean production branch
git checkout finals/alpha-genesis-clean

# Run setup script
sudo bash deploy/setup_gcp_test.sh
```

### Step 4: Configure Environment

```bash
# Edit .env file
sudo nano /opt/AlphaGenesis/.env

# Add your WEEX credentials:
# WEEX_API_KEY=your_key_here
# WEEX_API_SECRET=your_secret_here
# WEEX_API_PASSPHRASE=your_passphrase_here
# WEEX_BASE_URL=https://api-contract.weex.com
```

### Step 5: Start Trading System

```bash
# Start service
sudo systemctl start sdm-trading.service

# Check status
sudo systemctl status sdm-trading.service

# View logs
sudo journalctl -u sdm-trading.service -f
```

---

## 🟠 Alibaba Cloud Production

### Step 1: Create Alibaba Cloud ECS Instance

**Via Console:**
1. Login to Alibaba Cloud Console
2. Navigate to ECS → Instances
3. Click "Create Instance"
4. Select:
   - Region: Hong Kong (closer to WEEX servers)
   - Instance Type: ecs.c6.xlarge (4 vCPU, 8 GB RAM)
   - Image: Ubuntu 22.04 64-bit
   - System Disk: 50 GB SSD
   - Network: VPC with public IP
   - Security Group: Allow ports 22, 80, 443

**Via CLI:**
```bash
# Using Alibaba Cloud CLI
aliyun ecs CreateInstance \
  --RegionId cn-hongkong \
  --ImageId ubuntu_22_04_x64_20G_alibase \
  --InstanceType ecs.c6.xlarge \
  --SecurityGroupId sg-xxx \
  --VSwitchId vsw-xxx \
  --InstanceName alphagenesis-prod-alibaba \
  --InternetMaxBandwidthOut 100
```

### Step 2: Configure Security Group

```bash
# Allow SSH
aliyun ecs AuthorizeSecurityGroup \
  --SecurityGroupId sg-xxx \
  --IpProtocol tcp \
  --PortRange 22/22 \
  --SourceCidrIp 0.0.0.0/0

# Allow HTTPS for API access
aliyun ecs AuthorizeSecurityGroup \
  --SecurityGroupId sg-xxx \
  --IpProtocol tcp \
  --PortRange 443/443 \
  --SourceCidrIp 0.0.0.0/0
```

### Step 3: SSH and Setup

```bash
# SSH to instance
ssh root@<alibaba-instance-ip>

# Run setup script
bash <(curl -s https://raw.githubusercontent.com/wildhash/AlphaGenesis/finals/alpha-genesis-clean/deploy/setup_alibaba_cloud.sh)
```

### Step 4: Configure Trading System

```bash
# Navigate to project
cd /opt/AlphaGenesis

# Configure environment
nano .env

# Production settings for Alibaba Cloud
WEEX_API_KEY=your_production_key
WEEX_API_SECRET=your_production_secret
WEEX_API_PASSPHRASE=your_production_passphrase
WEEX_BASE_URL=https://api-contract.weex.com

# Trading config
INITIAL_CAPITAL=10000.0
UPDATE_INTERVAL=60
ENABLE_LIVE_TRADING=true
MAX_LEVERAGE=10

# Environment tag
DEPLOYMENT_ENV=alibaba-cloud-production
REGION=cn-hongkong
```

### Step 5: Start Production System

```bash
# Start service
systemctl start sdm-trading.service

# Enable auto-start on boot
systemctl enable sdm-trading.service

# Monitor
journalctl -u sdm-trading.service -f
```

---

## 🟢 AWS Singapore Production

### Step 1: Launch EC2 Instance

**Via AWS Console:**
1. Open EC2 Dashboard
2. Click "Launch Instance"
3. Configure:
   - Name: alphagenesis-prod-aws-sg
   - AMI: Ubuntu Server 22.04 LTS
   - Instance type: c6i.xlarge (4 vCPU, 8 GB RAM)
   - Key pair: Create or select existing
   - Network: Default VPC
   - Storage: 50 GB gp3
   - Security group: Allow SSH (22), HTTPS (443)

**Via AWS CLI:**
```bash
# Create instance
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type c6i.xlarge \
  --key-name alphagenesis-key \
  --security-group-ids sg-xxx \
  --subnet-id subnet-xxx \
  --region ap-southeast-1 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=alphagenesis-prod-aws}]' \
  --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=50,VolumeType=gp3}'
```

### Step 2: Configure Security Group

```bash
# Allow SSH
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxx \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0 \
  --region ap-southeast-1

# Allow HTTPS
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxx \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0 \
  --region ap-southeast-1
```

### Step 3: SSH and Deploy

```bash
# SSH to instance
ssh -i alphagenesis-key.pem ubuntu@<aws-instance-public-ip>

# Run automated setup
bash <(curl -s https://raw.githubusercontent.com/wildhash/AlphaGenesis/finals/alpha-genesis-clean/deploy/setup_aws_singapore.sh)
```

### Step 4: Configure Environment

```bash
# Navigate to project
cd /opt/AlphaGenesis

# Edit configuration
nano .env

# AWS Singapore production settings
WEEX_API_KEY=your_production_key
WEEX_API_SECRET=your_production_secret
WEEX_API_PASSPHRASE=your_production_passphrase
WEEX_BASE_URL=https://api-contract.weex.com

# Trading config
INITIAL_CAPITAL=10000.0
UPDATE_INTERVAL=60
ENABLE_LIVE_TRADING=true
MAX_LEVERAGE=10

# Environment tag
DEPLOYMENT_ENV=aws-singapore-production
REGION=ap-southeast-1
```

### Step 5: Launch System

```bash
# Start service
sudo systemctl start sdm-trading.service

# Enable on boot
sudo systemctl enable sdm-trading.service

# Monitor logs
sudo journalctl -u sdm-trading.service -f
```

---

## 📊 Monitoring & Management

### Health Check Script

Create a unified monitoring script:

```bash
# Save as monitor_all_deployments.sh
#!/bin/bash

echo "=== Multi-Cloud Trading System Status ==="
echo ""

# GCP Test
echo "🔵 GCP Test Environment:"
gcloud compute ssh alphagenesis-test --zone=us-central1-a --command="systemctl status sdm-trading.service | head -10"
echo ""

# Alibaba Cloud
echo "🟠 Alibaba Cloud Production:"
ssh root@<alibaba-ip> "systemctl status sdm-trading.service | head -10"
echo ""

# AWS Singapore
echo "🟢 AWS Singapore Production:"
ssh -i alphagenesis-key.pem ubuntu@<aws-ip> "systemctl status sdm-trading.service | head -10"
echo ""

echo "=== Check complete ==="
```

### Performance Monitoring

```bash
# On each instance, run:
python3 /opt/AlphaGenesis/scripts/check_weex_account.py
```

### Log Aggregation

Set up centralized logging (optional):

```bash
# Install filebeat on each instance
curl -L -O https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-8.0.0-amd64.deb
sudo dpkg -i filebeat-8.0.0-amd64.deb

# Configure to send logs to your ELK stack
sudo nano /etc/filebeat/filebeat.yml
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check logs for errors
journalctl -u sdm-trading.service -n 100 --no-pager

# Check dependencies
pip3 list | grep -E 'numpy|pandas|loguru'

# Reinstall if needed
pip3 install --upgrade numpy pandas loguru python-dotenv
```

#### 2. API Connection Issues

```bash
# Test WEEX API connectivity
curl -v https://api-contract.weex.com/api/v1/public/time

# Check credentials in .env
cat /opt/AlphaGenesis/.env | grep WEEX_

# Verify firewall allows HTTPS
sudo iptables -L | grep 443
```

#### 3. High Memory Usage

```bash
# Check memory
free -h

# Restart service if needed
systemctl restart sdm-trading.service

# Adjust memory limits in service file
sudo nano /etc/systemd/system/sdm-trading.service
# Set: MemoryLimit=4G
```

#### 4. Instance Stopped/Crashed

**GCP:**
```bash
gcloud compute instances start alphagenesis-test --zone=us-central1-a
```

**Alibaba Cloud:**
```bash
aliyun ecs StartInstance --InstanceId i-xxx
```

**AWS:**
```bash
aws ec2 start-instances --instance-ids i-xxx --region ap-southeast-1
```

### Emergency Commands

```bash
# Stop all trading immediately
for host in gcp-ip alibaba-ip aws-ip; do
  ssh $host "systemctl stop sdm-trading.service"
done

# Close all positions
python3 /opt/AlphaGenesis/scripts/close_all_positions.py

# Check account balance
python3 /opt/AlphaGenesis/scripts/check_weex_account.py
```

---

## 📱 Access Information

### GCP Test
- **Console**: https://console.cloud.google.com
- **Project ID**: gemiadvan
- **SSH**: `gcloud compute ssh alphagenesis-test --zone=us-central1-a`

### Alibaba Cloud Production
- **Console**: https://ecs.console.aliyun.com
- **Region**: Hong Kong (cn-hongkong)
- **SSH**: `ssh root@<instance-ip>`

### AWS Singapore Production
- **Console**: https://ap-southeast-1.console.aws.amazon.com/ec2
- **Region**: Singapore (ap-southeast-1)
- **SSH**: `ssh -i key.pem ubuntu@<instance-ip>`

---

## 🚀 Quick Reference Commands

### All Platforms

```bash
# Start trading
systemctl start sdm-trading.service

# Stop trading
systemctl stop sdm-trading.service

# Restart
systemctl restart sdm-trading.service

# View logs
journalctl -u sdm-trading.service -f

# Check status
systemctl status sdm-trading.service

# Check account
python3 scripts/check_weex_account.py

# Close all positions
python3 scripts/close_all_positions.py
```

---

## 📝 Deployment Checklist

### Pre-Deployment
- [ ] WEEX API credentials ready
- [ ] Cloud provider accounts configured
- [ ] SSH keys generated and added
- [ ] Repository access confirmed
- [ ] Firewall rules reviewed

### GCP Test
- [ ] VM instance created
- [ ] SSH access verified
- [ ] Dependencies installed
- [ ] .env configured
- [ ] Service started
- [ ] Logs showing activity

### Alibaba Cloud Production
- [ ] ECS instance created
- [ ] Security group configured
- [ ] SSH access verified
- [ ] Production .env configured
- [ ] Service enabled on boot
- [ ] Monitoring active

### AWS Singapore Production
- [ ] EC2 instance launched
- [ ] Security group rules set
- [ ] SSH key working
- [ ] Production .env configured
- [ ] Service enabled on boot
- [ ] CloudWatch monitoring set up

---

## 🎯 Next Steps

1. **Test Environment First**: Verify everything works on GCP test
2. **Deploy to Alibaba**: Primary production deployment
3. **Deploy to AWS**: Secondary/backup deployment
4. **Set Up Monitoring**: Ensure you can monitor all instances
5. **Test Failover**: Verify you can switch between deployments
6. **Document**: Keep notes on your specific configurations

---

## 📞 Support

- **Repository**: https://github.com/wildhash/AlphaGenesis
- **Issues**: https://github.com/wildhash/AlphaGenesis/issues
- **Documentation**: See /deploy directory for detailed guides

---

**Built for WEEX AI Wars Hackathon** 🏆

*Remember: Always test in the test environment first before deploying to production!*
