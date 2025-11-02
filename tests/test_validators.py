"""
Unit tests for validators.

Following pytest best practices.
"""

import pytest
from unittest.mock import Mock

from core.validators.image import (
    ImageValidator,
    PromptParameters,
    StepParameters,
    ValidationResult
)
from core.exceptions import ValidationError


class TestImageValidator:
    """Test ImageValidator class."""
    
    def test_valid_image(self):
        """Test validation of valid image."""
        validator = ImageValidator(max_size_mb=25)
        image = Mock()
        image.content_type = "image/png"
        image.size = 1024 * 1024  # 1MB
        
        result = validator.validate(image)
        
        assert result.is_valid is True
        assert result.error_message is None
    
    def test_invalid_content_type(self):
        """Test validation rejects non-image files."""
        validator = ImageValidator(max_size_mb=25)
        image = Mock()
        image.content_type = "application/pdf"
        image.size = 1024 * 1024
        
        result = validator.validate(image)
        
        assert result.is_valid is False
        assert "image" in result.error_message.lower()
    
    def test_file_too_large(self):
        """Test validation rejects files that are too large."""
        validator = ImageValidator(max_size_mb=25)
        image = Mock()
        image.content_type = "image/png"
        image.size = 26 * 1024 * 1024  # 26MB
        
        result = validator.validate(image)
        
        assert result.is_valid is False
        assert "large" in result.error_message.lower() or "size" in result.error_message.lower()


class TestPromptParameters:
    """Test PromptParameters Pydantic model."""
    
    def test_valid_prompt(self):
        """Test valid prompt passes validation."""
        params = PromptParameters(prompt="A beautiful landscape")
        assert params.prompt == "A beautiful landscape"
    
    def test_empty_prompt_fails(self):
        """Test empty prompt fails validation."""
        with pytest.raises(Exception):  # Pydantic validation error
            PromptParameters(prompt="")
    
    def test_too_long_prompt_fails(self):
        """Test prompt that's too long fails validation."""
        long_prompt = "x" * 2001  # Assuming max length is 2000
        
        with pytest.raises(Exception):  # Pydantic validation error
            PromptParameters(prompt=long_prompt)


class TestStepParameters:
    """Test StepParameters Pydantic model."""
    
    def test_valid_steps(self):
        """Test valid steps pass validation."""
        params = StepParameters(steps=30, min_steps=1, max_steps=150)
        assert params.steps == 30
    
    def test_steps_below_minimum_fails(self):
        """Test steps below minimum fail validation."""
        with pytest.raises(Exception):  # Pydantic validation error
            StepParameters(steps=0, min_steps=1, max_steps=150)
    
    def test_steps_above_maximum_fails(self):
        """Test steps above maximum fail validation."""
        with pytest.raises(Exception):  # Pydantic validation error
            StepParameters(steps=200, min_steps=1, max_steps=150)

