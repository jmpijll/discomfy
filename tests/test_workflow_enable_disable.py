"""
Test workflow enable/disable via environment variables.
"""

import os
import pytest
from unittest.mock import patch
from config.loader import ConfigManager


@pytest.mark.asyncio
async def test_workflow_enable_via_env():
    """Test enabling a workflow via environment variable."""
    with patch.dict(os.environ, {'WORKFLOW_HIDREAM_LORA_ENABLED': 'true'}):
        config_manager = ConfigManager("config.json")
        config = config_manager.load_config()
        
        assert 'hidream_lora' in config.workflows
        assert config.workflows['hidream_lora'].enabled is True


@pytest.mark.asyncio
async def test_workflow_disable_via_env():
    """Test disabling a workflow via environment variable."""
    with patch.dict(os.environ, {'WORKFLOW_FLUX_LORA_ENABLED': 'false'}):
        config_manager = ConfigManager("config.json")
        config = config_manager.load_config()
        
        assert 'flux_lora' in config.workflows
        assert config.workflows['flux_lora'].enabled is False


@pytest.mark.asyncio
async def test_workflow_disable_various_false_values():
    """Test that various false values work (false, 0, no, off)."""
    false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'NO', 'off', 'Off', 'OFF']
    
    for false_value in false_values:
        with patch.dict(os.environ, {'WORKFLOW_FLUX_LORA_ENABLED': false_value}):
            config_manager = ConfigManager("config.json")
            config = config_manager.load_config()
            
            assert config.workflows['flux_lora'].enabled is False, \
                f"Expected workflow to be disabled with value '{false_value}'"


@pytest.mark.asyncio
async def test_workflow_enable_various_true_values():
    """Test that various true values work (true, 1, yes, on)."""
    true_values = ['true', 'True', 'TRUE', '1', 'yes', 'Yes', 'YES', 'on', 'On', 'ON']
    
    for true_value in true_values:
        with patch.dict(os.environ, {'WORKFLOW_FLUX_LORA_ENABLED': true_value}):
            config_manager = ConfigManager("config.json")
            config = config_manager.load_config()
            
            assert config.workflows['flux_lora'].enabled is True, \
                f"Expected workflow to be enabled with value '{true_value}'"


@pytest.mark.asyncio
async def test_workflow_default_enabled_without_env():
    """Test that workflows are enabled by default when no env var is set."""
    # Ensure env vars are not set
    with patch.dict(os.environ, {}, clear=False):
        # Remove any workflow-related env vars
        for key in list(os.environ.keys()):
            if key.startswith('WORKFLOW_') and key.endswith('_ENABLED'):
                del os.environ[key]
        
        config_manager = ConfigManager("config.json")
        config = config_manager.load_config()
        
        # All workflows should be enabled by default (as per config.json)
        for workflow_name, workflow_config in config.workflows.items():
            # Check against what's in config.json (all are enabled by default)
            assert workflow_config.enabled is True, \
                f"Expected {workflow_name} to be enabled by default"


@pytest.mark.asyncio
async def test_list_available_workflows_filters_disabled():
    """Test that list_available_workflows filters out disabled workflows."""
    with patch.dict(os.environ, {
        'WORKFLOW_FLUX_LORA_ENABLED': 'true',
        'WORKFLOW_HIDREAM_LORA_ENABLED': 'false'
    }):
        config_manager = ConfigManager("config.json")
        config_manager.load_config()
        
        available = config_manager.list_available_workflows()
        
        assert 'flux_lora' in available
        assert 'hidream_lora' not in available


@pytest.mark.asyncio
async def test_multiple_workflows_via_env():
    """Test disabling multiple workflows at once."""
    with patch.dict(os.environ, {
        'WORKFLOW_FLUX_LORA_ENABLED': 'false',
        'WORKFLOW_HIDREAM_LORA_ENABLED': 'false',
        'WORKFLOW_ZITURBO_ENABLED': 'true'
    }):
        config_manager = ConfigManager("config.json")
        config = config_manager.load_config()
        
        assert config.workflows['flux_lora'].enabled is False
        assert config.workflows['hidream_lora'].enabled is False
        assert config.workflows['ziturbo'].enabled is True
