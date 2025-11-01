"""
Main entry point for DisComfy v2.0.

Following best practices for Discord bot entry points.
"""

import asyncio
import logging
import traceback
from pathlib import Path

from typing import Optional
import discord
from discord import app_commands

from utils.logging import setup_logging
from config import get_config
from bot.client import ComfyUIBot


async def main():
    """Main function to run the bot."""
    # Set up logging
    config = get_config()
    setup_logging(
        level=config.logging.level,
        format_string=config.logging.format,
        log_file=config.logging.file_path,
        max_bytes=config.logging.max_file_size_mb * 1024 * 1024,
        backup_count=config.logging.backup_count
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Create and configure bot
        bot = ComfyUIBot()
        
        # Register command handlers with v2.0 architecture
        try:
            # Try to register new command handlers
            from bot.commands.generate import generate_command_handler
            from bot.commands.edit import editflux_command_handler, editqwen_command_handler
            from bot.commands.status import status_command_handler, help_command_handler
            from bot.commands.loras import loras_command_handler
            
            # Create app_commands wrappers
            @bot.tree.command(name="generate", description="Generate images or videos using ComfyUI")
            @app_commands.describe(
                prompt="What you want to generate",
                image="Upload an image for video generation (optional)"
            )
            async def generate_command(interaction: discord.Interaction, prompt: str, image: Optional[discord.Attachment] = None):
                await generate_command_handler(interaction, bot, prompt, image)
            
            @bot.tree.command(name="editflux", description="Edit an image using Flux Kontext AI")
            @app_commands.describe(
                image="Upload the image you want to edit",
                prompt="Describe what you want to change",
                steps="Number of sampling steps (10-50, default: 20)"
            )
            async def editflux_command(interaction: discord.Interaction, image: discord.Attachment, prompt: str, steps: Optional[int] = 20):
                await editflux_command_handler(interaction, bot, image, prompt, steps)
            
            @bot.tree.command(name="editqwen", description="Edit images using Qwen AI")
            @app_commands.describe(
                image="Upload the primary image",
                prompt="Describe what you want to change",
                image2="Upload a second image (optional)",
                image3="Upload a third image (optional)",
                steps="Number of sampling steps (4-20, default: 8)"
            )
            async def editqwen_command(interaction: discord.Interaction, image: discord.Attachment, prompt: str, image2: Optional[discord.Attachment] = None, image3: Optional[discord.Attachment] = None, steps: Optional[int] = 8):
                await editqwen_command_handler(interaction, bot, image, prompt, image2, image3, steps)
            
            @bot.tree.command(name="status", description="Check bot and ComfyUI status")
            async def status_command(interaction: discord.Interaction):
                await status_command_handler(interaction, bot)
            
            @bot.tree.command(name="help", description="Show help information")
            async def help_command(interaction: discord.Interaction):
                await help_command_handler(interaction, bot)
            
            @bot.tree.command(name="loras", description="List available LoRAs")
            async def loras_command(interaction: discord.Interaction):
                await loras_command_handler(interaction, bot)
            
            logger.info("✅ Registered new v2.0 command handlers")
            
        except ImportError as e:
            logger.warning(f"Could not import new command handlers: {e}")
            logger.info("Using legacy command handlers from bot.py")
            # Fall back to old bot.py commands
            import bot as old_bot_module
            bot.tree.add_command(old_bot_module.generate_command)
            bot.tree.add_command(old_bot_module.editflux_command)
            bot.tree.add_command(old_bot_module.editqwen_command)
            bot.tree.add_command(old_bot_module.help_command)
            bot.tree.add_command(old_bot_module.status_command)
            bot.tree.add_command(old_bot_module.loras_command)
        
        logger.info("🤖 Bot is starting up...")
        
        # Run the bot
        await bot.start(bot.config.discord.token)
        
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())
        raise
    finally:
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())

