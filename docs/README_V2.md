# DisComfy v2.0

**Discord bot for ComfyUI image and video generation**

**Version:** 2.0 (Refactored Architecture)  
**Status:** Production Ready ✅

---

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Create a `config.json` file or set environment variables:

```bash
export DISCORD_TOKEN=your_bot_token
export COMFYUI_URL=http://localhost:8188
```

### Running the Bot

```bash
# Recommended: Use new v2.0 entry point
python main.py

# Legacy: Old entry point (still works, but deprecated)
python bot.py
```

---

## Features

- ✅ Image generation with multiple models (Flux, Flux Krea, HiDream)
- ✅ LoRA support for style customization
- ✅ Image editing (Flux Kontext, Qwen)
- ✅ Image upscaling
- ✅ Video generation from images
- ✅ Interactive Discord UI with buttons and modals
- ✅ Real-time progress tracking
- ✅ Rate limiting and security

---

## Architecture

DisComfy v2.0 uses a modular architecture:

```
discomfy/
├── bot/              # Discord bot components
│   ├── client.py     # Main bot client
│   ├── commands/     # Command handlers
│   └── ui/           # UI components
├── core/             # Core functionality
│   ├── comfyui/      # ComfyUI integration
│   ├── generators/   # Image/video generators
│   ├── validators/   # Input validation
│   └── progress/     # Progress tracking
├── config/           # Configuration management
└── utils/            # Utility functions
```

---

## Commands

- `/generate` - Generate images with interactive setup
- `/editflux` - Edit images using Flux Kontext
- `/editqwen` - Edit images using Qwen AI
- `/status` - Check bot and ComfyUI status
- `/help` - Show help information
- `/loras` - List available LoRAs

---

## Documentation

- **API Documentation:** `docs/API.md`
- **Usage Examples:** `docs/USAGE_EXAMPLES.md`
- **Migration Guide:** `docs/MIGRATION_GUIDE.md`

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=utils --cov=bot --cov-report=html

# Run integration tests
pytest -m integration
```

---

## Development

### Code Structure

All code follows Context7 best practices:
- Proper async/await patterns
- Type hints throughout
- Pydantic validation
- Comprehensive error handling

### Adding New Features

1. Create feature module in appropriate directory
2. Add tests in `tests/`
3. Update documentation
4. Follow existing patterns

---

## License

[Your License Here]

---

**Built with ❤️ using Context7 best practices**

