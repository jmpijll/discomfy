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
import time

import discord
from discord.ext import commands
from discord import app_commands

from config import get_config, BotConfig, validate_discord_token, validate_comfyui_url
from image_gen import ImageGenerator, ComfyUIAPIError, save_output_image, cleanup_old_outputs, get_unique_filename, ProgressInfo
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

    async def _create_unified_progress_callback(
        self, 
        interaction: discord.Interaction, 
        operation_type: str,
        prompt: str = "",
        settings_text: str = ""
    ):
        """Create a unified progress callback for consistent progress tracking.
        
        Args:
            interaction: Discord interaction to update
            operation_type: Type of operation (e.g., "Image Generation", "Upscaling", "Video Generation")
            prompt: User prompt (optional)
            settings_text: Settings text for footer (optional)
        """
        async def progress_callback(progress: ProgressInfo):
            try:
                title, description, color = progress.get_user_friendly_status()
                
                # Customize title based on operation type
                if progress.status == "running":
                    title = f"🎨 {operation_type}"
                elif progress.status == "completed":
                    title = f"✅ {operation_type} Complete"
                elif progress.status == "queued":
                    title = f"⏳ {operation_type} Queued"
                else:
                    title = f"🔄 Starting {operation_type}"
                
                # Add prompt to description if provided
                if prompt and len(prompt.strip()) > 0:
                    prompt_preview = prompt[:80] + "..." if len(prompt) > 80 else prompt
                    description = f"🎨 **Prompt:** `{prompt_preview}`\n\n{description}"
                
                embed = discord.Embed(
                    title=title,
                    description=description,
                    color=color
                )
                
                # Add settings in footer if provided
                if settings_text:
                    embed.set_footer(text=settings_text)
                
                # Always use edit_original_response since we already responded
                await interaction.edit_original_response(embed=embed)
                
                if progress.status == "completed":
                    self.logger.info(f"✅ Successfully sent completion status to Discord for {operation_type}")
                
            except discord.NotFound:
                # Interaction expired, log but don't crash
                self.logger.warning(f"Discord interaction expired for user {interaction.user.id}")
            except discord.HTTPException as e:
                # Log HTTP errors but don't crash
                self.logger.warning(f"Failed to update progress for user {interaction.user.id}: {e}")
            except Exception as e:
                self.logger.warning(f"Failed to update progress: {e}")
        
        return progress_callback

# Slash command for image generation with model and LoRA selection
@app_commands.command(name="generate", description="Generate images using ComfyUI with model and LoRA selection")
@app_commands.describe(
    prompt="The prompt for image generation",
    model="Choose the AI model to use (default: Flux)",
    lora="Select a LoRA (will be filtered based on selected model)",
    lora_strength="Strength of the selected LoRA (0.0-2.0, default: 1.0)",
    negative_prompt="Negative prompt (things to avoid)",
    width="Image width (default: 1024)",
    height="Image height (default: 1024)", 
    steps="Number of sampling steps (default: 30 for Flux, 50 for HiDream)",
    cfg="CFG scale (default: 5.0)",
    batch_size="Number of images to generate (default: 1)",
    seed="Random seed (leave empty for random)"
)
@app_commands.choices(
    model=[
        app_commands.Choice(name="Flux (Default)", value="flux"),
        app_commands.Choice(name="HiDream", value="hidream")
    ]
)
async def generate_command(
    interaction: discord.Interaction,
    prompt: str,
    model: str = "flux",
    lora: str = "none",
    lora_strength: float = 1.0,
    negative_prompt: str = "",
    width: int = 1024,
    height: int = 1024,
    steps: Optional[int] = None,
    cfg: float = 5.0,
    batch_size: int = 1,
    seed: Optional[int] = None
):
    """Generate images using ComfyUI with model and LoRA selection."""
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
        
        # Validate LoRA strength
        if lora_strength < 0.0 or lora_strength > 2.0:
            await bot._send_error_embed(
                interaction,
                "Invalid LoRA Strength",
                "LoRA strength must be between 0.0 and 2.0."
            )
            return
        
        # Determine workflow based on model
        workflow_name = f"{model}_lora"
        workflow_config = bot.config.workflows.get(workflow_name)
        
        if not workflow_config or not workflow_config.enabled:
            await bot._send_error_embed(
                interaction,
                "Model Not Available",
                f"The '{model}' model is not available or disabled."
            )
            return
        
        # Set default steps based on model if not specified
        if steps is None:
            steps = workflow_config.default_params.get('steps', 30)
        
        # Validate steps
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
        
        # Set model-specific defaults for dimensions
        if model == "hidream" and width == 1024 and height == 1024:
            # Use HiDream's preferred dimensions
            width = workflow_config.default_params.get('width', 1216)
            height = workflow_config.default_params.get('height', 1216)
        
        # Use model-specific default negative prompt if none provided
        if not negative_prompt.strip():
            negative_prompt = workflow_config.default_params.get('negative_prompt', "")
        
        # Prepare LoRA name for workflow
        lora_name = lora if lora != "none" else None
        
        # Send initial response
        model_display = "Flux" if model == "flux" else "HiDream"
        lora_info = f" with LoRA '{lora}' (strength: {lora_strength})" if lora_name else " (no LoRA)"
        
        await bot._send_progress_embed(
            interaction,
            f"Generating Image - {model_display}",
            f"🎨 Creating your image with prompt: `{prompt[:100]}{'...' if len(prompt) > 100 else ''}`\n"
            f"🤖 Model: {model_display}{lora_info}\n"
            f"📏 Size: {width}x{height} | 🔧 Steps: {steps} | ⚙️ CFG: {cfg}\n"
            f"🔄 Generating {batch_size} image{'s' if batch_size > 1 else ''}..."
        )
        
        # Progress callback for updates
        settings_text = f"Model: {model_display} | Size: {width}x{height} | Steps: {steps} | CFG: {cfg} | Batch: {batch_size}"
        if lora_name:
            settings_text += f" | LoRA: {lora} ({lora_strength})"
        
        progress_callback = await bot._create_unified_progress_callback(
            interaction,
            "Image Generation",
            prompt,
            settings_text
        )
        
        # Generate image
        try:
            async with bot.image_generator as gen:
                image_data, generation_info = await gen.generate_image(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    workflow_name=workflow_name,
                    width=width,
                    height=height,
                    steps=steps,
                    cfg=cfg,
                    batch_size=batch_size,
                    seed=seed,
                    lora_name=lora_name,
                    lora_strength=lora_strength,
                    progress_callback=progress_callback
                )
            
            # Send final completion status update
            try:
                final_progress = ProgressInfo()
                final_progress.mark_completed()
                await progress_callback(final_progress)
                bot.logger.info("✅ Sent final completion status to Discord")
                
                # Small delay to ensure the completion message is visible
                await asyncio.sleep(1)
            except Exception as progress_error:
                bot.logger.warning(f"Failed to send final progress update: {progress_error}")
            
            # Save image
            filename = get_unique_filename(f"discord_{interaction.user.id}")
            output_path = save_output_image(image_data, filename)
            file_data = image_data
                
        except Exception as gen_error:
            # If generation fails, we still need to handle the interaction
            raise gen_error
        
        # Create success embed
        success_embed = discord.Embed(
            title=f"✅ Image Generated Successfully - {model_display}!",
            description=f"**Prompt:** {prompt[:200]}{'...' if len(prompt) > 200 else ''}",
            color=discord.Color.green()
        )
        
        # Add generation details
        details_text = f"**Size:** {width}x{height}\n**Steps:** {steps} | **CFG:** {cfg}\n**Seed:** {generation_info.get('seed', 'Unknown')}\n**Images:** {generation_info.get('num_images', 1)}"
        
        success_embed.add_field(
            name="Generation Details",
            value=details_text,
            inline=True
        )
        
        # Add model and LoRA info
        model_info = f"**Model:** {model_display}\n"
        if lora_name:
            model_info += f"**LoRA:** {lora}\n**LoRA Strength:** {lora_strength}"
        else:
            model_info += f"**LoRA:** None"
        
        success_embed.add_field(
            name="Model Info",
            value=model_info,
            inline=True
        )
        
        success_embed.add_field(
            name="Technical Info",
            value=f"**Workflow:** {generation_info.get('workflow', 'Default')}\n"
                  f"**Prompt ID:** {generation_info.get('prompt_id', 'Unknown')[:8]}...",
            inline=True
        )
        
        success_embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        # Create action buttons view
        view = PostGenerationView(
            bot=bot,
            original_image_data=file_data,
            generation_info=generation_info,
            user_id=interaction.user.id
        )
        
        # Send content - try multiple approaches
        file = discord.File(BytesIO(file_data), filename=filename)
        
        try:
            # Try to edit the original response with the file
            await interaction.edit_original_response(
                embed=success_embed,
                attachments=[file],
                view=view
            )
            bot.logger.info(f"Successfully sent image via edit_original_response for {interaction.user}")
            
        except discord.NotFound:
            # Interaction expired, send as new followup message
            try:
                await interaction.followup.send(
                    embed=success_embed,
                    file=discord.File(BytesIO(file_data), filename=filename),  # Create new file object
                    view=view
                )
                bot.logger.info(f"Successfully sent image via followup for {interaction.user}")
            except Exception as followup_error:
                bot.logger.error(f"Failed to send followup image: {followup_error}")
                
        except discord.HTTPException as e:
            bot.logger.error(f"HTTP error sending image: {e}")
            # Try sending as followup
            try:
                await interaction.followup.send(
                    embed=success_embed,
                    file=discord.File(BytesIO(file_data), filename=filename),  # Create new file object
                    view=view
                )
                bot.logger.info(f"Successfully sent image via followup after HTTP error for {interaction.user}")
            except Exception as followup_error:
                bot.logger.error(f"Failed to send followup image after HTTP error: {followup_error}")
                
        except Exception as e:
            bot.logger.error(f"Unexpected error sending image: {e}")
            # Last resort: try simple followup
            try:
                await interaction.followup.send(
                    f"✅ Image generated successfully! (Failed to send with embed)",
                    file=discord.File(BytesIO(file_data), filename=filename),  # Create new file object
                    view=view
                )
                bot.logger.info(f"Successfully sent image via simple followup for {interaction.user}")
            except Exception as final_error:
                bot.logger.error(f"Complete failure to send image: {final_error}")
        
        bot.logger.info(f"Image generation process completed for {interaction.user} (ID: {interaction.user.id}) with model: {model}")
        
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

# Post-generation action buttons view
class PostGenerationView(discord.ui.View):
    """View with buttons for post-generation actions like upscaling and animation."""
    
    def __init__(self, bot: ComfyUIBot, original_image_data: bytes, generation_info: Dict[str, Any], user_id: int):
        super().__init__(timeout=None)  # No timeout - buttons work indefinitely
        self.bot = bot
        self.original_image_data = original_image_data
        self.generation_info = generation_info
        self.original_user_id = user_id  # Keep track of original user for reference
    
    @discord.ui.button(label="🔍 Upscale", style=discord.ButtonStyle.secondary)
    async def upscale_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle upscale button click."""
        # Allow any user to use the buttons
        
        # Check rate limiting for the current user (not original user)
        if not self.bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message("❌ You're sending requests too quickly. Please wait a moment.", ephemeral=True)
            return
        
        await interaction.response.send_message("🔍 Starting upscaling process...", ephemeral=True)
        
        try:
            # Progress callback for upscaling
            progress_callback = await self.bot._create_unified_progress_callback(
                interaction,
                "Image Upscaling",
                self.generation_info.get('prompt', ''),
                f"Factor: 2x | Denoise: 0.35 | Steps: 20 | CFG: 7.0"
            )
            
            # Generate upscaled image using ComfyUI
            async with self.bot.image_generator as gen:
                # Use the upscale workflow with image data directly
                upscaled_data, upscale_info = await gen.generate_upscale(
                    input_image_data=self.original_image_data,
                    prompt=self.generation_info.get('prompt', ''),
                    negative_prompt=self.generation_info.get('negative_prompt', ''),
                    upscale_factor=2.0,
                    denoise=0.35,
                    steps=20,
                    cfg=7.0,
                    progress_callback=progress_callback
                )
            
            # Create success embed
            upscale_embed = discord.Embed(
                title="✅ Image Upscaled Successfully!",
                description=f"**Original Prompt:** {self.generation_info.get('prompt', 'Unknown')[:150]}{'...' if len(self.generation_info.get('prompt', '')) > 150 else ''}",
                color=discord.Color.green()
            )
            
            upscale_embed.add_field(
                name="Upscale Details",
                value=f"**Factor:** 2x\n**Denoise:** 0.35\n**Steps:** 20\n**CFG:** 7.0",
                inline=True
            )
            
            upscale_embed.add_field(
                name="Requested by",
                value=interaction.user.display_name,
                inline=True
            )
            
            # Send upscaled image
            filename = f"upscaled_{int(__import__('time').time())}.png"
            file = discord.File(BytesIO(upscaled_data), filename=filename)
            
            await interaction.followup.send(
                embed=upscale_embed,
                file=file,
                ephemeral=False  # Make it visible to everyone
            )
            
            self.bot.logger.info(f"Successfully upscaled image for {interaction.user}")
                    
        except Exception as e:
            self.bot.logger.error(f"Upscaling error: {e}")
            await interaction.followup.send("❌ Upscaling failed. Please try again later.", ephemeral=True)
    
    @discord.ui.button(label="🎬 Animate", style=discord.ButtonStyle.secondary)
    async def animate_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle animate button click."""
        # Allow any user to use the buttons
        
        # Check rate limiting for the current user (not original user)
        if not self.bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message("❌ You're sending requests too quickly. Please wait a moment.", ephemeral=True)
            return
        
        await interaction.response.send_message("🎬 Starting animation process...", ephemeral=True)
        
        try:
            # Progress callback for video generation
            progress_callback = await self.bot._create_unified_progress_callback(
                interaction,
                "Video Generation",
                self.generation_info.get('prompt', ''),
                f"Resolution: 720x720 | Length: 81 frames | Strength: 0.7"
            )
            
            # Generate video using ComfyUI
            async with self.bot.video_generator as gen:
                video_data, filename, video_info = await gen.generate_video(
                    prompt=self.generation_info.get('prompt', ''),
                    negative_prompt=self.generation_info.get('negative_prompt', ''),
                    workflow_name="video_wan_vace_14B_i2v",
                    width=720,
                    height=720,
                    steps=6,
                    cfg=1.0,
                    length=81,
                    strength=0.7,
                    input_image_data=self.original_image_data,
                    progress_callback=progress_callback
                )
            
            # Create success embed
            video_embed = discord.Embed(
                title="✅ Video Generated Successfully!",
                description=f"**Original Prompt:** {self.generation_info.get('prompt', 'Unknown')[:150]}{'...' if len(self.generation_info.get('prompt', '')) > 150 else ''}",
                color=discord.Color.green()
            )
            
            video_embed.add_field(
                name="Video Details",
                value=f"**Resolution:** 720x720\n**Length:** 81 frames\n**Strength:** 0.7\n**Steps:** 6",
                inline=True
            )
            
            video_embed.add_field(
                name="Requested by",
                value=interaction.user.display_name,
                inline=True
            )
            
            # Send video file
            video_filename = f"animated_{int(__import__('time').time())}.mp4"
            file = discord.File(BytesIO(video_data), filename=video_filename)
            
            await interaction.followup.send(
                embed=video_embed,
                file=file,
                ephemeral=False  # Make it visible to everyone
            )
            
            self.bot.logger.info(f"Successfully generated video for {interaction.user}")
                    
        except Exception as e:
            self.bot.logger.error(f"Animation error: {e}")
            await interaction.followup.send("❌ Animation failed. Please try again later.", ephemeral=True)

# Help command
@app_commands.command(name="help", description="Show help information about the bot")
async def help_command(interaction: discord.Interaction):
    """Show help information about the bot."""
    embed = discord.Embed(
        title="🎨 ComfyUI Discord Bot Help",
        description="Generate amazing AI images directly in Discord with multiple models and LoRA support!",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📝 Basic Usage",
        value="Use `/generate` with a prompt to create images:\n"
              "`/generate prompt:a beautiful sunset over mountains`\n"
              "`/generate prompt:cyberpunk city model:flux`\n"
              "`/generate prompt:anime character model:hidream lora:hidream_anime.safetensors`",
        inline=False
    )
    
    embed.add_field(
        name="🔧 Available Commands",
        value="• `/generate` - Generate AI images with model and LoRA selection\n"
              "• `/loras` - List available LoRAs for each model\n"
              "• `/status` - Check bot and ComfyUI status\n"
              "• `/help` - Show this help message",
        inline=False
    )
    
    embed.add_field(
        name="🤖 Available Models",
        value="• **Flux** (Default) - High-quality, fast generation\n"
              "• **HiDream** - Specialized for detailed, artistic images\n"
              "\n*Each model has its own set of compatible LoRAs*",
        inline=False
    )
    
    embed.add_field(
        name="🎯 LoRA System",
        value="• **LoRAs** add specific styles or effects to your images\n"
              "• Use `/loras` to see available options for each model\n"
              "• **Flux LoRAs:** General-purpose styles and effects\n"
              "• **HiDream LoRAs:** Must contain 'hidream' in filename\n"
              "• **Strength:** 0.0-2.0 (default: 1.0) - higher = stronger effect",
        inline=False
    )
    
    embed.add_field(
        name="⚙️ Parameters",
        value="• **prompt** - What you want to generate (required)\n"
              "• **model** - Choose Flux or HiDream (default: Flux)\n"
              "• **lora** - Select a LoRA effect (optional)\n"
              "• **lora_strength** - LoRA intensity 0.0-2.0 (default: 1.0)\n"
              "• **negative_prompt** - What to avoid in the image\n"
              "• **width/height** - Image dimensions (256-2048)\n"
              "• **steps** - Quality vs speed (1-150, auto-defaults per model)\n"
              "• **cfg** - How closely to follow prompt (1.0-30.0)\n"
              "• **batch_size** - Number of images (1-4)\n"
              "• **seed** - For reproducible results",
        inline=False
    )
    
    embed.add_field(
        name="🎬 Post-Generation Actions",
        value="After generating an image, use the action buttons:\n"
              "• **🔍 Upscale** - Enhance image resolution (2x upscaling)\n"
              "• **🎬 Animate** - Convert image to MP4 video (720x720, 81 frames)\n"
              "*(Anyone can use these buttons on any generation)*",
        inline=False
    )
    
    embed.add_field(
        name="💡 Pro Tips",
        value="• Use `/loras` to find available LoRAs for your chosen model\n"
              "• Start with default settings and adjust gradually\n"
              "• **Flux:** Great for photorealistic and general images\n"
              "• **HiDream:** Excellent for artistic and stylized images\n"
              "• Higher steps = better quality but slower generation\n"
              "• CFG 5-8 works well for most prompts\n"
              "• Experiment with LoRA strengths (0.5-1.5 range usually works best)",
        inline=False
    )
    
    embed.add_field(
        name="🔧 Example Commands",
        value="`/generate prompt:cyberpunk city at night model:flux`\n"
              "`/generate prompt:anime girl model:hidream lora:hidream_anime.safetensors lora_strength:0.8`\n"
              "`/generate prompt:fantasy landscape width:1536 height:1024 steps:50`\n"
              "`/loras model:flux` - Show Flux LoRAs\n"
              "`/status` - Check if ComfyUI is online",
        inline=False
    )
    
    embed.set_footer(text="Powered by ComfyUI | Phase 4: Advanced Model & LoRA Support | Made with ❤️")
    
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

# Command to list available LoRAs
@app_commands.command(name="loras", description="List available LoRAs for each model")
@app_commands.describe(
    model="Filter LoRAs by model type (optional)"
)
@app_commands.choices(
    model=[
        app_commands.Choice(name="All Models", value="all"),
        app_commands.Choice(name="Flux", value="flux"),
        app_commands.Choice(name="HiDream", value="hidream")
    ]
)
async def loras_command(interaction: discord.Interaction, model: str = "all"):
    """List available LoRAs for each model."""
    bot: ComfyUIBot = interaction.client
    
    await interaction.response.defer()
    
    try:
        # Fetch LoRAs from ComfyUI
        async with bot.image_generator as gen:
            all_loras = await gen.get_available_loras()
        
        if not all_loras:
            embed = discord.Embed(
                title="📋 Available LoRAs",
                description="❌ No LoRAs found. Make sure ComfyUI is running and has LoRAs installed.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Filter LoRAs by model if specified
        if model != "all":
            filtered_loras = bot.image_generator.filter_loras_by_model(all_loras, model)
        else:
            filtered_loras = all_loras
        
        # Create embed
        embed = discord.Embed(
            title="📋 Available LoRAs",
            description=f"Found {len(filtered_loras)} LoRA{'s' if len(filtered_loras) != 1 else ''}" + 
                       (f" for {model.title()}" if model != "all" else ""),
            color=discord.Color.blue()
        )
        
        if model == "all":
            # Group by model type
            flux_loras = [lora for lora in filtered_loras if lora['type'] == 'flux']
            hidream_loras = [lora for lora in filtered_loras if lora['type'] == 'hidream']
            
            if flux_loras:
                flux_list = "\n".join([f"• `{lora['filename']}`" for lora in flux_loras[:10]])
                if len(flux_loras) > 10:
                    flux_list += f"\n... and {len(flux_loras) - 10} more"
                embed.add_field(
                    name=f"🚀 Flux LoRAs ({len(flux_loras)})",
                    value=flux_list,
                    inline=False
                )
            
            if hidream_loras:
                hidream_list = "\n".join([f"• `{lora['filename']}`" for lora in hidream_loras[:10]])
                if len(hidream_loras) > 10:
                    hidream_list += f"\n... and {len(hidream_loras) - 10} more"
                embed.add_field(
                    name=f"🎨 HiDream LoRAs ({len(hidream_loras)})",
                    value=hidream_list,
                    inline=False
                )
        else:
            # Show all LoRAs for the specific model
            lora_list = "\n".join([f"• `{lora['filename']}`" for lora in filtered_loras[:20]])
            if len(filtered_loras) > 20:
                lora_list += f"\n... and {len(filtered_loras) - 20} more"
            
            embed.add_field(
                name=f"LoRAs for {model.title()}",
                value=lora_list if lora_list else "No LoRAs found for this model.",
                inline=False
            )
        
        embed.add_field(
            name="💡 Usage Tips",
            value="• Copy the exact filename (with `.safetensors`) to use in `/generate`\n"
                  "• LoRA strength can be adjusted from 0.0 to 2.0 (default: 1.0)\n"
                  "• Use `lora:none` or leave empty to generate without LoRA",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        bot.logger.error(f"Error fetching LoRAs: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Failed to fetch LoRAs from ComfyUI. Please try again later.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)

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
    
    # Explicitly disable debug logging for all modules
    logging.getLogger('image_gen').setLevel(logging.INFO)
    logging.getLogger('video_gen').setLevel(logging.INFO)
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    
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
        bot.tree.add_command(loras_command)
        
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