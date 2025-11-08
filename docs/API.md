# DisComfy v2.0 API Documentation

**Version:** 2.0  
**Date:** November 2025

---

## Core Modules

### `core.comfyui.client.ComfyUIClient`

HTTP-based ComfyUI client following aiohttp best practices.

#### Methods

**`async initialize()`**
Initialize the client session.

**`async close()`**
Close the client session and cleanup resources.

**`async queue_prompt(workflow: Dict[str, Any]) -> str`**
Queue a prompt for generation and return prompt ID.

**`async get_history(prompt_id: str) -> Dict[str, Any]`**
Get execution history for a prompt.

**`async download_output(filename: str, subfolder: str = "", output_type: str = "output") -> bytes`**
Download generated output file.

**`async test_connection() -> bool`**
Test connection to ComfyUI server.

#### Example

```python
async with ComfyUIClient(base_url="http://localhost:8188") as client:
    prompt_id = await client.queue_prompt(workflow)
    history = await client.get_history(prompt_id)
    image_data = await client.download_output("output.png")
```

---

### `core.validators.image.ImageValidator`

Image validation utility.

#### Methods

**`validate(attachment: discord.Attachment) -> ValidationResult`**
Validate a Discord attachment as an image.

#### Example

```python
validator = ImageValidator(max_size_mb=25)
result = validator.validate(image)
if not result.is_valid:
    print(result.error_message)
```

---

### `utils.rate_limit.RateLimiter`

Rate limiting with per-user and global limits.

#### Methods

**`check_rate_limit(user_id: int) -> bool`**
Check if user is within rate limit.

**`get_user_remaining(user_id: int) -> int`**
Get remaining requests for a user.

**`reset_user(user_id: int) -> None`**
Reset rate limit for a specific user.

#### Example

```python
limiter = RateLimiter(RateLimitConfig(per_user=10, global_limit=100))
if limiter.check_rate_limit(user_id):
    # Process request
    pass
```

---

### `core.progress.tracker.ProgressTracker`

Simplified progress tracking.

#### Methods

**`update_percentage(percentage: float) -> None`**
Update progress percentage (0-100).

**`update_phase(phase: str) -> None`**
Update current phase description.

**`mark_completed() -> None`**
Mark progress as completed.

**`mark_failed(error_message: str) -> None`**
Mark progress as failed.

#### Example

```python
tracker = ProgressTracker()
tracker.update_percentage(50.0)
tracker.update_phase("Sampling")
tracker.mark_completed()
```

---

### `core.comfyui.workflows.updater.WorkflowUpdater`

Strategy-based workflow parameter updater.

#### Methods

**`update(workflow: Dict[str, Any], parameters: WorkflowParameters) -> Dict[str, Any]`**
Update workflow with new parameters.

#### Example

```python
updater = WorkflowUpdater()
params = WorkflowParameters(prompt="test", steps=30)
updated_workflow = updater.update(workflow, params)
```

---

## Bot Modules

### `bot.client.ComfyUIBot`

Main Discord bot client.

#### Methods

**`_check_rate_limit(user_id: int) -> bool`**
Check if user is rate limited.

**`async _create_unified_progress_callback(interaction, title, prompt, settings)`**
Create a progress callback for Discord updates.

---

## Command Handlers

All command handlers are in `bot/commands/`:

- `generate_command_handler()` - Handle /generate command
- `editflux_command_handler()` - Handle /editflux command
- `editqwen_command_handler()` - Handle /editqwen command
- `status_command_handler()` - Handle /status command
- `help_command_handler()` - Handle /help command
- `loras_command_handler()` - Handle /loras command

---

## Exceptions

All exceptions inherit from `DisComfyError`:

- `ValidationError` - Validation failures
- `ComfyUIError` - ComfyUI API errors
- `WorkflowError` - Workflow errors
- `GenerationError` - Generation failures
- `RateLimitError` - Rate limiting errors

---

## Configuration

Configuration is managed via `config` module:

```python
from config import get_config

config = get_config()
print(config.discord.token)
print(config.comfyui.url)
```

---

For more detailed documentation, see individual module docstrings.





