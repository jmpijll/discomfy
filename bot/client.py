"""
Main Discord bot client for DisComfy v2.0.

Following discord.py Bot best practices from Context7.
"""

import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from config import get_config, BotConfig, validate_discord_token, validate_comfyui_url
from core.comfyui.client import ComfyUIClient
from core.generators.image import ImageGenerator
from utils.rate_limit import RateLimiter, RateLimitConfig
from utils.logging import setup_logging
from core.exceptions import DisComfyError


class ComfyUIBot(commands.Bot):
    """Main Discord bot class for ComfyUI integration (v2.0 architecture)."""
    
    def __init__(self):
        """Initialize the bot with v2.0 architecture."""
        # Load configuration
        self.config: BotConfig = get_config()
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Validate configuration
        self._validate_config()
        
        # Initialize Discord bot
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix=self.config.discord.command_prefix,
            intents=intents,
            help_command=None
        )
        
        # Initialize ComfyUI client
        self.comfyui_client: Optional[ComfyUIClient] = None
        
        # Initialize generators (will be set up in setup_hook)
        self.image_generator: Optional[ImageGenerator] = None
        self.video_generator = None  # VideoGenerator instance
        
        # Initialize rate limiter
        rate_limit_config = RateLimitConfig(
            per_user=self.config.security.rate_limit_per_user,
            global_limit=self.config.security.rate_limit_global,
            window_seconds=60
        )
        self.rate_limiter = RateLimiter(rate_limit_config)
    
    def _validate_config(self) -> None:
        """Validate bot configuration."""
        try:
            # Validate Discord token
            if not validate_discord_token(self.config.discord.token):
                raise ValueError("Invalid Discord bot token format")
            
            # Validate ComfyUI URL
            if not validate_comfyui_url(self.config.comfyui.url):
                raise ValueError("Invalid ComfyUI URL format")
            
            self.logger.info("Configuration validation passed")
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            raise
    
    async def setup_hook(self) -> None:
        """Set up the bot after login.
        
        Following discord.py setup_hook patterns from Context7.
        """
        try:
            self.logger.info("Setting up bot...")
            
            # Initialize ComfyUI client
            self.comfyui_client = ComfyUIClient(
                base_url=self.config.comfyui.url,
                timeout=self.config.comfyui.timeout
            )
            await self.comfyui_client.initialize()
            
            # Test connection
            if not await self.comfyui_client.test_connection():
                self.logger.warning("ComfyUI connection test failed - bot will still start")
            
            # Initialize image generator
            # Prefer new architecture, fallback to old for compatibility
            try:
                # Try new ImageGenerator first
                from core.generators.image import ImageGenerator as NewImageGenerator
                self.image_generator = NewImageGenerator(self.comfyui_client, self.config)
                await self.image_generator.initialize()
            except (ImportError, AttributeError):
                # Fallback to old ImageGenerator for backward compatibility
                try:
                    from image_gen import ImageGenerator as OldImageGenerator
                    self.image_generator = OldImageGenerator()
                    await self.image_generator.initialize()
                    self.logger.warning("Using legacy ImageGenerator - consider migrating to v2.0 architecture")
                except ImportError:
                    self.logger.error("No ImageGenerator available")
                    raise
            
            # Initialize video generator with new v2.0 architecture
            from core.generators.video import VideoGenerator
            self.video_generator = VideoGenerator(
                comfyui_client=self.image_generator.client,
                config=self.config
            )
            self.logger.info("🎬 VideoGenerator initialized with new v2.0 architecture")
            
            # Sync slash commands
            if self.config.discord.guild_id:
                guild = discord.Object(id=int(self.config.discord.guild_id))
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                self.logger.info(f"Synced commands to guild {self.config.discord.guild_id}")
            else:
                await self.tree.sync()
                self.logger.info("Synced commands globally")
            
            self.logger.info("Bot setup completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during bot setup: {e}")
            raise
    
    async def on_ready(self) -> None:
        """Called when the bot is ready.
        
        Following discord.py on_ready patterns from Context7.
        """
        self.logger.info(f"✅ Bot logged in as {self.user} (ID: {self.user.id})")
        self.logger.info(f"📊 Connected to {len(self.guilds)} guild(s)")
    
    async def close(self) -> None:
        """Clean up resources when bot closes.
        
        Following discord.py close patterns from Context7.
        """
        self.logger.info("Shutting down bot...")
        
        # Close generators
        if self.image_generator:
            try:
                await self.image_generator.shutdown()
            except Exception as e:
                self.logger.error(f"Error shutting down image generator: {e}")
        
        if self.video_generator and hasattr(self.video_generator, 'shutdown'):
            try:
                await self.video_generator.shutdown()
            except Exception as e:
                self.logger.error(f"Error shutting down video generator: {e}")
        
        # Close ComfyUI client
        if self.comfyui_client:
            try:
                await self.comfyui_client.close()
            except Exception as e:
                self.logger.error(f"Error closing ComfyUI client: {e}")
        
        # Close Discord connection
        await super().close()
        self.logger.info("Bot shutdown complete")
    
    def _check_rate_limit(self, user_id: int) -> bool:
        """
        Check if user is within rate limit.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            True if within limit, False if rate limited
        """
        return self.rate_limiter.check_rate_limit(user_id)
    
    async def _create_unified_progress_callback(
        self,
        interaction: discord.Interaction,
        title: str,
        prompt: str,
        settings: str
    ):
        """
        Create a unified progress callback for Discord updates.
        
        This method maintains backward compatibility with existing code.
        Delegates to core/progress/callbacks for actual implementation.
        """
        from core.progress.callbacks import create_discord_progress_callback
        
        return await create_discord_progress_callback(
            interaction,
            title,
            prompt,
            settings
        )

