"""
Workflow parameter updater using Strategy pattern.

Following Context7 Pydantic best practices for validation.
"""

import random
import copy
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field, field_validator, ValidationError

from core.exceptions import WorkflowError


class WorkflowParameters(BaseModel):
    """Standardized workflow parameters with Pydantic validation.
    
    Following Pydantic dataclass patterns from Context7:
    - Automatic validation
    - Type coercion
    - Clear field constraints
    """
    prompt: str = Field(min_length=1, max_length=2000, description="Generation prompt")
    negative_prompt: str = Field(default="", max_length=2000, description="Negative prompt")
    width: int = Field(default=1024, ge=512, le=4096, description="Image width")
    height: int = Field(default=1024, ge=512, le=4096, description="Image height")
    steps: int = Field(default=50, ge=1, le=150, description="Sampling steps")
    cfg: float = Field(default=5.0, ge=1.0, le=20.0, description="CFG scale")
    seed: Optional[int] = Field(default=None, ge=0, description="Random seed")
    batch_size: int = Field(default=1, ge=1, le=10, description="Batch size")
    lora_name: Optional[str] = Field(default=None, description="LoRA name")
    lora_strength: float = Field(default=1.0, ge=0.0, le=2.0, description="LoRA strength")
    dype_exponent: Optional[float] = Field(default=None, ge=0.5, le=4.0, description="DyPE exponent for high-res generation")
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt_content(cls, v: str) -> str:
        """Validate prompt content."""
        if not v.strip():
            raise ValueError('Prompt cannot be empty or only whitespace')
        return v.strip()


class NodeUpdater(ABC):
    """Base class for node-specific updates using Strategy pattern."""
    
    @abstractmethod
    def can_update(self, node: dict) -> bool:
        """Check if this updater can handle the node.
        
        Args:
            node: Node dictionary to check
            
        Returns:
            True if this updater can handle the node
        """
        pass
    
    @abstractmethod
    def update(self, node: dict, params: WorkflowParameters) -> dict:
        """Update the node with parameters.
        
        Args:
            node: Node dictionary to update
            params: Workflow parameters
            
        Returns:
            Updated node dictionary
        """
        pass


class KSamplerUpdater(NodeUpdater):
    """Updates KSampler nodes (HiDream workflows)."""
    
    def can_update(self, node: dict) -> bool:
        """Check if node is a KSampler."""
        return node.get('class_type') == 'KSampler'
    
    def update(self, node: dict, params: WorkflowParameters) -> dict:
        """Update KSampler with sampling parameters."""
        if 'inputs' not in node:
            node['inputs'] = {}
        
        node['inputs']['seed'] = params.seed or random.randint(0, 2**32 - 1)
        node['inputs']['steps'] = params.steps
        node['inputs']['cfg'] = params.cfg
        
        # Update positive/negative prompts via connected nodes
        positive_input = node['inputs'].get('positive')
        if positive_input and isinstance(positive_input, list) and len(positive_input) >= 1:
            # Store reference for later update
            node['_update_positive_ref'] = positive_input[0]
        
        negative_input = node['inputs'].get('negative')
        if negative_input and isinstance(negative_input, list) and len(negative_input) >= 1:
            # Store reference for later update
            node['_update_negative_ref'] = negative_input[0]
        
        return node


class CLIPTextEncodeUpdater(NodeUpdater):
    """Updates CLIP text encode nodes for prompts."""
    
    def can_update(self, node: dict) -> bool:
        """Check if node is a CLIPTextEncode."""
        return node.get('class_type') == 'CLIPTextEncode'
    
    def update(self, node: dict, params: WorkflowParameters) -> dict:
        """Update text prompts based on node title."""
        if 'inputs' not in node:
            node['inputs'] = {}
        
        title = node.get('_meta', {}).get('title', '').lower()
        
        if 'positive' in title:
            node['inputs']['text'] = params.prompt
        elif 'negative' in title:
            node['inputs']['text'] = params.negative_prompt
        
        return node


class RandomNoiseUpdater(NodeUpdater):
    """Updates RandomNoise nodes (Flux workflows)."""
    
    def can_update(self, node: dict) -> bool:
        """Check if node is a RandomNoise."""
        return node.get('class_type') == 'RandomNoise'
    
    def update(self, node: dict, params: WorkflowParameters) -> dict:
        """Update RandomNoise with seed."""
        if 'inputs' not in node:
            node['inputs'] = {}
        
        node['inputs']['noise_seed'] = params.seed or random.randint(0, 2**32 - 1)
        return node


class BasicSchedulerUpdater(NodeUpdater):
    """Updates BasicScheduler nodes (Flux workflows)."""
    
    def can_update(self, node: dict) -> bool:
        """Check if node is a BasicScheduler."""
        return node.get('class_type') == 'BasicScheduler'
    
    def update(self, node: dict, params: WorkflowParameters) -> dict:
        """Update BasicScheduler with steps."""
        if 'inputs' not in node:
            node['inputs'] = {}
        
        node['inputs']['steps'] = params.steps
        return node


class LatentImageUpdater(NodeUpdater):
    """Updates EmptySD3LatentImage or EmptyLatentImage nodes."""
    
    def can_update(self, node: dict) -> bool:
        """Check if node is a latent image generator."""
        return node.get('class_type') in ['EmptySD3LatentImage', 'EmptyLatentImage']
    
    def update(self, node: dict, params: WorkflowParameters) -> dict:
        """Update latent image with dimensions."""
        if 'inputs' not in node:
            node['inputs'] = {}
        
        node['inputs']['width'] = params.width
        node['inputs']['height'] = params.height
        node['inputs']['batch_size'] = params.batch_size
        return node


class LoraLoaderUpdater(NodeUpdater):
    """Updates LoraLoaderModelOnly nodes."""
    
    def can_update(self, node: dict) -> bool:
        """Check if node is a LoraLoaderModelOnly."""
        return node.get('class_type') == 'LoraLoaderModelOnly'
    
    def update(self, node: dict, params: WorkflowParameters) -> dict:
        """Update LoRA loader with LoRA name and strength."""
        if 'inputs' not in node:
            node['inputs'] = {}
        
        if params.lora_name and params.lora_name != "none":
            node['inputs']['lora_name'] = params.lora_name
            node['inputs']['strength_model'] = params.lora_strength
        else:
            # No LoRA - disable by setting strength to 0
            node['inputs']['strength_model'] = 0.0
        
        return node


class DyPEFluxUpdater(NodeUpdater):
    """Updates DyPE_FLUX nodes for dynamic position encoding."""

    def can_update(self, node: dict) -> bool:
        """Check if node is a DyPE_FLUX."""
        return node.get('class_type') == 'DyPE_FLUX'

    def update(self, node: dict, params: WorkflowParameters) -> dict:
        """Update DyPE_FLUX with dimensions and dype_exponent."""
        if 'inputs' not in node:
            node['inputs'] = {}

        # Update dimensions for DyPE
        node['inputs']['width'] = params.width
        node['inputs']['height'] = params.height

        # Update dype_exponent if provided in params
        if params.dype_exponent is not None:
            node['inputs']['dype_exponent'] = params.dype_exponent

        return node


class WorkflowUpdater:
    """Updates workflow with parameters using registered updaters.

    Uses Strategy pattern for extensibility:
    - Easy to add new node types
    - Each updater is independent and testable
    - Clear separation of concerns
    """

    def __init__(self):
        """Initialize workflow updater with default node updaters."""
        self.updaters: List[NodeUpdater] = [
            KSamplerUpdater(),
            CLIPTextEncodeUpdater(),
            RandomNoiseUpdater(),
            BasicSchedulerUpdater(),
            LatentImageUpdater(),
            LoraLoaderUpdater(),
            DyPEFluxUpdater(),
        ]
    
    def register_updater(self, updater: NodeUpdater):
        """Register a custom node updater.
        
        Args:
            updater: Node updater to register
        """
        self.updaters.append(updater)
    
    def update_workflow(
        self,
        workflow: Dict[str, Any],
        params: WorkflowParameters
    ) -> Dict[str, Any]:
        """Update workflow with parameters.
        
        Pydantic will validate params automatically on creation.
        
        Args:
            workflow: Workflow dictionary to update
            params: Workflow parameters (validated by Pydantic)
            
        Returns:
            Updated workflow dictionary
            
        Raises:
            WorkflowError: If update fails
        """
        try:
            # Deep copy to avoid modifying original
            updated = copy.deepcopy(workflow)
            
            # First pass: update all nodes
            for node_id, node_data in updated.items():
                for updater in self.updaters:
                    if updater.can_update(node_data):
                        updated[node_id] = updater.update(node_data, params)
            
            # Second pass: handle KSampler positive/negative references
            for node_id, node_data in updated.items():
                # Update positive prompt nodes referenced by KSampler
                if '_update_positive_ref' in node_data:
                    ref_node_id = node_data['_update_positive_ref']
                    if ref_node_id in updated:
                        ref_node = updated[ref_node_id]
                        if ref_node.get('class_type') == 'CLIPTextEncode':
                            if 'inputs' not in ref_node:
                                ref_node['inputs'] = {}
                            ref_node['inputs']['text'] = params.prompt
                    del node_data['_update_positive_ref']
                
                # Update negative prompt nodes referenced by KSampler
                if '_update_negative_ref' in node_data:
                    ref_node_id = node_data['_update_negative_ref']
                    if ref_node_id in updated:
                        ref_node = updated[ref_node_id]
                        if ref_node.get('class_type') == 'CLIPTextEncode':
                            if 'inputs' not in ref_node:
                                ref_node['inputs'] = {}
                            ref_node['inputs']['text'] = params.negative_prompt
                    del node_data['_update_negative_ref']
            
            return updated
            
        except Exception as e:
            raise WorkflowError(f"Failed to update workflow parameters: {e}")





