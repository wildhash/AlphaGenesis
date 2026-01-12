# ⚡ EASIEST SETUP - GCP Browser Console (5 Minutes)

**No SSH client. No terminal. Just your web browser!**

---

## 🎯 **3 Simple Steps**

### **STEP 1: Open GCP Console & Connect** (1 minute)

1. Go to: **https://console.cloud.google.com**
2. Click: **☰ Menu** → **Compute Engine** → **VM instances**
3. Find your VM with IP: **34.133.16.230**
4. Click the **SSH** button (opens terminal in browser)

✅ **You're now connected!**

---

### **STEP 2: Copy-Paste This Setup** (3 minutes)

In the browser terminal, **copy and paste this entire block**:

```bash
cd /opt && \
mkdir -p AlphaGenesis && \
cd AlphaGenesis && \
git clone https://github.com/wildhash/AlphaGenesis.git . && \
git checkout claude/weex-trading-system-JjDSY && \
chmod +x deploy/setup_gcp_instance.sh && \
bash deploy/setup_gcp_instance.sh
```

**Press Enter** and wait (takes 3-4 minutes)

When it finishes, you'll see:
```
======================================================================
  Setup Complete!
======================================================================
```

✅ **Installation done!**

---

### **STEP 3: Add Your API Credentials** (1 minute)

#### **3A. Edit the .env file:**

```bash
nano /opt/AlphaGenesis/.env
```

#### **3B. Replace these 3 lines:**

Find:
```env
WEEX_API_KEY=your_api_key_here
WEEX_API_SECRET=your_api_secret_here
WEEX_API_PASSPHRASE=your_passphrase_here
```

Replace with your **actual WEEX API credentials** from the hackathon.

#### **3C. Save the file:**

- Press `Ctrl+X`
- Press `Y`
- Press `Enter`

#### **3D. Start the trading system:**

```bash
systemctl start sdm-trading.service
```

#### **3E. Check it's running:**

```bash
systemctl status sdm-trading.service
```

You should see: **"active (running)"** ✅

---

## 🎉 **Done! Your Trading System is Live!**

---

## 📊 **View What It's Doing**

```bash
journalctl -u sdm-trading.service -f
```

You'll see:
```
SDM TRADING ENGINE INITIALIZED
Intent Graph: Active with trading intents
STARTING SDM TRADING ENGINE
SDM ITERATION 1 - 2026-01-12 20:05:00
Observing market...
```

**Press Ctrl+C to stop viewing logs**

---

## 🎮 **Control Your System**

### **Stop Trading:**
```bash
systemctl stop sdm-trading.service
```

### **Start Trading:**
```bash
systemctl start sdm-trading.service
```

### **Check Status:**
```bash
systemctl status sdm-trading.service
```

### **View Logs:**
```bash
journalctl -u sdm-trading.service -f
```

---

## 🔧 **If Something Goes Wrong**

### **Service won't start?**

```bash
# Check what's wrong
journalctl -u sdm-trading.service -n 50

# Fix: Install dependencies manually
pip3 install numpy pandas loguru python-dotenv requests scikit-learn

# Restart
systemctl restart sdm-trading.service
```

### **Need to change API credentials?**

```bash
# Edit .env again
nano /opt/AlphaGenesis/.env

# Save: Ctrl+X, Y, Enter

# Restart service
systemctl restart sdm-trading.service
```

### **Browser SSH disconnected?**

Just click the **SSH** button again - everything is still running!

---

## 📱 **Access Anytime**

You can access your system from:
- 🖥️ Any computer
- 📱 GCP mobile app
- 🌐 Any browser

Just go to: https://console.cloud.google.com

---

## ✅ **Checklist**

- [ ] Opened GCP Console
- [ ] Clicked SSH button
- [ ] Ran setup script (copy-paste)
- [ ] Edited .env with API credentials
- [ ] Started service: `systemctl start sdm-trading.service`
- [ ] Verified running: `systemctl status sdm-trading.service`
- [ ] Viewed logs: `journalctl -u sdm-trading.service -f`

---

## 🏆 **Competition Starts Today!**

**Jan 12, 8 PM UTC+8**

Your SDM is ready to compete! 🚀

---

## 💡 **Quick Reference Commands**

```bash
# Check status
systemctl status sdm-trading.service

# View live logs
journalctl -u sdm-trading.service -f

# Stop
systemctl stop sdm-trading.service

# Start
systemctl start sdm-trading.service

# Restart
systemctl restart sdm-trading.service

# Health check
bash /opt/AlphaGenesis/monitor.sh

# See trades
journalctl -u sdm-trading.service | grep "EXECUTING ACTION"

# View reports
ls -lh /opt/AlphaGenesis/reports/sdm/
```

---

**That's it! Simple as 1-2-3!** ✨

**Need more details?** See:
- `GCP_BROWSER_CONSOLE_SETUP.md` - Detailed browser console guide
- `MANUAL_SETUP_GUIDE.md` - Complete manual setup
- `GCP_QUICK_REFERENCE.md` - All commands

**Good luck! May your intents propagate favorably! 🚀**
