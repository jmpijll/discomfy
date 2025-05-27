"""
Main Discord bot for ComfyUI integration.
Handles all Discord-related logic and user interactions.
"""

import asyncio
import logging
import traceback
from io import BytesIO
from pathlib import Path
from typing import Optional, Dict, Any

import discord
from discord.ext import commands
from discord import app_commands

from config import get_config, BotConfig, validate_discord_token, validate_comfyui_url
from image_gen import ImageGenerator, ComfyUIAPIError, save_output_image, cleanup_old_outputs, get_unique_filename

class ComfyUIBot(commands.Bot):
    """Main Discord bot class for ComfyUI integration."""
    
    def __init__(self):
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
        
        # Initialize image generator
        self.image_generator: Optional[ImageGenerator] = None
        
        # Rate limiting (simple in-memory storage)
        self.user_rate_limits: Dict[int, list] = {}
        self.global_rate_limit: list = []
    
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
        """Set up the bot after login."""
        try:
            self.logger.info("Setting up bot...")
            
            # Initialize image generator
            self.image_generator = ImageGenerator()
            
            # Test ComfyUI connection
            async with self.image_generator as gen:
                if not await gen.test_connection():
                    self.logger.warning("ComfyUI connection test failed - bot will still start")
            
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
            self.logger.error(f"Bot setup failed: {e}")
            raise
    
    async def on_ready(self) -> None:
        """Called when the bot is ready."""
        self.logger.info(f"🤖 Bot is ready! Logged in as {self.user}")
        self.logger.info(f"🎨 ComfyUI URL: {self.config.comfyui.url}")
        self.logger.info(f"🚀 Bot is ready! Use /generate to start creating!")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for /generate commands"
        )
        await self.change_presence(activity=activity)
        
        # Clean up old outputs
        cleanup_old_outputs(self.config.generation.output_limit)
    
    async def on_error(self, event: str, *args, **kwargs) -> None:
        """Handle bot errors."""
        self.logger.error(f"Bot error in event {event}: {traceback.format_exc()}")
    
    def _check_rate_limit(self, user_id: int) -> bool:
        """Check if user is rate limited."""
        import time
        
        current_time = time.time()
        
        # Clean old entries (older than 1 minute)
        cutoff_time = current_time - 60
        
        # Check user rate limit
        if user_id not in self.user_rate_limits:
            self.user_rate_limits[user_id] = []
        
        user_requests = self.user_rate_limits[user_id]
        user_requests[:] = [t for t in user_requests if t > cutoff_time]
        
        if len(user_requests) >= self.config.security.rate_limit_per_user:
            return False
        
        # Check global rate limit
        self.global_rate_limit[:] = [t for t in self.global_rate_limit if t > cutoff_time]
        
        if len(self.global_rate_limit) >= self.config.security.rate_limit_global:
            return False
        
        # Add current request
        user_requests.append(current_time)
        self.global_rate_limit.append(current_time)
        
        return True
    
    async def _send_error_embed(self, interaction: discord.Interaction, title: str, description: str) -> None:
        """Send an error embed to the user."""
        embed = discord.Embed(
            title=f"❌ {title}",
            description=description,
            color=discord.Color.red()
        )
        
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            self.logger.error(f"Failed to send error embed: {e}")
    
    async def _send_progress_embed(self, interaction: discord.Interaction, title: str, description: str) -> None:
        """Send a progress embed to the user."""
        embed = discord.Embed(
            title=f"⏳ {title}",
            description=description,
            color=discord.Color.blue()
        )
        
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.send_message(embed=embed)
        except Exception as e:
            self.logger.error(f"Failed to send progress embed: {e}")

# Slash command for image generation
@app_commands.describe(
    prompt="The prompt for image generation",
    negative_prompt="Negative prompt (things to avoid)",
    width="Image width (default: 1024)",
    height="Image height (default: 1024)",
    steps="Number of sampling steps (default: 50)",
    cfg="CFG scale (default: 5.0)",
    batch_size="Number of images to generate (default: 1)",
    seed="Random seed (leave empty for random)"
)
async def generate_command(
    interaction: discord.Interaction,
    prompt: str,
    negative_prompt: str = "",
    width: int = 1024,
    height: int = 1024,
    steps: int = 50,
    cfg: float = 5.0,
    batch_size: int = 1,
    seed: Optional[int] = None
):
    """Generate images using ComfyUI."""
    bot: ComfyUIBot = interaction.client
    
    try:
        # Check rate limiting
        if not bot._check_rate_limit(interaction.user.id):
            await bot._send_error_embed(
                interaction,
                "Rate Limited",
                "You're sending requests too quickly. Please wait a moment before trying again."
            )
            return
        
        # Validate inputs
        if not prompt.strip():
            await bot._send_error_embed(
                interaction,
                "Invalid Input",
                "Prompt cannot be empty."
            )
            return
        
        if len(prompt) > bot.config.security.max_prompt_length:
            await bot._send_error_embed(
                interaction,
                "Prompt Too Long",
                f"Prompt must be {bot.config.security.max_prompt_length} characters or less."
            )
            return
        
        if batch_size > bot.config.generation.max_batch_size:
            await bot._send_error_embed(
                interaction,
                "Batch Size Too Large",
                f"Maximum batch size is {bot.config.generation.max_batch_size}."
            )
            return
        
        # Validate dimensions
        if width < 256 or width > 2048 or height < 256 or height > 2048:
            await bot._send_error_embed(
                interaction,
                "Invalid Dimensions",
                "Width and height must be between 256 and 2048 pixels."
            )
            return
        
        if steps < 1 or steps > 150:
            await bot._send_error_embed(
                interaction,
                "Invalid Steps",
                "Steps must be between 1 and 150."
            )
            return
        
        if cfg < 1.0 or cfg > 30.0:
            await bot._send_error_embed(
                interaction,
                "Invalid CFG",
                "CFG scale must be between 1.0 and 30.0."
            )
            return
        
        # Send initial response
        embed = discord.Embed(
            title="🎨 Generating Image",
            description=f"**Prompt:** {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n"
                       f"**Size:** {width}x{height}\n"
                       f"**Steps:** {steps} | **CFG:** {cfg}\n"
                       f"**Batch:** {batch_size} image{'s' if batch_size > 1 else ''}",
            color=discord.Color.blue()
        )
        embed.set_footer(text="This may take a few moments...")
        
        await interaction.response.send_message(embed=embed)
        
        # Progress callback
        last_status = None
        async def progress_callback(status: str, queue_position: int = 0):
            nonlocal last_status
            if status != last_status:
                status_text = f"Status: {status.title()}"
                if queue_position > 0:
                    status_text += f" (Position in queue: {queue_position})"
                
                embed.description = f"**Prompt:** {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n" \
                                  f"**Size:** {width}x{height}\n" \
                                  f"**Steps:** {steps} | **CFG:** {cfg}\n" \
                                  f"**Batch:** {batch_size} image{'s' if batch_size > 1 else ''}\n\n" \
                                  f"⏳ {status_text}"
                
                try:
                    await interaction.edit_original_response(embed=embed)
                except:
                    pass  # Ignore edit failures
                
                last_status = status
        
        # Generate image
        async with bot.image_generator as gen:
            image_data, generation_info = await gen.generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                steps=steps,
                cfg=cfg,
                seed=seed,
                batch_size=batch_size,
                progress_callback=progress_callback
            )
        
        # Save image
        filename = get_unique_filename("generated")
        output_path = save_output_image(image_data, filename)
        
        # Create success embed
        success_embed = discord.Embed(
            title="✅ Image Generated Successfully!",
            description=f"**Prompt:** {prompt[:200]}{'...' if len(prompt) > 200 else ''}",
            color=discord.Color.green()
        )
        
        # Add generation details
        success_embed.add_field(
            name="Generation Details",
            value=f"**Size:** {width}x{height}\n"
                  f"**Steps:** {steps} | **CFG:** {cfg}\n"
                  f"**Seed:** {generation_info.get('seed', 'Unknown')}\n"
                  f"**Images:** {generation_info.get('num_images', 1)}",
            inline=True
        )
        
        success_embed.add_field(
            name="Technical Info",
            value=f"**Workflow:** {generation_info.get('workflow', 'Default')}\n"
                  f"**Prompt ID:** {generation_info.get('prompt_id', 'Unknown')[:8]}...",
            inline=True
        )
        
        success_embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        # Send image
        file = discord.File(BytesIO(image_data), filename=filename)
        
        await interaction.edit_original_response(
            embed=success_embed,
            attachments=[file]
        )
        
        bot.logger.info(f"Successfully generated image for {interaction.user} (ID: {interaction.user.id})")
        
        # Clean up old outputs
        cleanup_old_outputs(bot.config.generation.output_limit)
        
    except ComfyUIAPIError as e:
        bot.logger.error(f"ComfyUI API error for user {interaction.user.id}: {e}")
        await bot._send_error_embed(
            interaction,
            "Generation Failed",
            f"ComfyUI error: {str(e)[:200]}{'...' if len(str(e)) > 200 else ''}"
        )
        
    except Exception as e:
        bot.logger.error(f"Unexpected error in generate command: {e}")
        bot.logger.error(traceback.format_exc())
        await bot._send_error_embed(
            interaction,
            "Unexpected Error",
            "An unexpected error occurred. Please try again later."
        )

# Help command
@app_commands.describe()
async def help_command(interaction: discord.Interaction):
    """Show help information about the bot."""
    embed = discord.Embed(
        title="🎨 ComfyUI Discord Bot Help",
        description="Generate amazing AI images directly in Discord!",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📝 Basic Usage",
        value="Use `/generate` with a prompt to create images:\n"
              "`/generate prompt:a beautiful sunset over mountains`",
        inline=False
    )
    
    embed.add_field(
        name="⚙️ Parameters",
        value="• **prompt** - What you want to generate (required)\n"
              "• **negative_prompt** - What to avoid\n"
              "• **width/height** - Image dimensions (256-2048)\n"
              "• **steps** - Quality vs speed (1-150)\n"
              "• **cfg** - How closely to follow prompt (1.0-30.0)\n"
              "• **batch_size** - Number of images (1-4)\n"
              "• **seed** - For reproducible results",
        inline=False
    )
    
    embed.add_field(
        name="💡 Tips",
        value="• Be descriptive in your prompts\n"
              "• Use negative prompts to avoid unwanted elements\n"
              "• Higher steps = better quality but slower\n"
              "• CFG 5-8 works well for most prompts",
        inline=False
    )
    
    embed.add_field(
        name="🔧 Example Commands",
        value="`/generate prompt:cyberpunk city at night, neon lights`\n"
              "`/generate prompt:cute cat negative_prompt:blurry steps:30`\n"
              "`/generate prompt:fantasy landscape width:1536 height:1024`",
        inline=False
    )
    
    embed.set_footer(text="Powered by ComfyUI | Made with ❤️")
    
    await interaction.response.send_message(embed=embed)

# Status command
@app_commands.describe()
async def status_command(interaction: discord.Interaction):
    """Check bot and ComfyUI status."""
    bot: ComfyUIBot = interaction.client
    
    embed = discord.Embed(
        title="🔍 Bot Status",
        color=discord.Color.blue()
    )
    
    # Bot status
    embed.add_field(
        name="🤖 Discord Bot",
        value="✅ Online and ready",
        inline=True
    )
    
    # Test ComfyUI connection
    try:
        async with bot.image_generator as gen:
            comfyui_online = await gen.test_connection()
        
        if comfyui_online:
            embed.add_field(
                name="🎨 ComfyUI Server",
                value="✅ Connected and ready",
                inline=True
            )
        else:
            embed.add_field(
                name="🎨 ComfyUI Server",
                value="❌ Connection failed",
                inline=True
            )
    except Exception as e:
        embed.add_field(
            name="🎨 ComfyUI Server",
            value=f"❌ Error: {str(e)[:50]}...",
            inline=True
        )
    
    # Configuration info
    embed.add_field(
        name="⚙️ Configuration",
        value=f"**ComfyUI URL:** {bot.config.comfyui.url}\n"
              f"**Max Batch Size:** {bot.config.generation.max_batch_size}\n"
              f"**Output Limit:** {bot.config.generation.output_limit}",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

async def main():
    """Main function to run the bot."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/bot.log', encoding='utf-8')
        ]
    )
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    logger = logging.getLogger(__name__)
    
    try:
        # Create and configure bot
        bot = ComfyUIBot()
        
        # Add commands to the bot
        bot.tree.add_command(generate_command)
        bot.tree.add_command(help_command)
        bot.tree.add_command(status_command)
        
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