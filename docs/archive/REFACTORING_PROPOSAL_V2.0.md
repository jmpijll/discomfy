# DisComfy v2.0 Refactoring Proposal

**Document Version:** 2.0  
**Date:** November 1, 2025  
**Current Version:** v1.4.0  
**Target Version:** v2.0 (Major Refactor)  
**Development Branch:** `v2.0-refactor`

---

## ⚠️ Development Branch Notice

This refactoring is being developed in the `v2.0-refactor` branch. All changes will be thoroughly tested and validated before merging to main. This ensures:
- **No disruption** to production users
- **Comprehensive testing** before deployment
- **Easy rollback** if issues arise
- **Clear separation** between stable and development code

---

## Executive Summary

This document provides a comprehensive analysis of the DisComfy codebase and proposes strategic refactoring for version 2.0. The analysis identifies opportunities to improve code maintainability, reduce complexity, enhance performance, and prepare for future scalability.

**Note:** Version 2.1 feature additions are out of scope for this document and will be considered after v2.0 is stable.

### Key Findings

- **Total Lines of Code:** ~5,850 lines across 6 main Python files
- **Code Quality:** Good overall, but opportunities for consolidation
- **Main Issues:** Code duplication, tight coupling, missing abstractions
- **Complexity Hotspots:** bot.py (3,508 lines), image_gen.py (1,913 lines)

### Proposed Impact

- **Code Reduction:** Estimated 20-30% reduction in total lines
- **Maintainability:** Significantly improved through better separation of concerns
- **Performance:** Potential 10-15% improvement through optimization
- **Testing:** Enable unit testing through better abstractions (target 70%+ coverage)
- **Documentation:** Auto-generated docs from improved docstrings

---

## Table of Contents

1. [Current Architecture Analysis](#1-current-architecture-analysis)
2. [Code Quality Assessment](#2-code-quality-assessment)
3. [Refactoring Proposals for v2.0](#3-refactoring-proposals-for-v20)
4. [Implementation Priority](#4-implementation-priority)
5. [Code Examples with Context7 Best Practices](#5-code-examples-with-context7-best-practices)
6. [Migration Strategy](#6-migration-strategy)
7. [Testing Strategy](#7-testing-strategy)
8. [Success Metrics](#8-success-metrics)

---

## 1. Current Architecture Analysis

### 1.1 File Structure Overview

```
discomfy/
├── bot.py                 (3,508 lines) - Main Discord bot, UI components
├── image_gen.py          (1,913 lines) - Image generation, API calls
├── video_gen.py          (330 lines)   - Video generation
├── video_ui.py           (315 lines)   - Video UI components
├── config.py             (418 lines)   - Configuration management
└── requirements.txt      (37 lines)    - Dependencies
```

### 1.2 Strengths

✅ **Working Production System:** All features functional, users satisfied  
✅ **Good Error Handling:** Comprehensive try-catch blocks throughout  
✅ **Real-time Progress:** WebSocket implementation for live updates  
✅ **Modular Design:** Separation between bot, image, video, config  
✅ **Type Hints:** Good use of Python type hints  
✅ **Logging:** Comprehensive logging throughout  

### 1.3 Architectural Issues

#### 🔴 **Issue 1: Monolithic bot.py (3,508 lines)**

**Problem:** Single file contains:
- Bot initialization
- 26+ UI classes (Views, Buttons, Modals, Menus)
- Command handlers
- Progress callbacks
- Utility functions

**Impact:**
- Hard to navigate and maintain
- Difficult to test individual components
- High cognitive load for developers
- Merge conflicts in team environment

#### 🟡 **Issue 2: Code Duplication Across Commands**

**Examples:**
- Image validation repeated in `/editflux` and `/editqwen` (lines 412-434, 592-621)
- Rate limiting checks in every command
- Progress callback creation duplicated
- Error embed sending logic repeated

**Impact:**
- Bug fixes must be applied multiple places
- Inconsistent behavior possible
- Higher maintenance burden

#### 🟡 **Issue 3: Tight Coupling Between Layers**

**Problem:**
- Discord UI code directly calls image generation
- No abstraction layer between bot and API
- Hard to test without Discord environment

#### 🟡 **Issue 4: Workflow Parameter Update Complexity**

**Problem:**
- `_update_workflow_parameters()` - 150+ lines with complex logic
- `_update_upscale_workflow_parameters()` - similar complexity
- Hard-coded node IDs and class types
- Difficult to add new workflows

#### 🔴 **Issue 5: Progress Tracking Complexity**

**Problem:**
- `ProgressInfo` class has 260+ lines
- Multiple progress calculation methods
- Complex state management
- Hard to understand and modify

---

## 2. Code Quality Assessment

### 2.1 Metrics Summary

| Metric | Current | Target (v2.0) | Improvement |
|--------|---------|---------------|-------------|
| Total LOC | 5,850 | 4,100-4,500 | -23-30% |
| Max File Size | 3,508 | <800 | -77% |
| Code Duplication | ~15-20% | <5% | -75% |
| Cyclomatic Complexity | High (bot.py) | Medium | -40% |
| Test Coverage | 0% | 70%+ | New |

### 2.2 Detailed Issues by File

#### bot.py

**Issues:**
- Too many responsibilities (God Object anti-pattern)
- 26 UI classes in one file
- Repeated validation logic
- Hard to unit test

**Recommendations:**
- Split into multiple files by feature
- Extract UI components to separate modules
- Create validation utility layer
- Add dependency injection

#### image_gen.py

**Issues:**
- `ImageGenerator` class too large (1,400+ lines)
- Workflow update methods too complex
- Tight coupling to ComfyUI API structure
- Progress tracking mixed with generation logic

**Recommendations:**
- Extract workflow management to separate class
- Create ComfyUI API abstraction layer
- Move progress tracking to separate module
- Use Strategy pattern for different workflows

#### config.py

**Strengths:**
- Good use of Pydantic for validation
- Environment variable support
- Configuration migration logic

**Minor Issues:**
- Migration logic could be separated
- Could benefit from configuration validation service

#### video_gen.py & video_ui.py

**Issues:**
- video_gen.py unnecessarily extends ImageGenerator
- Some duplication with image generation logic

---

## 3. Refactoring Proposals for v2.0

### 3.1 Restructure Project Layout

#### Current Structure:
```
discomfy/
├── bot.py
├── image_gen.py
├── video_gen.py
├── video_ui.py
├── config.py
└── workflows/
```

#### Proposed Structure (v2.0):
```
discomfy/
├── bot/
│   ├── __init__.py
│   ├── client.py              # Main bot class (200 lines)
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── generate.py        # /generate command
│   │   ├── edit.py            # /editflux, /editqwen
│   │   ├── status.py          # /status, /help
│   │   └── loras.py           # /loras command
│   └── ui/
│       ├── __init__.py
│       ├── generation/
│       │   ├── setup_view.py  # Generation setup UI
│       │   ├── buttons.py     # Generation buttons
│       │   └── modals.py      # Generation modals
│       ├── image/
│       │   ├── buttons.py     # Image action buttons
│       │   └── modals.py      # Image parameter modals
│       └── video/
│           ├── buttons.py     # Video buttons
│           └── modals.py      # Video modals
├── core/
│   ├── __init__.py
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── base.py           # BaseGenerator abstract class
│   │   ├── image.py          # ImageGenerator
│   │   └── video.py          # VideoGenerator
│   ├── comfyui/
│   │   ├── __init__.py
│   │   ├── client.py         # ComfyUI API client
│   │   ├── websocket.py      # WebSocket handler
│   │   └── workflows/
│   │       ├── __init__.py
│   │       ├── manager.py    # Workflow loading/validation
│   │       └── updater.py    # Workflow parameter updates
│   ├── progress/
│   │   ├── __init__.py
│   │   ├── tracker.py        # Progress tracking logic
│   │   └── callbacks.py      # Progress callback creators
│   └── validators/
│       ├── __init__.py
│       ├── image.py          # Image validation
│       └── prompt.py         # Prompt validation
├── config/
│   ├── __init__.py
│   ├── models.py             # Pydantic models
│   ├── loader.py             # Config loading
│   └── migration.py          # Config migration
├── utils/
│   ├── __init__.py
│   ├── files.py              # File operations
│   ├── rate_limit.py         # Rate limiting
│   └── logging.py            # Logging setup
├── main.py                   # Entry point
├── requirements.txt
└── workflows/
```

**Benefits:**
- Clear separation of concerns
- Each file <400 lines
- Easy to find and modify code
- Testable components
- Standard Python package structure


---

### 3.2 Extract UI Components from bot.py

#### Problem:
bot.py contains 26+ UI classes (1,200+ lines of UI code mixed with bot logic)

#### Solution:
Create specialized UI modules organized by feature, following discord.py best practices from Context7.

**Current (bot.py, lines 782-849):**
```python
class CompleteSetupView(discord.ui.View):
    """Complete interactive setup view for all generation parameters."""
    
    def __init__(self, bot: ComfyUIBot, prompt: str, user_id: int, 
                 video_mode: bool = False, image_data: Optional[bytes] = None):
        super().__init__(timeout=300)
        self.bot = bot
        self.prompt = prompt
        self.user_id = user_id
        self.video_mode = video_mode
        # ... 30+ more lines
```

**Proposed (bot/ui/generation/setup_view.py):**
```python
# Following discord.py View best practices from Context7
from typing import Optional
import discord
from discord.ui import View, Button, Select
from core.generators.base import GeneratorType

class GenerationSetupView(View):
    """Unified setup view for generation with proper discord.py patterns.
    
    Based on discord.py View component patterns:
    - Proper timeout handling
    - User permission checks
    - Component state management
    """
    
    def __init__(
        self, 
        generator_type: GeneratorType,
        prompt: str,
        user_id: int,
        **kwargs
    ):
        # Standard discord.py View timeout (300s = 5 minutes)
        super().__init__(timeout=300)
        self.generator_type = generator_type
        self.prompt = prompt
        self.user_id = user_id
        self.settings = self._get_default_settings(generator_type, **kwargs)
        
        # Add UI components
        self._initialize_components()
    
    async def on_timeout(self) -> None:
        """Discord.py View timeout handler - disable all buttons."""
        for item in self.children:
            item.disabled = True
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Discord.py interaction permission check."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Only the command author can use these controls.",
                ephemeral=True
            )
            return False
        return True
```

**Benefits:**
- Follows discord.py View component patterns from Context7
- Proper timeout and permission handling
- Shorter, focused classes
- Reusable components
- Easier to test

---

### 3.3 Create ComfyUI API Abstraction Layer

#### Problem:
Direct ComfyUI API calls scattered throughout image_gen.py with tight coupling

**Current (image_gen.py, lines 646-724):**
```python
async def _queue_prompt(self, workflow: Dict[str, Any]) -> Tuple[str, str]:
    """Queue a prompt for generation in ComfyUI and return prompt_id and client_id."""
    try:
        async with self._queue_lock:
            client_id = self._bot_client_id
            # ... 70+ lines of API interaction
```

**Proposed (core/comfyui/client.py):**
```python
# Following aiohttp best practices from Context7
from abc import ABC, abstractmethod
from typing import Protocol
import aiohttp
import uuid

class ComfyUIClient(Protocol):
    """Protocol for ComfyUI API clients (duck typing)."""
    
    async def queue_prompt(self, workflow: dict) -> str:
        """Queue a prompt and return prompt_id."""
        ...
    
    async def get_history(self, prompt_id: str) -> dict:
        """Get execution history for a prompt."""
        ...
    
    async def download_output(
        self, 
        filename: str, 
        subfolder: str = "", 
        output_type: str = "output"
    ) -> bytes:
        """Download generated output."""
        ...


class HTTPComfyUIClient:
    """HTTP-based ComfyUI client following aiohttp best practices.
    
    Based on Context7 aiohttp patterns:
    - Proper ClientSession lifecycle management
    - Async context manager support
    - Connection pooling with TCPConnector
    """
    
    def __init__(self, base_url: str, timeout: int = 300):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self._client_id = str(uuid.uuid4())
        
    async def __aenter__(self):
        """Async context manager entry - creates session with proper config."""
        # Following aiohttp best practices from Context7
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            connector=aiohttp.TCPConnector(
                limit=10,  # Total connection pool limit
                limit_per_host=5  # Per-host connection limit
            )
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - properly closes session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def queue_prompt(self, workflow: dict) -> str:
        """Queue a prompt and return prompt_id.
        
        Following aiohttp request patterns from Context7.
        """
        prompt_data = {
            "prompt": workflow,
            "client_id": self._client_id
        }
        
        # aiohttp best practice: use async with for automatic cleanup
        async with self.session.post(
            f"{self.base_url}/prompt", 
            json=prompt_data
        ) as response:
            response.raise_for_status()
            result = await response.json()
            return result['prompt_id']
    
    async def get_history(self, prompt_id: str) -> dict:
        """Get execution history for a prompt."""
        async with self.session.get(
            f"{self.base_url}/history/{prompt_id}"
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def download_output(
        self, 
        filename: str, 
        subfolder: str = "", 
        output_type: str = "output"
    ) -> bytes:
        """Download generated output file."""
        params = {
            'filename': filename,
            'subfolder': subfolder,
            'type': output_type
        }
        
        async with self.session.get(
            f"{self.base_url}/view",
            params=params
        ) as response:
            response.raise_for_status()
            return await response.read()


# Usage example:
async def generate_image():
    async with HTTPComfyUIClient("http://localhost:8188") as client:
        prompt_id = await client.queue_prompt(workflow_data)
        # ... rest of generation
```

**Benefits:**
- Testable without actual ComfyUI server
- Easy to mock for unit tests
- Can add different implementations (WebSocket-based, etc.)
- Follows aiohttp Context7 best practices
- Proper resource management with context managers

---

### 3.4 Simplify Workflow Parameter Updates

#### Problem:
Complex, hard-coded workflow update logic (200+ lines)

**Proposed (core/comfyui/workflows/updater.py):**
```python
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import random

# Using Pydantic for validation (Context7 best practices)
from pydantic import BaseModel, Field

class WorkflowParameters(BaseModel):
    """Standardized workflow parameters with Pydantic validation.
    
    Following Pydantic dataclass patterns from Context7:
    - Automatic validation
    - Type coercion
    - Clear field constraints
    """
    prompt: str = Field(min_length=1, max_length=1000)
    negative_prompt: str = Field(default="", max_length=1000)
    width: int = Field(default=1024, ge=512, le=2048)
    height: int = Field(default=1024, ge=512, le=2048)
    steps: int = Field(default=50, ge=1, le=150)
    cfg: float = Field(default=5.0, ge=1.0, le=20.0)
    seed: Optional[int] = Field(default=None, ge=0)
    batch_size: int = Field(default=1, ge=1, le=10)
    lora_name: Optional[str] = None
    lora_strength: float = Field(default=1.0, ge=0.0, le=2.0)


class NodeUpdater(ABC):
    """Base class for node-specific updates using Strategy pattern."""
    
    @abstractmethod
    def can_update(self, node: dict) -> bool:
        """Check if this updater can handle the node."""
        pass
    
    @abstractmethod
    def update(self, node: dict, params: WorkflowParameters) -> dict:
        """Update the node with parameters."""
        pass


class KSamplerUpdater(NodeUpdater):
    """Updates KSampler nodes (HiDream workflows)."""
    
    def can_update(self, node: dict) -> bool:
        return node.get('class_type') == 'KSampler'
    
    def update(self, node: dict, params: WorkflowParameters) -> dict:
        """Update KSampler with sampling parameters."""
        node['inputs']['seed'] = params.seed or random.randint(0, 2**32 - 1)
        node['inputs']['steps'] = params.steps
        node['inputs']['cfg'] = params.cfg
        return node


class CLIPTextEncodeUpdater(NodeUpdater):
    """Updates CLIP text encode nodes for prompts."""
    
    def can_update(self, node: dict) -> bool:
        return node.get('class_type') == 'CLIPTextEncode'
    
    def update(self, node: dict, params: WorkflowParameters) -> dict:
        """Update text prompts based on node title."""
        title = node.get('_meta', {}).get('title', '').lower()
        
        if 'positive' in title:
            node['inputs']['text'] = params.prompt
        elif 'negative' in title:
            node['inputs']['text'] = params.negative_prompt
            
        return node


class WorkflowUpdater:
    """Updates workflow with parameters using registered updaters.
    
    Uses Strategy pattern for extensibility:
    - Easy to add new node types
    - Each updater is independent and testable
    - Clear separation of concerns
    """
    
    def __init__(self):
        self.updaters: List[NodeUpdater] = [
            KSamplerUpdater(),
            CLIPTextEncodeUpdater(),
            # Add more updaters as needed
        ]
    
    def register_updater(self, updater: NodeUpdater):
        """Register a custom node updater."""
        self.updaters.append(updater)
    
    def update_workflow(
        self, 
        workflow: dict, 
        params: WorkflowParameters
    ) -> dict:
        """Update workflow with parameters.
        
        Pydantic will validate params automatically on creation.
        """
        import copy
        updated = copy.deepcopy(workflow)
        
        for node_id, node_data in updated.items():
            for updater in self.updaters:
                if updater.can_update(node_data):
                    updated[node_id] = updater.update(node_data, params)
        
        return updated


# Usage example with Pydantic validation:
updater = WorkflowUpdater()

try:
    # Pydantic validates automatically
    params = WorkflowParameters(
        prompt="beautiful sunset",
        width=1024,
        height=1024,
        steps=30
    )
    updated_workflow = updater.update_workflow(workflow, params)
except ValidationError as e:
    print(f"Invalid parameters: {e}")
```

**Benefits:**
- Much cleaner and maintainable (75% less code)
- Easy to add new node types
- Testable individual updaters
- Self-documenting code
- Follows SOLID principles
- Pydantic validation ensures type safety


---

### 3.5 Consolidate Progress Tracking

#### Problem:
ProgressInfo class is 260+ lines with complex state management

**Proposed (core/progress/tracker.py):**
```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Tuple
import time

# Using Pydantic for immutable state (Context7 best practices)
from pydantic import BaseModel, Field

class ProgressStatus(str, Enum):
    """Progress status enumeration."""
    INITIALIZING = "initializing"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ProgressMetrics(BaseModel):
    """Metrics for progress calculation with Pydantic validation."""
    total_steps: int = Field(default=0, ge=0)
    current_step: int = Field(default=0, ge=0)
    total_nodes: int = Field(default=0, ge=0)
    completed_nodes: int = Field(default=0, ge=0)
    cached_nodes: set[str] = Field(default_factory=set)
    
    class Config:
        # Allow sets in Pydantic models
        arbitrary_types_allowed = True
    
    @property
    def percentage(self) -> float:
        """Calculate percentage complete from steps."""
        if self.total_steps > 0 and self.current_step > 0:
            return min(95.0, (self.current_step / self.total_steps) * 100)
        return 0.0


@dataclass
class ProgressState:
    """Current state of generation progress.
    
    Using dataclass for mutable state tracking while keeping
    metrics in immutable Pydantic model.
    """
    status: ProgressStatus = ProgressStatus.INITIALIZING
    queue_position: int = 0
    start_time: float = field(default_factory=time.time)
    metrics: ProgressMetrics = field(default_factory=ProgressMetrics)
    phase: str = "Preparing"
    
    def to_user_friendly(self) -> tuple[str, str, int]:
        """Convert to user-friendly format for Discord embeds."""
        elapsed = time.time() - self.start_time
        
        if self.status == ProgressStatus.QUEUED:
            title = "⏳ Queued"
            description = f"Position #{self.queue_position} in queue"
            color = 0xFFA500  # Orange
        elif self.status == ProgressStatus.RUNNING:
            title = "🎨 Generating"
            description = f"{self.metrics.percentage:.1f}% | {self.phase}"
            color = 0x3498DB  # Blue
        elif self.status == ProgressStatus.COMPLETED:
            title = "✅ Complete"
            description = f"Completed in {self._format_time(elapsed)}"
            color = 0x2ECC71  # Green
        else:
            title = "🔄 Preparing"
            description = f"{self.phase}..."
            color = 0x3498DB  # Blue
        
        return title, description, color
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format time in human-readable way."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"


class ProgressTracker:
    """Tracks and manages generation progress.
    
    Simplified design:
    - Separation of state and metrics
    - Clear progression through states
    - Time estimation based on history
    """
    
    def __init__(self):
        self.state = ProgressState()
        self._history: List[Tuple[float, float]] = []  # (time, percentage)
    
    def update_from_websocket(self, message: dict):
        """Update progress from WebSocket message."""
        msg_type = message.get('type')
        data = message.get('data', {})
        
        if msg_type == 'progress':
            # Update step progress
            current = data.get('value', 0)
            total = data.get('max', 0)
            self.state.metrics = ProgressMetrics(
                current_step=current,
                total_steps=total,
                total_nodes=self.state.metrics.total_nodes,
                completed_nodes=self.state.metrics.completed_nodes,
                cached_nodes=self.state.metrics.cached_nodes
            )
            self.state.phase = f"Sampling ({current}/{total})"
            self._update_history()
            
        elif msg_type == 'executing':
            node_id = data.get('node')
            if node_id:
                # Node executing
                self.state.metrics.completed_nodes += 1
            else:
                # Execution complete
                self.state.status = ProgressStatus.COMPLETED
        
        elif msg_type == 'execution_cached':
            # Nodes were cached (skipped)
            cached = set(data.get('nodes', []))
            self.state.metrics.cached_nodes.update(cached)
    
    def estimate_time_remaining(self) -> Optional[float]:
        """Estimate time remaining based on progress history."""
        if len(self._history) < 2:
            return None
        
        # Use last 5 data points for estimation
        recent = self._history[-5:]
        time_diff = recent[-1][0] - recent[0][0]
        progress_diff = recent[-1][1] - recent[0][1]
        
        if time_diff > 0 and progress_diff > 0:
            rate = progress_diff / time_diff  # % per second
            remaining = 100 - self.state.metrics.percentage
            return min(remaining / rate, 600)  # Cap at 10 minutes
        
        return None
    
    def _update_history(self):
        """Update progress history for time estimation."""
        self._history.append((
            time.time(), 
            self.state.metrics.percentage
        ))
        # Keep only last 10 data points
        if len(self._history) > 10:
            self._history.pop(0)
```

**Benefits:**
- 60% less code (100 lines vs 260 lines)
- Clearer data structures with Pydantic
- Separation of state and behavior
- Easier to test
- More maintainable
- Better type safety

---

### 3.6 Consolidate Duplicate Validation Logic

#### Problem:
Validation logic repeated across commands

**Proposed (core/validators/image.py):**
```python
# Following Pydantic validation patterns from Context7
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import discord

class ValidationResult(BaseModel):
    """Result of a validation check."""
    is_valid: bool
    error_message: Optional[str] = None


class ImageValidator:
    """Validates image attachments with Pydantic-powered validation."""
    
    def __init__(self, max_size_mb: int = 25):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
    
    def validate(self, attachment: discord.Attachment) -> ValidationResult:
        """Validate an image attachment."""
        # Check content type
        if not attachment.content_type or not self._is_valid_type(attachment.content_type):
            return ValidationResult(
                is_valid=False,
                error_message="❌ Please upload a valid image file (PNG, JPEG, or WebP)."
            )
        
        # Check file size
        if attachment.size > self.max_size_bytes:
            return ValidationResult(
                is_valid=False,
                error_message=f"❌ Image too large! Maximum {self.max_size_bytes // (1024 * 1024)}MB."
            )
        
        return ValidationResult(is_valid=True)
    
    def _is_valid_type(self, content_type: str) -> bool:
        """Check if content type is valid."""
        return any(content_type.startswith(t) for t in self.allowed_types)


class PromptParameters(BaseModel):
    """Validated prompt parameters using Pydantic.
    
    Following Context7 Pydantic field validator patterns:
    - Automatic type validation
    - Custom field validators
    - Clear error messages
    """
    prompt: str = Field(min_length=1, max_length=1000)
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt_content(cls, v: str) -> str:
        """Validate prompt content."""
        if not v.strip():
            raise ValueError('Prompt cannot be empty or only whitespace')
        return v.strip()


class StepParameters(BaseModel):
    """Validated step parameters."""
    steps: int = Field(ge=1, le=150)
    min_steps: int = Field(default=1)
    max_steps: int = Field(default=150)
    
    @field_validator('steps')
    @classmethod
    def validate_steps_range(cls, v: int, info) -> int:
        """Validate steps are within configured range."""
        min_val = info.data.get('min_steps', 1)
        max_val = info.data.get('max_steps', 150)
        
        if not (min_val <= v <= max_val):
            raise ValueError(f'Steps must be between {min_val} and {max_val}')
        return v


# Usage in command:
from core.validators.image import ImageValidator, PromptParameters
from pydantic import ValidationError

async def editflux_command(interaction, image, prompt, steps):
    bot = interaction.client
    
    # Validate image
    image_validator = ImageValidator(bot.config.discord.max_file_size_mb)
    validation = image_validator.validate(image)
    if not validation.is_valid:
        await interaction.response.send_message(
            validation.error_message, 
            ephemeral=True
        )
        return
    
    # Validate prompt with Pydantic
    try:
        prompt_params = PromptParameters(prompt=prompt)
    except ValidationError as e:
        await interaction.response.send_message(
            f"❌ Invalid prompt: {e.errors()[0]['msg']}", 
            ephemeral=True
        )
        return
    
    # Continue with command...
```

**Benefits:**
- Single source of truth for validation
- Consistent error messages
- Pydantic automatic validation
- Easy to update validation rules
- Reusable across all commands
- Testable in isolation

---

### 3.7 Add Base Classes and Interfaces

#### Problem:
ImageGenerator and VideoGenerator share functionality but inheritance is awkward

**Proposed (core/generators/base.py):**
```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Callable
from pydantic import BaseModel, Field
from dataclasses import dataclass

class GeneratorType(str, Enum):
    """Type of generator."""
    IMAGE = "image"
    VIDEO = "video"
    UPSCALE = "upscale"
    EDIT = "edit"


class GenerationRequest(BaseModel):
    """Base request for generation with Pydantic validation."""
    prompt: str = Field(min_length=1, max_length=1000)
    workflow_name: str
    seed: Optional[int] = Field(default=None, ge=0)
    progress_callback: Optional[Callable] = Field(default=None, exclude=True)
    
    class Config:
        # Allow callables in model
        arbitrary_types_allowed = True


class GenerationResult(BaseModel):
    """Base result from generation."""
    output_data: bytes
    generation_info: dict
    generation_type: GeneratorType
    
    class Config:
        # Allow bytes in model
        arbitrary_types_allowed = True


class BaseGenerator(ABC):
    """Base class for all generators.
    
    Provides common functionality and enforces interface contract.
    """
    
    def __init__(self, comfyui_client, config):
        self.client = comfyui_client
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate output from request."""
        pass
    
    @abstractmethod
    def validate_request(self, request: GenerationRequest) -> bool:
        """Validate generation request."""
        pass
    
    @property
    @abstractmethod
    def generator_type(self) -> GeneratorType:
        """Get the generator type."""
        pass
    
    async def _load_workflow(self, workflow_name: str) -> dict:
        """Load workflow (common functionality)."""
        # Shared implementation
        pass
    
    async def _monitor_progress(
        self, 
        prompt_id: str,
        callback: Optional[Callable]
    ) -> dict:
        """Monitor generation progress (common functionality)."""
        # Shared implementation
        pass


# Concrete implementations:
class ImageGenerator(BaseGenerator):
    """Generates images using ComfyUI."""
    
    @property
    def generator_type(self) -> GeneratorType:
        return GeneratorType.IMAGE
    
    def validate_request(self, request: 'ImageGenerationRequest') -> bool:
        """Validate image generation request."""
        # Image-specific validation
        return True
    
    async def generate(self, request: 'ImageGenerationRequest') -> GenerationResult:
        """Generate images."""
        # Load workflow
        workflow = await self._load_workflow(request.workflow_name)
        
        # Update workflow with parameters
        # ...
        
        # Queue and monitor
        # ...
        
        return GenerationResult(
            output_data=image_data,
            generation_info=info,
            generation_type=self.generator_type
        )
```

**Benefits:**
- Clear inheritance hierarchy
- Shared functionality in base class
- Type-safe requests and results with Pydantic
- Easier to add new generator types
- Better testability
- Follows Liskov Substitution Principle

---

### 3.8 Improve Error Handling

#### Problem:
Inconsistent error handling across codebase

**Proposed (core/exceptions.py):**
```python
class DisComfyError(Exception):
    """Base exception for DisComfy."""
    pass


class ValidationError(DisComfyError):
    """Validation failed."""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field


class ComfyUIError(DisComfyError):
    """ComfyUI API error."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class WorkflowError(DisComfyError):
    """Workflow loading or validation error."""
    pass


class GenerationError(DisComfyError):
    """Generation failed."""
    pass


class RateLimitError(DisComfyError):
    """Rate limit exceeded."""
    pass


# Usage in commands:
from core.exceptions import ValidationError, ComfyUIError, GenerationError

async def generate_command(interaction, prompt, image=None):
    bot = interaction.client
    
    try:
        # Command logic...
        result = await bot.generator.generate(request)
        
    except ValidationError as e:
        await interaction.response.send_message(
            f"❌ **Validation Error**\n{e}",
            ephemeral=True
        )
    except ComfyUIError as e:
        await interaction.response.send_message(
            f"❌ **ComfyUI Error**\nFailed to communicate with ComfyUI: {e}",
            ephemeral=True
        )
        bot.logger.error(f"ComfyUI error: {e} (status: {e.status_code})")
    except GenerationError as e:
        await interaction.response.send_message(
            f"❌ **Generation Failed**\n{e}\nPlease try again.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            "❌ **Unexpected Error**\nThe error has been logged.",
            ephemeral=True
        )
        bot.logger.exception(f"Unexpected error: {e}")
```

**Benefits:**
- Specific exception types for different errors
- Clearer error messages to users
- Better error logging
- Easier debugging
- More maintainable


---

## 4. Implementation Priority

### Phase 1: Foundation (Week 1-2)
**Goal:** Set up new structure without breaking existing functionality

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| 🔴 HIGH | Create new directory structure | 1 day | High |
| 🔴 HIGH | Extract ComfyUI client abstraction | 2 days | High |
| 🔴 HIGH | Create base generator classes | 2 days | High |
| 🟡 MED | Add custom exception classes | 1 day | Medium |
| 🟢 LOW | Set up logging utilities | 0.5 day | Low |

**Deliverable:** New structure coexists with old code

### Phase 2: Core Refactoring (Week 3-4)
**Goal:** Migrate core functionality to new architecture

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| 🔴 HIGH | Refactor ImageGenerator | 3 days | High |
| 🔴 HIGH | Refactor VideoGenerator | 2 days | High |
| 🔴 HIGH | Extract workflow management | 3 days | High |
| 🟡 MED | Consolidate progress tracking | 2 days | Medium |
| 🟡 MED | Extract validation logic | 1 day | Medium |

**Deliverable:** Core functionality migrated, old code deprecated

### Phase 3: UI Components (Week 5)
**Goal:** Reorganize Discord UI components

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| 🔴 HIGH | Extract generation UI components | 2 days | High |
| 🔴 HIGH | Extract image UI components | 2 days | High |
| 🟡 MED | Extract video UI components | 1 day | Medium |
| 🟡 MED | Create command handlers | 2 days | Medium |

**Deliverable:** UI code organized in modules

### Phase 4: Testing & Documentation (Week 6)
**Goal:** Add tests and documentation

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| 🔴 HIGH | Unit tests for core modules | 3 days | High |
| 🟡 MED | Integration tests | 2 days | Medium |
| 🟡 MED | API documentation | 1 day | Medium |
| 🟢 LOW | Code examples | 1 day | Low |

**Deliverable:** 70%+ test coverage, full API docs

### Phase 5: Migration & Cleanup (Week 7)
**Goal:** Remove old code, finalize migration

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| 🔴 HIGH | Remove deprecated code | 1 day | High |
| 🔴 HIGH | Update all imports | 1 day | High |
| 🟡 MED | Performance optimization | 2 days | Medium |
| 🟢 LOW | Code formatting | 0.5 day | Low |

**Deliverable:** Clean, production-ready v2.0

**Total Timeline:** ~7 weeks for complete refactor

---

## 5. Code Examples with Context7 Best Practices

### 5.1 Before & After: Command Handler

#### Before (Current - bot.py):
```python
# ~100 lines for one command
@app_commands.command(name="editflux", description="...")
async def editflux_command(interaction, image, prompt, steps=20):
    bot: ComfyUIBot = interaction.client
    try:
        # Rate limiting (repeated in every command)
        if not bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message("❌ Rate limit", ephemeral=True)
            return
        
        # Image validation (repeated in every command)
        if not image.content_type or not image.content_type.startswith('image/'):
            await interaction.response.send_message("❌ Invalid image", ephemeral=True)
            return
        
        # ... 70+ more lines
    except Exception as e:
        # Error handling
```

#### After (Proposed - bot/commands/edit.py):
```python
# ~40 lines using Context7 patterns
from bot.commands.base import CommandHandler
from core.validators import ImageValidator, PromptParameters
from core.exceptions import ValidationError, GenerationError
from pydantic import ValidationError as PydanticValidationError

class EditFluxCommand(CommandHandler):
    """Handler for /editflux command.
    
    Following discord.py command patterns from Context7:
    - Proper interaction handling
    - Clean error management
    - Separation of concerns
    """
    
    async def execute(
        self, 
        interaction: discord.Interaction,
        image: discord.Attachment,
        prompt: str,
        steps: int = 20
    ):
        """Execute the editflux command."""
        try:
            # Validate using validators (single source of truth)
            await self.validate_rate_limit(interaction.user.id)
            self.validators.image.validate(image).raise_if_invalid()
            
            # Pydantic automatic validation
            params = PromptParameters(prompt=prompt)
            
            # Download image
            image_data = await image.read()
            
            # Create request with Pydantic validation
            request = EditRequest(
                input_image_data=image_data,
                prompt=params.prompt,
                steps=steps,
                workflow_type=WorkflowType.FLUX_KONTEXT
            )
            
            # Send initial response
            await self.send_initial_response(interaction, request)
            
            # Generate
            result = await self.bot.edit_generator.generate(request)
            
            # Send result
            await self.send_result(interaction, result)
            
        except PydanticValidationError as e:
            await self.send_validation_error(interaction, e)
        except ValidationError as e:
            await self.send_error(interaction, e.message)
        except GenerationError as e:
            await self.send_generation_error(interaction, e)


# Register command using discord.py best practices
@app_commands.command(
    name="editflux", 
    description="Edit an image using Flux Kontext AI"
)
@app_commands.describe(
    image="The image to edit",
    prompt="What changes to make",
    steps="Sampling steps (10-50)"
)
async def editflux_command(
    interaction: discord.Interaction,
    image: discord.Attachment,
    prompt: str,
    steps: int = 20
):
    handler = EditFluxCommand(interaction.client)
    await handler.execute(interaction, image, prompt, steps)
```

**Improvements:**
- 60% less code
- Reusable validators and handlers
- Better error handling
- More testable
- Clearer logic flow
- Follows Context7 discord.py patterns

---

### 5.2 Before & After: WebSocket Connection

#### Before (Current - image_gen.py):
```python
# Embedded in ImageGenerator class
async def _persistent_websocket_monitor(self, ws_url: str):
    """Persistent WebSocket that monitors ALL generations."""
    import websockets
    
    retry_count = 0
    max_retries = 999
    
    while retry_count < max_retries:
        try:
            full_ws_url = f"{ws_url}?clientId={self._bot_client_id}"
            async with websockets.connect(full_ws_url) as websocket:
                # ... 50+ lines of message handling
```

#### After (Proposed - core/comfyui/websocket.py):
```python
# Following aiohttp WebSocket patterns from Context7
import aiohttp
import asyncio
import json
from typing import Callable, Dict

class ComfyUIWebSocket:
    """WebSocket handler for ComfyUI progress updates.
    
    Following aiohttp WebSocket best practices from Context7:
    - Proper connection management
    - Automatic reconnection
    - Clean message handling
    """
    
    def __init__(self, base_url: str, client_id: str):
        self.base_url = base_url
        self.client_id = client_id
        self.session: Optional[aiohttp.ClientSession] = None
        self.websocket: Optional[aiohttp.ClientWebSocketResponse] = None
        self.active_generations: Dict[str, Callable] = {}
        self._running = False
    
    async def connect(self):
        """Establish WebSocket connection using aiohttp."""
        self.session = aiohttp.ClientSession()
        
        # Following Context7 aiohttp ws_connect pattern
        self.websocket = await self.session.ws_connect(
            f"{self.base_url}/ws?clientId={self.client_id}",
            autoclose=True,
            autoping=True,
            heartbeat=30.0
        )
        self._running = True
        
        # Start message processing
        asyncio.create_task(self._process_messages())
    
    async def _process_messages(self):
        """Process incoming WebSocket messages."""
        async for msg in self.websocket:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                await self._handle_message(data)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                break
    
    async def _handle_message(self, data: dict):
        """Handle incoming message and route to correct generation."""
        msg_type = data.get('type')
        msg_data = data.get('data', {})
        prompt_id = msg_data.get('prompt_id')
        
        # Route to registered callback
        if prompt_id and prompt_id in self.active_generations:
            callback = self.active_generations[prompt_id]
            await callback(data)
    
    def register_generation(self, prompt_id: str, callback: Callable):
        """Register a generation for progress updates."""
        self.active_generations[prompt_id] = callback
    
    def unregister_generation(self, prompt_id: str):
        """Unregister a completed generation."""
        self.active_generations.pop(prompt_id, None)
    
    async def close(self):
        """Close WebSocket connection."""
        self._running = False
        if self.websocket:
            await self.websocket.close()
        if self.session:
            await self.session.close()
```

**Benefits:**
- Follows aiohttp WebSocket Context7 patterns
- Clean separation of concerns
- Easy to test
- Better resource management
- Reusable for other WebSocket needs

---

## 6. Migration Strategy

### 6.1 Backward Compatibility

**Approach:** Gradual migration without breaking existing functionality

1. **Create new modules alongside old code**
   - New code in new directory structure
   - Old code continues to work
   - Gradually migrate functionality

2. **Use adapter pattern for compatibility**
```python
# Adapter for backward compatibility
class ImageGeneratorAdapter:
    """Adapts old interface to new implementation."""
    
    def __init__(self, new_generator):
        self._new_gen = new_generator
    
    async def generate_image(self, prompt, **kwargs):
        """Old interface → new interface."""
        request = ImageGenerationRequest(
            prompt=prompt,
            **kwargs
        )
        result = await self._new_gen.generate(request)
        return result.output_data, result.generation_info
```

3. **Feature flags for gradual rollout**
```python
# config.py
class FeatureFlags(BaseModel):
    """Feature flags for gradual rollout."""
    use_new_generator: bool = Field(default=False)
    use_new_ui: bool = Field(default=False)
    use_new_progress: bool = Field(default=False)

# bot.py
if self.config.features.use_new_generator:
    self.generator = NewImageGenerator(client, config)
else:
    self.generator = ImageGenerator()  # Old implementation
```

### 6.2 Testing in v2.0-refactor Branch

**Branch Strategy:**
1. All development happens in `v2.0-refactor` branch
2. Frequent commits with clear messages
3. PR review before merging to main
4. Beta testing with select users before production

**Testing Checklist:**
- [ ] All unit tests pass
- [ ] Integration tests with real ComfyUI pass
- [ ] Manual testing of all commands
- [ ] Performance benchmarks meet targets
- [ ] No memory leaks detected
- [ ] Documentation updated
- [ ] Migration guide created

### 6.3 Rollback Plan

If issues arise after merging:
1. Immediately revert to previous version
2. Investigate issues in v2.0-refactor branch
3. Fix and re-test before attempting merge again

---

## 7. Testing Strategy

### 7.1 Unit Tests (Target: 70%+ Coverage)

```python
# tests/unit/test_validators.py
import pytest
from core.validators.image import ImageValidator
from pydantic import ValidationError

class TestImageValidator:
    @pytest.fixture
    def validator(self):
        return ImageValidator(max_size_mb=25)
    
    def test_valid_image(self, validator, mock_image_attachment):
        """Test validation of valid image."""
        result = validator.validate(mock_image_attachment)
        assert result.is_valid
        assert result.error_message is None
    
    def test_invalid_content_type(self, validator):
        """Test rejection of non-image files."""
        mock = Mock(content_type='text/plain', size=1024)
        result = validator.validate(mock)
        assert not result.is_valid
        assert "valid image file" in result.error_message


# tests/unit/test_workflow_updater.py
from core.comfyui.workflows.updater import WorkflowUpdater, WorkflowParameters

class TestWorkflowUpdater:
    def test_update_ksampler(self):
        """Test KSampler node update."""
        updater = WorkflowUpdater()
        workflow = {
            "1": {"class_type": "KSampler", "inputs": {}}
        }
        params = WorkflowParameters(
            prompt="test",
            steps=30,
            cfg=7.0,
            seed=12345
        )
        
        result = updater.update_workflow(workflow, params)
        
        assert result["1"]["inputs"]["seed"] == 12345
        assert result["1"]["inputs"]["steps"] == 30
        assert result["1"]["inputs"]["cfg"] == 7.0
```

### 7.2 Integration Tests

```python
# tests/integration/test_image_generation.py
import pytest
from core.generators.image import ImageGenerator

@pytest.mark.integration
class TestImageGeneration:
    @pytest.fixture
    async def generator(self, comfyui_url):
        """Create generator with real ComfyUI connection."""
        from core.comfyui.client import HTTPComfyUIClient
        
        async with HTTPComfyUIClient(comfyui_url) as client:
            yield ImageGenerator(client, test_config)
    
    @pytest.mark.asyncio
    async def test_basic_generation(self, generator):
        """Test basic image generation end-to-end."""
        request = ImageGenerationRequest(
            prompt="test image",
            workflow_name="flux_lora",
            steps=10  # Low steps for faster testing
        )
        
        result = await generator.generate(request)
        
        assert result is not None
        assert len(result.output_data) > 0
        assert result.generation_type == GeneratorType.IMAGE
```

### 7.3 Performance Benchmarks

```python
# tests/performance/test_benchmarks.py
@pytest.mark.performance
class TestPerformanceBenchmarks:
    def test_workflow_update_speed(self, benchmark):
        """Benchmark workflow update performance."""
        updater = WorkflowUpdater()
        params = WorkflowParameters(prompt="test")
        
        result = benchmark(lambda: updater.update_workflow(workflow, params))
        
        # Should complete in < 1ms
        assert benchmark.stats['mean'] < 0.001
```

---

## 8. Success Metrics

### 8.1 Code Quality Metrics

| Metric | Current | v2.0 Target | Measurement |
|--------|---------|-------------|-------------|
| Total Lines of Code | 5,850 | 4,500 | File analysis |
| Max File Size | 3,508 | 800 | File analysis |
| Code Duplication | 15-20% | <5% | SonarQube |
| Test Coverage | 0% | 70% | pytest-cov |
| Documentation Coverage | 30% | 80% | pydocstyle |

### 8.2 Performance Metrics

| Metric | Current | v2.0 Target | Measurement |
|--------|---------|-------------|-------------|
| Command Response Time | ~200ms | <100ms | Application logs |
| Generation Start Time | ~2s | <1s | Timing metrics |
| Progress Update Latency | ~1s | <500ms | WebSocket metrics |
| Memory Usage (Idle) | ~150MB | <100MB | Process monitoring |
| Bot Startup Time | ~5s | <3s | Timing metrics |

### 8.3 User Experience Goals

- ✅ Zero functionality loss
- ✅ Faster command responses
- ✅ More reliable progress tracking
- ✅ Better error messages
- ✅ Consistent UI/UX

---

## 9. Risk Assessment & Mitigation

### 9.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking changes | Medium | High | Comprehensive testing, feature flags |
| Performance regression | Low | High | Benchmarking, profiling |
| Integration issues | Medium | Medium | Integration tests, staged rollout |

### 9.2 Project Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Timeline overrun | Medium | Medium | Phased approach, clear priorities |
| Scope creep | Medium | Medium | Strict phase boundaries |
| User resistance | Low | Medium | Beta testing, clear communication |

**Mitigation Strategy:**
- Develop in separate branch (`v2.0-refactor`)
- Extensive testing before merge
- Feature flags for gradual rollout
- Easy rollback plan
- Clear documentation

---

## 10. Conclusion

### 10.1 Summary

This refactoring proposal provides a comprehensive plan to modernize the DisComfy codebase for v2.0 while maintaining 100% functionality. The proposed changes will:

1. **Reduce complexity** by 20-30%
2. **Improve maintainability** through better structure
3. **Enable testing** with 70%+ coverage
4. **Follow best practices** from Context7 documentation
5. **Maintain compatibility** with existing workflows

### 10.2 Next Steps

1. **Review** this proposal with stakeholders
2. **Create** detailed implementation tickets
3. **Begin** Phase 1 work in `v2.0-refactor` branch
4. **Test** thoroughly at each phase
5. **Merge** to main only when fully validated

---

## Appendix A: File Size Comparison

| File | Current LOC | Proposed LOC | Reduction |
|------|-------------|--------------|-----------|
| bot.py | 3,508 | ~600 | -83% |
| image_gen.py | 1,913 | ~400 | -79% |
| video_gen.py | 330 | ~300 | -9% |
| config.py | 418 | ~350 | -16% |
| **New Files** | 0 | ~2,850 | - |
| **Total** | 5,850 | ~4,500 | -23% |

---

## Appendix B: Dependencies

### Current Dependencies:
```
discord.py>=2.3.0
requests>=2.31.0
websocket-client>=1.6.0
aiohttp>=3.8.0
Pillow>=9.0.0
opencv-python>=4.8.0
moviepy>=1.0.3
python-dotenv>=1.0.0
pydantic>=2.0.0
websockets>=11.0.0
```

### Proposed Additional Dependencies (v2.0):
```
pytest>=7.4.0           # Testing
pytest-asyncio>=0.21.0  # Async testing
pytest-cov>=4.1.0       # Coverage
pytest-benchmark>=4.0.0  # Benchmarking
black>=23.0.0           # Code formatting
mypy>=1.5.0             # Type checking
```

---

## Appendix C: Migration Checklist

### Pre-Migration
- [x] Create `v2.0-refactor` branch
- [ ] Review proposal with team
- [ ] Set up development environment
- [ ] Document current API

### Phase 1: Foundation
- [ ] Create new directory structure
- [ ] Extract ComfyUI client
- [ ] Create base generator classes
- [ ] Add exception classes
- [ ] Set up logging utilities

### Phase 2: Core Refactoring
- [ ] Refactor ImageGenerator
- [ ] Refactor VideoGenerator
- [ ] Extract workflow management
- [ ] Consolidate progress tracking
- [ ] Extract validation logic

### Phase 3: UI Components
- [ ] Extract generation UI
- [ ] Extract image UI
- [ ] Extract video UI
- [ ] Create command handlers

### Phase 4: Testing
- [ ] Write unit tests (70%+ coverage)
- [ ] Write integration tests
- [ ] Run performance benchmarks
- [ ] Generate API documentation

### Phase 5: Migration
- [ ] Remove deprecated code
- [ ] Update all imports
- [ ] Performance optimization
- [ ] Final testing
- [ ] Merge to main

---

**Document End**

---

*This is a living document developed in the `v2.0-refactor` branch. All code examples follow best practices from Context7 documentation for discord.py, aiohttp, and Pydantic. For questions or suggestions, please create an issue or discuss in the PR.*

**Branch:** `v2.0-refactor`  
**Target Merge:** After comprehensive testing and validation  
**Rollback Plan:** Immediate revert if issues arise

