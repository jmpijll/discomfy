# Installation Guide

Complete installation instructions for DisComfy v2.0.

---

## 📋 Prerequisites

Before installing DisComfy, ensure you have:

### Required
- **Python 3.8 or higher** (for standard installation)
- **Docker** (for Docker installation)
- **Discord Bot Token** from Discord Developer Portal
- **ComfyUI instance** running (local or remote)

### Recommended
- Python 3.10+
- 8GB+ RAM
- SSD storage
- GPU-enabled ComfyUI instance

---

## 🐍 Standard Installation (Python)

### Step 1: Install Python

**Linux/Mac:**
```bash
# Check Python version
python3 --version

# Should be 3.8 or higher
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/)
- Check "Add Python to PATH" during installation

### Step 2: Clone Repository

```bash
git clone https://github.com/jmpijll/discomfy.git
cd discomfy
```

### Step 3: Create Virtual Environment

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies installed:**
- discord.py 2.x
- aiohttp
- pydantic 2.x
- pytest (for testing)
- Other required packages

### Step 5: Configure Bot

```bash
# Copy example configuration
cp config.example.json config.json

# Edit configuration
nano config.json  # or use your preferred editor
```

**Minimal config.json:**
```json
{
  "discord": {
    "token": "YOUR_DISCORD_BOT_TOKEN",
    "guild_id": "YOUR_SERVER_ID"
  },
  "comfyui": {
    "url": "http://localhost:8188",
    "timeout": 300
  },
  "generation": {
    "default_workflow": "flux_lora",
    "max_batch_size": 4,
    "output_limit": 100
  }
}
```

See **[[Configuration Guide]]** for all options.

### Step 6: Set Up Discord Bot

#### Create Bot
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application**
3. Name: "DisComfy" (or your preferred name)
4. Go to **Bot** section
5. Click **Add Bot**
6. Under **Privileged Gateway Intents**, enable:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
7. Click **Copy** under Token section
8. Paste token into `config.json`

#### Invite Bot to Server
1. In Developer Portal, go to **OAuth2** → **URL Generator**
2. Select scopes:
   - `bot`
   - `applications.commands`
3. Select bot permissions:
   - Send Messages
   - Use Slash Commands
   - Attach Files
   - Embed Links
   - Read Message History
   - Use External Emojis
4. Copy generated URL
5. Open in browser and invite to your server

**Or use this template:**
```
https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=277025508416&scope=bot%20applications.commands
```
Replace `YOUR_CLIENT_ID` with your Application ID.

### Step 7: Prepare ComfyUI

#### Verify ComfyUI is Running
```bash
curl http://localhost:8188/system_stats
```

Should return JSON with system information.

#### Add Workflow Files

Place workflow JSON files in `workflows/` directory:
- `flux_lora.json`
- `flux_krea_lora.json`
- `hidream_lora.json`
- `flux_kontext_edit.json`
- `qwen_image_edit.json`
- `upscale_config-1.json`
- `video_wan_vace_14B_i2v.json`

See **[[Custom Workflows]]** for creating your own.

### Step 8: Run Bot

```bash
python main.py
```

**Expected output:**
```
🤖 Bot is starting up...
✅ Connected to Discord as DisComfy#0430
🎨 ComfyUI connection verified
🚀 Bot is ready! Use /generate to start creating!
```

### Step 9: Test in Discord

```
/generate prompt:test image
```

If successful, you'll see the interactive setup view!

---

## 🐳 Docker Installation

DisComfy is available as pre-built Docker images from both GitHub Container Registry and Docker Hub.

### Option 1: Using Pre-built Image (Recommended)

#### From GitHub Container Registry

```bash
# Pull latest image
docker pull ghcr.io/jmpijll/discomfy:latest

# Or specific version
docker pull ghcr.io/jmpijll/discomfy:v2.0.0
```

#### From Docker Hub

```bash
# Pull latest image
docker pull jamiehakker/discomfy:latest

# Or specific version
docker pull jamiehakker/discomfy:v2.0.0
```

### Option 2: Quick Start with Environment Variables

**Simplest method - no config file needed:**

```bash
docker run -d \
  --name discomfy \
  -e DISCORD_TOKEN=your_discord_token \
  -e COMFYUI_URL=http://your-comfyui-url:8188 \
  -e DISCORD_GUILD_ID=your_server_id \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  ghcr.io/jmpijll/discomfy:latest
```

### Option 3: Using Config File

**For more control:**

```bash
# Create config directory
mkdir -p discomfy-data/workflows

# Create config.json
cat > discomfy-data/config.json << 'EOF'
{
  "discord": {
    "token": "YOUR_DISCORD_BOT_TOKEN",
    "guild_id": "YOUR_SERVER_ID"
  },
  "comfyui": {
    "url": "http://YOUR_COMFYUI_URL:8188",
    "timeout": 300
  }
}
EOF

# Run with config mount
docker run -d \
  --name discomfy \
  -v $(pwd)/discomfy-data/config.json:/app/config.json:ro \
  -v $(pwd)/discomfy-data/workflows:/app/workflows:ro \
  -v $(pwd)/discomfy-data/outputs:/app/outputs \
  -v $(pwd)/discomfy-data/logs:/app/logs \
  --restart unless-stopped \
  ghcr.io/jmpijll/discomfy:latest
```

### Option 4: Docker Compose (Recommended for Production)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  discomfy:
    image: ghcr.io/jmpijll/discomfy:latest
    # Or use: jamiehakker/discomfy:latest
    container_name: discomfy
    restart: unless-stopped
    
    # Option A: Environment variables (simpler)
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - COMFYUI_URL=${COMFYUI_URL:-http://localhost:8188}
      - DISCORD_GUILD_ID=${DISCORD_GUILD_ID}
    
    # Option B: Config file (more options)
    volumes:
      - ./config.json:/app/config.json:ro
      - ./workflows:/app/workflows:ro
      - ./outputs:/app/outputs
      - ./logs:/app/logs
    
    # If ComfyUI is in another container
    # depends_on:
    #   - comfyui
    
    # Network configuration
    networks:
      - discomfy-network

networks:
  discomfy-network:
    driver: bridge
```

Create `.env` file:
```bash
DISCORD_TOKEN=your_discord_token
COMFYUI_URL=http://localhost:8188
DISCORD_GUILD_ID=your_server_id
```

Run:
```bash
docker-compose up -d
```

### Docker Management

**View logs:**
```bash
docker logs discomfy -f
```

**Stop container:**
```bash
docker stop discomfy
```

**Start container:**
```bash
docker start discomfy
```

**Restart container:**
```bash
docker restart discomfy
```

**Remove container:**
```bash
docker stop discomfy
docker rm discomfy
```

**Update to latest:**
```bash
docker pull ghcr.io/jmpijll/discomfy:latest
docker stop discomfy
docker rm discomfy
# Then run container again with same command
```

### Building from Source (Optional)

```bash
# Clone repository
git clone https://github.com/jmpijll/discomfy.git
cd discomfy

# Build image
docker build -t discomfy:local .

# Run
docker run -d \
  --name discomfy \
  -e DISCORD_TOKEN=your_token \
  -e COMFYUI_URL=http://localhost:8188 \
  discomfy:local
```

---

## 🖥️ Unraid Installation

Complete guide for deploying DisComfy on Unraid.

### Method 1: Using Community Applications (Coming Soon)

DisComfy will be available in Unraid Community Applications.

### Method 2: Manual Docker Setup

#### Step 1: Add Container

1. Open Unraid web interface
2. Go to **Docker** tab
3. Click **Add Container**
4. Fill in details below

#### Step 2: Basic Configuration

**Repository:**
```
ghcr.io/jmpijll/discomfy:latest
```
Or use:
```
jamiehakker/discomfy:latest
```

**Name:**
```
discomfy
```

**Network Type:**
```
Bridge
```

**Console Shell Command:**
```
Bash
```

#### Step 3: Environment Variables

Add these variables:

| Key | Value | Description |
|-----|-------|-------------|
| `DISCORD_TOKEN` | your_token | Your Discord bot token |
| `COMFYUI_URL` | http://192.168.1.100:8188 | Your ComfyUI URL |
| `DISCORD_GUILD_ID` | your_guild_id | Optional: Your server ID |

**Important:** Replace IP address with your actual ComfyUI server IP.

#### Step 4: Volume Mappings

Add these paths:

| Container Path | Host Path | Access Mode |
|---------------|-----------|-------------|
| `/app/outputs` | `/mnt/user/appdata/discomfy/outputs` | Read/Write |
| `/app/logs` | `/mnt/user/appdata/discomfy/logs` | Read/Write |
| `/app/config.json` | `/mnt/user/appdata/discomfy/config.json` | Read Only |
| `/app/workflows` | `/mnt/user/appdata/discomfy/workflows` | Read Only |

#### Step 5: Apply Configuration

1. Click **Apply**
2. Container will download and start automatically
3. Check logs for success message

#### Step 6: Verify Installation

**Check logs:**
1. Click on **discomfy** container
2. Click **Logs**
3. Look for: `✅ Connected to Discord as DisComfy#XXXX`

### Unraid Template

```xml
<?xml version="1.0"?>
<Container version="2">
  <Name>discomfy</Name>
  <Repository>ghcr.io/jmpijll/discomfy:latest</Repository>
  <Registry>https://ghcr.io</Registry>
  <Network>bridge</Network>
  <Shell>bash</Shell>
  
  <Config Name="Discord Token" Target="DISCORD_TOKEN" Default="" Mode="" Description="Your Discord bot token" Type="Variable" Display="always" Required="true" Mask="true"/>
  
  <Config Name="ComfyUI URL" Target="COMFYUI_URL" Default="http://localhost:8188" Mode="" Description="URL to your ComfyUI instance" Type="Variable" Display="always" Required="true" Mask="false"/>
  
  <Config Name="Guild ID" Target="DISCORD_GUILD_ID" Default="" Mode="" Description="Optional: Your Discord server ID" Type="Variable" Display="always" Required="false" Mask="false"/>
  
  <Config Name="Outputs" Target="/app/outputs" Default="/mnt/user/appdata/discomfy/outputs" Mode="rw" Description="Generated images/videos" Type="Path" Display="always" Required="true" Mask="false"/>
  
  <Config Name="Logs" Target="/app/logs" Default="/mnt/user/appdata/discomfy/logs" Mode="rw" Description="Bot logs" Type="Path" Display="always" Required="true" Mask="false"/>
  
  <Config Name="Config File" Target="/app/config.json" Default="/mnt/user/appdata/discomfy/config.json" Mode="ro" Description="Optional: Custom config file" Type="Path" Display="advanced" Required="false" Mask="false"/>
  
  <Config Name="Workflows" Target="/app/workflows" Default="/mnt/user/appdata/discomfy/workflows" Mode="ro" Description="Optional: Custom workflows" Type="Path" Display="advanced" Required="false" Mask="false"/>
</Container>
```

### Unraid Troubleshooting

**Container won't start:**
1. Check logs for error message
2. Verify `DISCORD_TOKEN` is set correctly
3. Ensure ComfyUI URL is accessible from Unraid

**Permission errors:**
```bash
# SSH into Unraid
chmod -R 755 /mnt/user/appdata/discomfy
```

**Network issues:**
- Use IP address instead of `localhost`
- Verify ComfyUI is accessible: `curl http://192.168.1.100:8188/system_stats`
- Check firewall settings

---

## ⚙️ Post-Installation

### Verify Installation

#### Check Bot Status
In Discord:
```
/status
```

Should show:
- ✅ Bot online
- ✅ ComfyUI connected

#### Test Generation
```
/generate prompt:test
```

Should show interactive setup view.

### Configure Startup

#### Linux Service (systemd)

Create `/etc/systemd/system/discomfy.service`:

```ini
[Unit]
Description=DisComfy Discord Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/discomfy
Environment="PATH=/path/to/discomfy/venv/bin"
ExecStart=/path/to/discomfy/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable discomfy
sudo systemctl start discomfy
sudo systemctl status discomfy
```

#### macOS LaunchAgent

Create `~/Library/LaunchAgents/com.discomfy.bot.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.discomfy.bot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/discomfy/venv/bin/python</string>
        <string>/path/to/discomfy/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/discomfy</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load:
```bash
launchctl load ~/Library/LaunchAgents/com.discomfy.bot.plist
```

#### Windows Service

Use [NSSM](https://nssm.cc/):
```cmd
nssm install DisComfy "C:\path\to\discomfy\venv\Scripts\python.exe" "C:\path\to\discomfy\main.py"
nssm start DisComfy
```

### Update Bot

#### Standard Installation
```bash
cd discomfy
git pull
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt --upgrade
python main.py
```

#### Docker
```bash
docker pull ghcr.io/jmpijll/discomfy:latest
docker stop discomfy
docker rm discomfy
# Run container again with same command
```

#### Unraid
1. Go to Docker tab
2. Click on discomfy
3. Click **Force Update**
4. Click **Apply**

---

## 🔒 Security Best Practices

### Protect Bot Token
- Never commit `config.json` to git
- Use environment variables in production
- Rotate token if exposed

### File Permissions
```bash
# Secure config file
chmod 600 config.json

# Secure logs directory
chmod 700 logs/
```

### Network Security
- Use HTTPS for remote ComfyUI if possible
- Consider VPN for remote access
- Implement firewall rules

---

## 📊 Performance Optimization

### System Resources
- **CPU:** 2+ cores recommended
- **RAM:** 4GB minimum, 8GB recommended
- **Storage:** SSD for outputs directory
- **Network:** Stable connection to ComfyUI

### Configuration Tuning
```json
{
  "generation": {
    "max_batch_size": 2,  // Lower if low memory
    "output_limit": 50    // Clean up more frequently
  },
  "comfyui": {
    "timeout": 600        // Increase for complex workflows
  }
}
```

---

## ✅ Installation Checklist

- [ ] Python 3.8+ installed (or Docker)
- [ ] Repository cloned
- [ ] Virtual environment created and activated
- [ ] Dependencies installed
- [ ] Discord bot created and token obtained
- [ ] Bot invited to server with correct permissions
- [ ] ComfyUI running and accessible
- [ ] Workflow files in place
- [ ] Configuration file created and edited
- [ ] Bot started successfully
- [ ] Commands visible in Discord
- [ ] Test generation successful

---

## 🆘 Installation Troubleshooting

See **[[Troubleshooting]]** for detailed solutions.

**Quick fixes:**

**ModuleNotFoundError:**
```bash
pip install -r requirements.txt
```

**Permission denied:**
```bash
chmod +x main.py
```

**Port already in use (Docker):**
```bash
docker ps  # Check conflicting containers
```

---

**✅ Installation complete! Check out [[Getting Started]] for your first generation!**
