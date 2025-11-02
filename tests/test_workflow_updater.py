"""
Unit tests for workflow parameter updaters.

Following pytest best practices.
"""

import pytest
from core.comfyui.workflows.updater import (
    WorkflowUpdater,
    WorkflowParameters,
    KSamplerUpdater,
    CLIPTextEncodeUpdater
)


class TestWorkflowParameters:
    """Test WorkflowParameters Pydantic model."""
    
    def test_valid_parameters(self):
        """Test valid workflow parameters."""
        params = WorkflowParameters(
            prompt="test prompt",
            negative_prompt="test negative",
            width=1024,
            height=1024,
            steps=30,
            cfg=5.0,
            seed=12345
        )
        
        assert params.prompt == "test prompt"
        assert params.width == 1024
        assert params.steps == 30
    
    def test_default_values(self):
        """Test default parameter values."""
        params = WorkflowParameters(prompt="test")
        
        assert params.negative_prompt == ""
        assert params.width == 1024
        assert params.steps == 50  # Default from WorkflowParameters
        assert params.cfg == 5.0


class TestKSamplerUpdater:
    """Test KSamplerUpdater."""
    
    def test_update_basic(self):
        """Test basic workflow update."""
        node = {
            "inputs": {
                "seed": 12345,
                "steps": 20,
                "cfg": 4.0
            },
            "class_type": "KSampler"
        }
        
        params = WorkflowParameters(
            prompt="test",
            steps=30,
            cfg=5.0,
            seed=67890
        )
        
        updater = KSamplerUpdater()
        updated = updater.update(node, params)
        
        assert updated["inputs"]["steps"] == 30
        assert updated["inputs"]["cfg"] == 5.0
        assert updated["inputs"]["seed"] == 67890


class TestCLIPTextEncodeUpdater:
    """Test CLIPTextEncodeUpdater."""
    
    def test_update_prompt(self):
        """Test updating prompt in workflow."""
        node = {
            "inputs": {
                "text": "old prompt"
            },
            "class_type": "CLIPTextEncode",
            "_meta": {
                "title": "CLIP Text Encode (Positive Prompt)"
            }
        }
        
        params = WorkflowParameters(
            prompt="new prompt",
            negative_prompt="new negative"
        )
        
        updater = CLIPTextEncodeUpdater()
        updated = updater.update(node, params)
        
        # Should update text field based on title
        assert updated["inputs"]["text"] == "new prompt"

