# 🐳 Unraid Docker Setup Guide

This guide will help you set up DisComfy on Unraid using the Docker container.

## 📋 Prerequisites

- Unraid with Docker installed
- Discord Bot Token
- ComfyUI instance running (can be on another server)

## 🚀 Quick Setup

### Option 1: Using Environment Variables (Recommended)

1. **Add Container**:
   - Go to **Docker** tab in Unraid
   - Click **Add Container**
   - Set **Repository**: `jamiehakker/discomfy:latest`

2. **Required Environment Variables**:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   COMFYUI_URL=http://your-comfyui-server:8188
   ```

3. **Optional Environment Variables**:
   ```
   DISCORD_GUILD_ID=your_server_id_optional
   COMFYUI_API_KEY=your_api_key_if_needed
   ```

4. **Volume Mounts** (Optional but Recommended):
   - `/mnt/user/appdata/discomfy/config.json` → `/app/config.json:ro` (read-only)
   - `/mnt/user/appdata/discomfy/workflows` → `/app/workflows:ro` (read-only)
   - `/mnt/user/appdata/discomfy/outputs` → `/app/outputs`
   - `/mnt/user/appdata/discomfy/logs` → `/app/logs`

5. **Network Settings**:
   - Use **Bridge** mode (default)
   - Or **Custom** if ComfyUI is on the same network

6. **Click Apply** - Container should start automatically!

### Option 2: Using config.json File

1. **Prepare config.json**:
   ```bash
   # SSH into Unraid or use Unraid terminal
   mkdir -p /mnt/user/appdata/discomfy
   cd /mnt/user/appdata/discomfy
   
   # Download example config
   curl -o config.json https://raw.githubusercontent.com/jmpijll/discomfy/main/config.example.json
   
   # Edit with your settings
   nano config.json
   ```

2. **Edit config.json**:
   ```json
   {
     "discord": {
       "token": "YOUR_DISCORD_BOT_TOKEN",
       "guild_id": "YOUR_SERVER_ID_OPTIONAL"
     },
     "comfyui": {
       "url": "http://your-comfyui-server:8188",
       "timeout": 300
     },
     "generation": {
       "default_workflow": "flux_lora",
       "max_batch_size": 4,
       "output_limit": 100
     }
   }
   ```

3. **Add Container** with volume mount:
   - Repository: `jamiehakker/discomfy:latest`
   - Add Path: `/mnt/user/appdata/discomfy/config.json` → `/app/config.json:ro`

## ✅ Verify Container is Running

1. **Check Logs**:
   - In Unraid Docker tab, click container name
   - Click **Logs** button
   - You should see: `🤖 Bot is starting up...` followed by `✅ Connected to Discord as DisComfy#XXXX`

2. **If Container Exits Immediately**:
   - Check logs for error messages
   - Common issues:
     - Missing `DISCORD_TOKEN` environment variable
     - Invalid Discord token format
     - Network connectivity to ComfyUI

## 🔧 Troubleshooting

### Container Won't Start

**Error: "Invalid Discord bot token format"**
- Make sure `DISCORD_TOKEN` is set correctly
- Token should start with letters/numbers (no quotes needed in Unraid)
- Check logs: `docker logs discomfy` (if container name is `discomfy`)

**Error: "Configuration validation failed"**
- Ensure at minimum `DISCORD_TOKEN` environment variable is set
- Or mount a valid `config.json` file

**Container Starts Then Stops**
- Check logs for the actual error
- Usually indicates invalid Discord token or network issue

### Bot Not Responding in Discord

1. **Check Bot is Online**:
   - In Discord, check if bot shows as "Online" in member list
   - If offline, check container logs

2. **Check Commands**:
   - Bot needs to sync commands on first run (takes a few seconds)
   - Try `/help` command in Discord

3. **Check ComfyUI Connection**:
   - Logs will show: `🎨 ComfyUI connection verified` if successful
   - Warning message is okay - bot will still work but may have limited features

### Volume Mount Issues

**Permission Errors**:
- Ensure Unraid user has read/write access to mounted directories
- For outputs and logs: `chmod 755 /mnt/user/appdata/discomfy/outputs`
- For logs: `chmod 755 /mnt/user/appdata/discomfy/logs`

**Config File Not Found**:
- Ensure path is correct: `/mnt/user/appdata/discomfy/config.json`
- Check file exists: `ls -la /mnt/user/appdata/discomfy/config.json`
- Ensure mount point is `/app/config.json` in container

## 📝 Example Unraid Container Template

```
Repository: jamiehakker/discomfy:latest
Network Type: Bridge
Environment Variables:
  - DISCORD_TOKEN=your_token_here
  - COMFYUI_URL=http://192.168.1.100:8188
Volume Mappings:
  - /mnt/user/appdata/discomfy/outputs:/app/outputs
  - /mnt/user/appdata/discomfy/logs:/app/logs
```

## 🔗 Useful Commands

**View Container Logs**:
```bash
docker logs discomfy --follow
```

**Restart Container**:
- In Unraid: Docker tab → Click container → **Restart**

**Stop Container**:
- In Unraid: Docker tab → Click container → **Stop**

## 📚 Additional Resources

- **GitHub Repository**: https://github.com/jmpijll/discomfy
- **Full Documentation**: See README.md
- **Issues**: https://github.com/jmpijll/discomfy/issues

---

**Need Help?** Check the logs first - they usually tell you exactly what's wrong!

