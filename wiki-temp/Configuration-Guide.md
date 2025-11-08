# Configuration Guide

Complete guide to configuring DisComfy v2.0.

---

## 📋 Configuration Methods

DisComfy supports three configuration methods (in priority order):

1. **Environment Variables** (highest priority)
2. **config.json file** (medium priority)
3. **Default values** (lowest priority)

---

## 🔧 Configuration File (config.json)

### Location

```
discomfy/
├── config.json          # Your configuration
├── config.example.json  # Example template
└── ...
```

### Complete Configuration Example

```json
{
  "discord": {
    "token": "YOUR_DISCORD_BOT_TOKEN",
    "guild_id": "YOUR_SERVER_ID",
    "command_prefix": "!",
    "status_message": "🎨 Creating AI art"
  },
  "comfyui": {
    "url": "http://localhost:8188",
    "timeout": 300,
    "websocket_timeout": 30,
    "poll_interval": 2.0
  },
  "generation": {
    "default_workflow": "flux_lora",
    "max_batch_size": 4,
    "output_limit": 100,
    "default_width": 1024,
    "default_height": 1024,
    "default_steps": 30,
    "default_cfg": 7.5
  },
  "rate_limit": {
    "enabled": true,
    "per_user": 10,
    "global_limit": 100,
    "window_seconds": 60
  },
  "paths": {
    "workflows": "./workflows",
    "outputs": "./outputs",
    "logs": "./logs"
  },
  "logging": {
    "level": "INFO",
    "file": "logs/bot.log",
    "max_bytes": 10485760,
    "backup_count": 5
  },
  "workflows": {
    "flux_lora": {
      "file": "flux_lora.json",
      "name": "Flux",
      "description": "High-quality Flux generation",
      "enabled": true
    },
    "flux_krea_lora": {
      "file": "flux_krea_lora.json", 
      "name": "Flux Krea",
      "description": "Enhanced Flux Krea model",
      "enabled": true
    },
    "hidream_lora": {
      "file": "hidream_lora.json",
      "name": "HiDream",
      "description": "Alternative generation model",
      "enabled": true
    }
  }
}
```

---

## 📝 Configuration Sections

### Discord Configuration

```json
{
  "discord": {
    "token": "YOUR_DISCORD_BOT_TOKEN",
    "guild_id": "YOUR_SERVER_ID",
    "command_prefix": "!",
    "status_message": "🎨 Creating AI art"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `token` | string | ✅ Yes | Discord bot token from Developer Portal |
| `guild_id` | string | No | Specific server ID for command registration |
| `command_prefix` | string | No | Prefix for text commands (default: `!`) |
| `status_message` | string | No | Bot status message (default: "Creating art") |

**Getting Discord Token:**
1. [Discord Developer Portal](https://discord.com/developers/applications)
2. Your Application → Bot → Copy Token

**Getting Guild ID:**
1. Enable Developer Mode in Discord: User Settings → Advanced
2. Right-click server → Copy ID

### ComfyUI Configuration

```json
{
  "comfyui": {
    "url": "http://localhost:8188",
    "timeout": 300,
    "websocket_timeout": 30,
    "poll_interval": 2.0
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `url` | string | `http://localhost:8188` | ComfyUI server URL |
| `timeout` | integer | `300` | HTTP request timeout (seconds) |
| `websocket_timeout` | integer | `30` | WebSocket connection timeout |
| `poll_interval` | float | `2.0` | Status polling interval (seconds) |

**URL Examples:**
- Local: `http://localhost:8188`
- LAN: `http://192.168.1.100:8188`
- Remote: `https://comfyui.example.com`

**Timeout Recommendations:**
- Images: 300 seconds (5 minutes)
- Videos: 900 seconds (15 minutes)
- Complex workflows: 1800 seconds (30 minutes)

### Generation Configuration

```json
{
  "generation": {
    "default_workflow": "flux_lora",
    "max_batch_size": 4,
    "output_limit": 100,
    "default_width": 1024,
    "default_height": 1024,
    "default_steps": 30,
    "default_cfg": 7.5,
    "enable_progress_tracking": true
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `default_workflow` | string | `"flux_lora"` | Default generation workflow |
| `max_batch_size` | integer | `4` | Maximum images per batch |
| `output_limit` | integer | `100` | Max files before cleanup |
| `default_width` | integer | `1024` | Default image width |
| `default_height` | integer | `1024` | Default image height |
| `default_steps` | integer | `30` | Default sampling steps |
| `default_cfg` | float | `7.5` | Default CFG scale |
| `enable_progress_tracking` | boolean | `true` | Enable progress updates |

### Rate Limiting Configuration

```json
{
  "rate_limit": {
    "enabled": true,
    "per_user": 10,
    "global_limit": 100,
    "window_seconds": 60,
    "whitelist_users": [],
    "whitelist_roles": []
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable rate limiting |
| `per_user` | integer | `10` | Max requests per user per window |
| `global_limit` | integer | `100` | Max total requests per window |
| `window_seconds` | integer | `60` | Time window in seconds |
| `whitelist_users` | array | `[]` | User IDs exempt from limits |
| `whitelist_roles` | array | `[]` | Role IDs exempt from limits |

**Recommended Settings:**

**Small Server (< 50 users):**
```json
{
  "per_user": 10,
  "global_limit": 100,
  "window_seconds": 60
}
```

**Medium Server (50-200 users):**
```json
{
  "per_user": 5,
  "global_limit": 50,
  "window_seconds": 60
}
```

**Large Server (200+ users):**
```json
{
  "per_user": 3,
  "global_limit": 30,
  "window_seconds": 60
}
```

### Paths Configuration

```json
{
  "paths": {
    "workflows": "./workflows",
    "outputs": "./outputs",
    "logs": "./logs",
    "temp": "./temp"
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `workflows` | string | `"./workflows"` | Workflow JSON files directory |
| `outputs` | string | `"./outputs"` | Generated files directory |
| `logs` | string | `"./logs"` | Log files directory |
| `temp` | string | `"./temp"` | Temporary files directory |

**Absolute Paths:**
```json
{
  "paths": {
    "workflows": "/home/user/discomfy/workflows",
    "outputs": "/mnt/storage/discomfy/outputs"
  }
}
```

### Logging Configuration

```json
{
  "logging": {
    "level": "INFO",
    "file": "logs/bot.log",
    "max_bytes": 10485760,
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `level` | string | `"INFO"` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `file` | string | `"logs/bot.log"` | Log file path |
| `max_bytes` | integer | `10485760` | Max log file size (10MB) |
| `backup_count` | integer | `5` | Number of backup logs to keep |
| `format` | string | - | Log message format |

**Log Levels:**
- `DEBUG` - Detailed debugging information
- `INFO` - General information (recommended)
- `WARNING` - Warning messages only
- `ERROR` - Error messages only

### Workflow Configuration

```json
{
  "workflows": {
    "my_custom_workflow": {
      "file": "my_workflow.json",
      "name": "Custom Style",
      "description": "My custom ComfyUI workflow",
      "enabled": true,
      "category": "generation",
      "default_params": {
        "steps": 25,
        "cfg": 7.0
      }
    }
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | string | ✅ Yes | Workflow JSON filename |
| `name` | string | ✅ Yes | Display name |
| `description` | string | No | Workflow description |
| `enabled` | boolean | No | Enable/disable workflow (default: true) |
| `category` | string | No | Workflow category |
| `default_params` | object | No | Default parameters |

See **[[Custom Workflows]]** for detailed workflow creation guide.

---

## 🌍 Environment Variables

Environment variables override config.json values.

### Core Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DISCORD_TOKEN` | Discord bot token | `MTAx...` |
| `DISCORD_GUILD_ID` | Discord server ID | `123456789` |
| `COMFYUI_URL` | ComfyUI server URL | `http://localhost:8188` |
| `COMFYUI_API_KEY` | ComfyUI API key (if needed) | `your-api-key` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level | `INFO` |
| `OUTPUT_DIR` | Output directory | `./outputs` |
| `WORKFLOWS_DIR` | Workflows directory | `./workflows` |
| `MAX_BATCH_SIZE` | Max batch size | `4` |
| `RATE_LIMIT_ENABLED` | Enable rate limiting | `true` |

### Setting Environment Variables

**Linux/Mac:**
```bash
export DISCORD_TOKEN="your_token"
export COMFYUI_URL="http://localhost:8188"
```

**Windows CMD:**
```cmd
set DISCORD_TOKEN=your_token
set COMFYUI_URL=http://localhost:8188
```

**Windows PowerShell:**
```powershell
$env:DISCORD_TOKEN="your_token"
$env:COMFYUI_URL="http://localhost:8188"
```

**Docker:**
```bash
docker run -e DISCORD_TOKEN=your_token -e COMFYUI_URL=http://localhost:8188 ...
```

**Docker Compose (.env file):**
```env
DISCORD_TOKEN=your_token
COMFYUI_URL=http://localhost:8188
DISCORD_GUILD_ID=your_guild_id
LOG_LEVEL=INFO
```

---

## 🔐 Secure Configuration

### Best Practices

1. **Never commit secrets to git:**
```bash
# Add to .gitignore
echo "config.json" >> .gitignore
echo ".env" >> .gitignore
```

2. **Use environment variables for sensitive data:**
```bash
# Instead of storing token in config.json
export DISCORD_TOKEN="your_token"
```

3. **Restrict file permissions:**
```bash
chmod 600 config.json
chmod 600 .env
```

4. **Use separate configs for dev/prod:**
```
discomfy/
├── config.example.json
├── config.dev.json
├── config.prod.json  # Not committed
└── ...
```

### Docker Secrets

**Using Docker secrets (Docker Swarm):**

```yaml
version: '3.8'

services:
  discomfy:
    image: ghcr.io/jmpijll/discomfy:latest
    secrets:
      - discord_token
      - comfyui_url
    environment:
      - DISCORD_TOKEN_FILE=/run/secrets/discord_token

secrets:
  discord_token:
    file: ./secrets/discord_token.txt
  comfyui_url:
    file: ./secrets/comfyui_url.txt
```

---

## 🎯 Configuration Profiles

### Development Profile

```json
{
  "discord": {
    "token": "${DISCORD_TOKEN_DEV}",
    "guild_id": "dev_server_id"
  },
  "comfyui": {
    "url": "http://localhost:8188"
  },
  "logging": {
    "level": "DEBUG"
  },
  "rate_limit": {
    "enabled": false
  }
}
```

### Production Profile

```json
{
  "discord": {
    "token": "${DISCORD_TOKEN}",
    "guild_id": "prod_server_id"
  },
  "comfyui": {
    "url": "https://comfyui.example.com",
    "timeout": 600
  },
  "logging": {
    "level": "INFO"
  },
  "rate_limit": {
    "enabled": true,
    "per_user": 5,
    "global_limit": 50
  }
}
```

---

## ✅ Configuration Validation

### Validate Configuration

```bash
# Test configuration
python -c "from config import get_config; print(get_config())"
```

### Common Validation Errors

**Invalid Discord Token:**
```
Error: Invalid Discord bot token format
```
- Check token has no extra spaces
- Verify token from Discord Developer Portal
- Regenerate token if needed

**ComfyUI Connection Failed:**
```
Warning: Could not connect to ComfyUI
```
- Verify ComfyUI is running
- Check URL is correct
- Test: `curl http://localhost:8188/system_stats`

**Missing Required Fields:**
```
Error: Configuration validation failed: discord.token is required
```
- Ensure all required fields are set
- Check config.json syntax (valid JSON)

---

## 📊 Performance Tuning

### Low-Memory Systems

```json
{
  "generation": {
    "max_batch_size": 1,
    "output_limit": 25
  },
  "comfyui": {
    "timeout": 120
  }
}
```

### High-Performance Systems

```json
{
  "generation": {
    "max_batch_size": 8,
    "output_limit": 500
  },
  "comfyui": {
    "timeout": 600,
    "poll_interval": 1.0
  }
}
```

### Remote ComfyUI

```json
{
  "comfyui": {
    "url": "https://comfyui.example.com",
    "timeout": 900,
    "websocket_timeout": 60,
    "poll_interval": 3.0
  }
}
```

---

## 🔄 Dynamic Configuration

### Reload Configuration

Bot restart required for config changes:
```bash
# Standard installation
Ctrl+C
python main.py

# Docker
docker restart discomfy

# Systemd
sudo systemctl restart discomfy
```

### Hot-Reload Workflows

Workflows are loaded on bot startup. To add new workflows:
1. Add workflow JSON to `workflows/` directory
2. Update `config.json` workflows section
3. Restart bot

---

## 📖 Example Configurations

### Minimal Configuration

```json
{
  "discord": {
    "token": "YOUR_TOKEN"
  },
  "comfyui": {
    "url": "http://localhost:8188"
  }
}
```

### Multi-Server Configuration

```json
{
  "discord": {
    "token": "YOUR_TOKEN"
    // No guild_id = registers commands globally
  },
  "comfyui": {
    "url": "http://localhost:8188"
  }
}
```

### High-Security Configuration

```json
{
  "discord": {
    "token": "${DISCORD_TOKEN}"
  },
  "comfyui": {
    "url": "${COMFYUI_URL}"
  },
  "rate_limit": {
    "enabled": true,
    "per_user": 3,
    "global_limit": 20,
    "whitelist_users": ["admin_user_id"]
  },
  "logging": {
    "level": "WARNING"
  }
}
```

---

## 🆘 Troubleshooting Configuration

### Config File Not Found

```bash
# Check file exists
ls -la config.json

# Create from example
cp config.example.json config.json
```

### JSON Syntax Error

```bash
# Validate JSON
python -m json.tool config.json
```

### Environment Variables Not Working

```bash
# Check variables are set
echo $DISCORD_TOKEN
env | grep DISCORD
```

---

**⚙️ Configuration complete! See [[Installation Guide]] for setup and [[Features]] for usage.**
