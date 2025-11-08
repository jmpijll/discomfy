"""
Pytest configuration and fixtures for DisComfy v2.0 tests.

Following pytest best practices from Context7.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from config import get_config
from core.comfyui.client import ComfyUIClient
from utils.rate_limit import RateLimiter, RateLimitConfig


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = get_config()
    # Override sensitive values for testing
    config.discord.token = "TEST_TOKEN"
    config.comfyui.url = "http://localhost:8188"
    return config


@pytest.fixture
def mock_comfyui_client():
    """Create a mock ComfyUI client for testing."""
    client = Mock(spec=ComfyUIClient)
    client.queue_prompt = AsyncMock(return_value="test_prompt_id")
    client.get_history = AsyncMock(return_value={"test_prompt_id": {"outputs": {}}})
    client.download_output = AsyncMock(return_value=b"fake_image_data")
    client.test_connection = AsyncMock(return_value=True)
    return client


@pytest.fixture
def rate_limiter():
    """Create a rate limiter for testing."""
    config = RateLimitConfig(
        per_user=10,
        global_limit=100,
        window_seconds=60
    )
    return RateLimiter(config)


@pytest.fixture
def mock_discord_interaction():
    """Create a mock Discord interaction for testing."""
    interaction = Mock()
    interaction.user.id = 12345
    interaction.user.display_name = "TestUser"
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.response.is_done = Mock(return_value=False)
    interaction.edit_original_response = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


@pytest.fixture
def sample_workflow():
    """Sample workflow dictionary for testing."""
    return {
        "1": {
            "inputs": {
                "text": "test prompt"
            },
            "class_type": "CLIPTextEncode"
        }
    }





