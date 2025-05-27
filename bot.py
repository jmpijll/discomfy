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
from video_gen import VideoGenerator, save_output_video, get_unique_video_filename

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
        
        # Initialize shared image generator
        self.image_generator: Optional[ImageGenerator] = None
        
        # Initialize video generator
        self.video_generator: Optional[VideoGenerator] = None
        
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
            
            # Initialize video generator
            self.video_generator = VideoGenerator()
            
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
                # Interaction already responded to, use followup
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                # First response to interaction
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.NotFound:
            # Interaction expired
            self.logger.warning(f"Discord interaction expired when sending error to {interaction.user.id}")
        except discord.HTTPException as e:
            if e.code == 40060:  # Interaction already acknowledged
                try:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                except:
                    self.logger.error(f"Failed to send error followup: {e}")
            else:
                self.logger.error(f"Failed to send error embed: {e}")
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
                # Interaction already responded to, use followup
                await interaction.followup.send(embed=embed)
            else:
                # First response to interaction
                await interaction.response.send_message(embed=embed)
        except discord.NotFound:
            # Interaction expired
            self.logger.warning(f"Discord interaction expired when sending progress to {interaction.user.id}")
        except discord.HTTPException as e:
            if e.code == 40060:  # Interaction already acknowledged
                try:
                    await interaction.followup.send(embed=embed)
                except:
                    self.logger.error(f"Failed to send progress followup: {e}")
            else:
                self.logger.error(f"Failed to send progress embed: {e}")
        except Exception as e:
            self.logger.error(f"Failed to send progress embed: {e}")

# Slash command for image generation
@app_commands.command(name="generate", description="Generate images using ComfyUI")
@app_commands.describe(
    prompt="The prompt for image generation",
    workflow="Workflow to use (default: auto-detect)",
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
    workflow: str = "",
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
        
        # Determine workflow and generator type
        selected_workflow = workflow.strip() if workflow else ""
        workflow_config = None
        generator_type = "image"  # default
        
        if selected_workflow:
            # User specified a workflow
            if selected_workflow in bot.config.workflows:
                workflow_config = bot.config.workflows[selected_workflow]
                generator_type = workflow_config.type
            else:
                await bot._send_error_embed(
                    interaction,
                    "Invalid Workflow",
                    f"Workflow '{selected_workflow}' not found. Use `/workflows` to see available options."
                )
                return
        else:
            # Auto-detect: use default image workflow
            selected_workflow = bot.config.generation.default_workflow
            if selected_workflow in bot.config.workflows:
                workflow_config = bot.config.workflows[selected_workflow]
                generator_type = workflow_config.type
        
        # Send initial response
        await bot._send_progress_embed(
            interaction,
            "Generating Content",
            f"🎨 Creating your {generator_type} with prompt: `{prompt[:100]}{'...' if len(prompt) > 100 else ''}`\n"
            f"📏 Size: {width}x{height} | 🔧 Steps: {steps} | ⚙️ CFG: {cfg}\n"
            f"🖼️ Workflow: {workflow_config.name if workflow_config else selected_workflow}\n"
            f"🔄 Generating {batch_size} {generator_type}{'s' if batch_size > 1 else ''}..."
        )
        
        # Progress callback for updates
        async def progress_callback(status: str, queue_position: int = 0):
            try:
                if queue_position > 0:
                    description = f"⏳ Queue position: {queue_position}\n📊 Status: {status.title()}"
                else:
                    description = f"📊 Status: {status.title()}"
                
                embed = discord.Embed(
                    title=f"⏳ Generating {generator_type.title()}",
                    description=f"🎨 Prompt: `{prompt[:80]}{'...' if len(prompt) > 80 else ''}`\n\n{description}",
                    color=discord.Color.blue()
                )
                
                # Always use edit_original_response since we already responded
                await interaction.edit_original_response(embed=embed)
                
            except discord.NotFound:
                # Interaction expired, log but don't crash
                bot.logger.warning(f"Discord interaction expired for user {interaction.user.id}")
            except discord.HTTPException as e:
                # Log HTTP errors but don't crash
                bot.logger.warning(f"Failed to update progress for user {interaction.user.id}: {e}")
            except Exception as e:
                bot.logger.warning(f"Failed to update progress: {e}")
        
        # Generate content based on type
        try:
            if generator_type == "video":
                # Video generation
                async with bot.video_generator as gen:
                    video_data, filename, generation_info = await gen.generate_video(
                        prompt=prompt,
                        negative_prompt=negative_prompt,
                        workflow_name=selected_workflow,
                        width=width,
                        height=height,
                        steps=steps,
                        cfg=cfg,
                        seed=seed,
                        progress_callback=progress_callback
                    )
                
                # Save video
                output_path = save_output_video(video_data, filename)
                file_data = video_data
                
            else:
                # Image generation (default)
                async with bot.image_generator as gen:
                    image_data, generation_info = await gen.generate_image(
                        prompt=prompt,
                        negative_prompt=negative_prompt,
                        workflow_name=selected_workflow,
                        width=width,
                        height=height,
                        steps=steps,
                        cfg=cfg,
                        batch_size=batch_size,
                        seed=seed,
                        progress_callback=progress_callback
                    )
                
                # Save image
                filename = get_unique_filename(f"discord_{interaction.user.id}")
                output_path = save_output_image(image_data, filename)
                file_data = image_data
                
        except Exception as gen_error:
            # If generation fails, we still need to handle the interaction
            raise gen_error
        
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
        
        # Send content - try multiple approaches
        file = discord.File(BytesIO(file_data), filename=filename)
        
        try:
            # Try to edit the original response with the file
            await interaction.edit_original_response(
                embed=success_embed,
                attachments=[file]
            )
            bot.logger.info(f"Successfully sent {generator_type} via edit_original_response for {interaction.user}")
            
        except discord.NotFound:
            # Interaction expired, send as new followup message
            try:
                await interaction.followup.send(
                    embed=success_embed,
                    file=discord.File(BytesIO(file_data), filename=filename)  # Create new file object
                )
                bot.logger.info(f"Successfully sent {generator_type} via followup for {interaction.user}")
            except Exception as followup_error:
                bot.logger.error(f"Failed to send followup {generator_type}: {followup_error}")
                
        except discord.HTTPException as e:
            bot.logger.error(f"HTTP error sending {generator_type}: {e}")
            # Try sending as followup
            try:
                await interaction.followup.send(
                    embed=success_embed,
                    file=discord.File(BytesIO(file_data), filename=filename)  # Create new file object
                )
                bot.logger.info(f"Successfully sent {generator_type} via followup after HTTP error for {interaction.user}")
            except Exception as followup_error:
                bot.logger.error(f"Failed to send followup {generator_type} after HTTP error: {followup_error}")
                
        except Exception as e:
            bot.logger.error(f"Unexpected error sending {generator_type}: {e}")
            # Last resort: try simple followup
            try:
                await interaction.followup.send(
                    f"✅ {generator_type.title()} generated successfully! (Failed to send with embed)",
                    file=discord.File(BytesIO(file_data), filename=filename)  # Create new file object
                )
                bot.logger.info(f"Successfully sent {generator_type} via simple followup for {interaction.user}")
            except Exception as final_error:
                bot.logger.error(f"Complete failure to send {generator_type}: {final_error}")
        
        bot.logger.info(f"{generator_type.title()} generation process completed for {interaction.user} (ID: {interaction.user.id})")
        
        # Clean up old outputs
        cleanup_old_outputs(bot.config.generation.output_limit)
        
    except ComfyUIAPIError as e:
        bot.logger.error(f"ComfyUI API error for user {interaction.user.id}: {e}")
        try:
            await bot._send_error_embed(
                interaction,
                "Generation Failed",
                f"ComfyUI error: {str(e)[:200]}{'...' if len(str(e)) > 200 else ''}"
            )
        except:
            # If we can't send error embed, try simple message
            try:
                if interaction.response.is_done():
                    await interaction.followup.send("❌ Generation failed. Please try again.")
                else:
                    await interaction.response.send_message("❌ Generation failed. Please try again.")
            except:
                bot.logger.error("Failed to send error response to user")
        
    except Exception as e:
        bot.logger.error(f"Unexpected error in generate command: {e}")
        bot.logger.error(traceback.format_exc())
        try:
            await bot._send_error_embed(
                interaction,
                "Unexpected Error",
                "An unexpected error occurred. Please try again later."
            )
        except:
            # If we can't send error embed, try simple message
            try:
                if interaction.response.is_done():
                    await interaction.followup.send("❌ An unexpected error occurred. Please try again later.")
                else:
                    await interaction.response.send_message("❌ An unexpected error occurred. Please try again later.")
            except:
                bot.logger.error("Failed to send error response to user")

# Help command
@app_commands.command(name="help", description="Show help information about the bot")
async def help_command(interaction: discord.Interaction):
    """Show help information about the bot."""
    embed = discord.Embed(
        title="🎨 ComfyUI Discord Bot Help",
        description="Generate amazing AI images directly in Discord!",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📝 Basic Usage",
        value="Use `/generate` with a prompt to create content:\n"
              "`/generate prompt:a beautiful sunset over mountains`\n"
              "`/generate prompt:cat video workflow:video_wan_vace_14B_i2v`",
        inline=False
    )
    
    embed.add_field(
        name="🔧 New Commands",
        value="• `/workflows` - List all available workflows\n"
              "• `/generate workflow:name` - Use specific workflow\n"
              "• `/status` - Check bot and ComfyUI status",
        inline=False
    )
    
    embed.add_field(
        name="⚙️ Parameters",
        value="• **prompt** - What you want to generate (required)\n"
              "• **workflow** - Choose image, video, or upscale workflow\n"
              "• **negative_prompt** - What to avoid\n"
              "• **width/height** - Content dimensions (256-2048)\n"
              "• **steps** - Quality vs speed (1-150)\n"
              "• **cfg** - How closely to follow prompt (1.0-30.0)\n"
              "• **batch_size** - Number of images (1-4)\n"
              "• **seed** - For reproducible results",
        inline=False
    )
    
    embed.add_field(
        name="🎬 Content Types",
        value="• **Images** - High-quality AI-generated images\n"
              "• **Videos** - Convert images to MP4 animations\n"
              "• **Upscaling** - Enhance image resolution",
        inline=False
    )
    
    embed.add_field(
        name="💡 Tips",
        value="• Use `/workflows` to see all available options\n"
              "• Be descriptive in your prompts\n"
              "• Use negative prompts to avoid unwanted elements\n"
              "• Higher steps = better quality but slower\n"
              "• CFG 5-8 works well for most prompts",
        inline=False
    )
    
    embed.add_field(
        name="🔧 Example Commands",
        value="`/generate prompt:cyberpunk city at night, neon lights`\n"
              "`/generate prompt:cute cat workflow:video_wan_vace_14B_i2v`\n"
              "`/generate prompt:fantasy landscape width:1536 height:1024`\n"
              "`/workflows` - See all available workflows",
        inline=False
    )
    
    embed.set_footer(text="Powered by ComfyUI | Made with ❤️")
    
    await interaction.response.send_message(embed=embed)

# Status command
@app_commands.command(name="status", description="Check bot and ComfyUI status")
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

# Workflows command
@app_commands.command(name="workflows", description="List available workflows")
async def workflows_command(interaction: discord.Interaction):
    """List all available workflows."""
    bot: ComfyUIBot = interaction.client
    
    embed = discord.Embed(
        title="🔧 Available Workflows",
        description="Choose from these workflows for different generation types:",
        color=discord.Color.blue()
    )
    
    # Group workflows by type
    workflow_types = {}
    for name, config in bot.config.workflows.items():
        if config.enabled:
            workflow_type = config.type
            if workflow_type not in workflow_types:
                workflow_types[workflow_type] = []
            workflow_types[workflow_type].append((name, config))
    
    # Add fields for each type
    type_emojis = {
        "image": "🖼️",
        "video": "🎬",
        "upscale": "🔍"
    }
    
    for workflow_type, workflows in workflow_types.items():
        emoji = type_emojis.get(workflow_type, "⚙️")
        workflow_list = []
        
        for name, config in workflows:
            is_default = name == bot.config.generation.default_workflow
            default_marker = " ⭐" if is_default else ""
            workflow_list.append(f"**{name}**{default_marker}\n{config.description}")
        
        embed.add_field(
            name=f"{emoji} {workflow_type.title()} Workflows",
            value="\n\n".join(workflow_list) if workflow_list else "None available",
            inline=False
        )
    
    # Add usage instructions
    embed.add_field(
        name="💡 Usage",
        value="Use `/generate workflow:workflow_name` to specify a workflow\n"
              "⭐ = Default workflow (used when no workflow specified)",
        inline=False
    )
    
    embed.set_footer(text="Use /help for more generation options")
    
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
        bot.tree.add_command(workflows_command)
        
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