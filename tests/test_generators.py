"""
Unit tests for generators.

Following pytest best practices.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, mock_open

from core.generators.base import BaseGenerator, GeneratorType, GenerationRequest, GenerationResult
from core.exceptions import WorkflowError


class TestBaseGenerator:
    """Test BaseGenerator abstract class."""
    
    def test_base_generator_initialization(self, mock_config, mock_comfyui_client):
        """Test BaseGenerator initialization."""
        # Create concrete implementation for testing
        class TestGenerator(BaseGenerator):
            async def generate(self, request: GenerationRequest) -> GenerationResult:
                return GenerationResult(
                    output_data=b"test",
                    generation_type=GeneratorType.IMAGE
                )
            
            def validate_request(self, request: GenerationRequest) -> bool:
                return True
            
            @property
            def generator_type(self) -> GeneratorType:
                return GeneratorType.IMAGE
        
        generator = TestGenerator(mock_comfyui_client, mock_config)
        
        assert generator.client == mock_comfyui_client
        assert generator.config == mock_config
        assert generator.logger is not None
    
    @pytest.mark.asyncio
    async def test_load_workflow_success(self, mock_config, mock_comfyui_client):
        """Test successful workflow loading."""
        class TestGenerator(BaseGenerator):
            async def generate(self, request: GenerationRequest) -> GenerationResult:
                pass
            
            def validate_request(self, request: GenerationRequest) -> bool:
                return True
            
            @property
            def generator_type(self) -> GeneratorType:
                return GeneratorType.IMAGE
        
        generator = TestGenerator(mock_comfyui_client, mock_config)
        
        # Mock workflow config
        mock_config.workflows = {
            "test_workflow": Mock(
                enabled=True,
                file="test.json"
            )
        }
        
        with patch("builtins.open", mock_open(read_data='{"1": {"class_type": "Test"}}')):
            with patch("pathlib.Path.exists", return_value=True):
                workflow = await generator._load_workflow("test_workflow")
                
                assert workflow is not None
    
    @pytest.mark.asyncio
    async def test_load_workflow_not_found(self, mock_config, mock_comfyui_client):
        """Test loading non-existent workflow raises error."""
        class TestGenerator(BaseGenerator):
            async def generate(self, request: GenerationRequest) -> GenerationResult:
                pass
            
            def validate_request(self, request: GenerationRequest) -> bool:
                return True
            
            @property
            def generator_type(self) -> GeneratorType:
                return GeneratorType.IMAGE
        
        generator = TestGenerator(mock_comfyui_client, mock_config)
        
        mock_config.workflows = {}
        
        with pytest.raises(WorkflowError):
            await generator._load_workflow("nonexistent")
    
    def test_generation_request_validation(self):
        """Test GenerationRequest Pydantic validation."""
        # Valid request
        request = GenerationRequest(
            prompt="test prompt",
            workflow_name="test_workflow"
        )
        assert request.prompt == "test prompt"
        assert request.workflow_name == "test_workflow"
        
        # Invalid request (empty prompt)
        with pytest.raises(Exception):  # Pydantic validation error
            GenerationRequest(prompt="", workflow_name="test")
    
    def test_generation_result(self):
        """Test GenerationResult creation."""
        result = GenerationResult(
            output_data=b"test_data",
            generation_type=GeneratorType.IMAGE,
            generation_info={"seed": 12345}
        )
        
        assert result.output_data == b"test_data"
        assert result.generation_type == GeneratorType.IMAGE
        assert result.generation_info["seed"] == 12345


@pytest.mark.asyncio
class TestGeneratorTypes:
    """Test GeneratorType enum."""
    
    def test_generator_type_enum(self):
        """Test GeneratorType enum values."""
        assert GeneratorType.IMAGE == "image"
        assert GeneratorType.VIDEO == "video"
        assert GeneratorType.UPSCALE == "upscale"
        assert GeneratorType.EDIT == "edit"

