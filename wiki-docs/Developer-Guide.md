# Developer Guide 🛠️

Complete guide for developers who want to contribute to DisComfy or integrate new features.

---

## 🏗️ Architecture Overview

### Core Components

```
discomfy/
├── bot.py              # Discord bot, commands, UI components
├── image_gen.py        # Image generation, ComfyUI integration
├── video_gen.py        # Video generation workflows
├── video_ui.py         # Video-specific UI components
├── config.py           # Configuration management
└── workflows/          # ComfyUI workflow definitions
```

### Component Responsibilities

**bot.py** - Discord Interface
- Slash command registration
- Discord UI (buttons, modals, select menus)
- User interaction handling
- Progress update management
- Error handling and user feedback

**image_gen.py** - Generation Engine
- ComfyUI API communication
- Workflow loading and validation
- Parameter management
- WebSocket progress tracking
- Image/video downloading

**config.py** - Configuration
- JSON configuration loading
- Environment variable support
- Configuration validation
- Default value management

---

## 🚀 Development Setup

### Prerequisites
- Python 3.10+ (for best compatibility)
- Git
- Text editor/IDE (VS Code recommended)
- ComfyUI instance for testing

### Initial Setup

```bash
# Clone and setup
git clone https://github.com/jmpijll/discomfy.git
cd discomfy

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pylint black mypy
```

### Development Configuration

Create `config-dev.json`:
```json
{
  "discord": {
    "token": "YOUR_DEV_BOT_TOKEN",
    "guild_id": "YOUR_TEST_SERVER_ID"
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
  "logging": {
    "level": "DEBUG"
  }
}
```

---

## 📝 Code Style Guidelines

### Python Style
Follow PEP 8 with these conventions:

```python
# Type hints for all functions
async def generate_image(
    self,
    prompt: str,
    width: int = 1024,
    height: int = 1024,
) -> Tuple[List[bytes], Dict[str, Any]]:
    """Generate images using ComfyUI.
    
    Args:
        prompt: Image generation prompt
        width: Image width in pixels
        height: Image height in pixels
        
    Returns:
        Tuple of (image_data_list, generation_info_dict)
        
    Raises:
        ComfyUIAPIError: If generation fails
    """
    pass

# Docstrings for classes
class ImageGenerator:
    """Handles image generation using ComfyUI API.
    
    This class manages all communication with ComfyUI including:
    - Workflow loading and validation
    - Prompt queuing
    - Progress tracking via WebSocket
    - Image downloading
    """
    pass

# Clear variable names
user_prompt = interaction.options.get('prompt')
generation_params = self._prepare_parameters(user_prompt)
```

### Formatting

```bash
# Format code with black
black bot.py image_gen.py

# Check with pylint
pylint bot.py

# Type check with mypy
mypy bot.py
```

---

## 🔧 Adding New Features

### Adding a New Slash Command

**Step 1: Define Command in bot.py**

```python
@app_commands.command(
    name="mycommand",
    description="Description of what command does"
)
@app_commands.describe(
    prompt="What to generate",
    parameter="Description of parameter"
)
async def my_command(
    self,
    interaction: discord.Interaction,
    prompt: str,
    parameter: int = 10
):
    """Command implementation."""
    try:
        await interaction.response.defer()
        
        # Your logic here
        result = await self._process_command(prompt, parameter)
        
        # Send response
        await interaction.followup.send(
            content="Command complete!",
            file=discord.File(result, filename="output.png")
        )
        
    except Exception as e:
        self.logger.error(f"Command failed: {e}")
        await interaction.followup.send(
            f"❌ Error: {str(e)}",
            ephemeral=True
        )
```

**Step 2: Register Command**

```python
# In ComfyUIBot.__init__()
self.tree.add_command(self.my_command)
```

### Adding a New Button

**Step 1: Create Button Class**

```python
class MyCustomButton(discord.ui.Button):
    """Custom button for specific action."""
    
    def __init__(self):
        super().__init__(
            label="My Action",
            emoji="🎨",
            style=discord.ButtonStyle.primary,
            custom_id="my_custom_button"
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Handle button click."""
        try:
            # Get bot instance
            bot: ComfyUIBot = interaction.client
            
            # Check rate limit
            if not bot.check_rate_limit(interaction.user.id):
                await interaction.response.send_message(
                    "⏳ Please wait before using this again",
                    ephemeral=True
                )
                return
            
            # Your logic here
            await interaction.response.send_modal(MyCustomModal())
            
        except Exception as e:
            bot.logger.error(f"Button callback failed: {e}")
            await interaction.response.send_message(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )
```

**Step 2: Add to View**

```python
# In button group or view
class MyActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MyCustomButton())
```

### Adding a New Modal

```python
class MyCustomModal(discord.ui.Modal, title="Custom Settings"):
    """Modal for collecting user input."""
    
    # Define input fields
    input_field = discord.ui.TextInput(
        label="Input Label",
        placeholder="Enter value here",
        default="default value",
        required=True,
        max_length=100
    )
    
    number_field = discord.ui.TextInput(
        label="Number Setting",
        placeholder="10-50",
        default="30",
        required=False,
        max_length=3
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission."""
        try:
            # Get values
            input_value = self.input_field.value
            number_value = int(self.number_field.value)
            
            # Validate
            if not 10 <= number_value <= 50:
                raise ValueError("Number must be between 10 and 50")
            
            # Process
            await interaction.response.defer()
            result = await self._process(input_value, number_value)
            
            # Send result
            await interaction.followup.send("Processing complete!")
            
        except ValueError as e:
            await interaction.response.send_message(
                f"❌ Invalid input: {e}",
                ephemeral=True
            )
        except Exception as e:
            self.bot.logger.error(f"Modal submission failed: {e}")
            await interaction.followup.send(f"❌ Error: {e}")
```

---

## 🎨 Adding New Workflows

### Step 1: Create Workflow in ComfyUI

1. Design workflow in ComfyUI
2. Test thoroughly
3. Export using **"Save (API Format)"**
4. Save to `workflows/my_workflow.json`

### Step 2: Validate Workflow Structure

Ensure each node has:
```json
{
  "node_id": {
    "inputs": {
      "parameter": "value"
    },
    "class_type": "NodeType",
    "_meta": {
      "title": "Node Title"
    }
  }
}
```

### Step 3: Add Workflow Configuration

In `config.json`:
```json
"workflows": {
  "my_workflow": {
    "file": "my_workflow.json",
    "name": "My Custom Workflow",
    "description": "Description of workflow",
    "enabled": true
  }
}
```

### Step 4: Add Parameter Update Logic

In `image_gen.py`, create update method:

```python
def _update_my_workflow_parameters(
    self,
    workflow: Dict[str, Any],
    prompt: str,
    custom_param: float,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """Update workflow with user parameters."""
    try:
        updated_workflow = json.loads(json.dumps(workflow))
        
        if seed is None:
            seed = random.randint(0, 2**32 - 1)
        
        # Update specific nodes
        for node_id, node_data in updated_workflow.items():
            class_type = node_data.get('class_type')
            
            if class_type == 'KSampler':
                node_data['inputs']['seed'] = seed
            
            elif class_type == 'CLIPTextEncode':
                title = node_data.get('_meta', {}).get('title', '')
                if 'positive' in title.lower():
                    node_data['inputs']['text'] = prompt
            
            elif class_type == 'CustomNode':
                node_data['inputs']['custom_param'] = custom_param
        
        return updated_workflow
        
    except Exception as e:
        self.logger.error(f"Failed to update workflow: {e}")
        raise ComfyUIAPIError(f"Workflow update failed: {e}")
```

### Step 5: Integrate with Command

```python
# Use in generate command
workflow = self._load_workflow("my_workflow")
updated_workflow = self._update_my_workflow_parameters(
    workflow, prompt, custom_param, seed
)
prompt_id, client_id = await self._queue_prompt(updated_workflow)
```

---

## 📊 Progress Tracking Integration

### Adding Progress Support

```python
async def my_generation_function(
    self,
    params: dict,
    progress_callback=None
) -> bytes:
    """Generate with progress tracking."""
    
    # Queue generation
    prompt_id, client_id = await self._queue_prompt(workflow)
    
    # Wait with progress updates
    history = await self._wait_for_completion_with_websocket(
        prompt_id,
        client_id,
        workflow,
        progress_callback  # Pass callback through
    )
    
    # Download result
    result = await self._download_images(history)
    return result[0]
```

### Creating Progress Callback

```python
async def _create_progress_callback(
    interaction: discord.Interaction,
    title: str,
    description: str
):
    """Create callback for progress updates."""
    
    last_update = 0
    
    async def callback(progress: ProgressInfo):
        nonlocal last_update
        
        # Rate limit updates (every 2 seconds)
        if time.time() - last_update < 2:
            return
        
        last_update = time.time()
        
        # Get status information
        status_title, status_desc, color = progress.get_user_friendly_status()
        
        # Create embed
        embed = discord.Embed(
            title=f"{title} - {status_title}",
            description=f"{description}\n\n{status_desc}",
            color=color
        )
        
        # Update message
        try:
            await interaction.edit_original_response(embed=embed)
        except:
            pass  # Ignore errors (e.g., message deleted)
    
    return callback
```

---

## 🧪 Testing

### Unit Tests

Create `tests/test_image_gen.py`:

```python
import unittest
from image_gen import ImageGenerator

class TestImageGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = ImageGenerator()
    
    def test_workflow_validation(self):
        """Test workflow validation."""
        valid_workflow = {
            "1": {
                "inputs": {},
                "class_type": "KSampler"
            }
        }
        # Should not raise
        self.generator._validate_workflow(valid_workflow, "test")
    
    def test_invalid_workflow(self):
        """Test invalid workflow detection."""
        invalid_workflow = {
            "1": {
                "inputs": {}
                # Missing class_type
            }
        }
        with self.assertRaises(Exception):
            self.generator._validate_workflow(invalid_workflow, "test")
```

### Integration Tests

```python
async def test_full_generation():
    """Test complete generation flow."""
    async with ImageGenerator() as gen:
        # Test connection
        assert await gen.test_connection()
        
        # Test generation
        images, info = await gen.generate_image(
            prompt="test image",
            width=512,
            height=512,
            steps=10
        )
        
        assert len(images) > 0
        assert info['num_images'] > 0
```

### Manual Testing Checklist

- [ ] Command appears in Discord
- [ ] All parameters work correctly
- [ ] Error messages are clear and helpful
- [ ] Progress updates display correctly
- [ ] Buttons respond properly
- [ ] Rate limiting works
- [ ] Results are correct format
- [ ] Logs show appropriate information

---

## 🐛 Debugging

### Enable Debug Logging

```json
// config.json
"logging": {
  "level": "DEBUG"
}
```

### Common Debugging Scenarios

**Command Not Appearing:**
```python
# Check registration
print(f"Registered commands: {[cmd.name for cmd in bot.tree.get_commands()]}")

# Sync commands manually
await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
```

**ComfyUI Communication Issues:**
```python
# Add detailed logging
self.logger.debug(f"Sending request to: {url}")
self.logger.debug(f"Payload: {json.dumps(data, indent=2)}")
self.logger.debug(f"Response status: {response.status}")
self.logger.debug(f"Response body: {await response.text()}")
```

**Progress Not Updating:**
```python
# Log progress updates
async def debug_callback(progress):
    logger.debug(f"Progress update: {progress.percentage}%")
    logger.debug(f"Status: {progress.status}")
    logger.debug(f"Phase: {progress.phase}")
    await original_callback(progress)
```

---

## 📚 API Reference

### ImageGenerator Class

**Main Methods:**

```python
async def generate_image(
    prompt: str,
    negative_prompt: str = "",
    workflow_name: Optional[str] = None,
    width: int = 1024,
    height: int = 1024,
    steps: int = 50,
    cfg: float = 5.0,
    seed: Optional[int] = None,
    batch_size: int = 1,
    lora_name: Optional[str] = None,
    lora_strength: float = 1.0,
    progress_callback=None
) -> Tuple[List[bytes], Dict[str, Any]]
```

```python
async def generate_upscale(
    input_image_data: bytes,
    prompt: str = "",
    negative_prompt: str = "",
    upscale_factor: float = 2.0,
    denoise: float = 0.35,
    steps: int = 20,
    cfg: float = 7.0,
    seed: Optional[int] = None,
    progress_callback=None
) -> Tuple[bytes, Dict[str, Any]]
```

```python
async def generate_edit(
    input_image_data: bytes,
    edit_prompt: str,
    width: int = 1024,
    height: int = 1024,
    steps: int = 20,
    cfg: float = 2.5,
    seed: Optional[int] = None,
    progress_callback=None,
    workflow_type: str = "flux",
    additional_images: Optional[List[bytes]] = None
) -> Tuple[bytes, Dict[str, Any]]
```

### VideoGenerator Class

```python
async def generate_video(
    input_image: bytes,
    prompt: str,
    negative_prompt: str = "",
    num_frames: int = 121,
    strength: float = 0.7,
    steps: int = 4,
    seed: Optional[int] = None,
    progress_callback=None
) -> Tuple[bytes, Dict[str, Any]]
```

---

## 🔒 Security Best Practices

### Input Validation

```python
# Always validate user input
if len(prompt) > MAX_PROMPT_LENGTH:
    raise ValueError(f"Prompt too long (max {MAX_PROMPT_LENGTH})")

if not 512 <= width <= 2048:
    raise ValueError("Width must be between 512 and 2048")

if not isinstance(steps, int) or steps < 1:
    raise ValueError("Steps must be positive integer")
```

### Rate Limiting

```python
def check_rate_limit(self, user_id: int) -> bool:
    """Check if user can perform action."""
    now = time.time()
    last_use = self.last_use_times.get(user_id, 0)
    
    if now - last_use < self.rate_limit_seconds:
        return False
    
    self.last_use_times[user_id] = now
    return True
```

### Error Handling

```python
try:
    result = await risky_operation()
except SpecificError as e:
    # Handle specific error
    self.logger.warning(f"Known issue: {e}")
    return default_value
except Exception as e:
    # Log unexpected errors
    self.logger.error(f"Unexpected error: {e}", exc_info=True)
    raise CustomError(f"Operation failed: {e}")
finally:
    # Always cleanup
    cleanup_resources()
```

---

## 📦 Contributing Guidelines

### Contribution Process

1. **Fork Repository**
2. **Create Feature Branch**
   ```bash
   git checkout -b feature/my-amazing-feature
   ```
3. **Make Changes**
   - Follow code style guidelines
   - Add tests if applicable
   - Update documentation
4. **Commit Changes**
   ```bash
   git commit -m "Add amazing feature: description"
   ```
5. **Push to Fork**
   ```bash
   git push origin feature/my-amazing-feature
   ```
6. **Create Pull Request**
   - Clear title and description
   - Reference related issues
   - Include testing details

### Commit Message Format

```
Type: Brief description

Detailed explanation of changes.

- Change 1
- Change 2
- Change 3

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, etc)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

---

## 🎯 Next Steps

- **[[Custom Workflows]]** - Learn workflow creation
- **[[Architecture Overview]]** - Understand system design
- **[[API Reference]]** - Detailed API documentation
- **[[Contributing]]** - Contribution guidelines

---

**🛠️ Ready to contribute? Start with a simple feature and grow from there!**

