# Configuration Guide ⚙️

Complete guide to configuring DisComfy for your specific needs.

---

## 📁 Configuration File Structure

DisComfy uses `config.json` for all configuration. The file has the following structure:

```json
{
  "discord": { },
  "comfyui": { },
  "generation": { },
  "security": { },
  "logging": { },
  "workflows": { }
}
```

---

## 🤖 Discord Configuration

### Basic Settings
```json
"discord": {
  "token": "YOUR_BOT_TOKEN",
  "guild_id": "YOUR_SERVER_ID"
}
```

**Parameters:**
- `token` (required) - Discord bot token from Developer Portal
- `guild_id` (optional) - Server ID for slash command registration
  - If provided: Commands register only to that server (instant)
  - If omitted: Commands register globally (takes up to 1 hour)

### Finding Your Guild ID
1. Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
2. Right-click your server icon
3. Click "Copy ID"

---

## 🎨 ComfyUI Configuration

### Connection Settings
```json
"comfyui": {
  "url": "http://localhost:8188",
  "timeout": 300
}
```

**Parameters:**
- `url` (required) - ComfyUI server URL
  - Local: `http://localhost:8188`
  - Remote: `http://your-server-ip:8188`
  - HTTPS: `https://your-domain.com`
- `timeout` (required) - Maximum generation time in seconds
  - Image generation: 300 (5 minutes) recommended
  - Video generation: 900 (15 minutes) for complex videos

### Example Configurations

**Local ComfyUI:**
```json
"comfyui": {
  "url": "http://localhost:8188",
  "timeout": 300
}
```

**Remote ComfyUI:**
```json
"comfyui": {
  "url": "http://192.168.1.100:8188",
  "timeout": 600
}
```

**ComfyUI Behind Reverse Proxy:**
```json
"comfyui": {
  "url": "https://comfyui.yourdomain.com",
  "timeout": 300
}
```

---

## 🎯 Generation Settings

### Default Parameters
```json
"generation": {
  "default_workflow": "flux_lora",
  "max_batch_size": 4,
  "output_limit": 100
}
```

**Parameters:**
- `default_workflow` (required) - Default workflow to use
  - Options: `"flux_lora"`, `"flux_krea_lora"`, `"hidream_lora"`
  - Must match a workflow key in `workflows` section
- `max_batch_size` (required) - Maximum images per generation
  - Range: 1-10
  - Recommended: 4 (balances speed and memory)
- `output_limit` (required) - Maximum files to keep in `outputs/`
  - Older files automatically deleted when limit reached
  - Recommended: 50-200 depending on disk space

---

## 🛡️ Security Settings

### Rate Limiting and Validation
```json
"security": {
  "max_prompt_length": 1000,
  "rate_limit_seconds": 5
}
```

**Parameters:**
- `max_prompt_length` (required) - Maximum characters in prompts
  - Prevents extremely long prompts
  - Range: 100-5000
  - Recommended: 1000
- `rate_limit_seconds` (required) - Cooldown between user commands
  - Prevents spam
  - Range: 1-60
  - Recommended: 5-10

---

## 📝 Logging Configuration

### Log Levels and Paths
```json
"logging": {
  "level": "INFO",
  "file": "logs/bot.log",
  "max_file_size": 10485760
}
```

**Parameters:**
- `level` (optional) - Logging verbosity
  - `"DEBUG"` - Detailed diagnostic information
  - `"INFO"` - General informational messages (recommended)
  - `"WARNING"` - Warning messages only
  - `"ERROR"` - Error messages only
- `file` (optional) - Log file path
  - Default: `"logs/bot.log"`
  - Relative to DisComfy root directory
- `max_file_size` (optional) - Maximum log file size in bytes
  - Default: 10485760 (10 MB)
  - Logs rotate when size exceeded

---

## 🔧 Workflow Configuration

### Default Workflows
```json
"workflows": {
  "flux_lora": {
    "file": "flux_lora.json",
    "name": "Flux with LoRA",
    "description": "Standard Flux model with LoRA support",
    "enabled": true
  },
  "flux_krea_lora": {
    "file": "flux_krea_lora.json",
    "name": "Flux Krea ✨",
    "description": "Enhanced Flux Krea model with LoRA",
    "enabled": true
  },
  "hidream_lora": {
    "file": "hidream_lora.json",
    "name": "HiDream",
    "description": "HiDream model with LoRA support",
    "enabled": true
  }
}
```

**Workflow Parameters:**
- `file` (required) - Workflow JSON filename in `workflows/` directory
- `name` (required) - Display name shown to users
- `description` (required) - Brief description of workflow
- `enabled` (required) - Whether workflow is available
  - `true` - Available for use
  - `false` - Hidden from users

### Adding Custom Workflows

1. **Export from ComfyUI:**
   - Design workflow in ComfyUI
   - Use **"Save (API Format)"** (not regular Save)
   - Save to `discomfy/workflows/` directory

2. **Add to config.json:**
   ```json
   "workflows": {
     "my_custom_workflow": {
       "file": "my_custom_workflow.json",
       "name": "My Custom Style",
       "description": "Custom workflow for artistic images",
       "enabled": true
     }
   }
   ```

3. **Set as default (optional):**
   ```json
   "generation": {
     "default_workflow": "my_custom_workflow"
   }
   ```

See **[[Custom Workflows]]** for detailed workflow creation guide.

---

## 📋 Complete Configuration Example

### Production Configuration
```json
{
  "discord": {
    "token": "YOUR_BOT_TOKEN_HERE",
    "guild_id": "123456789012345678"
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
  },
  "logging": {
    "level": "INFO",
    "file": "logs/bot.log",
    "max_file_size": 10485760
  },
  "workflows": {
    "flux_lora": {
      "file": "flux_lora.json",
      "name": "Flux with LoRA",
      "description": "Standard Flux model with LoRA support",
      "enabled": true
    },
    "flux_krea_lora": {
      "file": "flux_krea_lora.json",
      "name": "Flux Krea ✨ NEW",
      "description": "Enhanced Flux Krea model with LoRA",
      "enabled": true
    },
    "hidream_lora": {
      "file": "hidream_lora.json",
      "name": "HiDream",
      "description": "HiDream model with LoRA support",
      "enabled": true
    }
  }
}
```

### Development Configuration
```json
{
  "discord": {
    "token": "YOUR_DEV_BOT_TOKEN",
    "guild_id": "987654321098765432"
  },
  "comfyui": {
    "url": "http://localhost:8188",
    "timeout": 600
  },
  "generation": {
    "default_workflow": "flux_lora",
    "max_batch_size": 2,
    "output_limit": 50
  },
  "security": {
    "max_prompt_length": 2000,
    "rate_limit_seconds": 1
  },
  "logging": {
    "level": "DEBUG",
    "file": "logs/bot-dev.log",
    "max_file_size": 52428800
  },
  "workflows": {
    "flux_lora": {
      "file": "flux_lora.json",
      "name": "Flux (Dev)",
      "description": "Development testing",
      "enabled": true
    }
  }
}
```

---

## 🔐 Security Best Practices

### Protecting Sensitive Data

**Never commit sensitive data:**
```bash
# Add to .gitignore
echo "config.json" >> .gitignore
echo "*.log" >> .gitignore
```

**Use environment variables (alternative):**
```python
# In config.py - DisComfy already supports this
import os

token = os.getenv('DISCORD_TOKEN', config.get('discord', {}).get('token'))
```

**Set environment variable:**
```bash
# Linux/Mac
export DISCORD_TOKEN="your_token_here"

# Windows
set DISCORD_TOKEN=your_token_here

# Or use .env file
echo "DISCORD_TOKEN=your_token_here" > .env
```

---

## 🎛️ Performance Tuning

### For Faster Generations
```json
"generation": {
  "max_batch_size": 1,  // Single image at a time
  "output_limit": 50     // Less file management
},
"comfyui": {
  "timeout": 120         // Shorter timeout
}
```

### For Quality/Batch Processing
```json
"generation": {
  "max_batch_size": 8,   // More images per generation
  "output_limit": 200    // Keep more outputs
},
"comfyui": {
  "timeout": 900         // Longer timeout for complex workflows
}
```

### For High-Traffic Servers
```json
"security": {
  "rate_limit_seconds": 10,      // Slower rate
  "max_prompt_length": 500       // Shorter prompts
},
"generation": {
  "max_batch_size": 2            // Reduce concurrent load
}
```

---

## 🔄 Configuration Reload

DisComfy requires restart to apply configuration changes:

```bash
# Stop bot (Ctrl+C)
# Edit config.json
# Restart bot
python bot.py
```

**Configuration changes requiring restart:**
- All Discord settings
- ComfyUI URL changes
- Workflow changes
- Security settings

---

## ✅ Configuration Validation

### Test Your Configuration

**Validate JSON syntax:**
```bash
python -m json.tool config.json
```

**Test ComfyUI connection:**
```bash
# Linux/Mac
curl http://localhost:8188/system_stats

# Windows PowerShell
Invoke-WebRequest -Uri "http://localhost:8188/system_stats"
```

**Verify workflow files:**
```bash
# Check all workflow files exist
ls workflows/*.json
```

**Start bot in test mode:**
```bash
python bot.py
# Check startup messages for errors
```

---

## 🚨 Common Configuration Issues

### Bot Won't Start

**Invalid JSON syntax:**
```
Error: JSONDecodeError
Solution: Validate JSON with `python -m json.tool config.json`
```

**Missing required fields:**
```
Error: KeyError: 'discord'
Solution: Ensure all required sections exist
```

### ComfyUI Connection Failed

**Wrong URL:**
```json
// Bad
"url": "localhost:8188"

// Good
"url": "http://localhost:8188"
```

**Firewall blocking:**
```bash
# Test connection
curl http://localhost:8188/system_stats
```

### Workflow Not Found

**File doesn't exist:**
```
Error: FileNotFoundError: workflows/my_workflow.json
Solution: Ensure file exists in workflows/ directory
```

**Wrong workflow name:**
```json
// In config.json
"default_workflow": "flux_lora"  // Must match key in workflows section
```

---

## 📖 Advanced Configuration

### Multiple Bot Instances

Run multiple bots with different configs:

```bash
# Bot 1 (production)
python bot.py --config config.json

# Bot 2 (development)
python bot.py --config config-dev.json
```

### Custom Config Location

```python
# Modify bot.py
config_path = os.getenv('DISCOMFY_CONFIG', 'config.json')
config = get_config(config_path)
```

---

## 🎯 Next Steps

- **[[User Guide]]** - Learn how to use configured features
- **[[Custom Workflows]]** - Add custom ComfyUI workflows
- **[[Performance Tuning]]** - Optimize for your hardware
- **[[Troubleshooting]]** - Fix configuration issues

---

**⚙️ Configuration complete? Start using DisComfy with [[User Guide]]!**

