"""
Image validation with Pydantic-powered validation.

Following Pydantic validation patterns from Context7.
"""

from typing import Optional
import discord

from pydantic import BaseModel, Field, field_validator

from core.exceptions import ValidationError


class ValidationResult(BaseModel):
    """Result of a validation check."""
    is_valid: bool
    error_message: Optional[str] = None


class ImageValidator:
    """Validates image attachments with Pydantic-powered validation."""
    
    def __init__(self, max_size_mb: int = 25):
        """
        Initialize image validator.
        
        Args:
            max_size_mb: Maximum file size in MB
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
    
    def validate(self, attachment: discord.Attachment) -> ValidationResult:
        """Validate an image attachment.
        
        Args:
            attachment: Discord attachment to validate
            
        Returns:
            ValidationResult with validation status
        """
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
        """Check if content type is valid.
        
        Args:
            content_type: Content type string
            
        Returns:
            True if valid, False otherwise
        """
        if not content_type:
            return False
        return any(content_type.startswith(t) for t in self.allowed_types)


class PromptParameters(BaseModel):
    """Validated prompt parameters using Pydantic.
    
    Following Context7 Pydantic field validator patterns:
    - Automatic type validation
    - Custom field validators
    - Clear error messages
    """
    prompt: str = Field(min_length=1, max_length=1000, description="Generation prompt")
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt_content(cls, v: str) -> str:
        """Validate prompt content."""
        if not v.strip():
            raise ValueError('Prompt cannot be empty or only whitespace')
        return v.strip()


class StepParameters(BaseModel):
    """Validated step parameters."""
    steps: int = Field(ge=1, le=150, description="Sampling steps")
    min_steps: int = Field(default=1, description="Minimum steps")
    max_steps: int = Field(default=150, description="Maximum steps")
    
    @field_validator('steps')
    @classmethod
    def validate_steps_range(cls, v: int, info) -> int:
        """Validate steps are within configured range."""
        min_val = info.data.get('min_steps', 1)
        max_val = info.data.get('max_steps', 150)
        
        if not (min_val <= v <= max_val):
            raise ValueError(f'Steps must be between {min_val} and {max_val}')
        return v

