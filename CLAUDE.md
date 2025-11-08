# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DisComfy is a Discord bot that integrates with ComfyUI to provide AI image and video generation capabilities. The project underwent a major v2.0 architectural refactoring in November 2025, transitioning from monolithic files to a modular architecture while maintaining 100% backward compatibility with v1.4.0. Version 2.1.0 adds ultra high-resolution support via the DyPE Flux Krea model.

**Key Facts:**
- Discord bot using discord.py with slash commands
- Integrates with ComfyUI backend via HTTP/WebSocket
- Supports image generation, video generation, image editing, and upscaling
- Real-time progress tracking via WebSocket
- Multi-workflow support (Flux, Flux Krea, DyPE Flux Krea, HiDream, Qwen, etc.)
- **NEW in v2.1**: Ultra high-resolution support (up to 4096x4096) with DyPE technology

## Development Commands

### Running the Bot
```bash
# Recommended: Use new v2.0 entry point
python main.py

# Legacy: Old entry point (still supported)
python bot.py
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=utils --cov=bot --cov=config

# Run specific test file
pytest tests/test_comfyui_client.py

# Run tests with verbose output
pytest -v
```

### Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy example config
cp config.example.json config.json
# Edit config.json with your Discord token and ComfyUI URL
```

### Docker
```bash
# Build image
docker build -t discomfy:local .

# Run container
docker run -d --name discomfy \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v $(pwd)/workflows:/app/workflows:ro \
  -v $(pwd)/outputs:/app/outputs \
  ghcr.io/jmpijll/discomfy:latest
```

## Architecture

### Modular Structure (v2.0)

The codebase follows a modular architecture with clear separation of concerns:

```
bot/              # Discord bot layer
  client.py       # Main bot class (ComfyUIBot)
  commands/       # Command handlers (generate, edit, status, loras)
  ui/             # Discord UI components (views, buttons, modals)

core/             # Business logic layer
  comfyui/        # ComfyUI integration
    client.py     # HTTP client (aiohttp-based)
    websocket.py  # WebSocket client for real-time updates
    workflows/    # Workflow management
  generators/     # Generation engines
    base.py       # BaseGenerator abstract class
    image.py      # ImageGenerator
    video.py      # VideoGenerator
  progress/       # Progress tracking
    tracker.py    # ProgressTracker
    callbacks.py  # Discord progress callbacks
  validators/     # Input validation
    image.py      # ImageValidator, PromptParameters
  exceptions.py   # Custom exceptions

config/           # Configuration layer
  models.py       # Pydantic models (BotConfig, etc.)
  loader.py       # Config loading (get_config, ConfigManager)
  migration.py    # v1.x -> v2.0 migration
  validation.py   # Token/URL validation

utils/            # Utilities layer
  files.py        # File operations (save_output_image, cleanup)
  logging.py      # Logging setup (colorlog-based)
  rate_limit.py   # RateLimiter (per-user + global)
```

### Key Design Patterns

**ComfyUIClient (aiohttp best practices):**
- Proper async context manager support (`__aenter__`/`__aexit__`)
- Connection pooling with `TCPConnector`
- Session lifecycle management
- Never create multiple sessions; use singleton pattern via `get_config()`

**Generators Pattern:**
- All generators inherit from `BaseGenerator`
- Async initialization via `initialize()` method
- Clean shutdown via `shutdown()` method
- Progress callbacks for Discord updates

**Discord Bot (discord.py best practices):**
- Main bot in `bot/client.py` extends `commands.Bot`
- `setup_hook()` for post-login initialization
- Command handlers separated in `bot/commands/`
- UI components (Views, Buttons, Modals) in `bot/ui/`

**Configuration:**
- Pydantic models for type safety and validation
- Environment variable support with `.env` file
- `get_config()` returns cached singleton
- Automatic migration from v1.x to v2.0 config format

### Workflow Management

Workflows are ComfyUI JSON files stored in `workflows/` directory:
- `flux_lora.json` - Standard Flux generation
- `flux_krea_lora.json` - Enhanced Flux Krea model
- `dype-flux-krea-lora.json` - **NEW in v2.1** DyPE Flux Krea for ultra high-resolution (up to 4K)
- `flux_kontext_edit.json` - Flux Kontext image editing
- `qwen_image_edit*.json` - Qwen 2.5 VL editing (1-3 images)
- `upscale_config-1.json` - Image upscaling
- `video_wan_vace_14B_i2v.json` - Video generation

**WorkflowManager (`core/comfyui/workflows/manager.py`):**
- Loads workflows from JSON files
- Caches workflows in memory
- Updates workflow parameters dynamically

**WorkflowUpdater (`core/comfyui/workflows/updater.py`):**
- Finds and updates specific nodes in workflows
- Handles prompt, LoRA, image, video parameters
- Type-safe parameter updates

### Progress Tracking System

**Real-time Updates:**
- WebSocket connection to ComfyUI for live progress
- Fallback to HTTP polling if WebSocket unavailable
- Step-based progress calculation (not time-based)
- Detects cached nodes and multi-phase workflows

**Discord Integration:**
- `create_discord_progress_callback()` returns async callback
- Updates Discord embed with progress bar, node info, ETA
- Throttled updates (max 1 per 2 seconds) to avoid rate limits

### Rate Limiting

**Two-tier system:**
- Per-user limit (default: 5 requests/minute)
- Global limit (default: 20 requests/minute)
- Sliding window algorithm
- Configurable via `config.json`

## Important Code Patterns

### Using ComfyUIClient

```python
from core.comfyui.client import ComfyUIClient
from config import get_config

config = get_config()

# Always use async context manager
async with ComfyUIClient(config.comfyui.url, timeout=300) as client:
    prompt_id = await client.queue_prompt(workflow)
    # Client session is automatically closed on exit
```

### Creating Generators

```python
from core.generators.image import ImageGenerator
from core.comfyui.client import ComfyUIClient
from config import get_config

config = get_config()
async with ComfyUIClient(config.comfyui.url) as client:
    generator = ImageGenerator(client, config)
    await generator.initialize()

    # Generate image
    result = await generator.generate(
        prompt="a cat in a hat",
        width=1024,
        height=1024
    )
```

### Discord Command Handlers

Command handlers are in `bot/commands/`:
- Accept `interaction: discord.Interaction` and `bot: ComfyUIBot`
- Check rate limits via `bot._check_rate_limit(user_id)`
- Validate inputs using validators from `core/validators/`
- Use `interaction.response.defer()` for long operations
- Create progress callbacks via `bot._create_unified_progress_callback()`

### Adding New Commands

1. Create handler in `bot/commands/your_command.py`
2. Register in `main.py` using `@bot.tree.command()`
3. Add to fallback import in `main.py` (line 94-100) for backward compatibility

### Workflow Updates

```python
from core.comfyui.workflows import WorkflowManager, WorkflowUpdater

# Load workflow
manager = WorkflowManager(config)
workflow = manager.get_workflow("flux_lora")

# Update parameters
updater = WorkflowUpdater(workflow)
updater.update_prompt("10", "a beautiful sunset")
updater.update_lora("11", "style_lora", 0.8)
```

## Configuration Management

**Config Files:**
- `config.json` - Main configuration (use `config.example.json` as template)
- `.env` - Environment variables (optional)

**Priority:** Environment variables > config.json > defaults

**Getting Config:**
```python
from config import get_config

config = get_config()  # Returns cached singleton
config.discord.token   # Access nested config
config.comfyui.url
```

**Migration:** Old v1.x configs are automatically migrated to v2.0 format on first load.

## Testing Conventions

- Tests in `tests/` directory
- Use pytest with `pytest-asyncio` for async tests
- Mock external dependencies (ComfyUI, Discord)
- Test file naming: `test_<module>.py`
- Integration tests in `tests/integration/`
- Current test status: 85/86 passing (99% pass rate)

**Test Structure:**
```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_something():
    # Arrange
    mock_client = AsyncMock()

    # Act
    result = await function_to_test()

    # Assert
    assert result is not None
```

## Error Handling

**Custom Exceptions (`core/exceptions.py`):**
- `DisComfyError` - Base exception
- `ValidationError` - Input validation errors
- `ComfyUIError` - ComfyUI API errors
- `GenerationError` - Generation process errors

**Best Practices:**
- Always use custom exceptions from `core.exceptions`
- Include context in error messages
- Log errors with appropriate level (error, warning, info)
- Send user-friendly messages to Discord (no stack traces)

## Backward Compatibility

**v2.0 maintains 100% backward compatibility with v1.4.0:**
- Old `bot.py` entry point still works
- Old imports (`from image_gen import ImageGenerator`) still work
- Old command handlers exist as fallback
- Old config format auto-migrated
- See `docs/MIGRATION_GUIDE.md` for details

**When editing code:**
- Prefer new modular architecture for new features
- Keep old code paths working for backward compatibility
- Test both old and new entry points
- Update both old and new code if fixing bugs

## Common Pitfalls

1. **Don't create multiple ComfyUIClient sessions** - Use singleton via `get_config()` or async context manager
2. **Don't forget to defer interactions** - Discord interactions timeout in 3 seconds; use `await interaction.response.defer()` for long operations
3. **Don't hardcode workflow parameters** - Use `WorkflowUpdater` to modify workflows dynamically
4. **Don't skip rate limit checks** - Always check via `bot._check_rate_limit()` before processing
5. **Don't use sync file operations** - Use `aiofiles` or `asyncio.to_thread()` for file I/O
6. **Don't expose ComfyUI errors directly to users** - Wrap in user-friendly messages
7. **Always initialize generators** - Call `await generator.initialize()` before use
8. **Always close resources** - Use async context managers or call cleanup methods

## ComfyUI Integration Details

**Connection:**
- HTTP client for API calls (queue, history, download)
- WebSocket client for real-time progress
- Both clients share same base URL
- Timeout: 300s for generation, 900s for video

**Workflow Execution Flow:**
1. Load workflow JSON from `workflows/`
2. Update workflow parameters via `WorkflowUpdater`
3. Upload images if needed via `client.upload_image()`
4. Queue workflow via `client.queue_prompt()`
5. Connect WebSocket for progress updates
6. Poll history until complete
7. Download outputs via `client.download_output()`
8. Save to `output/` directory
9. Send to Discord

**Progress Tracking:**
- WebSocket messages: `executing`, `progress`, `execution_complete`
- Calculate percentage from sampling steps
- Handle multi-node workflows
- Detect cached nodes (skipped)
- Update Discord embed every 2 seconds

## Discord UI Components

**Views (`bot/ui/`):**
- `GenerationSetupView` - Parameter selection modal
- `ImageActionView` - Upscale/Edit/Animate buttons
- `VideoActionView` - Video-specific actions

**Buttons:**
- Anyone can use buttons (not just original requester)
- Buttons never expire (persistent views)
- Rate limiting applied per user

**Modals:**
- Used for parameter input (upscale ratio, steps, etc.)
- Pre-filled with defaults
- Validation on submit
