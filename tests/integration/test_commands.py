"""
Integration tests for command handlers.

Following pytest best practices for integration testing.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import discord

from bot.commands.generate import generate_command_handler
from bot.commands.edit import editflux_command_handler


@pytest.mark.integration
@pytest.mark.asyncio
class TestCommandIntegration:
    """Integration tests for command handlers."""
    
    async def test_generate_command_flow(self):
        """Test complete /generate command flow."""
        # Setup mocks
        bot = Mock()
        bot._check_rate_limit = Mock(return_value=True)
        bot.config = Mock()
        bot.config.discord.max_file_size_mb = 25
        bot.logger = Mock()
        
        interaction = Mock(spec=discord.Interaction)
        interaction.user.id = 12345
        interaction.user.display_name = "TestUser"
        interaction.response.send_message = AsyncMock()
        interaction.response.is_done = Mock(return_value=False)
        
        # Execute command
        await generate_command_handler(
            interaction,
            bot,
            "A beautiful landscape"
        )
        
        # Verify response was sent
        assert interaction.response.send_message.called
    
    async def test_edit_command_flow(self):
        """Test complete /editflux command flow."""
        # Setup mocks
        bot = Mock()
        bot._check_rate_limit = Mock(return_value=True)
        bot.config = Mock()
        bot.config.discord.max_file_size_mb = 25
        bot.logger = Mock()
        bot.image_generator = Mock()
        bot.image_generator.generate_edit = AsyncMock(
            return_value=(b"fake_image", {"seed": 12345})
        )
        bot._create_unified_progress_callback = AsyncMock(
            return_value=AsyncMock()
        )
        
        interaction = Mock(spec=discord.Interaction)
        interaction.user.id = 12345
        interaction.response.send_message = AsyncMock()
        interaction.response.is_done = Mock(return_value=False)
        interaction.followup.send = AsyncMock()
        
        image = Mock()
        image.content_type = "image/png"
        image.size = 1024 * 1024
        image.read = AsyncMock(return_value=b"fake_image_data")
        
        # Execute command
        await editflux_command_handler(
            interaction,
            bot,
            image,
            "make it blue",
            20
        )
        
        # Verify initial response
        assert interaction.response.send_message.called


