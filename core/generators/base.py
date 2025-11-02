"""
Base generator classes for DisComfy v2.0.

Provides common functionality and enforces interface contract.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Callable
import logging

from pydantic import BaseModel, Field, ConfigDict


class GeneratorType(str, Enum):
    """Type of generator."""
    IMAGE = "image"
    VIDEO = "video"
    UPSCALE = "upscale"
    EDIT = "edit"


class GenerationRequest(BaseModel):
    """Base request for generation with Pydantic validation."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    prompt: str = Field(min_length=1, max_length=1000, description="Generation prompt")
    workflow_name: str = Field(description="Name of the workflow to use")
    seed: Optional[int] = Field(default=None, ge=0, description="Random seed")
    progress_callback: Optional[Callable] = Field(default=None, exclude=True, description="Progress callback")


class UpscaleGenerationRequest(BaseModel):
    """Request for image upscaling."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    input_image_data: bytes = Field(description="Input image data to upscale")
    workflow_name: str = Field(default="upscale_config-1", description="Upscale workflow to use")
    upscale_factor: float = Field(default=2.0, ge=2.0, le=8.0, description="Upscale factor (2, 4, or 8)")
    denoise: float = Field(default=0.35, ge=0.0, le=1.0, description="Denoising strength")
    steps: int = Field(default=20, ge=1, le=150, description="Sampling steps")
    cfg: float = Field(default=7.0, ge=1.0, le=20.0, description="CFG scale")
    seed: Optional[int] = Field(default=None, ge=0, description="Random seed")
    progress_callback: Optional[Callable] = Field(default=None, exclude=True, description="Progress callback")


class EditGenerationRequest(BaseModel):
    """Request for image editing."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    input_image_data: bytes = Field(description="Input image data to edit")
    edit_prompt: str = Field(min_length=1, max_length=1000, description="Edit instruction prompt")
    workflow_type: str = Field(default="flux", description="Edit type: 'flux' or 'qwen'")
    width: int = Field(default=1024, ge=512, le=2048, description="Output width")
    height: int = Field(default=1024, ge=512, le=2048, description="Output height")
    steps: int = Field(default=20, ge=1, le=150, description="Sampling steps")
    cfg: float = Field(default=2.5, ge=1.0, le=20.0, description="CFG scale")
    seed: Optional[int] = Field(default=None, ge=0, description="Random seed")
    additional_images: Optional[list[bytes]] = Field(default=None, description="Additional images for Qwen multi-image edit")
    progress_callback: Optional[Callable] = Field(default=None, exclude=True, description="Progress callback")


class GenerationResult(BaseModel):
    """Base result from generation."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    output_data: bytes = Field(description="Generated output data")
    generation_info: dict = Field(default_factory=dict, description="Additional generation information")
    generation_type: GeneratorType = Field(description="Type of generation")


class BaseGenerator(ABC):
    """Base class for all generators.
    
    Provides common functionality and enforces interface contract.
    """
    
    def __init__(self, comfyui_client, config):
        """
        Initialize base generator.
        
        Args:
            comfyui_client: ComfyUI client instance
            config: Bot configuration
        """
        self.client = comfyui_client
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate output from request.
        
        Args:
            request: Generation request
            
        Returns:
            Generation result
        """
        pass
    
    @abstractmethod
    def validate_request(self, request: GenerationRequest) -> bool:
        """Validate generation request.
        
        Args:
            request: Generation request to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def generator_type(self) -> GeneratorType:
        """Get the generator type.
        
        Returns:
            Generator type enum
        """
        pass
    
    async def _load_workflow(self, workflow_name: str) -> dict:
        """Load workflow from file (common functionality).
        
        Args:
            workflow_name: Name of the workflow
            
        Returns:
            Workflow dictionary
            
        Raises:
            WorkflowError: If workflow cannot be loaded
        """
        from pathlib import Path
        from core.exceptions import WorkflowError
        import json
        
        # Get workflow config
        workflow_config = self.config.workflows.get(workflow_name)
        if not workflow_config:
            raise WorkflowError(f"Workflow '{workflow_name}' not found in configuration")
        
        if not workflow_config.enabled:
            raise WorkflowError(f"Workflow '{workflow_name}' is disabled")
        
        # Load workflow file
        workflows_dir = Path("workflows")
        workflow_path = workflows_dir / workflow_config.file
        
        if not workflow_path.exists():
            raise WorkflowError(f"Workflow file not found: {workflow_path}")
        
        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            return workflow
        except json.JSONDecodeError as e:
            raise WorkflowError(f"Invalid JSON in workflow file: {e}")
        except Exception as e:
            raise WorkflowError(f"Failed to load workflow: {e}")
    
    async def initialize(self):
        """Initialize the generator (optional override)."""
        pass
    
    async def shutdown(self):
        """Shutdown the generator (optional override)."""
        pass

