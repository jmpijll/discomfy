# DisComfy v2.0 Migration Guide

**Date:** November 2025  
**From:** v1.4.0  
**To:** v2.0

---

## Overview

This guide helps you migrate from DisComfy v1.4.0 to v2.0. The refactoring introduces a new modular architecture while maintaining backward compatibility.

---

## Breaking Changes

### None! ✅

All changes are backward compatible. The old `bot.py` entry point still works, and new modules coexist with old code.

---

## New Entry Point

### Recommended: Use `main.py`

```bash
# New v2.0 entry point
python main.py
```

The new entry point:
- Uses v2.0 command handlers
- Has better error handling
- Supports graceful fallback to old handlers

### Legacy: Still Supported

```bash
# Old entry point (still works)
python bot.py
```

---

## Import Changes

### Old Imports (Still Work)
```python
from image_gen import ImageGenerator
from video_gen import VideoGenerator
from config import get_config
```

### New Imports (Recommended)
```python
# ComfyUI Client
from core.comfyui.client import ComfyUIClient

# Generators
from core.generators.image import ImageGenerator
from core.generators.base import BaseGenerator, GeneratorType

# Configuration
from config import get_config  # Still works!
from config.models import BotConfig

# Validators
from core.validators.image import ImageValidator, PromptParameters

# Utilities
from utils.rate_limit import RateLimiter
from utils.files import save_output_image, get_unique_filename

# Exceptions
from core.exceptions import (
    ValidationError,
    ComfyUIError,
    GenerationError
)
```

---

## Configuration

No changes needed! Your existing `config.json` works as-is.

Environment variables still work:
```bash
export DISCORD_TOKEN=your_token
export COMFYUI_URL=http://localhost:8188
```

---

## Command Usage

No changes! All commands work exactly the same:

```
/generate prompt:Your prompt
/editflux image:<upload> prompt:Edit prompt
/editqwen image:<upload> prompt:Edit prompt
/status
/help
/loras
```

---

## Code Changes (For Developers)

### Using New Architecture

**Old Way:**
```python
from image_gen import ImageGenerator

generator = ImageGenerator()
await generator.initialize()
images, info = await generator.generate_image(...)
```

**New Way:**
```python
from core.comfyui.client import ComfyUIClient
from core.generators.image import ImageGenerator
from config import get_config

config = get_config()
async with ComfyUIClient(config.comfyui.url) as client:
    generator = ImageGenerator(client, config)
    await generator.initialize()
    # Use new architecture
```

---

## Testing

New test suite available:

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run with coverage
pytest --cov=core --cov=utils --cov=bot
```

---

## Performance Improvements

v2.0 includes:
- Better connection pooling (aiohttp)
- Reduced code duplication
- Optimized workflow updates
- Simplified progress tracking

---

## Rollback Plan

If you encounter issues:

1. **Use old entry point:**
   ```bash
   python bot.py
   ```

2. **Old imports still work:**
   - All old imports are preserved
   - Old code coexists with new

3. **No data migration needed:**
   - Configuration unchanged
   - Workflows unchanged
   - No database migrations

---

## Next Steps

1. **Try new entry point:**
   ```bash
   python main.py
   ```

2. **Gradually adopt new imports:**
   - Start using new modules in new code
   - Old code continues to work

3. **Run tests:**
   ```bash
   pytest
   ```

4. **Report issues:**
   - File issues if you find problems
   - Old code remains available as fallback

---

## Support

- **Documentation:** See `docs/API.md` and `docs/USAGE_EXAMPLES.md`
- **Tests:** See `tests/` directory
- **Examples:** See `docs/USAGE_EXAMPLES.md`

---

**Migration is safe and backward compatible!** ✅


