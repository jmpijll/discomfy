"""
Configuration migration logic.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any


logger = logging.getLogger(__name__)


def get_default_workflows() -> Dict[str, Any]:
    """Get default workflow configurations."""
    return {
        "flux_lora": {
            "name": "Flux with LoRA",
            "description": "High-quality image generation with Flux model and LoRA support",
            "file": "flux_lora.json",
            "type": "image",
            "model_type": "flux",
            "enabled": True,
            "supports_lora": True
        },
        "flux_krea_lora": {
            "name": "Flux Krea with LoRA",
            "description": "Enhanced Flux Krea model with LoRA support - high-quality creative generation",
            "file": "flux_krea_lora.json",
            "type": "image",
            "model_type": "flux_krea",
            "enabled": True,
            "supports_lora": True
        },
        "hidream_lora": {
            "name": "HiDream with LoRA",
            "description": "High-quality image generation with HiDream model and LoRA support",
            "file": "hidream_lora.json",
            "type": "image",
            "model_type": "hidream",
            "enabled": True,
            "supports_lora": True
        },
        "flux_kontext_edit": {
            "name": "Flux Kontext Edit",
            "description": "Edit images using natural language prompts with Flux Kontext model",
            "file": "flux_kontext_edit.json",
            "type": "edit",
            "model_type": "flux",
            "enabled": True,
            "supports_lora": False
        }
    }


def migrate_config(config_data: Dict[str, Any], config_path: Path) -> Dict[str, Any]:
    """
    Smart config migration that adds missing workflows while preserving user settings.
    
    Args:
        config_data: Current configuration data
        config_path: Path to configuration file
        
    Returns:
        Migrated configuration data
    """
    try:
        # Get the current example config to see what's new
        example_config_path = Path("config.example.json")
        example_workflows = {}
        
        if example_config_path.exists():
            with open(example_config_path, 'r', encoding='utf-8') as f:
                example_data = json.load(f)
                example_workflows = example_data.get('workflows', {})
        else:
            # Use built-in defaults if no example
            example_workflows = get_default_workflows()
        
        # Get user's current workflows
        user_workflows = config_data.get('workflows', {})
        
        # Find missing workflows
        missing_workflows = {}
        for workflow_name, workflow_config in example_workflows.items():
            if workflow_name not in user_workflows:
                missing_workflows[workflow_name] = workflow_config
                logger.info(f"Adding missing workflow: {workflow_name}")
        
        # Add missing workflows to user config
        if missing_workflows:
            config_data.setdefault('workflows', {}).update(missing_workflows)
            
            # Save the updated config back to file
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Config migrated: added {len(missing_workflows)} missing workflows")
        
        return config_data
        
    except Exception as e:
        logger.error(f"Config migration failed: {e}")
        # Return original config if migration fails
        return config_data





