# Installation Guide 🚀

This comprehensive guide will walk you through installing and setting up DisComfy from scratch.

---

## 📋 Prerequisites

Before starting, ensure you have:

### Required
- **Python 3.8 or higher** ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/downloads))
- **Discord Account** with permissions to create bots
- **ComfyUI Instance** (local or remote)

### Recommended
- **Python 3.10+** for best compatibility
- **ComfyUI with GPU** for faster generation
- **8GB+ RAM** for smooth operation
- **SSD Storage** for faster file operations

---

## 🎯 Installation Steps

### Step 1: Install Python

#### Windows
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run installer and **check "Add Python to PATH"**
3. Verify installation:
   ```cmd
   python --version
   ```

#### Linux/Mac
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# macOS (using Homebrew)
brew install python3

# Verify installation
python3 --version
```

### Step 2: Install ComfyUI

DisComfy requires a running ComfyUI instance.

#### Option A: Local Installation
```bash
# Clone ComfyUI
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI

# Install dependencies
pip install -r requirements.txt

# Start ComfyUI
python main.py --port 8188
```

#### Option B: Use Existing ComfyUI
If you already have ComfyUI running:
1. Note the URL (e.g., `http://localhost:8188`)
2. Ensure it's accessible from where DisComfy will run
3. Test by visiting `http://your-comfyui-url/system_stats`

### Step 3: Create Discord Bot

1. **Go to Discord Developer Portal:**
   - Visit [discord.com/developers/applications](https://discord.com/developers/applications)
   - Click "New Application"
   - Name it (e.g., "DisComfy")

2. **Create Bot:**
   - Go to "Bot" section
   - Click "Add Bot"
   - Copy the **Bot Token** (save it securely!)

3. **Enable Intents:**
   - Scroll to "Privileged Gateway Intents"
   - Enable:
     - ✅ Presence Intent
     - ✅ Server Members Intent
     - ✅ Message Content Intent

4. **Generate Invite Link:**
   - Go to "OAuth2" → "URL Generator"
   - Select scopes:
     - ✅ `bot`
     - ✅ `applications.commands`
   - Select permissions:
     - ✅ Send Messages
     - ✅ Send Messages in Threads
     - ✅ Attach Files
     - ✅ Embed Links
     - ✅ Read Message History
     - ✅ Use Slash Commands
   - Copy the generated URL

5. **Invite Bot to Server:**
   - Open the generated URL
   - Select your server
   - Click "Authorize"

### Step 4: Install DisComfy

#### Clone Repository
```bash
# Clone the repository
git clone https://github.com/jmpijll/discomfy.git
cd discomfy
```

#### Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### Install Dependencies
```bash
# Install required packages
pip install -r requirements.txt
```

**Expected packages:**
- `discord.py` - Discord bot framework
- `aiohttp` - Async HTTP client
- `requests` - HTTP library
- `websockets` - WebSocket client
- `Pillow` - Image processing
- `python-dotenv` - Environment variables

### Step 5: Configure DisComfy

#### Create Configuration File
```bash
# Copy example configuration
cp config.example.json config.json

# Edit the configuration
# Windows: notepad config.json
# Linux/Mac: nano config.json
```

#### Basic Configuration
Edit `config.json` with your settings:

```json
{
  "discord": {
    "token": "YOUR_DISCORD_BOT_TOKEN_HERE",
    "guild_id": "YOUR_SERVER_ID_HERE"
  },
  "comfyui": {
    "url": "http://localhost:8188",
    "timeout": 300
  },
  "generation": {
    "default_workflow": "flux_lora",
    "max_batch_size": 4,
    "output_limit": 100
  },
  "security": {
    "max_prompt_length": 1000,
    "rate_limit_seconds": 5
  }
}
```

**Configuration Details:**
- `discord.token` - Your Discord bot token from Step 3
- `discord.guild_id` - Your Discord server ID (right-click server → Copy ID)
- `comfyui.url` - URL where ComfyUI is running
- `comfyui.timeout` - Maximum generation time (seconds)

See **[[Configuration Guide]]** for detailed configuration options.

### Step 6: Prepare Workflows

DisComfy needs ComfyUI workflow files in the `workflows/` directory.

#### Default Workflows
The repository includes several default workflows:
- `flux_lora.json` - Flux with LoRA support
- `flux_krea_lora.json` - Enhanced Flux Krea
- `hidream_lora.json` - HiDream model
- `upscale_config-1.json` - Image upscaling
- `video_wan_vace_14B_i2v.json` - Video generation
- `flux_kontext_edit.json` - Flux Kontext editing
- `qwen_image_edit.json` - Qwen fast editing (1 image)
- `qwen_image_edit_2.json` - Qwen multi-image (2 images)
- `qwen_image_edit_3.json` - Qwen multi-image (3 images)

#### Install Required Models
Ensure ComfyUI has the required models installed:

**For Flux workflows:**
- `FLUX1/flux1-dev-fp8.safetensors` - Flux model
- `FLUX1/ae.safetensors` - VAE model
- CLIP models in `long_clip/` and `t5/` directories

**For HiDream workflows:**
- HiDream checkpoint files

**For Video generation:**
- WanVace model files

See **[[Custom Workflows]]** for creating your own workflows.

### Step 7: Start the Bot

#### Launch DisComfy
```bash
# Ensure virtual environment is activated
# Then start the bot
python bot.py
```

#### Successful Startup
You should see:
```
🤖 Bot is starting up...
✅ Connected to Discord as DisComfy#0430
🎨 ComfyUI connection verified
📁 Loaded 6 workflows
🚀 Bot is ready! Use /generate to start creating!
```

#### Test the Bot
In your Discord server:
```
/generate prompt:a beautiful sunset over mountains
```

---

## 🔧 Verification Checklist

Before considering installation complete, verify:

- [ ] Python 3.8+ installed and accessible
- [ ] Git installed
- [ ] ComfyUI running and accessible
- [ ] Discord bot created and invited to server
- [ ] DisComfy repository cloned
- [ ] Virtual environment created and activated
- [ ] Dependencies installed successfully
- [ ] `config.json` configured with:
  - [ ] Valid Discord bot token
  - [ ] Correct guild ID
  - [ ] Working ComfyUI URL
- [ ] Workflow files present in `workflows/` directory
- [ ] ComfyUI has required models installed
- [ ] Bot starts without errors
- [ ] `/generate` command works

---

## 🚨 Troubleshooting Installation

### Python Not Found
```bash
# Windows: Reinstall Python and check "Add to PATH"
# Linux: Install python3 package
sudo apt install python3 python3-pip
```

### Discord Token Invalid
- Regenerate token in Discord Developer Portal
- Ensure no extra spaces in config.json
- Check token is from "Bot" section, not "OAuth2"

### ComfyUI Connection Failed
```bash
# Test ComfyUI accessibility
curl http://localhost:8188/system_stats

# Or visit in browser
http://localhost:8188
```

### Dependencies Install Failed
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Retry installation
pip install -r requirements.txt --upgrade
```

### Bot Won't Start
```bash
# Check Python version
python --version  # Must be 3.8+

# Verify config.json syntax
python -m json.tool config.json

# Check logs
tail -f logs/bot.log
```

### Module Not Found Errors
```bash
# Ensure virtual environment is activated
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## 🔄 Updating DisComfy

To update to the latest version:

```bash
# Pull latest changes
git pull origin main

# Update dependencies (if requirements changed)
pip install -r requirements.txt --upgrade

# Restart the bot
python bot.py
```

---

## 📦 Optional: Run as System Service

### Linux (systemd)

Create `/etc/systemd/system/discomfy.service`:

```ini
[Unit]
Description=DisComfy Discord Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/discomfy
Environment="PATH=/path/to/discomfy/venv/bin"
ExecStart=/path/to/discomfy/venv/bin/python /path/to/discomfy/bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable discomfy
sudo systemctl start discomfy
sudo systemctl status discomfy
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: At startup
4. Action: Start a program
   - Program: `C:\path\to\discomfy\venv\Scripts\python.exe`
   - Arguments: `C:\path\to\discomfy\bot.py`
   - Start in: `C:\path\to\discomfy`

---

## 🎯 Next Steps

After successful installation:

1. **[[Configuration Guide]]** - Customize DisComfy for your needs
2. **[[User Guide]]** - Learn how to use all features
3. **[[Custom Workflows]]** - Create custom ComfyUI workflows
4. **[[Performance Tuning]]** - Optimize for your setup

---

## 💡 Tips for Success

1. **Start Simple** - Test with basic generation first
2. **Check Logs** - Monitor `logs/bot.log` for issues
3. **Keep Updated** - Regularly pull latest changes
4. **Backup Config** - Save your `config.json` before updates
5. **Test ComfyUI** - Ensure ComfyUI works standalone first

---

**🎨 Installation complete? Start creating with [[User Guide]]!**

