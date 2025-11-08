"""
Unit tests for command handlers.

Following pytest best practices.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from bot.commands.generate import generate_command_handler
from bot.commands.edit import editflux_command_handler, editqwen_command_handler
from bot.commands.status import status_command_handler, help_command_handler
from bot.commands.loras import loras_command_handler


@pytest.mark.asyncio
class TestGenerateCommand:
    """Test /generate command handler."""
    
    async def test_rate_limited(self, mock_discord_interaction):
        """Test that rate limiting works."""
        bot = Mock()
        bot._check_rate_limit = Mock(return_value=False)
        bot.config = Mock()
        bot.config.discord.max_file_size_mb = 25
        bot.logger = Mock()
        
        await generate_command_handler(
            mock_discord_interaction,
            bot,
            "test prompt"
        )
        
        mock_discord_interaction.response.send_message.assert_called_once()
        call_args = mock_discord_interaction.response.send_message.call_args[0][0]
        assert "too quickly" in call_args.lower()
    
    async def test_invalid_prompt(self, mock_discord_interaction):
        """Test that invalid prompts are rejected."""
        bot = Mock()
        bot._check_rate_limit = Mock(return_value=True)
        bot.config = Mock()
        bot.config.discord.max_file_size_mb = 25
        bot.logger = Mock()
        
        # Empty prompt should fail validation
        await generate_command_handler(
            mock_discord_interaction,
            bot,
            ""  # Empty prompt
        )
        
        # Should send error message
        assert mock_discord_interaction.response.send_message.called
    
    async def test_valid_image_generation(self, mock_discord_interaction):
        """Test successful image generation setup."""
        bot = Mock()
        bot._check_rate_limit = Mock(return_value=True)
        bot.config = Mock()
        bot.config.discord.max_file_size_mb = 25
        bot.logger = Mock()
        
        await generate_command_handler(
            mock_discord_interaction,
            bot,
            "A beautiful landscape"
        )
        
        # Should send setup view
        assert mock_discord_interaction.response.send_message.called


@pytest.mark.asyncio
class TestEditCommands:
    """Test edit command handlers."""
    
    async def test_editflux_rate_limited(self, mock_discord_interaction):
        """Test editflux rate limiting."""
        bot = Mock()
        bot._check_rate_limit = Mock(return_value=False)
        bot.config = Mock()
        bot.config.discord.max_file_size_mb = 25
        bot.logger = Mock()
        
        image = Mock()
        image.content_type = "image/png"
        image.size = 1024 * 1024
        
        await editflux_command_handler(
            mock_discord_interaction,
            bot,
            image,
            "edit prompt",
            20
        )
        
        assert mock_discord_interaction.response.send_message.called
    
    async def test_editflux_invalid_image(self, mock_discord_interaction):
        """Test editflux with invalid image."""
        bot = Mock()
        bot._check_rate_limit = Mock(return_value=True)
        bot.config = Mock()
        bot.config.discord.max_file_size_mb = 25
        bot.logger = Mock()
        
        image = Mock()
        image.content_type = "application/pdf"  # Invalid
        image.size = 1024 * 1024
        
        await editflux_command_handler(
            mock_discord_interaction,
            bot,
            image,
            "edit prompt",
            20
        )
        
        # Should send error about invalid image
        assert mock_discord_interaction.response.send_message.called


@pytest.mark.asyncio
class TestStatusCommand:
    """Test /status command handler."""
    
    async def test_status_success(self, mock_discord_interaction):
        """Test successful status check."""
        bot = Mock()
        bot.image_generator = Mock()
        bot.image_generator.session = Mock()
        bot.logger = Mock()
        
        # Mock successful connection test
        async def mock_test_connection():
            return True
        
        bot.image_generator.test_connection = AsyncMock(return_value=True)
        
        # Mock queue response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "queue_pending": [],
            "queue_running": []
        })
        
        async def mock_get(*args, **kwargs):
            class MockContext:
                async def __aenter__(self):
                    return mock_response
                async def __aexit__(self, *args):
                    pass
            return MockContext()
        
        bot.image_generator.session.get = mock_get
        
        await status_command_handler(mock_discord_interaction, bot)
        
        assert mock_discord_interaction.response.send_message.called


@pytest.mark.asyncio
class TestLorasCommand:
    """Test /loras command handler."""
    
    async def test_loras_success(self, mock_discord_interaction):
        """Test successful LoRAs listing."""
        bot = Mock()
        bot.image_generator = Mock()
        bot.logger = Mock()
        
        # Mock LoRAs
        mock_loras = [
            {"filename": "lora1.safetensors", "display_name": "LoRA 1", "model_type": "flux"},
            {"filename": "lora2.safetensors", "display_name": "LoRA 2", "model_type": "flux"}
        ]
        
        bot.image_generator.get_available_loras = AsyncMock(return_value=mock_loras)
        
        await loras_command_handler(mock_discord_interaction, bot)
        
        assert mock_discord_interaction.response.send_message.called
    
    async def test_loras_no_loras(self, mock_discord_interaction):
        """Test LoRAs command when no LoRAs available."""
        bot = Mock()
        bot.image_generator = Mock()
        bot.logger = Mock()
        
        bot.image_generator.get_available_loras = AsyncMock(return_value=[])
        
        await loras_command_handler(mock_discord_interaction, bot)
        
        assert mock_discord_interaction.response.send_message.called





