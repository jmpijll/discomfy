# Workflow Management Guide

This guide explains how to enable and disable workflows in DisComfy to control which models and features are available to users.

## Overview

DisComfy supports multiple AI models and workflows (Flux, Flux Krea, DyPE, HiDream, ZI Turbo, video generation, upscaling, etc.). You can easily enable or disable any workflow without modifying code or deleting workflow files.

## Default Behavior

**By default, all workflows are enabled.** This means all models and features are available to users unless you explicitly disable them.

## How to Disable/Enable Workflows

There are two ways to control workflow availability:

### Method 1: Environment Variables (Recommended)

The easiest way to enable/disable workflows is via environment variables in your `.env` file.

**Format:**
```bash
WORKFLOW_<WORKFLOW_NAME>_ENABLED=true/false
```

**Accepted Values:**
- **Enable:** `true`, `1`, `yes`, `on` (case-insensitive)
- **Disable:** `false`, `0`, `no`, `off` (case-insensitive)

**Example `.env` file:**
```bash
# Discord and ComfyUI config
DISCORD_TOKEN=your_token_here
COMFYUI_URL=http://localhost:8188

# Disable HiDream model
WORKFLOW_HIDREAM_LORA_ENABLED=false

# Disable video generation
WORKFLOW_VIDEO_WAN_VACE_14B_I2V_ENABLED=false

# Keep everything else enabled (default)
```

### Method 2: config.json

You can also set the `enabled` field directly in `config.json`:

```json
{
  "workflows": {
    "hidream_lora": {
      "name": "HiDream with LoRA",
      "file": "hidream_lora.json",
      "enabled": false,  // ← Set to false to disable
      "supports_lora": true
    }
  }
}
```

**Note:** Environment variables override `config.json` settings.

## Available Workflows

Here are all the workflows you can enable/disable:

| Workflow Name | Env Variable | Description | Type |
|--------------|--------------|-------------|------|
| `flux_lora` | `WORKFLOW_FLUX_LORA_ENABLED` | Standard Flux generation | Image |
| `flux_krea_lora` | `WORKFLOW_FLUX_KREA_LORA_ENABLED` | Enhanced Flux Krea model | Image |
| `dype_flux_krea_lora` | `WORKFLOW_DYPE_FLUX_KREA_LORA_ENABLED` | DyPE 4K ultra-resolution | Image |
| `hidream_lora` | `WORKFLOW_HIDREAM_LORA_ENABLED` | HiDream model | Image |
| `ziturbo` | `WORKFLOW_ZITURBO_ENABLED` | ZI Turbo fast generation | Image |
| `qwen_image_2512_lora` | `WORKFLOW_QWEN_IMAGE_2512_LORA_ENABLED` | Qwen Image 2512 with hi-res fix | Image |
| `flux_kontext_edit` | `WORKFLOW_FLUX_KONTEXT_EDIT_ENABLED` | Flux Kontext image editing | Edit |
| `video_wan_vace_14B_i2v` | `WORKFLOW_VIDEO_WAN_VACE_14B_I2V_ENABLED` | Image to video generation | Video |
| `upscale_config_1` | `WORKFLOW_UPSCALE_CONFIG_1_ENABLED` | Image upscaling | Upscale |

**Note:** The workflow name in the env variable is the same as in `config.json`, but uppercase with dashes replaced by underscores.

### Name Conversion Examples:
- `flux_lora` → `WORKFLOW_FLUX_LORA_ENABLED`
- `flux_krea_lora` → `WORKFLOW_FLUX_KREA_LORA_ENABLED`
- `upscale_config-1` → `WORKFLOW_UPSCALE_CONFIG_1_ENABLED`

## What Happens When a Workflow is Disabled?

When you disable a workflow:

1. ✅ **It's filtered from model selection menus** - Users won't see it as an option
2. ✅ **It can't be used via commands** - Any attempt to use it will fail gracefully
3. ✅ **Existing workflow files remain** - No files are deleted, just disabled
4. ✅ **Easy to re-enable** - Just change the env var back to `true`

### Error Handling

If a user tries to use a disabled workflow, they'll see a friendly error:

```
❌ Workflow 'hidream_lora' is disabled
```

The bot continues to function normally - only the specific workflow is unavailable.

## Common Use Cases

### Retiring Old Models

When you want to phase out an old model:

```bash
# Disable old HiDream model
WORKFLOW_HIDREAM_LORA_ENABLED=false
```

### Testing New Models

Enable only the model you're testing:

```bash
# Disable everything except the new model
WORKFLOW_FLUX_LORA_ENABLED=false
WORKFLOW_FLUX_KREA_LORA_ENABLED=false
WORKFLOW_HIDREAM_LORA_ENABLED=false
WORKFLOW_ZITURBO_ENABLED=true  # ← Testing this one
```

### Reducing Server Load

Disable resource-intensive features:

```bash
# Disable video generation (most resource-intensive)
WORKFLOW_VIDEO_WAN_VACE_14B_I2V_ENABLED=false

# Disable 4K generation
WORKFLOW_DYPE_FLUX_KREA_LORA_ENABLED=false
```

### Maintenance Mode

Keep only basic functionality:

```bash
# Only allow standard Flux generation
WORKFLOW_FLUX_LORA_ENABLED=true
# (All others disabled)
```

## Docker Usage

For Docker deployments, pass environment variables in your `docker-compose.yml`:

```yaml
version: '3.8'

services:
  discomfy:
    image: ghcr.io/jmpijll/discomfy:latest
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - COMFYUI_URL=${COMFYUI_URL}
      # Disable workflows as needed
      - WORKFLOW_HIDREAM_LORA_ENABLED=false
      - WORKFLOW_VIDEO_WAN_VACE_14B_I2V_ENABLED=false
    volumes:
      - ./config.json:/app/config.json:ro
      - ./workflows:/app/workflows:ro
      - ./outputs:/app/outputs
```

Or pass them directly in `docker run`:

```bash
docker run -d \
  --name discomfy \
  -e DISCORD_TOKEN=your_token \
  -e COMFYUI_URL=http://localhost:8188 \
  -e WORKFLOW_HIDREAM_LORA_ENABLED=false \
  -e WORKFLOW_VIDEO_WAN_VACE_14B_I2V_ENABLED=false \
  ghcr.io/jmpijll/discomfy:latest
```

## Verifying Configuration

To see which workflows are currently enabled, check the bot logs on startup:

```
INFO - Workflow 'hidream_lora' disabled via environment variable WORKFLOW_HIDREAM_LORA_ENABLED
INFO - Configuration loaded successfully
```

You can also use the `/status` command (if available) to see active workflows.

## Troubleshooting

### Workflow still appears after disabling

1. **Restart the bot** - Config is loaded on startup
2. **Check env var name** - Must match exactly (case-sensitive)
3. **Verify .env file** - Make sure it's in the correct directory
4. **Check docker env** - Verify env vars are passed to container

### All workflows disabled

If no workflows are available, check:

1. **Env vars are correct** - Should be `true`, not `True` or `TRUE` (though all are supported)
2. **config.json has enabled:true** - Default should be true
3. **Check logs** - Look for "disabled via environment variable" messages

### Can't find workflow name

The workflow name is the key in `config.json` under `workflows`:

```json
"workflows": {
  "flux_lora": {  // ← This is the workflow name
    "name": "Flux with LoRA",  // ← This is the display name
    ...
  }
}
```

Use the key (e.g., `flux_lora`), not the display name.

## Best Practices

1. **Use environment variables** for temporary changes (testing, maintenance)
2. **Use config.json** for permanent changes (retiring old models)
3. **Keep workflow files** even when disabled (easier to re-enable)
4. **Document changes** in your own notes when disabling workflows
5. **Test in dev** before disabling workflows in production
6. **Check dependent features** - Some commands may depend on specific workflows

## Migration Path for Retiring Features

When you want to fully retire a workflow:

1. **Week 1-2:** Disable via env var, monitor for issues
   ```bash
   WORKFLOW_HIDREAM_LORA_ENABLED=false
   ```

2. **Week 3-4:** If stable, update config.json permanently
   ```json
   "hidream_lora": {
     "enabled": false
   }
   ```

3. **Week 5+:** If no longer needed, optionally remove workflow file
   ```bash
   # Optional: Backup first
   mv workflows/hidream_lora.json workflows/_archived/
   ```

This gradual approach lets you easily rollback if needed.

## FAQ

**Q: What happens to old images generated with a disabled workflow?**
A: They remain accessible. Disabling only prevents new generations.

**Q: Can I disable the upscale feature?**
A: Yes, set `WORKFLOW_UPSCALE_CONFIG_1_ENABLED=false`

**Q: Can I disable all image generation?**
A: Technically yes, but the bot won't be useful. At least one image workflow should be enabled.

**Q: Do I need to restart the bot after changing env vars?**
A: Yes, config is loaded on startup. Use `docker restart discomfy` or restart the Python process.

**Q: Can I disable editing but keep generation?**
A: Yes, disable `flux_kontext_edit` and keep image workflows enabled.

**Q: What's the performance impact of having many workflows?**
A: None when disabled. Only enabled workflows are loaded and checked.

## Related Documentation

- [Configuration Guide](Configuration-Guide.md) - Complete config reference
- [Installation Guide](Installation-Guide.md) - Setup instructions
- [Migration Guide](MIGRATION_GUIDE.md) - Upgrading from older versions
- [API Documentation](API.md) - Technical details

---

**Need help?** Check the [Troubleshooting Guide](Troubleshooting.md) or open an issue on GitHub.
