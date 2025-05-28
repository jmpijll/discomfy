"""
Configuration management for Discord ComfyUI Bot.
Handles all configurable values and environment variables.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
    
    @validator('max_batch_size')
    def validate_batch_size(cls, v):
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
    discord: DiscordConfig
    comfyui: ComfyUIConfig
    generation: GenerationConfig
    workflows: Dict[str, WorkflowConfig] = Field(default_factory=dict)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

class ConfigManager:
    """Manages configuration loading, validation, and access."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config: Optional[BotConfig] = None
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """Set up basic logging before config is loaded."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> BotConfig:
        """Load and validate configuration from file and environment."""
        try:
            # Load from file if it exists
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            else:
                config_data = {}
                self.logger.warning(f"Config file {self.config_path} not found, using defaults")
            
            # Override with environment variables
            config_data = self._apply_env_overrides(config_data)
            
            # Validate and create config
            self.config = BotConfig(**config_data)
            
            # Update logging configuration
            self._configure_logging()
            
            self.logger.info("Configuration loaded successfully")
            return self.config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to config data."""
        # Discord configuration
        if not config_data.get('discord'):
            config_data['discord'] = {}
        
        if os.getenv('DISCORD_TOKEN'):
            config_data['discord']['token'] = os.getenv('DISCORD_TOKEN')
        if os.getenv('DISCORD_GUILD_ID'):
            config_data['discord']['guild_id'] = os.getenv('DISCORD_GUILD_ID')
        
        # ComfyUI configuration
        if not config_data.get('comfyui'):
            config_data['comfyui'] = {}
        
        if os.getenv('COMFYUI_URL'):
            config_data['comfyui']['url'] = os.getenv('COMFYUI_URL')
        if os.getenv('COMFYUI_API_KEY'):
            config_data['comfyui']['api_key'] = os.getenv('COMFYUI_API_KEY')
        
        return config_data
    
    def _configure_logging(self) -> None:
        """Configure logging based on loaded configuration."""
        if not self.config:
            return
        
        log_config = self.config.logging
        
        # Set logging level
        level = getattr(logging, log_config.level.upper(), logging.INFO)
        logging.getLogger().setLevel(level)
        
        # Configure file logging if specified
        if log_config.file_path:
            from logging.handlers import RotatingFileHandler
            
            log_path = Path(log_config.file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=log_config.max_file_size_mb * 1024 * 1024,
                backupCount=log_config.backup_count
            )
            file_handler.setFormatter(logging.Formatter(log_config.format))
            logging.getLogger().addHandler(file_handler)
    
    def get_workflow_config(self, workflow_name: str) -> Optional[WorkflowConfig]:
        """Get configuration for a specific workflow."""
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        
        return self.config.workflows.get(workflow_name)
    
    def list_available_workflows(self) -> List[str]:
        """Get list of available workflow names."""
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        
        return [name for name, config in self.config.workflows.items() if config.enabled]
    
    def validate_workflow_files(self) -> bool:
        """Validate that all configured workflow files exist."""
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        
        workflows_dir = Path("workflows")
        missing_files = []
        
        for name, workflow_config in self.config.workflows.items():
            workflow_path = workflows_dir / workflow_config.file
            if not workflow_path.exists():
                missing_files.append(f"{name}: {workflow_config.file}")
        
        if missing_files:
            self.logger.error(f"Missing workflow files: {missing_files}")
            return False
        
        return True
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        if not self.config:
            raise RuntimeError("No configuration to save")
        
        try:
            config_dict = self.config.dict()
            # Remove sensitive information from saved config
            if 'discord' in config_dict and 'token' in config_dict['discord']:
                config_dict['discord']['token'] = "SET_VIA_ENVIRONMENT"
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise

# Global configuration manager instance
config_manager = ConfigManager()

def get_config() -> BotConfig:
    """Get the current configuration, loading it if necessary."""
    if config_manager.config is None:
        config_manager.load_config()
    return config_manager.config

def reload_config() -> BotConfig:
    """Reload configuration from file."""
    return config_manager.load_config()

# Configuration validation functions
def validate_discord_token(token: str) -> bool:
    """Validate Discord bot token format."""
    if not token or len(token) < 50:
        return False
    # Basic format check for Discord bot tokens
    return token.count('.') >= 2

def validate_comfyui_url(url: str) -> bool:
    """Validate ComfyUI URL format."""
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None 