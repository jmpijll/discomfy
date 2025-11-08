"""
Custom exceptions for DisComfy v2.0.
"""

from typing import Optional


class DisComfyError(Exception):
    """Base exception for DisComfy."""
    pass


class ValidationError(DisComfyError):
    """Validation failed."""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field
        self.message = message


class ComfyUIError(DisComfyError):
    """ComfyUI API error."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class WorkflowError(DisComfyError):
    """Workflow loading or validation error."""
    pass


class GenerationError(DisComfyError):
    """Generation failed."""
    pass


class RateLimitError(DisComfyError):
    """Rate limit exceeded."""
    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after
        self.message = message





