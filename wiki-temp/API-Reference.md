# API Reference

Complete API documentation for DisComfy v2.0.

---

## 🏗️ Architecture Overview

DisComfy v2.0 follows a modular architecture with clear separation of concerns:

```
discomfy/
├── bot/                    # Discord bot layer
│   ├── client.py          # Main bot client
│   ├── commands/          # Command handlers
│   └── ui/                # Discord UI components
├── core/                  # Core functionality
│   ├── comfyui/          # ComfyUI integration
│   ├── generators/       # Generation engines
│   ├── progress/         # Progress tracking
│   └── validators/       # Input validation
├── config/               # Configuration management
├── utils/                # Utility functions
└── main.py               # Entry point
```

---

## 🔌 Core Modules

### core.comfyui.client.ComfyUIClient

HTTP-based ComfyUI client following aiohttp best practices.

#### Constructor

```python
ComfyUIClient(base_url: str, timeout: int = 300)
```

**Parameters:**
- `base_url` - ComfyUI server URL
- `timeout` - Request timeout in seconds

#### Methods

**`async initialize() -> None`**

Initialize the client session.

```python
client = ComfyUIClient("http://localhost:8188")
await client.initialize()
```

**`async close() -> None`**

Close the client session and cleanup resources.

```python
await client.close()
```

**`async queue_prompt(workflow: Dict[str, Any]) -> str`**

Queue a prompt for generation and return prompt ID.

```python
workflow = {...}  # ComfyUI workflow dict
prompt_id = await client.queue_prompt(workflow)
print(f"Queued: {prompt_id}")
```

**Returns:** Prompt ID string

**Raises:** 
- `ComfyUIError` - If queueing fails

**`async get_history(prompt_id: str) -> Dict[str, Any]`**

Get execution history for a prompt.

```python
history = await client.get_history(prompt_id)
if prompt_id in history:
    # Process history
    pass
```

**`async download_output(filename: str, subfolder: str = "", output_type: str = "output") -> bytes`**

Download generated output file.

```python
image_data = await client.download_output(
    filename="output_001.png",
    subfolder="",
    output_type="output"
)
```

**Returns:** File data as bytes

**`async test_connection() -> bool`**

Test connection to ComfyUI server.

```python
if await client.test_connection():
    print("ComfyUI connected!")
```

#### Context Manager

```python
async with ComfyUIClient(base_url="http://localhost:8188") as client:
    prompt_id = await client.queue_prompt(workflow)
    history = await client.get_history(prompt_id)
    data = await client.download_output("output.png")
```

---

### core.validators.image.ImageValidator

Image validation utility.

#### Constructor

```python
ImageValidator(
    max_size_mb: int = 25,
    allowed_extensions: Optional[Set[str]] = None
)
```

#### Methods

**`validate(attachment: discord.Attachment) -> ValidationResult`**

Validate a Discord attachment as an image.

```python
validator = ImageValidator(max_size_mb=25)
result = validator.validate(image_attachment)

if result.is_valid:
    print("Image valid!")
else:
    print(f"Error: {result.error_message}")
```

**ValidationResult fields:**
- `is_valid: bool` - Whether validation passed
- `error_message: Optional[str]` - Error description if failed
- `file_size: Optional[int]` - File size in bytes
- `extension: Optional[str]` - File extension

---

### core.validators.image.PromptParameters

Pydantic model for prompt validation.

```python
from core.validators.image import PromptParameters

params = PromptParameters(
    prompt="a beautiful landscape",
    width=1024,
    height=1024,
    steps=30,
    cfg=7.5,
    seed=-1,
    batch_size=1
)
```

**Fields:**
- `prompt: str` - Required, 1-500 characters
- `width: int` - 256-2048, multiple of 64
- `height: int` - 256-2048, multiple of 64
- `steps: int` - 1-50
- `cfg: float` - 1.0-20.0
- `seed: int` - -1 or positive
- `batch_size: int` - 1-4

**Raises:** `ValidationError` if parameters invalid

---

### utils.rate_limit.RateLimiter

Rate limiting with per-user and global limits.

#### Constructor

```python
from utils.rate_limit import RateLimiter, RateLimitConfig

config = RateLimitConfig(
    per_user=10,
    global_limit=100,
    window_seconds=60
)
limiter = RateLimiter(config)
```

#### Methods

**`check_rate_limit(user_id: int) -> bool`**

Check if user is within rate limit.

```python
if limiter.check_rate_limit(user_id):
    # Process request
    pass
else:
    # User is rate limited
    pass
```

**`get_user_remaining(user_id: int) -> int`**

Get remaining requests for a user.

```python
remaining = limiter.get_user_remaining(user_id)
print(f"Remaining: {remaining}")
```

**`reset_user(user_id: int) -> None`**

Reset rate limit for a specific user.

```python
limiter.reset_user(user_id)
```

---

### core.progress.tracker.ProgressTracker

Simplified progress tracking.

#### Methods

**`update_percentage(percentage: float) -> None`**

Update progress percentage (0-100).

```python
tracker = ProgressTracker()
tracker.update_percentage(50.0)
```

**`update_phase(phase: str) -> None`**

Update current phase description.

```python
tracker.update_phase("Sampling")
```

**`mark_completed() -> None`**

Mark progress as completed.

```python
tracker.mark_completed()
```

**`mark_failed(error_message: str) -> None`**

Mark progress as failed.

```python
tracker.mark_failed("Generation failed")
```

**`get_metrics() -> ProgressMetrics`**

Get current progress metrics.

```python
metrics = tracker.get_metrics()
print(f"Progress: {metrics.percentage}%")
print(f"Phase: {metrics.phase}")
```

---

### core.comfyui.workflows.updater.WorkflowUpdater

Strategy-based workflow parameter updater.

#### Methods

**`update(workflow: Dict[str, Any], parameters: WorkflowParameters) -> Dict[str, Any]`**

Update workflow with new parameters.

```python
from core.comfyui.workflows.updater import WorkflowUpdater, WorkflowParameters

updater = WorkflowUpdater()
params = WorkflowParameters(
    prompt="test prompt",
    steps=30,
    cfg=7.5
)
updated_workflow = updater.update(workflow, params)
```

---

## 🎮 Bot Modules

### bot.client.ComfyUIBot

Main Discord bot client.

#### Methods

**`_check_rate_limit(user_id: int) -> bool`**

Check if user is rate limited.

```python
if bot._check_rate_limit(interaction.user.id):
    # Allow request
    pass
```

**`async _create_unified_progress_callback(interaction, title, prompt, settings)`**

Create a progress callback for Discord updates.

---

## 🎯 Command Handlers

Located in `bot/commands/`:

### generate.py

**`generate_command_handler(bot, interaction, ...)`**

Handle `/generate` command with interactive setup.

### edit.py

**`editflux_command_handler(bot, interaction, ...)`**

Handle `/editflux` command for Flux editing.

**`editqwen_command_handler(bot, interaction, ...)`**

Handle `/editqwen` command for Qwen editing.

### status.py

**`status_command_handler(bot, interaction)`**

Handle `/status` command.

### loras.py

**`loras_command_handler(bot, interaction)`**

Handle `/loras` command to list available LoRAs.

---

## ❌ Exceptions

All exceptions inherit from `DisComfyError`.

### Exception Hierarchy

```python
DisComfyError (base)
├── ValidationError
├── ComfyUIError
├── WorkflowError
├── GenerationError
└── RateLimitError
```

### Usage

```python
from core.exceptions import (
    ValidationError,
    ComfyUIError,
    GenerationError
)

try:
    # Your code
    pass
except ValidationError as e:
    print(f"Validation error: {e}")
    print(f"Field: {e.field}")
except ComfyUIError as e:
    print(f"ComfyUI error: {e}")
    print(f"Status code: {e.status_code}")
except GenerationError as e:
    print(f"Generation failed: {e}")
```

---

## ⚙️ Configuration

### Loading Configuration

```python
from config import get_config

config = get_config()
print(config.discord.token)
print(config.comfyui.url)
```

### Configuration Models

```python
from config.models import (
    BotConfig,
    DiscordConfig,
    ComfyUIConfig,
    GenerationConfig
)

# Access configuration
discord_config: DiscordConfig = config.discord
comfyui_config: ComfyUIConfig = config.comfyui
```

---

## 🔧 Utility Functions

### utils.files

**`save_output_image(image_data: bytes, prefix: str = "output") -> str`**

Save image data to output directory.

```python
from utils.files import save_output_image

filepath = save_output_image(image_data, prefix="gen")
print(f"Saved to: {filepath}")
```

**`get_unique_filename(prefix: str = "output", extension: str = "png") -> str`**

Generate unique filename with timestamp.

```python
from utils.files import get_unique_filename

filename = get_unique_filename(prefix="image", extension="png")
# Returns: "image_20250102_143025_abc123.png"
```

**`cleanup_old_files(directory: str, max_files: int = 100) -> int`**

Clean up old files in directory.

```python
from utils.files import cleanup_old_files

removed = cleanup_old_files("./outputs", max_files=100)
print(f"Removed {removed} files")
```

### utils.logging

**`setup_logging(config: LoggingConfig) -> None`**

Set up logging configuration.

```python
from utils.logging import setup_logging
from config.models import LoggingConfig

log_config = LoggingConfig(
    level="INFO",
    file="logs/bot.log"
)
setup_logging(log_config)
```

---

## 🎨 UI Components

### bot.ui.modals

Discord modals for parameter input.

**`UpscaleModal`** - Upscale parameters  
**`VideoModal`** - Video generation parameters  
**`EditModal`** - Edit prompt input  

### bot.ui.buttons

Action buttons for generated content.

**`UpscaleButton`** - Trigger upscaling  
**`EditFluxButton`** - Flux editing  
**`EditQwenButton`** - Qwen editing  
**`AnimateButton`** - Video generation  

### bot.ui.view

Views containing buttons and dropdowns.

**`SetupView`** - Interactive generation setup  
**`PostView`** - Post-generation action buttons  

---

## 📝 Creating Custom Generators

### Base Generator

```python
from core.generators.base import BaseGenerator, GeneratorType
from typing import Optional, Tuple

class MyGenerator(BaseGenerator):
    """Custom generator implementation."""
    
    @property
    def generator_type(self) -> GeneratorType:
        return GeneratorType.IMAGE
    
    async def initialize(self) -> None:
        """Initialize generator resources."""
        pass
    
    async def shutdown(self) -> None:
        """Cleanup generator resources."""
        pass
    
    async def generate(
        self,
        prompt: str,
        **kwargs
    ) -> Tuple[bytes, dict]:
        """
        Generate content.
        
        Args:
            prompt: Generation prompt
            **kwargs: Additional parameters
            
        Returns:
            Tuple of (content_data, metadata)
        """
        # Implementation
        pass
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_validators.py

# Run with coverage
pytest --cov=core --cov=utils --cov=bot

# Run integration tests
pytest -m integration
```

### Writing Tests

```python
import pytest
from core.validators.image import ImageValidator

def test_image_validation():
    """Test image validator."""
    validator = ImageValidator(max_size_mb=25)
    # Test logic
    assert validator is not None

@pytest.mark.asyncio
async def test_comfyui_client():
    """Test ComfyUI client."""
    from core.comfyui.client import ComfyUIClient
    
    async with ComfyUIClient("http://localhost:8188") as client:
        connected = await client.test_connection()
        assert connected is True
```

---

## 📚 Advanced Usage

### Custom Workflow Integration

```python
from core.comfyui.workflows.updater import WorkflowUpdater
from core.comfyui.workflows.manager import WorkflowManager

# Load custom workflow
manager = WorkflowManager(workflows_dir="./workflows")
workflow = manager.load_workflow("my_custom_workflow")

# Update parameters
updater = WorkflowUpdater()
updated = updater.update(workflow, parameters)

# Queue for generation
async with ComfyUIClient(url) as client:
    prompt_id = await client.queue_prompt(updated)
```

### Custom Progress Callbacks

```python
from core.progress.tracker import ProgressTracker

def my_progress_callback(metrics):
    """Custom progress handler."""
    print(f"Progress: {metrics.percentage}%")
    print(f"Phase: {metrics.phase}")

tracker = ProgressTracker()
tracker.add_callback(my_progress_callback)
tracker.update_percentage(50.0)
```

### Custom Validation

```python
from pydantic import BaseModel, Field, validator

class CustomParameters(BaseModel):
    """Custom parameter validation."""
    
    custom_field: str = Field(..., min_length=1, max_length=100)
    
    @validator('custom_field')
    def validate_custom(cls, v):
        if "bad_word" in v.lower():
            raise ValueError("Invalid content")
        return v

# Use
try:
    params = CustomParameters(custom_field="test")
except Exception as e:
    print(f"Validation failed: {e}")
```

---

## 🔌 Extension Points

### Adding New Commands

```python
# In bot/commands/my_command.py

async def my_command_handler(bot, interaction):
    """Handle custom command."""
    await interaction.response.send_message("Hello!")

# In bot/client.py
from bot.commands.my_command import my_command_handler

@bot.tree.command(name="mycommand", description="My custom command")
async def mycommand(interaction: discord.Interaction):
    await my_command_handler(bot, interaction)
```

### Adding New Workflows

1. Create workflow JSON in ComfyUI (Save as API Format)
2. Place in `workflows/` directory
3. Add to `config.json`:

```json
{
  "workflows": {
    "my_workflow": {
      "file": "my_workflow.json",
      "name": "My Workflow",
      "enabled": true
    }
  }
}
```

### Adding Custom UI Components

```python
from discord.ui import Button, Modal, TextInput
from bot.ui.buttons import BaseButton

class MyButton(BaseButton):
    """Custom button implementation."""
    
    def __init__(self):
        super().__init__(label="My Action", style=discord.ButtonStyle.Primary)
    
    async def callback(self, interaction):
        await interaction.response.send_message("Button clicked!")
```

---

## 📖 Code Examples

See **[[Usage Examples]]** for practical code examples.

### Complete Generation Example

```python
import asyncio
from core.comfyui.client import ComfyUIClient
from core.validators.image import PromptParameters
from core.comfyui.workflows.manager import WorkflowManager
from core.comfyui.workflows.updater import WorkflowUpdater

async def generate_image():
    """Complete image generation example."""
    
    # Validate parameters
    params = PromptParameters(
        prompt="a beautiful landscape",
        width=1024,
        height=1024,
        steps=30
    )
    
    # Load workflow
    manager = WorkflowManager()
    workflow = manager.load_workflow("flux_lora")
    
    # Update workflow
    updater = WorkflowUpdater()
    updated_workflow = updater.update(workflow, params)
    
    # Generate
    async with ComfyUIClient("http://localhost:8188") as client:
        prompt_id = await client.queue_prompt(updated_workflow)
        
        # Wait for completion
        while True:
            history = await client.get_history(prompt_id)
            if prompt_id in history:
                break
            await asyncio.sleep(2)
        
        # Download result
        outputs = history[prompt_id]['outputs']
        for node_id, node_output in outputs.items():
            if 'images' in node_output:
                for image in node_output['images']:
                    data = await client.download_output(
                        image['filename'],
                        image.get('subfolder', '')
                    )
                    # Save or process data
                    print(f"Generated image: {len(data)} bytes")

# Run
asyncio.run(generate_image())
```

---

**🔧 For more examples, see the test files in the `tests/` directory.**

