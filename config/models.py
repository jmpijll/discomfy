"""
Pydantic models for DisComfy configuration.

Following Pydantic best practices from Context7:
- Automatic validation
- Type coercion
- Clear field constraints
"""

from typing import Dict, Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class DiscordConfig(BaseModel):
    """Discord-specific configuration."""
    token: str = Field(..., description="Discord bot token")
    guild_id: Optional[str] = Field(None, description="Discord server ID for slash commands")
    command_prefix: str = Field("!", description="Command prefix for text commands")
    max_file_size_mb: int = Field(25, description="Maximum file size for uploads in MB")


class ComfyUIConfig(BaseModel):
    """ComfyUI API configuration."""
    url: str = Field("http://localhost:8188", description="ComfyUI server URL")
    api_key: Optional[str] = Field(None, description="ComfyUI API key if required")
    timeout: int = Field(300, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum number of API retries")
    retry_delay: float = Field(1.0, description="Delay between retries in seconds")


class GenerationConfig(BaseModel):
    """Image/video generation configuration."""
    default_workflow: str = Field("hidream_full_config-1", description="Default workflow to use")
    max_batch_size: int = Field(4, description="Maximum number of images to generate at once")
    output_limit: int = Field(50, description="Maximum number of output files to keep")
    default_width: int = Field(1024, description="Default image width")
    default_height: int = Field(1024, description="Default image height")
    default_steps: int = Field(50, description="Default sampling steps")
    default_cfg: float = Field(5.0, description="Default CFG scale")
    
    @field_validator('max_batch_size')
    @classmethod
    def validate_batch_size(cls, v: int) -> int:
        if v < 1 or v > 10:
            raise ValueError('Batch size must be between 1 and 10')
        return v


class WorkflowConfig(BaseModel):
    """Configuration for a specific workflow."""
    file: str = Field(..., description="Workflow JSON filename")
    name: str = Field(..., description="Human-readable workflow name")
    description: str = Field("", description="Workflow description")
    type: str = Field("image", description="Workflow type: image, video, upscale")
    model_type: Optional[str] = Field(None, description="Model type: flux, hidream, etc.")
    parameters: Dict[str, str] = Field(default_factory=dict, description="Node ID mappings for parameters")
    enabled: bool = Field(True, description="Whether this workflow is enabled")
    supports_lora: bool = Field(False, description="Whether this workflow supports LoRA")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field("INFO", description="Logging level")
    format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    file_path: Optional[str] = Field(None, description="Log file path")
    max_file_size_mb: int = Field(10, description="Maximum log file size in MB")
    backup_count: int = Field(5, description="Number of backup log files to keep")


class SecurityConfig(BaseModel):
    """Security and rate limiting configuration."""
    rate_limit_per_user: int = Field(10, description="Max requests per user per minute")
    rate_limit_global: int = Field(100, description="Max global requests per minute")
    allowed_file_types: List[str] = Field(
        default_factory=lambda: [".png", ".jpg", ".jpeg", ".webp", ".gif"],
        description="Allowed file extensions for uploads"
    )
    max_prompt_length: int = Field(1000, description="Maximum prompt length")


class BotConfig(BaseModel):
    """Main bot configuration."""
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    discord: DiscordConfig
    comfyui: ComfyUIConfig
    generation: GenerationConfig
    workflows: Dict[str, WorkflowConfig] = Field(default_factory=dict)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

