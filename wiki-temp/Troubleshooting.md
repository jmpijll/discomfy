# Troubleshooting Guide

Common issues and solutions for DisComfy v2.0.

---

## 🚨 Quick Diagnostics

### Check Bot Status

```bash
# View logs
tail -f logs/bot.log

# Check if bot is running
ps aux | grep python | grep discomfy

# Docker: Check container
docker ps | grep discomfy
docker logs discomfy -f
```

### Test Components

```bash
# Test ComfyUI connection
curl http://localhost:8188/system_stats

# Test configuration
python -c "from config import get_config; print(get_config())"

# Test Python imports
python -c "import discord; import aiohttp; print('OK')"
```

---

## 🔧 Installation Issues

### Bot Won't Start

#### Error: "Invalid Discord bot token format"

**Symptoms:**
```
Error: Invalid Discord bot token format
Bot failed to start
```

**Solutions:**
1. Verify token in config.json has no extra spaces:
```json
{
  "discord": {
    "token": "MTAx..." // No quotes in value, no spaces
  }
}
```

2. Regenerate token:
   - Go to Discord Developer Portal
   - Your Application → Bot → Reset Token
   - Copy new token to config.json

3. Check environment variable:
```bash
echo $DISCORD_TOKEN  # Should show your token
```

#### Error: "ModuleNotFoundError"

**Symptoms:**
```
ModuleNotFoundError: No module named 'discord'
ModuleNotFoundError: No module named 'aiohttp'
```

**Solutions:**
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Verify virtual environment is activated:
```bash
which python  # Should point to venv
source venv/bin/activate
```

3. Reinstall in virtual environment:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Error: "Permission denied"

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: 'logs/bot.log'
```

**Solutions:**
1. Create directories:
```bash
mkdir -p logs outputs workflows
chmod 755 logs outputs
```

2. Fix file permissions:
```bash
chmod 644 config.json
chmod 755 main.py
```

3. Run with correct user (not root):
```bash
# Don't use sudo
python main.py
```

---

## 🔌 Connection Issues

### ComfyUI Connection Failed

#### Error: "Could not connect to ComfyUI"

**Symptoms:**
```
⚠️ Warning: Could not connect to ComfyUI at http://localhost:8188
Bot will start but some features may not work
```

**Diagnostics:**
```bash
# Test ComfyUI is running
curl http://localhost:8188/system_stats

# Check ComfyUI logs
# (varies by ComfyUI installation)

# Test from Python
python -c "import aiohttp; import asyncio; asyncio.run(aiohttp.ClientSession().get('http://localhost:8188/system_stats'))"
```

**Solutions:**

1. **Start ComfyUI:**
```bash
# Navigate to ComfyUI directory
cd /path/to/ComfyUI
python main.py
```

2. **Fix URL in config:**
```json
{
  "comfyui": {
    "url": "http://localhost:8188"  // Check port number
  }
}
```

3. **Remote ComfyUI:**
```json
{
  "comfyui": {
    "url": "http://192.168.1.100:8188"  // Use IP, not localhost
  }
}
```

4. **Firewall issues:**
```bash
# Allow ComfyUI port (Linux)
sudo ufw allow 8188

# Check if port is listening
netstat -an | grep 8188
```

5. **Docker network issues:**
```yaml
# docker-compose.yml
services:
  discomfy:
    # Use host network or link to ComfyUI container
    network_mode: host
    # OR
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

Then use:
```json
{
  "comfyui": {
    "url": "http://host.docker.internal:8188"
  }
}
```

### WebSocket Connection Issues

#### Symptoms:
```
⚠️ WebSocket disconnected
⚠️ Progress tracking may be degraded
```

**Solutions:**

1. **Normal behavior** - Bot will automatically reconnect
2. **Persistent issues:**
```json
{
  "comfyui": {
    "websocket_timeout": 60,  // Increase timeout
    "poll_interval": 3.0       // Slower polling
  }
}
```

3. **Disable WebSocket (use HTTP polling only):**
```json
{
  "generation": {
    "enable_progress_tracking": false
  }
}
```

---

## 💬 Discord Issues

### Commands Not Appearing

#### Symptoms:
- Type `/` but no DisComfy commands show up
- Commands worked before but disappeared

**Solutions:**

1. **Wait for sync (1-2 minutes):**
Commands need time to register after bot starts.

2. **Restart bot:**
```bash
Ctrl+C
python main.py
```

3. **Check bot permissions:**
- Bot needs `applications.commands` scope
- Reinvite with correct URL:
```
https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=277025508416&scope=bot%20applications.commands
```

4. **Guild-specific registration:**
```json
{
  "discord": {
    "guild_id": "YOUR_SERVER_ID"  // Add this for faster sync
  }
}
```

5. **Clear command cache (Discord):**
- Discord Settings → Advanced → Developer Mode (enable)
- Right-click server → Copy ID
- Restart Discord client

### Bot Shows Offline

#### Symptoms:
Bot appears offline in member list

**Solutions:**

1. **Check bot is running:**
```bash
# Standard
ps aux | grep python | grep discomfy

# Docker
docker ps | grep discomfy
```

2. **Check logs for errors:**
```bash
tail -f logs/bot.log
```

3. **Verify token:**
```bash
# Token should be ~70 characters starting with letters/numbers
python -c "from config import get_config; print(len(get_config().discord.token))"
```

4. **Check intents:**
Discord Developer Portal → Your App → Bot → Privileged Gateway Intents:
- ✅ Presence Intent
- ✅ Server Members Intent
- ✅ Message Content Intent

### "Bot is not responding"

#### Symptoms:
Commands exist but nothing happens when used

**Solutions:**

1. **Check rate limiting:**
```
/status
```
If rate limited, wait or contact admin.

2. **Check ComfyUI connection:**
Bot may be waiting for ComfyUI. Check ComfyUI is running.

3. **Check logs:**
```bash
tail -f logs/bot.log | grep ERROR
```

4. **Restart bot:**
```bash
Ctrl+C
python main.py
```

---

## 🎨 Generation Issues

### "Generation timed out"

#### Symptoms:
```
❌ Generation timed out after 300 seconds
```

**Solutions:**

1. **Increase timeout:**
```json
{
  "comfyui": {
    "timeout": 600  // 10 minutes instead of 5
  }
}
```

2. **For videos:**
```json
{
  "comfyui": {
    "timeout": 900  // 15 minutes for video generation
  }
}
```

3. **Check ComfyUI:**
- ComfyUI may have crashed
- Check ComfyUI logs
- Restart ComfyUI

4. **Reduce complexity:**
- Lower steps (30 → 20)
- Smaller batch size (4 → 1)
- Lower resolution

### "Workflow validation failed"

#### Symptoms:
```
❌ Workflow validation failed: Node 'XXX' is missing class_type property
```

**Solutions:**

1. **Re-export workflow from ComfyUI:**
- In ComfyUI: Save → **Save (API Format)**
- NOT "Save" or "Save As Image"

2. **Check workflow file:**
```bash
# Validate JSON
python -m json.tool workflows/your_workflow.json
```

3. **Verify node structure:**
```json
{
  "1": {
    "class_type": "KSampler",  // Must have this
    "inputs": { ... }
  }
}
```

4. **Use provided workflows:**
Copy working workflows from repository:
```bash
git pull origin main  # Get latest workflows
```

### "Failed to queue prompt"

#### Symptoms:
```
❌ Failed to queue prompt: 500 Internal Server Error
```

**Solutions:**

1. **Check ComfyUI errors:**
Look at ComfyUI console for error messages

2. **Common causes:**
- Missing models
- Missing custom nodes
- Out of memory
- Workflow incompatible with ComfyUI version

3. **Test workflow directly:**
- Load workflow in ComfyUI web interface
- Try to queue manually
- Fix errors shown in ComfyUI

4. **Verify models installed:**
```bash
# Check ComfyUI models directory
ls ComfyUI/models/checkpoints/
ls ComfyUI/models/loras/
```

### Progress Stuck at "Checking status..."

#### Symptoms:
Progress shows "Checking status..." but never updates

**Solutions:**

1. **Normal for queued generation:**
If ComfyUI is busy, generation waits in queue.

2. **Check ComfyUI queue:**
Visit: `http://localhost:8188` in browser
Check queue status

3. **WebSocket reconnection:**
Bot may be reconnecting WebSocket. Wait 30 seconds.

4. **Force restart:**
```bash
Ctrl+C
python main.py
```

5. **Fallback mode:**
Bot will fall back to HTTP polling automatically after 30 seconds.

---

## 🐳 Docker Issues

### Container Exits Immediately

#### Symptoms:
```bash
docker ps  # Container not listed
docker ps -a  # Shows "Exited (1)"
```

**Solutions:**

1. **Check logs:**
```bash
docker logs discomfy
```

2. **Common causes:**
- Missing `DISCORD_TOKEN` environment variable
- Invalid configuration
- Network issues

3. **Test configuration:**
```bash
docker run -it --rm \
  -e DISCORD_TOKEN=your_token \
  -e COMFYUI_URL=http://host.docker.internal:8188 \
  ghcr.io/jmpijll/discomfy:latest \
  python -c "from config import get_config; print(get_config())"
```

4. **Use config file:**
```bash
docker run -d \
  --name discomfy \
  -v $(pwd)/config.json:/app/config.json:ro \
  ghcr.io/jmpijll/discomfy:latest
```

### Volume Mount Issues

#### Symptoms:
```
Error: config.json not found
Permission denied
```

**Solutions:**

1. **Verify file exists:**
```bash
ls -la $(pwd)/config.json
```

2. **Check absolute path:**
```bash
docker run -d \
  -v /full/path/to/config.json:/app/config.json:ro \
  ghcr.io/jmpijll/discomfy:latest
```

3. **Fix permissions:**
```bash
chmod 644 config.json
chmod 755 outputs logs
```

4. **SELinux (if applicable):**
```bash
# Add :z flag for SELinux
docker run -d \
  -v $(pwd)/config.json:/app/config.json:ro,z \
  ghcr.io/jmpijll/discomfy:latest
```

### Network Issues (Docker)

#### Symptoms:
Cannot connect to ComfyUI from container

**Solutions:**

1. **Use host network:**
```bash
docker run -d --network host ghcr.io/jmpijll/discomfy:latest
```

2. **Use host.docker.internal:**
```json
{
  "comfyui": {
    "url": "http://host.docker.internal:8188"
  }
}
```

3. **Custom bridge network:**
```yaml
# docker-compose.yml
services:
  comfyui:
    # Your ComfyUI container
    networks:
      - app-network
  
  discomfy:
    image: ghcr.io/jmpijll/discomfy:latest
    environment:
      - COMFYUI_URL=http://comfyui:8188
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

---

## 🖥️ Unraid Issues

### Container Won't Start (Unraid)

**Solutions:**

1. **Check template variables:**
- Ensure `DISCORD_TOKEN` is set
- Check `COMFYUI_URL` format
- Use IP address, not `localhost`

2. **View container logs:**
- Click container name
- Click "Logs"
- Look for error message

3. **Fix paths:**
- Use `/mnt/user/appdata/discomfy/` prefix
- Ensure directories exist
- Check permissions

4. **Example working config:**
```
Repository: ghcr.io/jmpijll/discomfy:latest
DISCORD_TOKEN: your_token_here
COMFYUI_URL: http://192.168.1.100:8188
/mnt/user/appdata/discomfy/outputs -> /app/outputs (RW)
/mnt/user/appdata/discomfy/logs -> /app/logs (RW)
```

---

## ⚙️ Performance Issues

### Bot is Slow

**Solutions:**

1. **Check ComfyUI performance:**
- ComfyUI may be the bottleneck
- Check CPU/GPU usage
- Verify models loaded properly

2. **Optimize configuration:**
```json
{
  "generation": {
    "max_batch_size": 2,  // Lower batch size
    "output_limit": 50    // More frequent cleanup
  },
  "comfyui": {
    "poll_interval": 2.0  // Faster polling
  }
}
```

3. **Check system resources:**
```bash
# CPU and memory
top
htop

# Disk I/O
iostat

# Docker resources
docker stats discomfy
```

### High Memory Usage

**Solutions:**

1. **Lower output limit:**
```json
{
  "generation": {
    "output_limit": 25  // Clean up more frequently
  }
}
```

2. **Manual cleanup:**
```bash
rm -rf outputs/*
```

3. **Docker memory limit:**
```bash
docker run -d --memory=4g ghcr.io/jmpijll/discomfy:latest
```

---

## 🔍 Debug Mode

### Enable Detailed Logging

```json
{
  "logging": {
    "level": "DEBUG"
  }
}
```

Then restart bot and check logs:
```bash
tail -f logs/bot.log
```

### Test Individual Components

```bash
# Test configuration
python -c "from config import get_config; print(get_config())"

# Test ComfyUI client
python -c "
import asyncio
from core.comfyui.client import ComfyUIClient

async def test():
    async with ComfyUIClient('http://localhost:8188') as client:
        print('Connected:', await client.test_connection())

asyncio.run(test())
"

# Test validators
python -c "
from core.validators.image import PromptParameters
params = PromptParameters(prompt='test')
print('Validation OK:', params.prompt)
"
```

---

## 📋 Diagnostic Checklist

When reporting issues, provide:

- [ ] Bot version: `git describe --tags`
- [ ] Python version: `python --version`
- [ ] Operating system
- [ ] Installation method (standard/Docker/Unraid)
- [ ] Error messages from logs
- [ ] ComfyUI version
- [ ] Steps to reproduce
- [ ] `config.json` (without token!)

---

## 🆘 Getting Help

### Before Asking for Help

1. ✅ Check this troubleshooting guide
2. ✅ Review logs: `tail -f logs/bot.log`
3. ✅ Test ComfyUI connection
4. ✅ Verify configuration
5. ✅ Try with default settings
6. ✅ Search existing issues

### Where to Get Help

1. **GitHub Issues:** [https://github.com/jmpijll/discomfy/issues](https://github.com/jmpijll/discomfy/issues)
2. **Provide Information:**
   - Error messages
   - Log excerpts
   - Steps to reproduce
   - Your setup (OS, Docker, etc.)

### Useful Commands for Reports

```bash
# Bot version
git describe --tags

# Python/package versions
pip list | grep -E "discord|aiohttp|pydantic"

# System info
uname -a
python --version

# Configuration (remove token!)
cat config.json | sed 's/"token": ".*"/"token": "REDACTED"/'

# Recent logs
tail -50 logs/bot.log

# Docker info (if applicable)
docker version
docker logs discomfy --tail 50
```

---

## ✅ Common Solutions Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| Bot won't start | Check token, verify dependencies |
| Commands missing | Wait 2 min, restart bot, check permissions |
| ComfyUI connection | Verify URL, check ComfyUI is running |
| Timeout | Increase timeout in config |
| Workflow errors | Re-export as API format |
| Slow performance | Lower batch size, check ComfyUI |
| Docker exits | Check logs, verify env vars |
| Permission denied | Fix file/directory permissions |

---

**💡 Still having issues? Check [[FAQ]] or create a GitHub issue with detailed information!**
