"""
Unit tests for configuration management.

Following pytest best practices.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
import json
import os

from config import get_config, BotConfig
from config.validation import validate_discord_token, validate_comfyui_url


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_validate_discord_token_valid(self):
        """Test validation of valid Discord token."""
        valid_token = "MTIzNDU2Nzg5MDEyMzQ1Njc4OQ.ABCDEF.abcdefghijklmnopqrstuvwxyz1234567890"
        assert validate_discord_token(valid_token) is True
    
    def test_validate_discord_token_invalid(self):
        """Test validation of invalid Discord token."""
        invalid_tokens = [
            "",
            "short",
            "not.a.valid.token",
            None
        ]
        
        for token in invalid_tokens:
            assert validate_discord_token(token) is False
    
    def test_validate_comfyui_url_valid(self):
        """Test validation of valid ComfyUI URL."""
        valid_urls = [
            "http://localhost:8188",
            "https://example.com",
            "http://192.168.1.1:8188"
        ]
        
        for url in valid_urls:
            assert validate_comfyui_url(url) is True
    
    def test_validate_comfyui_url_invalid(self):
        """Test validation of invalid ComfyUI URL."""
        invalid_urls = [
            "",
            "not-a-url",
            "ftp://example.com"
        ]
        
        for url in invalid_urls:
            assert validate_comfyui_url(url) is False
        
        # None should be handled separately (returns False without regex)
        assert validate_comfyui_url(None) is False


class TestConfigManager:
    """Test ConfigManager class."""
    
    def test_get_config(self):
        """Test get_config returns valid config."""
        # This tests the actual config loading
        config = get_config()
        
        assert config is not None
        assert hasattr(config, 'discord')
        assert hasattr(config, 'comfyui')
        assert hasattr(config, 'generation')
    
    def test_config_has_required_fields(self):
        """Test config has all required fields."""
        config = get_config()
        
        # Discord config
        assert config.discord.token is not None
        assert config.discord.command_prefix is not None
        
        # ComfyUI config
        assert config.comfyui.url is not None
        assert config.comfyui.timeout > 0

