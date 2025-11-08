# Developer Guide

Guide for developers working with or extending DisComfy v2.0.

---

## 🏗️ Architecture

DisComfy v2.0 follows a clean, modular architecture:

```
discomfy/
├── main.py              # Entry point
├── bot/                 # Discord bot layer
│   ├── client.py       # Main bot client
│   ├── commands/       # Command handlers
│   └── ui/             # Discord UI components
├── core/               # Core functionality
│   ├── comfyui/       # ComfyUI integration
│   ├── generators/    # Generation engines
│   ├── progress/      # Progress tracking
│   └── validators/    # Input validation
├── config/            # Configuration
├── utils/             # Utilities
└── tests/             # Test suite
```

---

## 🚀 Getting Started

### Development Setup

```bash
# Clone repository
git clone https://github.com/jmpijll/discomfy.git
cd discomfy

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Start bot
python main.py
```

### Code Style

DisComfy follows:
- PEP 8 style guide
- Type hints throughout
- Docstrings for all public methods
- Async/await patterns
- Context managers for resources

---

## 🔧 Core Components

### Bot Client

Main bot class in `bot/client.py`:

```python
class ComfyUIBot(commands.Bot):
    """Main Discord bot client."""
    
    def __init__(self, config: BotConfig):
        # Initialize bot with config
        pass
    
    async def setup_hook(self):
        # Initialize generators, sync commands
        pass
    
    async def close(self):
        # Cleanup resources
        pass
```

### Command Handlers

Commands in `bot/commands/`:

```python
# bot/commands/my_command.py

async def my_command_handler(bot, interaction, **params):
    """
    Handle custom command.
    
    Args:
        bot: Bot instance
        interaction: Discord interaction
        **params: Command parameters
    """
    await interaction.response.defer()
    
    # Process command
    
    await interaction.followup.send("Done!")
```

Register in `bot/client.py`:

```python
from bot.commands.my_command import my_command_handler

@bot.tree.command(name="mycommand", description="My custom command")
async def mycommand(interaction: discord.Interaction):
    await my_command_handler(bot, interaction)
```

### Generators

Base generator class in `core/generators/base.py`:

```python
from abc import ABC, abstractmethod
from typing import Tuple
from enum import Enum

class GeneratorType(Enum):
    IMAGE = "image"
    VIDEO = "video"

class BaseGenerator(ABC):
    """Base class for generators."""
    
    @property
    @abstractmethod
    def generator_type(self) -> GeneratorType:
        """Return generator type."""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize generator."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanup generator."""
        pass
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> Tuple[bytes, dict]:
        """
        Generate content.
        
        Args:
            prompt: Generation prompt
            **kwargs: Additional parameters
            
        Returns:
            Tuple of (content_data, metadata)
        """
        pass
```

### Validators

Pydantic models in `core/validators/`:

```python
from pydantic import BaseModel, Field, validator

class MyParameters(BaseModel):
    """Parameter validation model."""
    
    field1: str = Field(..., min_length=1, max_length=100)
    field2: int = Field(..., ge=1, le=100)
    
    @validator('field1')
    def validate_field1(cls, v):
        # Custom validation
        if "bad" in v.lower():
            raise ValueError("Invalid content")
        return v
```

### UI Components

Discord UI in `bot/ui/`:

```python
from discord.ui import Button, Modal, TextInput, View

class MyButton(Button):
    """Custom button."""
    
    def __init__(self):
        super().__init__(
            label="My Action",
            style=discord.ButtonStyle.Primary,
            custom_id="my_button"
        )
    
    async def callback(self, interaction):
        """Handle button click."""
        await interaction.response.send_message("Clicked!")

class MyModal(Modal):
    """Custom modal."""
    
    def __init__(self):
        super().__init__(title="My Modal")
        
        self.field = TextInput(
            label="Input",
            placeholder="Enter value",
            required=True
        )
        self.add_item(self.field)
    
    async def on_submit(self, interaction):
        """Handle modal submission."""
        value = self.field.value
        await interaction.response.send_message(f"Got: {value}")
```

---

## 🧪 Testing

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_validators.py

# With coverage
pytest --cov=core --cov=utils --cov=bot

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Writing Tests

```python
import pytest
from core.validators.image import PromptParameters

def test_prompt_validation():
    """Test prompt parameter validation."""
    # Valid prompt
    params = PromptParameters(prompt="test prompt")
    assert params.prompt == "test prompt"
    
    # Invalid prompt (too short)
    with pytest.raises(ValueError):
        PromptParameters(prompt="")

@pytest.mark.asyncio
async def test_comfyui_client():
    """Test ComfyUI client."""
    from core.comfyui.client import ComfyUIClient
    
    async with ComfyUIClient("http://localhost:8188") as client:
        connected = await client.test_connection()
        assert connected is True

@pytest.fixture
def mock_config():
    """Provide mock configuration."""
    from config.models import BotConfig
    return BotConfig(
        discord={"token": "test"},
        comfyui={"url": "http://localhost:8188"}
    )
```

### Test Coverage

Current coverage: **99%** (85/86 tests passing)

```bash
# Generate coverage report
pytest --cov=core --cov=utils --cov=bot --cov-report=html

# View report
open htmlcov/index.html
```

---

## 📦 Adding Features

### Adding a New Command

1. **Create command handler** in `bot/commands/my_command.py`:

```python
async def my_command_handler(bot, interaction, param1: str, param2: int):
    """
    Handle my custom command.
    
    Args:
        bot: Bot instance
        interaction: Discord interaction
        param1: First parameter
        param2: Second parameter
    """
    await interaction.response.defer()
    
    try:
        # Process command
        result = f"Processed: {param1} with {param2}"
        await interaction.followup.send(result)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")
```

2. **Register in bot** in `bot/client.py`:

```python
from bot.commands.my_command import my_command_handler

@self.tree.command(name="mycommand", description="My custom command")
@app_commands.describe(
    param1="First parameter",
    param2="Second parameter"
)
async def mycommand(
    interaction: discord.Interaction,
    param1: str,
    param2: int = 10
):
    await my_command_handler(self, interaction, param1, param2)
```

3. **Write tests** in `tests/test_my_command.py`:

```python
import pytest

@pytest.mark.asyncio
async def test_my_command():
    """Test custom command."""
    # Test logic
    pass
```

### Adding a New Generator

1. **Create generator** in `core/generators/my_generator.py`:

```python
from core.generators.base import BaseGenerator, GeneratorType
from typing import Tuple

class MyGenerator(BaseGenerator):
    """Custom generator implementation."""
    
    def __init__(self, client, config):
        self.client = client
        self.config = config
    
    @property
    def generator_type(self) -> GeneratorType:
        return GeneratorType.IMAGE
    
    async def initialize(self) -> None:
        """Initialize generator."""
        # Setup resources
        pass
    
    async def shutdown(self) -> None:
        """Cleanup generator."""
        # Cleanup resources
        pass
    
    async def generate(
        self,
        prompt: str,
        **kwargs
    ) -> Tuple[bytes, dict]:
        """Generate content."""
        # Implementation
        workflow = self._prepare_workflow(prompt, **kwargs)
        prompt_id = await self.client.queue_prompt(workflow)
        
        # Wait for completion
        # Download result
        # Return data and metadata
        
        return image_data, {"prompt": prompt, **kwargs}
```

2. **Integrate in bot** in `bot/client.py`:

```python
from core.generators.my_generator import MyGenerator

async def setup_hook(self):
    # ... existing code ...
    self.my_generator = MyGenerator(self.client, self.config)
    await self.my_generator.initialize()
```

### Adding a New Workflow

1. **Create workflow in ComfyUI:**
   - Design workflow in ComfyUI web interface
   - Save → **Save (API Format)**
   - Save as `my_workflow.json`

2. **Add to workflows directory:**
```bash
cp ~/Downloads/my_workflow.json workflows/
```

3. **Add to config.json:**
```json
{
  "workflows": {
    "my_workflow": {
      "file": "my_workflow.json",
      "name": "My Workflow",
      "description": "Custom workflow for X",
      "enabled": true
    }
  }
}
```

4. **Create workflow updater** (if needed):

```python
# In core/comfyui/workflows/strategies.py

class MyWorkflowStrategy:
    """Update strategy for my workflow."""
    
    def update(self, workflow: dict, params: WorkflowParameters) -> dict:
        """Update workflow with parameters."""
        # Find relevant nodes
        # Update node inputs
        # Return updated workflow
        return workflow
```

---

## 🔌 Extension Points

### Custom Validators

```python
from pydantic import BaseModel, validator

class CustomValidator(BaseModel):
    """Custom validation logic."""
    
    custom_field: str
    
    @validator('custom_field')
    def validate_custom(cls, v):
        # Custom validation
        if not v.startswith("prefix_"):
            raise ValueError("Must start with prefix_")
        return v
```

### Custom Progress Callbacks

```python
from core.progress.tracker import ProgressTracker

def my_progress_handler(metrics):
    """Handle progress updates."""
    print(f"Progress: {metrics.percentage}%")
    # Custom logic

tracker = ProgressTracker()
tracker.add_callback(my_progress_handler)
```

### Custom UI Components

```python
from discord.ui import View, Button

class MyView(View):
    """Custom view with buttons."""
    
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MyButton())

class MyButton(Button):
    """Custom button."""
    
    async def callback(self, interaction):
        await interaction.response.send_message("Custom action!")
```

---

## 📚 Best Practices

### Code Organization

1. **One responsibility per module**
2. **Clear module names**
3. **Logical directory structure**
4. **Avoid circular imports**

### Async Patterns

```python
# Use context managers for resources
async with ComfyUIClient(url) as client:
    # Use client
    pass

# Proper error handling
try:
    result = await async_operation()
except SpecificError as e:
    # Handle specific error
    pass
finally:
    # Cleanup
    pass

# Use asyncio.gather for parallel operations
results = await asyncio.gather(
    operation1(),
    operation2(),
    return_exceptions=True
)
```

### Error Handling

```python
from core.exceptions import DisComfyError, ValidationError

def my_function(param):
    """Function with proper error handling."""
    try:
        # Operation
        result = process(param)
        return result
    except ValidationError as e:
        # Handle validation error
        logger.error(f"Validation failed: {e}")
        raise
    except Exception as e:
        # Convert to DisComfy error
        logger.exception("Unexpected error")
        raise DisComfyError(f"Operation failed: {e}") from e
```

### Type Hints

```python
from typing import Optional, List, Dict, Any, Tuple

async def my_function(
    param1: str,
    param2: Optional[int] = None,
    param3: List[str] = None
) -> Tuple[bytes, Dict[str, Any]]:
    """Function with type hints."""
    if param3 is None:
        param3 = []
    
    # Implementation
    data = b"result"
    metadata = {"key": "value"}
    
    return data, metadata
```

### Documentation

```python
def my_function(param1: str, param2: int) -> str:
    """
    Short description of function.
    
    Longer description explaining what the function does,
    any important details, and usage examples.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is invalid
        DisComfyError: When operation fails
        
    Example:
        >>> result = my_function("test", 42)
        >>> print(result)
        "test_42"
    """
    # Implementation
    pass
```

---

## 🐛 Debugging

### Enable Debug Logging

```json
{
  "logging": {
    "level": "DEBUG"
  }
}
```

### Interactive Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use built-in breakpoint()
breakpoint()
```

### Print Debugging

```python
import logging
logger = logging.getLogger(__name__)

logger.debug(f"Variable: {variable}")
logger.info(f"Processing: {item}")
logger.warning(f"Unusual condition: {condition}")
logger.error(f"Error occurred: {error}")
```

### Test Individual Components

```bash
# Test specific module
python -m core.validators.image

# Test with Python REPL
python
>>> from core.comfyui.client import ComfyUIClient
>>> import asyncio
>>> client = ComfyUIClient("http://localhost:8188")
>>> asyncio.run(client.initialize())
```

---

## 📖 Resources

- **[[API Reference]]** - Complete API documentation
- **[[Testing Guide]]** - Testing documentation
- **[[Architecture Overview]]** - System design
- **GitHub Repository** - https://github.com/jmpijll/discomfy

---

## 🤝 Contributing

### Before Contributing

1. Read the code of conduct
2. Check existing issues
3. Discuss major changes first

### Development Workflow

1. Fork repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes
4. Write tests
5. Run tests: `pytest`
6. Commit: `git commit -m "Add feature"`
7. Push: `git push origin feature/my-feature`
8. Create pull request

### Pull Request Guidelines

- Clear description of changes
- Tests for new features
- Update documentation
- Follow code style
- Reference related issues

---

**🔧 Ready to extend DisComfy? Check out the [[API Reference]] for detailed API docs!**
