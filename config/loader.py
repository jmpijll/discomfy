"""
Configuration loading and management.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from dotenv import load_dotenv
from config.models import BotConfig, WorkflowConfig
from config.migration import migrate_config, get_default_workflows
from config.validation import validate_discord_token, validate_comfyui_url

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration loading, validation, and access."""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.config: Optional[BotConfig] = None
        self._setup_initial_logging()
    
    def _setup_initial_logging(self) -> None:
        """Set up basic logging before config is loaded."""
        # Simple logging setup without external dependencies to avoid circular imports
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    def load_config(self) -> BotConfig:
        """
        Load and validate configuration from file and environment.
        
        Returns:
            Loaded BotConfig instance
            
        Raises:
            ValueError: If configuration is invalid
        """
        try:
            # Load from file if it exists
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Perform smart migration to add missing workflows
                config_data = migrate_config(config_data, self.config_path)
                
            else:
                # Try to auto-create from example config
                config_data = self._create_default_config()
            
            # Override with environment variables
            config_data = self._apply_env_overrides(config_data)
            
            # Validate and create config
            self.config = BotConfig(**config_data)
            
            # Update logging configuration
            self._configure_logging()
            
            logger.info("Configuration loaded successfully")
            return self.config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to config data.
        
        Args:
            config_data: Configuration data dictionary
            
        Returns:
            Updated configuration data
        """
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
        
        # Import here to avoid circular dependency
        from utils.logging import setup_logging
        
        # Set up logging with configuration values
        setup_logging(
            level=log_config.level,
            format_string=log_config.format,
            log_file=log_config.file_path,
            max_bytes=log_config.max_file_size_mb * 1024 * 1024,
            backup_count=log_config.backup_count
        )
    
    def get_workflow_config(self, workflow_name: str) -> Optional[WorkflowConfig]:
        """
        Get configuration for a specific workflow.
        
        Args:
            workflow_name: Name of the workflow
            
        Returns:
            WorkflowConfig if found, None otherwise
        """
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        
        return self.config.workflows.get(workflow_name)
    
    def list_available_workflows(self) -> List[str]:
        """
        Get list of available workflow names.
        
        Returns:
            List of enabled workflow names
        """
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        
        return [name for name, config in self.config.workflows.items() if config.enabled]
    
    def validate_workflow_files(self) -> bool:
        """
        Validate that all configured workflow files exist.
        
        Returns:
            True if all files exist, False otherwise
        """
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        
        workflows_dir = Path("workflows")
        missing_files = []
        
        for name, workflow_config in self.config.workflows.items():
            workflow_path = workflows_dir / workflow_config.file
            if not workflow_path.exists():
                missing_files.append(f"{name}: {workflow_config.file}")
        
        if missing_files:
            logger.error(f"Missing workflow files: {missing_files}")
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
            
            logger.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    def _create_default_config(self) -> Dict[str, Any]:
        """
        Create default configuration from example file or built-in defaults.
        
        Returns:
            Default configuration data
        """
        example_config_path = Path("config.example.json")
        
        if example_config_path.exists():
            try:
                # Load from example config
                with open(example_config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Create the actual config file for future use
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2)
                
                logger.info(f"Created {self.config_path} from {example_config_path}")
                return config_data
                
            except Exception as e:
                logger.error(f"Failed to load example config: {e}")
        
        # Fall back to built-in minimal defaults
        logger.warning(f"Config file {self.config_path} not found and no example available, using minimal defaults")
        return {
            "discord": {
                "token": "SET_VIA_ENVIRONMENT"
            },
            "comfyui": {
                "url": "http://localhost:8188"
            },
            "generation": {
                "default_workflow": "flux_lora"
            },
            "workflows": get_default_workflows()
        }


# Global configuration manager instance
config_manager = ConfigManager()


def get_config() -> BotConfig:
    """
    Get the current configuration, loading it if necessary.
    
    Returns:
        BotConfig instance
    """
    if config_manager.config is None:
        config_manager.load_config()
    return config_manager.config


def reload_config() -> BotConfig:
    """
    Reload configuration from file.
    
    Returns:
        Reloaded BotConfig instance
    """
    return config_manager.load_config()

