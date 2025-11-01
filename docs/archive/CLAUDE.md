# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DisComfy is a Discord bot that integrates with ComfyUI to provide AI image and video generation capabilities. The bot uses Discord slash commands and interactive buttons to allow users to generate images, upscale them, edit them, and convert them to videos using various AI models (Flux, Flux Krea, HiDream, Qwen, etc.).

**Key Technologies:**
- Python 3.11+ with discord.py for Discord integration
- ComfyUI API for AI generation (HTTP + WebSocket)
- aiohttp for async HTTP requests
- Pillow for image processing
- Pydantic for configuration validation

## Architecture

### Core Modules

**bot.py** (~3500 lines)
- Main Discord bot implementation using discord.py
- Handles all slash commands: `/generate`, `/editflux`, `/editqwen`, `/animate`
- Implements interactive Discord UI components (buttons, modals)
- Manages rate limiting and user permissions
- Coordinates between Discord interactions and generation modules

**image_gen.py** (~1900 lines)
- ImageGenerator class handles all image generation via ComfyUI API
- Maintains persistent WebSocket connection to ComfyUI for real-time progress
- Implements sophisticated progress tracking using step-based calculations
- Manages HTTP session pooling and connection reuse
- Handles workflow JSON manipulation and parameter injection

**video_gen.py** (~330 lines)
- VideoGenerator extends ImageGenerator to handle video workflows
- Shares HTTP session and WebSocket connection with ImageGenerator
- Updates video-specific workflow parameters (frame count, strength)
- Uses same progress tracking infrastructure as image generation

**video_ui.py** (~314 lines)
- Discord UI components for video generation
- VideoParameterSettingsModal for customizing video settings
- GenerateVideoButton for initiating video generation

**config.py** (~417 lines)
- Configuration management using Pydantic models
- Loads from config.json with environment variable overrides
- Validates Discord token, ComfyUI URL, and workflow configurations
- Supports multiple workflow definitions with metadata

### Workflow System

ComfyUI workflow JSON files are stored in `workflows/`:
- `flux_lora.json` - Standard Flux model with LoRA support
- `flux_krea_lora.json` - Enhanced Flux Krea model
- `flux_kontext_edit.json` - Image editing with Flux Kontext
- `qwen_image_edit.json`, `qwen_image_edit_2.json`, `qwen_image_edit_3.json` - Fast editing (1-3 images)
- `hidream_lora.json` - HiDream model
- `upscale_config-1.json` - Image upscaling (2x, 4x, 8x)
- `video_wan_vace_14B_i2v.json` - Image-to-video conversion

Each workflow is configured in config.json with metadata about its type, model, and capabilities.

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy example config
cp config.example.json config.json
# Edit config.json with your Discord token and ComfyUI URL
```

### Running the Bot
```bash
# Standard run
python bot.py

# With environment variables
DISCORD_TOKEN=xxx COMFYUI_URL=http://localhost:8188 python bot.py
```

### Docker
```bash
# Build local image
docker build -t discomfy:local .

# Run with docker-compose
docker-compose up -d

# Pull from GitHub Container Registry
docker pull ghcr.io/jmpijll/discomfy:latest

# Pull from Docker Hub
docker pull jamiehakker/discomfy:latest
```

### Testing
```bash
# Test shared client ID functionality
python test_shared_clientid.py
```

## Critical Implementation Details

### WebSocket Connection & Progress Tracking

The bot maintains a **single persistent WebSocket connection** to ComfyUI that is shared between ImageGenerator and VideoGenerator. This is critical for real-time progress tracking.

**Key Implementation Details:**
1. **Client ID Retrieval**: Connect to WebSocket first, receive `client_id` from status message
2. **Prompt Submission**: Submit prompt with `client_id` to associate it with the WebSocket
3. **Progress Messages**: Listen for `progress`, `executing`, `executed`, `execution_success` messages
4. **Step-Based Calculation**: Progress is calculated from sampling steps (e.g., 152/161), not node execution
5. **Fallback Support**: HTTP polling fallback if WebSocket fails

**Progress Tracking States:**
- Before first sampling step: Show "Loading..." (0%)
- During sampling: Calculate as `(current_step / total_steps) * 100`
- Multiple sampling nodes: Handle different step counts (common in video generation)
- Final processing: Show 95-100% for post-sampling operations

See `docs/GUIDELINES.md` lines 88-156 for detailed WebSocket implementation requirements.

### Shared Session Management

ImageGenerator and VideoGenerator share:
- HTTP aiohttp.ClientSession (connection pooling)
- WebSocket connection
- Client ID for ComfyUI
- Active generation tracking dictionary

This prevents connection overhead and ensures consistent progress tracking.

### Configuration System

Configuration cascade:
1. `config.json` - Base configuration
2. Environment variables - Override config.json (e.g., `DISCORD_TOKEN`, `COMFYUI_URL`)
3. Pydantic validation - Ensures all values are valid

**Important Config Sections:**
- `discord.token` - Discord bot token (set via env var)
- `comfyui.url` - ComfyUI server URL
- `comfyui.timeout` - Default 300s for images, 900s for videos
- `workflows` - Dictionary of available workflows with metadata
- `generation` - Default parameters (width, height, steps, cfg)

### Rate Limiting & Security

Simple in-memory rate limiting:
- Per-user: 5 requests per minute (configurable)
- Global: 20 requests per minute (configurable)
- File type validation: Only allowed extensions
- Max prompt length: 2000 characters
- Max file size: 25MB

### File Management

- All outputs saved to `outputs/` directory
- Automatic cleanup keeps only last 100 files (configurable)
- Unique filenames using UUID to prevent conflicts
- Proper cleanup of temporary files

### Discord Interaction Patterns

**Slash Commands:**
- `/generate` - Generate images with full parameter control
- `/editflux` - Edit images using Flux Kontext (high quality, 10-50 steps)
- `/editqwen` - Edit images using Qwen 2.5 VL (fast, 4-20 steps, supports 1-3 images)
- `/animate` - Convert images to videos

**Interactive Buttons:**
- Added to all generation results
- Anyone can use buttons (not just original user)
- Buttons never expire
- Actions: Upscale (2x/4x/8x), Flux Edit, Qwen Edit, Animate

**Modals:**
- Parameter customization before generation
- Pre-filled with sensible defaults
- Input validation with helpful error messages

## Development Guidelines

**From docs/GUIDELINES.md:**

1. **Modular Architecture**: Keep Discord logic in bot.py, generation logic in image_gen.py/video_gen.py
2. **Configuration Management**: Never hardcode values; all settings in config.json or environment variables
3. **Error Handling**: Comprehensive try-catch blocks; user-friendly error messages; never crash
4. **Async Operations**: Use async/await for all I/O; no blocking operations
5. **Type Hints**: All functions must have type hints and docstrings
6. **Progress Tracking**: Must use WebSocket for real-time progress; HTTP fallback if needed
7. **Git Workflow**: Commit after every completed feature; meaningful commit messages

**Prohibited:**
- Hardcoded values (except constants)
- Blocking operations in main thread
- Direct file system access without validation
- Skipping error handling
- Incomplete features in releases

## Troubleshooting

**Bot won't start:**
- Verify `DISCORD_TOKEN` in environment or config.json
- Check bot permissions in Discord server
- Ensure Python 3.8+ is installed

**ComfyUI connection failed:**
- Verify ComfyUI is running: `curl http://localhost:8188/system_stats`
- Check firewall settings
- Ensure correct URL in config.json

**Generation fails:**
- Check ComfyUI logs for errors
- Verify required models are installed in ComfyUI
- Ensure workflow JSON files exist in `workflows/` directory

**Progress tracking not working:**
- Check WebSocket connection to ComfyUI (should be ws://host:port/ws)
- Verify client_id is being retrieved before prompt submission
- Check for WebSocket timeout errors in logs

## Version History

Current version: v1.4.0 (see CHANGELOG.md for full history)

Major releases:
- v1.4.0: Fixed concurrent generation hanging bug, 5-10x faster queue times
- v1.3.0: Added Qwen multi-image editing (1-3 images)
- v1.2.0: Added Flux Krea model support
- v1.1.0: Added video generation with custom animation prompts
- v1.0.0: Initial release with image generation and upscaling
