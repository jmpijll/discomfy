# Troubleshooting Guide 🔧

Solutions to common issues and problems with DisComfy.

---

## 🚨 Bot Won't Start

### Discord Token Invalid

**Symptoms:**
```
discord.errors.LoginFailure: Improper token has been passed
```

**Solutions:**
1. **Regenerate token** in Discord Developer Portal
2. **Check config.json** for extra spaces or quotes
3. **Ensure token is from "Bot" section**, not "OAuth2"
4. **Don't share your token** - regenerate if exposed

**How to get new token:**
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application → Bot
3. Click "Reset Token"
4. Copy new token to `config.json`

### Module Not Found

**Symptoms:**
```
ModuleNotFoundError: No module named 'discord'
```

**Solutions:**
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Config File Issues

**Symptoms:**
```
json.decoder.JSONDecodeError
KeyError: 'discord'
```

**Solutions:**
1. **Validate JSON syntax:**
   ```bash
   python -m json.tool config.json
   ```
2. **Check all required fields** exist
3. **Ensure no trailing commas** in JSON
4. **Use example config** as template:
   ```bash
   cp config.example.json config.json
   ```

---

## 🌐 Connection Issues

### ComfyUI Not Accessible

**Symptoms:**
```
Failed to connect to ComfyUI
ComfyUI connection failed
```

**Diagnostics:**
```bash
# Test ComfyUI is running
curl http://localhost:8188/system_stats

# Or in browser
http://localhost:8188
```

**Solutions:**

**1. ComfyUI Not Running**
```bash
# Start ComfyUI
cd ComfyUI
python main.py --port 8188
```

**2. Wrong URL in Config**
```json
// Check config.json
"comfyui": {
  "url": "http://localhost:8188"  // Must include http://
}
```

**3. Firewall Blocking**
```bash
# Allow port 8188
# Windows Firewall: Add inbound rule
# Linux: sudo ufw allow 8188
```

**4. ComfyUI on Different Machine**
```json
"comfyui": {
  "url": "http://192.168.1.100:8188"  // Use IP address
}
```

### Timeout Errors

**Symptoms:**
```
Generation timeout after 300 seconds
ComfyUI may be overloaded
```

**Solutions:**

**1. Increase Timeout**
```json
"comfyui": {
  "timeout": 600  // 10 minutes for complex generations
}
```

**2. Check ComfyUI Resources**
```
Visit: http://localhost:8188/system_stats
Check: RAM, VRAM, GPU usage
```

**3. Reduce Generation Complexity**
```
- Lower steps (try 20-30)
- Smaller batch size (1-2)
- Smaller dimensions (512x512)
```

---

## 🎨 Generation Problems

### Generation Fails Immediately

**Symptoms:**
```
Failed to load workflow
Workflow validation failed
Node missing class_type property
```

**Solutions:**

**1. Workflow Format Wrong**
- Re-export from ComfyUI using **"Save (API Format)"**
- Not regular "Save"

**2. Missing Models**
```
Check ComfyUI has required models:
- models/checkpoints/
- models/clip/
- models/vae/
- models/loras/
```

**3. Workflow Validation Issues**
See v1.3.1+ error messages for specific fixes:
```
Workflow 'my_workflow' has invalid node(s):
  - Node #1: Missing required 'class_type' property

To fix: In ComfyUI, use 'Save (API Format)'
```

### Poor Quality Results

**Symptoms:**
- Blurry images
- Missing details
- Wrong style

**Solutions:**

**1. Increase Steps**
```
/generate prompt:your prompt steps:50
```

**2. Adjust CFG Scale**
```
# Try lower (2-4) if oversaturated
# Try higher (8-10) if lacking detail
/generate prompt:your prompt cfg:7
```

**3. Better Prompts**
- Be specific and descriptive
- Include style keywords
- Use negative prompts
- Add quality tags ("high quality", "detailed")

**4. Check Model**
- Ensure correct model for style
- Verify model files aren't corrupted
- Try different model

### Prompt Ignored

**Symptoms:**
- Generated image doesn't match prompt
- Always similar output regardless of prompt

**Solutions:**

**1. Increase CFG**
```
/generate prompt:specific description cfg:8
```

**2. More Descriptive Prompt**
```
# Instead of: "a cat"
# Try: "a fluffy orange tabby cat sitting on a windowsill, sunlight, photorealistic"
```

**3. Use Negative Prompts**
```
/generate prompt:what you want negative_prompt:what to avoid
```

**4. Check Workflow**
- Ensure CLIPTextEncode nodes exist
- Verify title metadata ("Positive", "Negative")
- Test workflow in ComfyUI first

---

## 🔘 Interactive Features Issues

### Buttons Not Working

**Symptoms:**
- Clicking buttons does nothing
- "Interaction failed" errors
- Rate limit messages

**Solutions:**

**1. Rate Limited**
```
⏳ Please wait before using this again
Solution: Wait 5-10 seconds between clicks
```

**2. Bot Restarted**
```
Buttons lose functionality after bot restart
Solution: Buttons are persistent now in v1.2.11+, but restart clears them
```

**3. Permissions Issue**
```
Check bot has permissions:
- Send Messages
- Attach Files
- Embed Links
- Use External Emojis
```

### Modal Not Opening

**Symptoms:**
- Click button, nothing happens
- Modal appears then disappears

**Solutions:**

**1. Discord App Issue**
```
- Restart Discord
- Try different device/browser
- Update Discord app
```

**2. Bot Lag**
```
- Check bot logs for errors
- Verify ComfyUI is responsive
- Reduce server load
```

### Progress Not Updating

**Symptoms:**
- Stuck at "Queued"
- No percentage shown
- Progress jumps to 100%

**Solutions:**

**1. WebSocket Connection**
```
Check logs for:
"📡 Persistent WebSocket CONNECTED"

If missing:
- Restart bot
- Check firewall
- Verify ComfyUI WebSocket port
```

**2. ComfyUI Busy**
```
If stuck at "Queued (#1)":
- Another generation may be running
- Check ComfyUI queue: http://localhost:8188/queue
- Wait for current generation to complete
```

---

## 💾 File and Storage Issues

### Out of Disk Space

**Symptoms:**
```
No space left on device
Failed to save output
```

**Solutions:**

**1. Adjust Output Limit**
```json
"generation": {
  "output_limit": 50  // Reduce from 100
}
```

**2. Manual Cleanup**
```bash
# Remove old outputs
rm -rf outputs/*

# Keep bot logs small
truncate -s 0 logs/bot.log
```

**3. Check Disk Space**
```bash
# Linux/Mac
df -h

# Windows
Get-PSDrive C
```

### File Permission Errors

**Symptoms:**
```
Permission denied: 'outputs/image.png'
Cannot write to logs/
```

**Solutions:**

**Linux/Mac:**
```bash
# Fix permissions
chmod 755 discomfy/
chmod -R 755 outputs/ logs/ workflows/
```

**Windows:**
```
Right-click folder → Properties → Security
Ensure your user has Write permissions
```

---

## 🐌 Performance Issues

### Slow Generations

**Symptoms:**
- Takes 5+ minutes for simple images
- Progress very slow
- Timeouts frequent

**Diagnostics:**
```bash
# Check ComfyUI stats
curl http://localhost:8188/system_stats

# Check system resources
top  # Linux
Task Manager  # Windows
```

**Solutions:**

**1. ComfyUI Performance**
```
- Ensure GPU is being used
- Check VRAM isn't full
- Close other GPU applications
- Reduce ComfyUI queue size
```

**2. Reduce Generation Complexity**
```
- Fewer steps (20-30 instead of 50)
- Smaller dimensions (512x512 for testing)
- Lower batch size (1-2)
```

**3. Optimize Models**
```
- Use fp8 quantized models
- Enable model offloading in ComfyUI
- Use lighter models for testing
```

### High Memory Usage

**Symptoms:**
- Bot crashes
- System slowdown
- Out of memory errors

**Solutions:**

**1. Reduce Concurrent Generations**
```json
"generation": {
  "max_batch_size": 1  // One at a time
}
```

**2. Restart Periodically**
```bash
# Cron job to restart daily
0 4 * * * systemctl restart discomfy
```

**3. Monitor Resources**
```bash
# Check memory usage
free -h  # Linux
Get-Process python | Select-Object WorkingSet  # Windows
```

---

## 📝 Logging and Debugging

### Enable Debug Logs

**config.json:**
```json
"logging": {
  "level": "DEBUG",
  "file": "logs/bot-debug.log"
}
```

### Check Logs

```bash
# View live logs
tail -f logs/bot.log

# Search for errors
grep ERROR logs/bot.log

# Last 100 lines
tail -100 logs/bot.log
```

### Common Log Messages

**Normal:**
```
INFO - Bot is starting up...
INFO - ✅ Connected to Discord
INFO - 🎨 ComfyUI connection verified
INFO - 🚀 Bot is ready!
```

**Warnings:**
```
WARNING - ComfyUI response slow
WARNING - High memory usage
WARNING - Rate limit triggered
```

**Errors:**
```
ERROR - Failed to load workflow
ERROR - ComfyUI connection failed
ERROR - Generation timeout
```

---

## 🔄 Recovery Procedures

### Complete Reset

If nothing works, try a complete reset:

```bash
# 1. Stop bot
# Ctrl+C or kill process

# 2. Backup config
cp config.json config.backup.json

# 3. Clean install
rm -rf venv/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Restore config
cp config.backup.json config.json

# 5. Restart bot
python bot.py
```

### Database/Cache Issues

```bash
# Clear any cached data
rm -rf __pycache__/
rm -rf *.pyc

# Clear old outputs
rm -rf outputs/*

# Restart fresh
python bot.py
```

---

## 🆘 Getting Help

### Before Asking for Help

1. **Check this guide** for your issue
2. **Review logs** for error messages
3. **Test ComfyUI** standalone
4. **Try simple generation** first
5. **Check GitHub issues** for similar problems

### Reporting Issues

**Include:**
1. DisComfy version (`git log -1`)
2. Python version (`python --version`)
3. Operating system
4. Error messages (from logs)
5. Steps to reproduce
6. Config (redact token!)

**Create issue:**
https://github.com/jmpijll/discomfy/issues/new

### Useful Commands

```bash
# System info
python --version
git log -1 --oneline

# Config check (redact token first!)
python -m json.tool config.json

# Test ComfyUI
curl http://localhost:8188/system_stats

# Check processes
ps aux | grep python
```

---

## 📚 Additional Resources

- **[[FAQ]]** - Frequently asked questions
- **[[User Guide]]** - Complete usage guide
- **[[Installation Guide]]** - Setup instructions
- **[[Configuration Guide]]** - Config reference

---

**🔧 Still having issues? Create an [issue on GitHub](https://github.com/jmpijll/discomfy/issues)!**

