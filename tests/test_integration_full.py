"""
Full integration tests for DisComfy v2.0.

Following pytest best practices for integration testing.
These tests verify end-to-end functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import discord

from bot.commands.generate import generate_command_handler
from bot.ui.generation.complete_setup_view import CompleteSetupView
from core.comfyui.client import ComfyUIClient
from utils.rate_limit import RateLimiter


@pytest.mark.integration
@pytest.mark.asyncio
class TestFullIntegration:
    """Full integration tests."""
    
    async def test_generate_command_full_flow(self):
        """Test complete /generate command flow with UI."""
        # Setup
        bot = Mock()
        bot._check_rate_limit = Mock(return_value=True)
        bot.config = Mock()
        bot.config.discord.max_file_size_mb = 25
        bot.config.security.max_prompt_length = 2000
        bot.logger = Mock()
        bot.image_generator = Mock()
        bot.image_generator.get_available_loras = AsyncMock(return_value=[])
        bot.image_generator.generate_image = AsyncMock(
            return_value=([b"fake_image"], {"seed": 12345})
        )
        bot._create_unified_progress_callback = AsyncMock(
            return_value=AsyncMock()
        )
        
        interaction = Mock(spec=discord.Interaction)
        interaction.user.id = 12345
        interaction.user.display_name = "TestUser"
        interaction.response.send_message = AsyncMock()
        interaction.response.is_done = Mock(return_value=False)
        
        # Execute
        await generate_command_handler(
            interaction,
            bot,
            "A beautiful landscape"
        )
        
        # Verify
        assert interaction.response.send_message.called
        # Verify CompleteSetupView was created
        call_args = interaction.response.send_message.call_args
        assert "embed" in call_args.kwargs
        assert "view" in call_args.kwargs
        assert isinstance(call_args.kwargs["view"], CompleteSetupView)
    
    async def test_rate_limiting_integration(self):
        """Test rate limiting integration across system."""
        from utils.rate_limit import RateLimitConfig
        
        config = RateLimitConfig(per_user=3, global_limit=10, window_seconds=60)
        limiter = RateLimiter(config)
        
        # Simulate multiple users
        user1 = 11111
        user2 = 22222
        
        # User 1 makes requests
        assert limiter.check_rate_limit(user1) is True  # 1st
        assert limiter.check_rate_limit(user1) is True  # 2nd
        assert limiter.check_rate_limit(user1) is True  # 3rd
        assert limiter.check_rate_limit(user1) is False  # 4th - rate limited
        
        # User 2 should still work
        assert limiter.check_rate_limit(user2) is True
        assert limiter.check_rate_limit(user2) is True
    
    async def test_comfyui_client_integration(self, mock_comfyui_client):
        """Test ComfyUI client integration."""
        client = mock_comfyui_client
        
        # Test workflow
        workflow = {"1": {"inputs": {}, "class_type": "Test"}}
        
        # Queue prompt
        prompt_id = await client.queue_prompt(workflow)
        assert prompt_id == "test_prompt_id"
        
        # Get history
        history = await client.get_history(prompt_id)
        assert history is not None
        
        # Download output
        image_data = await client.download_output("test.png")
        assert image_data == b"fake_image_data"
    
    async def test_validator_integration(self):
        """Test validator integration in command flow."""
        from core.validators.image import ImageValidator, PromptParameters
        
        # Image validation
        validator = ImageValidator(max_size_mb=25)
        image = Mock()
        image.content_type = "image/png"
        image.size = 1024 * 1024
        
        result = validator.validate(image)
        assert result.is_valid is True
        
        # Prompt validation
        params = PromptParameters(prompt="Valid prompt")
        assert params.prompt == "Valid prompt"
    
    async def test_error_handling_integration(self):
        """Test error handling across modules."""
        from core.exceptions import ValidationError, ComfyUIError
        
        # Validation error
        try:
            raise ValidationError("Invalid input", field="prompt")
        except ValidationError as e:
            assert e.field == "prompt"
            assert str(e) == "Invalid input"
        
        # ComfyUI error
        try:
            raise ComfyUIError("API failed", status_code=500)
        except ComfyUIError as e:
            assert e.status_code == 500
            assert str(e) == "API failed"


