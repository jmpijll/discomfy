# Getting Started with DisComfy

This guide will help you get DisComfy up and running quickly.

---

## 📋 Prerequisites

Before you begin, ensure you have:

- **Python 3.8 or higher** installed
- **ComfyUI** running (locally or remotely)
- **Discord Bot Token** from Discord Developer Portal
- **Basic command line knowledge**

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Clone the Repository

```bash
git clone https://github.com/jmpijll/discomfy.git
cd discomfy
```

### Step 2: Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure the Bot

```bash
# Copy example configuration
cp config.example.json config.json

# Edit configuration with your details
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

### Step 5: Get Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application**
3. Name your application (e.g., "DisComfy")
4. Go to **Bot** section
5. Click **Add Bot**
6. Click **Copy** under the token section
7. Paste token into `config.json`

### Step 6: Invite Bot to Your Server

Generate invite link with required permissions:

```
https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=277025508416&scope=bot%20applications.commands
```

Replace `YOUR_CLIENT_ID` with your Application ID from Discord Developer Portal.

**Required Permissions:**
- Send Messages
- Use Slash Commands
- Attach Files
- Embed Links
- Read Message History
- Use External Emojis

### Step 7: Verify ComfyUI is Running

Test ComfyUI connection:
```bash
curl http://localhost:8188/system_stats
```

If successful, you should see JSON output with system statistics.

### Step 8: Launch the Bot

```bash
python main.py
```

**Expected Output:**
```
🤖 Bot is starting up...
✅ Connected to Discord as DisComfy#0430
🎨 ComfyUI connection verified
🚀 Bot is ready! Use /generate to start creating!
```

---

## ✅ Verify Installation

### Test in Discord

1. Go to your Discord server
2. Type `/` in any channel
3. You should see DisComfy commands:
   - `/generate` - Generate AI images
   - `/editflux` - Edit images with Flux Kontext
   - `/editqwen` - Edit images with Qwen 2.5 VL
   - `/status` - Check bot status
   - `/help` - Get help
   - `/loras` - List available LoRAs

### First Generation

Try a simple generation:
```
/generate prompt:a beautiful sunset over the ocean
```

The bot will:
1. Show an interactive setup view
2. Let you choose model, LoRA, and parameters
3. Generate the image with real-time progress
4. Display the result with action buttons

---

## 🐳 Docker Quick Start

If you prefer Docker, here's a faster setup:

### Using Pre-built Image

```bash
# Pull the image
docker pull ghcr.io/jmpijll/discomfy:latest

# Create config directory
mkdir -p discomfy-data

# Create config.json
cat > discomfy-data/config.json << EOF
{
  "discord": {
    "token": "YOUR_DISCORD_BOT_TOKEN",
    "guild_id": "YOUR_SERVER_ID"
  },
  "comfyui": {
    "url": "http://YOUR_COMFYUI_URL:8188"
  }
}
EOF

# Run container
docker run -d \
  --name discomfy \
  -v $(pwd)/discomfy-data/config.json:/app/config.json:ro \
  -v $(pwd)/discomfy-data/outputs:/app/outputs \
  -v $(pwd)/discomfy-data/logs:/app/logs \
  ghcr.io/jmpijll/discomfy:latest
```

### Using Environment Variables

```bash
docker run -d \
  --name discomfy \
  -e DISCORD_TOKEN=your_token \
  -e COMFYUI_URL=http://your-comfyui-url:8188 \
  -e DISCORD_GUILD_ID=your_server_id \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/logs:/app/logs \
  ghcr.io/jmpijll/discomfy:latest
```

See **[[Installation Guide]]** for more Docker options including Docker Compose and Unraid.

---

## 🔧 ComfyUI Setup

### Requirements

DisComfy expects certain ComfyUI workflows and models to be available.

### Default Workflows

Place these workflow JSON files in the `workflows/` directory:
- `flux_lora.json` - Main Flux generation workflow
- `flux_krea_lora.json` - Flux Krea enhanced workflow
- `hidream_lora.json` - HiDream workflow
- `flux_kontext_edit.json` - Flux editing workflow
- `qwen_image_edit.json` - Qwen editing workflow
- `upscale_config-1.json` - Upscaling workflow
- `video_wan_vace_14B_i2v.json` - Video generation workflow

### Required Models

Install in your ComfyUI:
- **Flux models** for generation
- **Flux Kontext** for high-quality editing
- **Qwen 2.5 VL** for fast editing
- **Upscale models** for image upscaling
- **WanVace Video models** for video generation

See **[[Custom Workflows]]** for information on creating your own workflows.

---

## 📖 Next Steps

Now that you're up and running:

1. **[[User Guide]]** - Learn all the features and commands
2. **[[Usage Examples]]** - See practical examples
3. **[[Configuration Guide]]** - Customize your setup
4. **[[Custom Workflows]]** - Add your own ComfyUI workflows
5. **[[Troubleshooting]]** - If you encounter issues

---

## 🆘 Common Issues

### Bot Won't Start

**"Invalid Discord bot token"**
- Verify token in config.json is correct
- Ensure no extra spaces or quotes
- Regenerate token if needed

**"ComfyUI connection failed"**
- Verify ComfyUI is running
- Check URL is correct in config.json
- Test with: `curl http://localhost:8188/system_stats`

### Bot Shows Offline in Discord

- Check bot token is valid
- Verify bot was invited with correct permissions
- Check logs: `tail -f logs/bot.log`

### Commands Don't Appear

- Wait 1-2 minutes for command sync
- Try reinviting bot with updated permissions
- Restart bot: `Ctrl+C` then `python main.py`

See **[[Troubleshooting]]** for more solutions.

---

## 💡 Tips

- **Use environment variables** for sensitive data (recommended for production)
- **Mount outputs directory** to persist generated images
- **Check logs** regularly for errors: `logs/bot.log`
- **Update regularly** to get latest features and fixes
- **Test with simple prompts** first before complex generations

---

## 🎯 Quick Reference

### Start Bot
```bash
python main.py
```

### Stop Bot
Press `Ctrl+C`

### View Logs
```bash
tail -f logs/bot.log
```

### Update Bot
```bash
git pull
pip install -r requirements.txt --upgrade
python main.py
```

### Test Connection
```bash
# Test ComfyUI
curl http://localhost:8188/system_stats

# Test bot configuration
python -c "from config import get_config; print(get_config())"
```

---

**🎉 Congratulations! DisComfy is ready to create amazing AI art!**

Try your first generation with: `/generate prompt:a majestic dragon in flight`

