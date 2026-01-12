# GCP Browser Console Setup Guide
## Using Google Cloud Console (No SSH Client Needed!)

This guide shows you how to deploy the SDM Trading System using **only your web browser** - no terminal or SSH client required!

---

## 🌐 **Access Your GCP Instance via Browser**

### **Step 1: Open GCP Console**

1. Go to: https://console.cloud.google.com
2. Sign in with your Google account
3. Select your project

### **Step 2: Navigate to Your VM Instance**

1. Click the **hamburger menu** (☰) in top-left
2. Go to **Compute Engine** → **VM instances**
3. Find your instance with IP **34.133.16.230**

### **Step 3: Open SSH in Browser**

Click the **SSH** button next to your instance

![SSH Button](https://cloud.google.com/compute/images/ssh-button.png)

A new browser window will open with a terminal!

**That's it! You're now connected to your GCP instance.**

---

## 🚀 **Complete Setup (Browser Console)**

Now that you're in the GCP browser console, follow these steps:

### **Step 1: Download the Setup Script**

```bash
# Create directory
mkdir -p /opt/AlphaGenesis
cd /opt/AlphaGenesis

# Download the repository
git clone https://github.com/wildhash/AlphaGenesis.git .
git checkout claude/weex-trading-system-JjDSY
```

### **Step 2: Run the Setup Script**

```bash
# Make script executable
chmod +x deploy/setup_gcp_instance.sh

# Run setup
bash deploy/setup_gcp_instance.sh
```

This will:
- Install all dependencies
- Set up Python and Poetry
- Create the service user
- Configure systemd service
- Create monitoring tools

**Wait for it to complete** (takes 3-5 minutes)

### **Step 3: Configure API Credentials**

```bash
# Edit the .env file
nano /opt/AlphaGenesis/.env
```

You'll see a file like this:
```env
# WEEX API Configuration
WEEX_API_KEY=your_api_key_here
WEEX_API_SECRET=your_api_secret_here
WEEX_API_PASSPHRASE=your_passphrase_here
WEEX_BASE_URL=https://api-contract.weex.com

# Trading Configuration
INITIAL_CAPITAL=1000.0
UPDATE_INTERVAL=300

# Model Configuration
MODEL_DEVICE=cpu

# Risk Management
MAX_LEVERAGE=20

# Logging
LOG_LEVEL=INFO

# Feature Flags
ENABLE_LIVE_TRADING=true
```

**Replace the placeholder values** with your actual WEEX API credentials:
- Change `your_api_key_here` to your actual API key
- Change `your_api_secret_here` to your actual secret
- Change `your_passphrase_here` to your actual passphrase

**Save and exit:**
- Press `Ctrl+X`
- Press `Y` to confirm
- Press `Enter` to save

### **Step 4: Start the Trading System**

```bash
# Start the service
systemctl start sdm-trading.service

# Check if it's running
systemctl status sdm-trading.service
```

You should see:
```
● sdm-trading.service - SDM Trading System for WEEX AI Wars
   Loaded: loaded (/etc/systemd/system/sdm-trading.service; enabled)
   Active: active (running) since ...
```

If you see **"active (running)"** - **SUCCESS!** ✅

### **Step 5: View the Logs**

```bash
# View live logs (press Ctrl+C to stop)
journalctl -u sdm-trading.service -f
```

You should see:
```
=====================================================================
           SEMANTIC DATAFLOW MACHINE TRADING SYSTEM
                   WEEX AI Wars: Alpha Awakens
=====================================================================

SDM TRADING ENGINE INITIALIZED
Intent Graph: Active with trading intents
Semantic Binding: Model registry initialized
...
```

---

## 📊 **Monitor Your System (Browser Console)**

Keep the GCP browser console open and use these commands:

### **Check Status**
```bash
systemctl status sdm-trading.service
```

### **View Live Logs**
```bash
journalctl -u sdm-trading.service -f
```
*(Press Ctrl+C to stop viewing)*

### **View Last 50 Log Lines**
```bash
journalctl -u sdm-trading.service -n 50
```

### **Check for Trades**
```bash
journalctl -u sdm-trading.service | grep "EXECUTING ACTION"
```

### **Run Health Check**
```bash
bash /opt/AlphaGenesis/monitor.sh
```

### **View Reports**
```bash
ls -lh /opt/AlphaGenesis/reports/sdm/
```

---

## 🎮 **Control Commands (Browser Console)**

### **Stop Trading**
```bash
systemctl stop sdm-trading.service
```

### **Start Trading**
```bash
systemctl start sdm-trading.service
```

### **Restart**
```bash
systemctl restart sdm-trading.service
```

### **View Configuration**
```bash
cat /opt/AlphaGenesis/.env
```

### **Edit Configuration**
```bash
nano /opt/AlphaGenesis/.env
# Make changes
# Press Ctrl+X, Y, Enter to save
# Then restart: systemctl restart sdm-trading.service
```

---

## 📁 **Using the File Editor (Alternative to nano)**

GCP Console also has a **built-in code editor**!

### **Open Cloud Shell Editor**

1. In the GCP Console, click the **pencil icon** (✏️) in the top-right
2. Or go to: https://ssh.cloud.google.com/cloudshell/editor
3. Navigate to: `/opt/AlphaGenesis/.env`
4. Edit visually (like VS Code)
5. Save with `Ctrl+S`

This is easier than using `nano` if you're not familiar with terminal editors!

---

## 🔄 **Keep Browser Console Open**

The GCP browser SSH session will:
- ✅ Stay connected for hours
- ✅ Auto-reconnect if disconnected
- ✅ Work from any computer
- ✅ No SSH keys needed

**Tip:** Keep the browser tab open to monitor your system during the competition!

---

## 📱 **Access from Multiple Locations**

You can open the GCP Console from:
- 🖥️ Your desktop
- 💻 Your laptop
- 📱 Your phone (GCP has a mobile app!)
- 🌐 Any computer with internet

Just go to: https://console.cloud.google.com

---

## 🚨 **Troubleshooting (Browser Console)**

### **SSH Button is Grayed Out**

1. Make sure the VM is **running** (green checkmark)
2. If stopped, click the **Start** button
3. Wait 30 seconds for it to boot
4. Try SSH again

### **Can't See VM Instance**

1. Make sure you selected the correct **project** (top of page)
2. Check you're in the right **region**
3. The IP should be **34.133.16.230**

### **Service Won't Start**

```bash
# Check what went wrong
journalctl -u sdm-trading.service -n 100

# Common fix: Install dependencies manually
pip3 install numpy pandas loguru python-dotenv requests scikit-learn

# Then restart
systemctl restart sdm-trading.service
```

### **Connection Timeout**

If the browser console disconnects:
1. It will try to auto-reconnect
2. Or just click **SSH** button again
3. All your setup is still there!

---

## 📋 **Quick Start Checklist (Browser Method)**

- [ ] 1. Open https://console.cloud.google.com
- [ ] 2. Go to Compute Engine → VM instances
- [ ] 3. Click **SSH** button for your instance (34.133.16.230)
- [ ] 4. Run: `cd /opt && git clone https://github.com/wildhash/AlphaGenesis.git && cd AlphaGenesis && git checkout claude/weex-trading-system-JjDSY`
- [ ] 5. Run: `bash deploy/setup_gcp_instance.sh`
- [ ] 6. Edit: `nano /opt/AlphaGenesis/.env` (add your API credentials)
- [ ] 7. Start: `systemctl start sdm-trading.service`
- [ ] 8. Check: `systemctl status sdm-trading.service`
- [ ] 9. Monitor: `journalctl -u sdm-trading.service -f`

---

## 🎯 **Complete Copy-Paste Script**

If you want to do it all at once, copy and paste this entire block:

```bash
# 1. Setup
cd /opt
mkdir -p AlphaGenesis
cd AlphaGenesis
git clone https://github.com/wildhash/AlphaGenesis.git .
git checkout claude/weex-trading-system-JjDSY

# 2. Run setup script
chmod +x deploy/setup_gcp_instance.sh
bash deploy/setup_gcp_instance.sh

# 3. Now edit .env with your credentials
echo ""
echo "======================================================================="
echo "IMPORTANT: Now edit .env with your WEEX API credentials"
echo "======================================================================="
echo ""
echo "Run this command:"
echo "  nano /opt/AlphaGenesis/.env"
echo ""
echo "Replace:"
echo "  - your_api_key_here → your actual API key"
echo "  - your_api_secret_here → your actual secret"
echo "  - your_passphrase_here → your actual passphrase"
echo ""
echo "Save with: Ctrl+X, Y, Enter"
echo ""
echo "Then start the service:"
echo "  systemctl start sdm-trading.service"
echo "  systemctl status sdm-trading.service"
echo ""
echo "======================================================================="
```

Then manually:
1. Edit `.env`: `nano /opt/AlphaGenesis/.env`
2. Add your credentials
3. Save (Ctrl+X, Y, Enter)
4. Start: `systemctl start sdm-trading.service`
5. Check: `systemctl status sdm-trading.service`

---

## 💡 **Tips for Browser Console**

### **Copy/Paste**

- **Copy** from browser console: Select text, `Ctrl+C`
- **Paste** into browser console: `Ctrl+V` or `Shift+Insert`

### **Multiple Tabs**

You can open **multiple SSH sessions**:
1. Open GCP Console in multiple tabs
2. Click SSH in each tab
3. Monitor logs in one, run commands in another!

### **Upload Files**

To upload files directly:
1. Click the **⚙️ gear icon** in top-right of SSH window
2. Select **Upload file**
3. Choose your `.env` file
4. It uploads to your home directory
5. Move it: `mv ~/.env /opt/AlphaGenesis/.env`

---

## 🎬 **Video Guide (If Available)**

Google has official guides:
- [Connecting to VMs](https://cloud.google.com/compute/docs/instances/connecting-to-instance)
- [Using SSH in Browser](https://cloud.google.com/compute/docs/ssh-in-browser)

---

## 📞 **Quick Help**

**Browser console not loading?**
- Try a different browser (Chrome works best)
- Disable browser extensions
- Check pop-up blocker settings

**Need to exit?**
- Just close the browser tab
- Or type: `exit`

**Come back later?**
- Just open GCP Console again
- Click SSH button
- You're back in!

---

## ✅ **You're Ready!**

Using the GCP browser console is **the easiest method**:
- ✅ No SSH client needed
- ✅ No SSH keys to manage
- ✅ Works from anywhere
- ✅ Built-in file editor
- ✅ Auto-reconnect

**Start here:** https://console.cloud.google.com

**The competition starts TODAY at 8 PM UTC+8!** ⏰

---

**Good luck! 🚀**
