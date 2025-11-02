"""
Unit tests for custom exceptions.

Following pytest best practices.
"""

import pytest
from core.exceptions import (
    DisComfyError,
    ValidationError,
    ComfyUIError,
    WorkflowError,
    GenerationError,
    RateLimitError
)


class TestExceptions:
    """Test custom exception classes."""
    
    def test_discomfy_error_base(self):
        """Test base DisComfyError."""
        error = DisComfyError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_validation_error_with_field(self):
        """Test ValidationError with field."""
        error = ValidationError("Invalid input", field="prompt")
        assert str(error) == "Invalid input"
        assert error.field == "prompt"
    
    def test_validation_error_without_field(self):
        """Test ValidationError without field."""
        error = ValidationError("Invalid input")
        assert str(error) == "Invalid input"
        assert error.field is None
    
    def test_comfyui_error_with_status(self):
        """Test ComfyUIError with status code."""
        error = ComfyUIError("API error", status_code=500)
        assert str(error) == "API error"
        assert error.status_code == 500
    
    def test_comfyui_error_without_status(self):
        """Test ComfyUIError without status code."""
        error = ComfyUIError("API error")
        assert str(error) == "API error"
        assert error.status_code is None
    
    def test_workflow_error(self):
        """Test WorkflowError."""
        error = WorkflowError("Workflow failed")
        assert str(error) == "Workflow failed"
        assert isinstance(error, DisComfyError)
    
    def test_generation_error(self):
        """Test GenerationError."""
        error = GenerationError("Generation failed")
        assert str(error) == "Generation failed"
        assert isinstance(error, DisComfyError)
    
    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError("Rate limit exceeded", retry_after=60.0)
        assert str(error) == "Rate limit exceeded"
        assert error.retry_after == 60.0
        assert error.message == "Rate limit exceeded"

