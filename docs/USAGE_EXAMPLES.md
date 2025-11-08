# DisComfy v2.0 Usage Examples

**Date:** November 2025

---

## Basic Usage

### Running the Bot

```bash
python main.py
```

Or using the legacy entry point:

```bash
python bot.py
```

---

## Command Examples

### Generate Images

```
/generate prompt:A beautiful sunset over the ocean
```

The bot will show an interactive setup view where you can:
- Select model (Flux, Flux Krea, HiDream)
- Choose LoRA
- Adjust settings (width, height, steps, CFG)
- Generate with selected parameters

### Edit Images

```
/editflux image:<upload> prompt:Make the sky more blue steps:20
```

Edits an uploaded image using Flux Kontext AI.

### Check Status

```
/status
```

Shows bot and ComfyUI connection status.

### List LoRAs

```
/loras
```

Lists all available LoRAs organized by model.

---

## Programmatic Usage

### Using ComfyUI Client

```python
from core.comfyui.client import ComfyUIClient

async with ComfyUIClient(base_url="http://localhost:8188") as client:
    # Queue a prompt
    prompt_id = await client.queue_prompt(workflow)
    
    # Get history
    history = await client.get_history(prompt_id)
    
    # Download output
    image_data = await client.download_output("output.png")
```

### Using Validators

```python
from core.validators.image import ImageValidator, PromptParameters

# Validate image
validator = ImageValidator(max_size_mb=25)
result = validator.validate(image_attachment)
if not result.is_valid:
    print(f"Error: {result.error_message}")

# Validate prompt
try:
    params = PromptParameters(prompt="A beautiful landscape")
    print(f"Valid prompt: {params.prompt}")
except Exception as e:
    print(f"Invalid prompt: {e}")
```

### Using Rate Limiter

```python
from utils.rate_limit import RateLimiter, RateLimitConfig

config = RateLimitConfig(per_user=10, global_limit=100)
limiter = RateLimiter(config)

if limiter.check_rate_limit(user_id):
    # Process request
    remaining = limiter.get_user_remaining(user_id)
    print(f"Remaining requests: {remaining}")
else:
    print("Rate limited!")
```

### Using Progress Tracker

```python
from core.progress.tracker import ProgressTracker

tracker = ProgressTracker()

# Update progress
tracker.update_percentage(50.0)
tracker.update_phase("Sampling")

# Get current metrics
metrics = tracker.get_metrics()
print(f"Progress: {metrics.percentage}%")

# Mark complete
tracker.mark_completed()
```

---

## Error Handling

```python
from core.exceptions import (
    ValidationError,
    ComfyUIError,
    GenerationError
)

try:
    # Your code here
    pass
except ValidationError as e:
    print(f"Validation error: {e} (field: {e.field})")
except ComfyUIError as e:
    print(f"ComfyUI error: {e} (status: {e.status_code})")
except GenerationError as e:
    print(f"Generation failed: {e}")
```

---

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=utils --cov=bot

# Run specific test file
pytest tests/test_validators.py

# Run integration tests
pytest -m integration
```

---

## Configuration

Create a `config.json` file:

```json
{
  "discord": {
    "token": "YOUR_BOT_TOKEN",
    "guild_id": "YOUR_GUILD_ID"
  },
  "comfyui": {
    "url": "http://localhost:8188",
    "timeout": 300
  }
}
```

Or use environment variables:

```bash
export DISCORD_TOKEN=your_token
export COMFYUI_URL=http://localhost:8188
```

---

For more examples, see the test files in `tests/`.





