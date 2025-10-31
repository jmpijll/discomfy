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
from video_ui import VideoParameterSettingsButton, GenerateVideoButton

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
            await self.image_generator.initialize()
            
            # Initialize video generator (shares session with image generator)
            self.video_generator = VideoGenerator()
            self.video_generator.set_image_generator(self.image_generator)
            await self.video_generator.initialize()
            
            # Test ComfyUI connection (no context manager needed)
            if not await self.image_generator.test_connection():
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
    
    async def close(self) -> None:
        """Clean shutdown of the bot."""
        self.logger.info("🛑 Bot shutdown initiated...")
        
        # Shutdown generators
        if self.image_generator:
            await self.image_generator.shutdown()
        
        if self.video_generator:
            await self.video_generator.shutdown()
        
        # Call parent close
        await super().close()
        
        self.logger.info("✅ Bot shutdown complete")
    
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

@app_commands.command(name="generate", description="Generate images or videos using ComfyUI with interactive setup")
@app_commands.describe(
    prompt="What you want to generate",
    image="Upload an image for video generation (optional - if provided, generates video instead of image)"
)
async def generate_command(
    interaction: discord.Interaction,
    prompt: str,
    image: Optional[discord.Attachment] = None
):
    """Generate images or videos with interactive parameter selection."""
    bot: ComfyUIBot = interaction.client
    try:
        # Check rate limiting first
        if not bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message("❌ You're making requests too quickly. Please wait a moment.", ephemeral=True)
            return
        
        # Validate prompt length
        if len(prompt) > bot.config.security.max_prompt_length:
            await interaction.response.send_message(f"❌ Prompt too long! Maximum {bot.config.security.max_prompt_length} characters.", ephemeral=True)
            return
        
        # Determine if this is video generation (image provided) or image generation
        if image:
            # Video generation mode
            if not image.content_type or not image.content_type.startswith('image/'):
                await interaction.response.send_message("❌ Please upload a valid image file.", ephemeral=True)
                return
            
            if image.size > bot.config.discord.max_file_size_mb * 1024 * 1024:
                await interaction.response.send_message(f"❌ Image too large! Maximum {bot.config.discord.max_file_size_mb}MB.", ephemeral=True)
                return
            
            # Download image data
            image_data = await image.read()
            
            # Create video setup view
            setup_view = CompleteSetupView(bot, prompt, interaction.user.id, video_mode=True, image_data=image_data)
            
            # Create setup embed for video
            setup_embed = discord.Embed(
                title="🎬 Video Generation Setup",
                description=f"**Prompt:** {prompt[:150]}{'...' if len(prompt) > 150 else ''}",
                color=discord.Color.purple()
            )
            
            setup_embed.add_field(
                name="Input Image",
                value=f"**File:** {image.filename}\n**Size:** {image.size / 1024:.1f} KB",
                inline=True
            )
            
            setup_embed.add_field(
                name="Default Settings",
                value=f"**Frames:** 81 (2.5s video)\n**Steps:** 6\n**Strength:** 0.7",
                inline=True
            )
            
            setup_embed.add_field(
                name="Next Steps",
                value="📹 Configure video settings below\n🎬 Generate your video\n⏱️ Estimated time: 5-15 minutes",
                inline=False
            )
            
            await interaction.response.send_message(embed=setup_embed, view=setup_view)
            
        else:
            # Image generation mode - show model selection
            setup_view = CompleteSetupView(bot, prompt, interaction.user.id)
            
            # Create setup embed
            setup_embed = discord.Embed(
                title="🎨 Image Generation Setup",
                description=f"**Prompt:** {prompt[:150]}{'...' if len(prompt) > 150 else ''}",
                color=discord.Color.blue()
            )
            
            setup_embed.add_field(
                name="Default Settings",
                value=f"**Model:** Flux (Fast)\n**Size:** 1024x1024\n**Steps:** 30\n**Batch:** 1",
                inline=True
            )
            
            setup_embed.add_field(
                name="Next Steps",
                value="🔧 Configure settings below\n🎨 Generate your images\n⏱️ Estimated time: 30-60 seconds",
                inline=True
            )
            
            # Initialize default LoRAs for the flux model
            await setup_view.initialize_default_loras()
            
            await interaction.response.send_message(embed=setup_embed, view=setup_view)
    
    except Exception as e:
        bot.logger.error(f"Error in generate command: {e}")
        try:
            await interaction.response.send_message("❌ An error occurred. Please try again.", ephemeral=True)
        except:
            pass

@app_commands.command(name="editflux", description="Edit an image using Flux Kontext AI with natural language prompts")
@app_commands.describe(
    image="Upload the image you want to edit",
    prompt="Describe what you want to change in the image",
    steps="Number of sampling steps (10-50, default: 20)"
)
async def editflux_command(
    interaction: discord.Interaction,
    image: discord.Attachment,
    prompt: str,
    steps: Optional[int] = 20
):
    """Edit an uploaded image using Flux Kontext with natural language prompts."""
    bot: ComfyUIBot = interaction.client
    try:
        # Check rate limiting first
        if not bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message("❌ You're making requests too quickly. Please wait a moment.", ephemeral=True)
            return
        
        # Validate image
        if not image.content_type or not image.content_type.startswith('image/'):
            await interaction.response.send_message("❌ Please upload a valid image file.", ephemeral=True)
            return
        
        if image.size > bot.config.discord.max_file_size_mb * 1024 * 1024:
            await interaction.response.send_message(f"❌ Image too large! Maximum {bot.config.discord.max_file_size_mb}MB.", ephemeral=True)
            return
        
        # Validate prompt
        if not prompt.strip():
            await interaction.response.send_message("❌ Edit prompt cannot be empty!", ephemeral=True)
            return
        
        if len(prompt) > bot.config.security.max_prompt_length:
            await interaction.response.send_message(f"❌ Prompt too long! Maximum {bot.config.security.max_prompt_length} characters.", ephemeral=True)
            return
        
        # Validate steps
        if steps is not None and not (10 <= steps <= 50):
            await interaction.response.send_message("❌ Steps must be between 10 and 50!", ephemeral=True)
            return
        
        # Use default if steps not provided
        if steps is None:
            steps = 20
        
        # Download image data
        image_data = await image.read()
        
        # Send initial response
        initial_embed = discord.Embed(
            title="✏️ Starting Image Edit - Flux Kontext",
            description=f"**Edit Prompt:** {prompt[:150]}{'...' if len(prompt) > 150 else ''}",
            color=discord.Color.orange()
        )
        
        initial_embed.add_field(
            name="Input Image",
            value=f"**File:** {image.filename}\n**Size:** {image.size / 1024:.1f} KB",
            inline=True
        )
        
        initial_embed.add_field(
            name="Settings",
            value=f"**Model:** Flux Kontext\n**Steps:** {steps}\n**CFG:** 2.5\n**Size:** 1024x1024",
            inline=True
        )
        
        initial_embed.add_field(
            name="Processing",
            value="🔄 Uploading image and starting edit...\n⏱️ Estimated time: 1-3 minutes",
            inline=False
        )
        
        await interaction.response.send_message(embed=initial_embed)
        
        # Create progress callback
        progress_callback = await bot._create_unified_progress_callback(
            interaction,
            "Image Editing",
            prompt,
            f"Method: Flux Kontext | Steps: {steps} | CFG: 2.5 | Size: 1024x1024"
        )
        
        # Perform the edit using Flux workflow
        edited_data, edit_info = await bot.image_generator.generate_edit(
            input_image_data=image_data,
            edit_prompt=prompt,
            width=1024,
            height=1024,
            steps=steps,
            cfg=2.5,
            workflow_type="flux",
            progress_callback=progress_callback
        )
        
        # Send final completion status
        try:
            from image_gen import ProgressInfo
            final_progress = ProgressInfo()
            final_progress.mark_completed()
            await progress_callback(final_progress)
            bot.logger.info("✅ Successfully sent completion status to Discord for Image Editing")
        except Exception as progress_error:
            bot.logger.warning(f"Failed to send final edit progress: {progress_error}")
        
        # Save edited image
        from image_gen import save_output_image, get_unique_filename
        filename = get_unique_filename(f"edited_{interaction.user.id}")
        save_output_image(edited_data, filename)
        
        # Create success embed
        success_embed = discord.Embed(
            title="✅ Image Edited Successfully!",
            description=f"Your image has been edited using **Flux Kontext**",
            color=discord.Color.green()
        )
        
        success_embed.add_field(
            name="Edit Details",
            value=f"**Edit Prompt:** {prompt[:200]}{'...' if len(prompt) > 200 else ''}\n**Steps:** {steps}\n**CFG:** 2.5",
            inline=False
        )
        
        success_embed.add_field(
            name="Original Image",
            value=f"**File:** {image.filename}\n**Size:** {image.size / 1024:.1f} KB",
            inline=True
        )
        
        success_embed.add_field(
            name="Output",
            value=f"**Size:** 1024x1024\n**Model:** Flux Kontext\n**Format:** PNG",
            inline=True
        )
        
        success_embed.set_footer(text=f"Edited by {interaction.user.display_name}")
        
        # Create view for the edited image (allows further editing, upscaling, etc.)
        edited_view = IndividualImageView(
            bot=bot,
            image_data=edited_data,
            generation_info=edit_info,
            image_index=0  # Standalone edited image
        )
        
        # Send the edited image
        from io import BytesIO
        file = discord.File(BytesIO(edited_data), filename=filename)
        await interaction.followup.send(
            embed=success_embed,
            file=file,
            view=edited_view
        )
        
        bot.logger.info(f"Successfully processed /editflux command for {interaction.user}")
        
    except Exception as e:
        bot.logger.error(f"Error in editflux command: {e}")
        try:
            error_embed = discord.Embed(
                title="❌ Image Editing Failed",
                description=f"Failed to edit image: {str(e)[:200]}{'...' if len(str(e)) > 200 else ''}",
                color=discord.Color.red()
            )
            
            if interaction.response.is_done():
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
        except:
            pass

@app_commands.command(name="editqwen", description="Edit images using Qwen AI with natural language prompts (1-3 images)")
@app_commands.describe(
    image="Upload the primary image you want to edit (required)",
    prompt="Describe what you want to change in the image",
    image2="Upload a second image for multi-image editing (optional)",
    image3="Upload a third image for multi-image editing (optional)",
    steps="Number of sampling steps (4-20, default: 8)"
)
async def editqwen_command(
    interaction: discord.Interaction,
    image: discord.Attachment,
    prompt: str,
    image2: Optional[discord.Attachment] = None,
    image3: Optional[discord.Attachment] = None,
    steps: Optional[int] = 8
):
    """Edit one or more uploaded images using Qwen Image Edit with natural language prompts."""
    bot: ComfyUIBot = interaction.client
    try:
        # Check rate limiting first
        if not bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message("❌ You're making requests too quickly. Please wait a moment.", ephemeral=True)
            return
        
        # Validate primary image
        if not image.content_type or not image.content_type.startswith('image/'):
            await interaction.response.send_message("❌ Please upload a valid image file.", ephemeral=True)
            return
        
        if image.size > bot.config.discord.max_file_size_mb * 1024 * 1024:
            await interaction.response.send_message(f"❌ Image too large! Maximum {bot.config.discord.max_file_size_mb}MB.", ephemeral=True)
            return
        
        # Validate additional images if provided
        additional_images = []
        if image2:
            if not image2.content_type or not image2.content_type.startswith('image/'):
                await interaction.response.send_message("❌ Image 2 must be a valid image file.", ephemeral=True)
                return
            if image2.size > bot.config.discord.max_file_size_mb * 1024 * 1024:
                await interaction.response.send_message(f"❌ Image 2 too large! Maximum {bot.config.discord.max_file_size_mb}MB.", ephemeral=True)
                return
            additional_images.append(image2)
        
        if image3:
            if not image2:
                await interaction.response.send_message("❌ Cannot provide image3 without image2!", ephemeral=True)
                return
            if not image3.content_type or not image3.content_type.startswith('image/'):
                await interaction.response.send_message("❌ Image 3 must be a valid image file.", ephemeral=True)
                return
            if image3.size > bot.config.discord.max_file_size_mb * 1024 * 1024:
                await interaction.response.send_message(f"❌ Image 3 too large! Maximum {bot.config.discord.max_file_size_mb}MB.", ephemeral=True)
                return
            additional_images.append(image3)
        
        # Validate prompt
        if not prompt.strip():
            await interaction.response.send_message("❌ Edit prompt cannot be empty!", ephemeral=True)
            return
        
        if len(prompt) > bot.config.security.max_prompt_length:
            await interaction.response.send_message(f"❌ Prompt too long! Maximum {bot.config.security.max_prompt_length} characters.", ephemeral=True)
            return
        
        # Validate steps
        if steps is not None and not (4 <= steps <= 20):
            await interaction.response.send_message("❌ Steps must be between 4 and 20 for Qwen!", ephemeral=True)
            return
        
        # Use default if steps not provided
        if steps is None:
            steps = 8
        
        # Download image data
        image_data = await image.read()
        additional_image_data = []
        for img in additional_images:
            data = await img.read()
            additional_image_data.append(data)
        
        total_images = 1 + len(additional_images)
        
        # Send initial response
        initial_embed = discord.Embed(
            title=f"✏️ Starting Multi-Image Edit - Qwen ({total_images} images)",
            description=f"**Edit Prompt:** {prompt[:150]}{'...' if len(prompt) > 150 else ''}",
            color=discord.Color.purple()
        )
        
        input_info = f"**Primary:** {image.filename} ({image.size / 1024:.1f} KB)"
        if image2:
            input_info += f"\n**Image 2:** {image2.filename} ({image2.size / 1024:.1f} KB)"
        if image3:
            input_info += f"\n**Image 3:** {image3.filename} ({image3.size / 1024:.1f} KB)"
        
        initial_embed.add_field(
            name="Input Images",
            value=input_info,
            inline=True
        )
        
        initial_embed.add_field(
            name="Settings",
            value=f"**Model:** Qwen 2.5 VL\n**Steps:** {steps}\n**CFG:** 1.0\n**Speed:** Very Fast",
            inline=True
        )
        
        initial_embed.add_field(
            name="Processing",
            value=f"🔄 Uploading {total_images} image(s) and starting edit...\n⏱️ Estimated time: 30-60 seconds",
            inline=False
        )
        
        await interaction.response.send_message(embed=initial_embed)
        
        # Create progress callback
        progress_callback = await bot._create_unified_progress_callback(
            interaction,
            "Image Editing",
            prompt,
            f"Method: Qwen 2.5 VL ({total_images} images) | Steps: {steps} | CFG: 1.0"
        )
        
        # Perform the edit using Qwen workflow
        edited_data, edit_info = await bot.image_generator.generate_edit(
            input_image_data=image_data,
            edit_prompt=prompt,
            width=1024,
            height=1024,
            steps=steps,
            cfg=1.0,
            workflow_type="qwen",
            progress_callback=progress_callback,
            additional_images=additional_image_data if additional_image_data else None
        )
        
        # Send final completion status
        try:
            from image_gen import ProgressInfo
            final_progress = ProgressInfo()
            final_progress.mark_completed()
            await progress_callback(final_progress)
            bot.logger.info("✅ Successfully sent completion status to Discord for Qwen Image Editing")
        except Exception as progress_error:
            bot.logger.warning(f"Failed to send final edit progress: {progress_error}")
        
        # Save edited image
        from image_gen import save_output_image, get_unique_filename
        filename = get_unique_filename(f"qwen_edited_{interaction.user.id}")
        save_output_image(edited_data, filename)
        
        # Create success embed
        success_embed = discord.Embed(
            title="✅ Image Edited Successfully!",
            description=f"Your image has been edited using **Qwen 2.5 VL**",
            color=discord.Color.green()
        )
        
        success_embed.add_field(
            name="Edit Details",
            value=f"**Edit Prompt:** {prompt[:200]}{'...' if len(prompt) > 200 else ''}\n**Steps:** {steps}\n**CFG:** 1.0",
            inline=False
        )
        
        success_embed.add_field(
            name="Original Image",
            value=f"**File:** {image.filename}\n**Size:** {image.size / 1024:.1f} KB",
            inline=True
        )
        
        success_embed.add_field(
            name="Output",
            value=f"**Model:** Qwen 2.5 VL\n**Speed:** Very Fast\n**Format:** PNG",
            inline=True
        )
        
        success_embed.set_footer(text=f"Edited by {interaction.user.display_name}")
        
        # Create view for the edited image (allows further editing, upscaling, etc.)
        edited_view = IndividualImageView(
            bot=bot,
            image_data=edited_data,
            generation_info=edit_info,
            image_index=0  # Standalone edited image
        )
        
        # Send the edited image
        from io import BytesIO
        file = discord.File(BytesIO(edited_data), filename=filename)
        await interaction.followup.send(
            embed=success_embed,
            file=file,
            view=edited_view
        )
        
        bot.logger.info(f"Successfully processed /editqwen command for {interaction.user}")
        
    except Exception as e:
        bot.logger.error(f"Error in editqwen command: {e}")
        try:
            error_embed = discord.Embed(
                title="❌ Image Editing Failed",
                description=f"Failed to edit image: {str(e)[:200]}{'...' if len(str(e)) > 200 else ''}",
                color=discord.Color.red()
            )
            
            if interaction.response.is_done():
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
        except:
            pass

# Complete interactive setup view with all parameters
class CompleteSetupView(discord.ui.View):
    """Complete interactive setup view for all generation parameters."""
    
    def __init__(self, bot: ComfyUIBot, prompt: str, user_id: int, video_mode: bool = False, image_data: Optional[bytes] = None):
        super().__init__(timeout=300)  # 5-minute timeout for setup
        self.bot = bot
        self.prompt = prompt
        self.user_id = user_id
        self.video_mode = video_mode
        self.image_data = image_data
        
        if video_mode:
            # Video generation parameters
            self.frames = 121  # Default frame count
            self.strength = 0.7  # Default animation strength
            self.steps = 4  # Default sampling steps for video
            
            # Add video-specific controls
            self.add_item(VideoParameterSettingsButton())
            self.add_item(GenerateVideoButton())
        else:
            # Image generation parameters - default to flux
            self.model = "flux"  # Set default model to flux
            self.selected_lora = None
            self.lora_strength = 1.0
            self.negative_prompt = ""
            self.loras = []  # Will be populated during async initialization
            
            # Default parameters for flux model
            self.width = 1024
            self.height = 1024
            self.steps = 30
            self.cfg = 5.0
            self.batch_size = 1
            self.seed = None
            
            # Add image generation controls
            self.add_item(ModelSelectMenu(self.model))
            # LoRA selector will be added during async initialization if LoRAs are available
            self.add_item(ParameterSettingsButton())
            self.add_item(GenerateNowButton())
        
        # Track setup message for cleanup
        self.setup_message = None
    
    async def initialize_default_loras(self):
        """Initialize LoRAs for the default flux model."""
        if not self.video_mode and self.model == "flux":
            try:
                # Load LoRAs for flux model (same logic as in ModelSelectMenu callback)
                all_loras = await self.bot.image_generator.get_available_loras()
                self.loras = self.bot.image_generator.filter_loras_by_model(all_loras, self.model)
                    
                # Add LoRA selector if LoRAs are available
                if self.loras:
                    # Insert LoRA selector after ModelSelectMenu (index 1)
                    # Use children.insert() instead of insert_item() which doesn't exist
                    self.children.insert(1, LoRASelectMenu(self.loras, self.selected_lora))
                    
            except Exception as e:
                self.bot.logger.error(f"Failed to load default LoRAs: {e}")
                self.loras = []
    
    async def on_timeout(self):
        """Called when the view times out."""
        for item in self.children:
            item.disabled = True

# Interactive view for generation setup with LoRA selection
class GenerationSetupView(discord.ui.View):
    """Interactive view for setting up image generation with LoRA selection."""
    
    def __init__(self, bot: ComfyUIBot, generation_params: dict, loras: list, user_id: int):
        super().__init__(timeout=300)  # 5 minute timeout
        self.bot = bot
        self.generation_params = generation_params
        self.loras = loras
        self.user_id = user_id
        self.selected_lora = None
        self.lora_strength = 1.0
        
        # Add LoRA selection dropdown if LoRAs are available
        if self.loras:
            select_menu = LoRASelectMenu(self.loras)
            self.add_item(select_menu)
            self.add_item(LoRAStrengthButton())
        
        # Add generation buttons
        self.add_item(GenerateButton())
        if self.loras:
            self.add_item(GenerateWithoutLoRAButton())
    
    async def on_timeout(self):
        """Called when the view times out."""
        # Disable all items
        for item in self.children:
            item.disabled = True
    
    async def _start_generation(self, interaction: discord.Interaction, lora_name: Optional[str], lora_strength: float):
        """Start the actual image generation process."""
        try:
            # Prepare LoRA name for workflow
            lora_filename = lora_name if lora_name else None
            
            # Send progress update and clean up the setup message first
            if self.generation_params['model'] == "flux":
                model_display = "Flux"
            elif self.generation_params['model'] == "flux_krea":
                model_display = "Flux Krea ✨ NEW"
            else:
                model_display = "HiDream"
            lora_info = f" with LoRA '{lora_name}' (strength: {lora_strength})" if lora_filename else " (no LoRA)"
            
            progress_embed = discord.Embed(
                title=f"🎨 Generating Image - {model_display}",
                description=f"🎨 Creating your image with prompt: `{self.generation_params['prompt'][:100]}{'...' if len(self.generation_params['prompt']) > 100 else ''}`\n"
                           f"🤖 Model: {model_display}{lora_info}\n"
                           f"📏 Size: {self.generation_params['width']}x{self.generation_params['height']} | "
                           f"🔧 Steps: {self.generation_params['steps']} | ⚙️ CFG: {self.generation_params['cfg']}\n"
                           f"🔄 Generating {self.generation_params['batch_size']} image{'s' if self.generation_params['batch_size'] > 1 else ''}...",
                color=discord.Color.blue()
            )
            
            await interaction.edit_original_response(embed=progress_embed, view=None)
            
            # Try to delete the setup message to clean up chat
            try:
                # Find the setup message by looking for the most recent message with "Settings Updated!" or similar
                # This is a bit tricky with interaction-based responses, so we'll handle this differently
                # For now, we'll focus on the generation flow and handle cleanup later
                pass
            except Exception as cleanup_error:
                self.bot.logger.warning(f"Could not clean up setup message: {cleanup_error}")
            
            # Progress callback for updates
            settings_text = f"Model: {model_display} | Size: {self.generation_params['width']}x{self.generation_params['height']} | " + \
                           f"Steps: {self.generation_params['steps']} | CFG: {self.generation_params['cfg']} | " + \
                           f"Batch: {self.generation_params['batch_size']}"
            if lora_filename:
                settings_text += f" | LoRA: {lora_name} ({lora_strength})"
            
            progress_callback = await self.bot._create_unified_progress_callback(
                interaction,
                "Image Generation",
                self.generation_params['prompt'],
                settings_text
            )
            
            # Generate images (returns list of individual images)
            images_list, generation_info = await self.bot.image_generator.generate_image(
                prompt=self.generation_params['prompt'],
                negative_prompt=self.generation_params['negative_prompt'],
                workflow_name=self.generation_params['workflow_name'],
                width=self.generation_params['width'],
                height=self.generation_params['height'],
                steps=self.generation_params['steps'],
                cfg=self.generation_params['cfg'],
                batch_size=self.generation_params['batch_size'],
                seed=self.generation_params['seed'],
                lora_name=lora_filename,
                lora_strength=lora_strength,
                progress_callback=progress_callback
            )
            
            # Send final completion status update
            try:
                final_progress = ProgressInfo()
                final_progress.mark_completed()
                await progress_callback(final_progress)
                self.bot.logger.info("✅ Sent final completion status to Discord")
                
                # Small delay to ensure the completion message is visible
                await asyncio.sleep(1)
            except Exception as progress_error:
                self.bot.logger.warning(f"Failed to send final progress update: {progress_error}")
            
            # Send individual images with individual action buttons
            for i, image_data in enumerate(images_list):
                # Save image
                filename = get_unique_filename(f"discord_{interaction.user.id}_{i}")
                save_output_image(image_data, filename)
                
                # Create success embed for this image
                success_embed = discord.Embed(
                    title=f"✅ Image {i + 1}/{len(images_list)} Generated - {model_display}!",
                    description=f"**Prompt:** {self.generation_params['prompt'][:200]}{'...' if len(self.generation_params['prompt']) > 200 else ''}",
                    color=discord.Color.green()
                )
                
                # Add generation details
                details_text = f"**Size:** {self.generation_params['width']}x{self.generation_params['height']}\n" + \
                              f"**Steps:** {self.generation_params['steps']} | **CFG:** {self.generation_params['cfg']}\n" + \
                              f"**Seed:** {generation_info.get('seed', 'Unknown')}\n" + \
                              f"**Batch:** {i + 1} of {generation_info.get('num_images', 1)}"
                
                success_embed.add_field(
                    name="Generation Details",
                    value=details_text,
                    inline=True
                )
                
                # Add model and LoRA info
                model_info = f"**Model:** {model_display}\n"
                if lora_filename:
                    model_info += f"**LoRA:** {lora_name}\n**LoRA Strength:** {lora_strength}"
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
                
                # Create individual action buttons view for this image
                individual_view = IndividualImageView(
                    bot=self.bot,
                    image_data=image_data,
                    generation_info=generation_info,
                    image_index=i
                )
                
                # Send this individual image
                file = discord.File(BytesIO(image_data), filename=filename)
                
                try:
                    if i == 0:
                        # Edit the original response for the first image
                        await interaction.edit_original_response(
                            embed=success_embed,
                            attachments=[file],
                            view=individual_view
                        )
                        self.bot.logger.info(f"Successfully sent image {i + 1} via edit_original_response for {interaction.user}")
                    else:
                        # Send followup messages for additional images
                        await interaction.followup.send(
                            embed=success_embed,
                            file=file,
                            view=individual_view
                        )
                        self.bot.logger.info(f"Successfully sent image {i + 1} via followup for {interaction.user}")
                        
                except Exception as send_error:
                    self.bot.logger.error(f"Error sending image {i + 1}: {send_error}")
                    # Try sending as followup if edit fails
                    try:
                        await interaction.followup.send(
                            embed=success_embed,
                            file=discord.File(BytesIO(image_data), filename=filename),  # Create new file object
                            view=individual_view
                        )
                        self.bot.logger.info(f"Successfully sent image {i + 1} via fallback followup for {interaction.user}")
                    except Exception as followup_error:
                        self.bot.logger.error(f"Failed to send followup image {i + 1}: {followup_error}")
            
            self.bot.logger.info(f"Image generation process completed for {interaction.user} (ID: {interaction.user.id}) with model: {self.generation_params['model']}")
            
            # Clean up old outputs
            cleanup_old_outputs(self.bot.config.generation.output_limit)
            
        except ComfyUIAPIError as e:
            self.bot.logger.error(f"ComfyUI API error for user {interaction.user.id}: {e}")
            try:
                error_embed = discord.Embed(
                    title="❌ Generation Failed",
                    description=f"ComfyUI error: {str(e)[:200]}{'...' if len(str(e)) > 200 else ''}",
                    color=discord.Color.red()
                )
                await interaction.edit_original_response(embed=error_embed, view=None)
            except:
                # If we can't edit, try followup
                try:
                    await interaction.followup.send("❌ Generation failed. Please try again.")
                except:
                    self.bot.logger.error("Failed to send error response to user")
            
        except Exception as e:
            self.bot.logger.error(f"Unexpected error in generation: {e}")
            try:
                error_embed = discord.Embed(
                    title="❌ Unexpected Error",
                    description="An unexpected error occurred. Please try again later.",
                    color=discord.Color.red()
                )
                await interaction.edit_original_response(embed=error_embed, view=None)
            except:
                # If we can't edit, try followup
                try:
                    await interaction.followup.send("❌ An unexpected error occurred. Please try again later.", ephemeral=True)
                except:
                    self.bot.logger.error("Failed to send error followup")

class LoRASelectMenu(discord.ui.Select):
    """Select menu for choosing LoRA."""
    
    def __init__(self, loras: list, selected_lora: Optional[str] = None):
        # Ensure we have valid LoRAs and limit to 25 options (Discord limit)
        if not loras:
            # Create a dummy option since Discord requires at least one
            options = [discord.SelectOption(
                label="No LoRAs available",
                value="none",
                description="No compatible LoRAs found for this model"
            )]
            disabled = True
            placeholder = "No LoRAs available"
        else:
            display_loras = loras[:25]  # Discord limit
            options = []
            
            for lora in display_loras:
                # Ensure we have valid lora data
                filename = lora.get('filename', 'unknown.safetensors')
                display_name = lora.get('display_name', filename)
                
                # Truncate label and description to Discord limits
                label = display_name[:100] if display_name else filename[:100]
                description = f"File: {filename[:50]}{'...' if len(filename) > 50 else ''}"
                
                options.append(discord.SelectOption(
                    label=label,
                    value=filename,
                    description=description,
                    default=(selected_lora == filename)
                ))
            
            disabled = False
            
            # Set placeholder based on selection
            if selected_lora:
                # Find display name for selected LoRA
                selected_display_name = "Unknown"
                for lora in loras:
                    if lora.get('filename') == selected_lora:
                        selected_display_name = lora.get('display_name', lora.get('filename', 'Unknown'))
                        break
                placeholder = f"🎯 {selected_display_name} (Selected)"
            else:
                placeholder = "🎯 Choose a LoRA..."
        
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
            disabled=disabled
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Handle LoRA selection."""
        view = self.view
        
        # Handle both CompleteSetupView and GenerationSetupView
        if hasattr(view, 'user_id'):
            # Check authorization for CompleteSetupView
            if interaction.user.id != view.user_id:
                await interaction.response.send_message(
                    "❌ Only the person who started this generation can use these controls.",
                    ephemeral=True
                )
                return
        
        # Handle the case where no LoRAs are available
        if self.values[0] == "none":
            await interaction.response.send_message(
                "❌ No LoRAs are available for this model.",
                ephemeral=True
            )
            return
        
        view.selected_lora = self.values[0]
        
        # Find the display name for the selected LoRA
        selected_display_name = "Unknown"
        loras_list = getattr(view, 'loras', [])
        for lora in loras_list:
            if lora.get('filename') == view.selected_lora:
                selected_display_name = lora.get('display_name', lora.get('filename', 'Unknown'))
                break
        
        # For CompleteSetupView, add LoRA strength button and send clean ephemeral response
        if isinstance(view, CompleteSetupView):
            # Add LoRA strength button if not already present
            if view.selected_lora and not any(isinstance(item, LoRAStrengthButton) for item in view.children):
                # Rebuild the view with updated placeholders to show selections
                view.clear_items()
                view.add_item(ModelSelectMenu(view.model))
                view.add_item(LoRASelectMenu(view.loras, view.selected_lora))
                view.add_item(LoRAStrengthButton())
                view.add_item(ParameterSettingsButton())
                view.add_item(GenerateNowButton())
                
                # Update the original message with the new view and updated info
                try:
                    if view.model == "flux":
                        model_display = "Flux"
                    elif view.model == "flux_krea":
                        model_display = "Flux Krea ✨ NEW"
                    else:
                        model_display = "HiDream"
                    updated_embed = discord.Embed(
                        title="🎨 Image Generation Setup",
                        description=f"**Prompt:** {view.prompt[:200]}{'...' if len(view.prompt) > 200 else ''}\n\n" +
                                   f"**Model:** {model_display}\n" +
                                   f"**Size:** {view.width}x{view.height} | **Steps:** {view.steps} | **CFG:** {view.cfg}",
                        color=discord.Color.blue()
                    )
                    
                    status_text = f"✅ **Model Selected:** {model_display}\n"
                    status_text += f"📋 **LoRA Selected:** {selected_display_name} (strength: {view.lora_strength})\n"
                    status_text += f"⚙️ **Settings:** Ready (click 'Adjust Settings' to customize)\n"
                    status_text += f"🚀 **Ready to generate!**"
                    
                    updated_embed.add_field(
                        name="📊 Current Configuration",
                        value=status_text,
                        inline=False
                    )
                    
                    updated_embed.set_footer(text=f"Requested by {interaction.user.display_name}")
                    
                    await interaction.response.edit_message(embed=updated_embed, view=view)
                except:
                    # Fallback to simple ephemeral response if editing fails
                    await interaction.response.send_message(
                        f"✅ **LoRA Selected:** {selected_display_name}\n" +
                        f"💪 **Strength:** {view.lora_strength}",
                        ephemeral=True
                    )
            else:
                await interaction.response.send_message(
                    f"✅ **LoRA Selected:** {selected_display_name}\n" +
                    f"💪 **Strength:** {view.lora_strength}",
                    ephemeral=True
                )
        else:
            # Original behavior for GenerationSetupView
            await interaction.response.send_message(
                f"✅ **LoRA Selected:** {selected_display_name}\n" +
                f"📄 **Filename:** `{view.selected_lora}`\n" +
                f"💪 **Strength:** {view.lora_strength}\n\n" +
                f"Click **Adjust Strength** to change strength, or **Generate Image** to proceed!",
                ephemeral=True
            )


class LoRAStrengthButton(discord.ui.Button):
    """Button to adjust LoRA strength."""
    
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="⚙️ Adjust Strength",
            emoji="💪"
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Show modal to adjust LoRA strength."""
        view = self.view
        
        # Check authorization for both view types
        if hasattr(view, 'user_id') and interaction.user.id != view.user_id:
            await interaction.response.send_message(
                "❌ Only the person who started this generation can use these controls.",
                ephemeral=True
            )
            return
        
        modal = LoRAStrengthModal(view.lora_strength, view)
        await interaction.response.send_modal(modal)


class LoRAStrengthModal(discord.ui.Modal):
    """Modal for adjusting LoRA strength."""
    
    def __init__(self, current_strength: float, view):
        super().__init__(title="Adjust LoRA Strength")
        self.view = view
        self.strength_input = discord.ui.TextInput(
            label="LoRA Strength",
            placeholder="Enter a value between 0.0 and 2.0",
            default=str(current_strength),
            min_length=1,
            max_length=5
        )
        self.add_item(self.strength_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle strength adjustment."""
        try:
            strength = float(self.strength_input.value)
            if 0.0 <= strength <= 2.0:
                # Update the view's lora_strength
                self.view.lora_strength = strength
                
                # For CompleteSetupView, update the main embed
                if isinstance(self.view, CompleteSetupView):
                    # Rebuild the view to keep dropdowns showing current selections
                    self.view.clear_items()
                    self.view.add_item(ModelSelectMenu(self.view.model))
                    self.view.add_item(LoRASelectMenu(self.view.loras, self.view.selected_lora))
                    self.view.add_item(LoRAStrengthButton())
                    self.view.add_item(ParameterSettingsButton())
                    self.view.add_item(GenerateNowButton())
                    
                    await interaction.response.send_message(
                        f"✅ **LoRA strength updated to {strength}**",
                        ephemeral=True
                    )
                else:
                    # Original behavior for GenerationSetupView
                    await interaction.response.send_message(
                        f"✅ **LoRA strength updated to {strength}**\n" +
                        f"Click **Generate Image** to proceed with generation!",
                        ephemeral=True
                    )
            else:
                await interaction.response.send_message(
                    "❌ **Invalid strength!** Please enter a value between 0.0 and 2.0.",
                    ephemeral=True
                )
        except ValueError:
            await interaction.response.send_message(
                "❌ **Invalid input!** Please enter a valid number between 0.0 and 2.0.",
                ephemeral=True
            )


class GenerateButton(discord.ui.Button):
    """Button to start generation with selected LoRA."""
    
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.success,
            label="🎨 Generate Image",
            emoji="✨"
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Start image generation."""
        view: GenerationSetupView = self.view
        
        # Check if user is the original requester
        if interaction.user.id != view.user_id:
            await interaction.response.send_message(
                "❌ Only the person who started this generation can use these buttons.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        # Start generation with selected parameters
        await view._start_generation(interaction, view.selected_lora, view.lora_strength)


class GenerateWithoutLoRAButton(discord.ui.Button):
    """Button to start generation without LoRA."""
    
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label="Generate Without LoRA",
            emoji="🚀"
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Start image generation without LoRA."""
        view: GenerationSetupView = self.view
        
        # Check if user is the original requester
        if interaction.user.id != view.user_id:
            await interaction.response.send_message(
                "❌ Only the person who started this generation can use these buttons.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        # Start generation without LoRA
        await view._start_generation(interaction, None, 0.0)

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
            # Use the upscale workflow with image data directly
            upscaled_data, upscale_info = await self.bot.image_generator.generate_upscale(
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
    
    @discord.ui.button(label="✏️ Flux Edit", style=discord.ButtonStyle.secondary)
    async def flux_edit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle Flux edit button click."""
        # Allow any user to use the buttons
        
        # Check rate limiting for the current user (not original user)
        if not self.bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message("❌ You're sending requests too quickly. Please wait a moment.", ephemeral=True)
            return
        
        # Show Flux edit prompt modal
        modal = PostGenerationEditModal(self, interaction.user, workflow_type="flux")
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="⚡ Qwen Edit", style=discord.ButtonStyle.secondary)
    async def qwen_edit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle Qwen edit button click."""
        # Allow any user to use the buttons
        
        # Check rate limiting for the current user (not original user)
        if not self.bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message("❌ You're sending requests too quickly. Please wait a moment.", ephemeral=True)
            return
        
        # Show Qwen edit prompt modal
        modal = PostGenerationEditModal(self, interaction.user, workflow_type="qwen")
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🎬 Animate", style=discord.ButtonStyle.secondary)
    async def animate_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle animate button click."""
        # Allow any user to use the buttons
        
        # Check rate limiting for the current user (not original user)
        if not self.bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message("❌ You're sending requests too quickly. Please wait a moment.", ephemeral=True)
            return
        
        # Show animation parameter modal instead of direct generation
        modal = PostGenerationAnimationModal(self, interaction.user)
        await interaction.response.send_modal(modal)

class PostGenerationAnimationModal(discord.ui.Modal):
    """Modal for animating images from PostGenerationView."""
    
    def __init__(self, post_gen_view, user):
        super().__init__(title="🎬 Animation Settings")
        self.post_gen_view = post_gen_view
        self.user = user
        
        # Get original prompt for pre-filling
        original_prompt = post_gen_view.generation_info.get('prompt', '')
        
        # Animation prompt input (pre-filled with original)
        self.animation_prompt_input = discord.ui.TextInput(
            label="Animation Prompt",
            placeholder="Describe the animation or leave as original...",
            default=original_prompt[:500],  # Limit to modal max length
            style=discord.TextStyle.paragraph,
            max_length=500,
            required=True
        )
        self.add_item(self.animation_prompt_input)
        
        # Frame count input
        self.frames_input = discord.ui.TextInput(
            label="Frame Count (81/121/161)",
            placeholder="Default: 81",
            default="81",
            max_length=3,
            required=False
        )
        self.add_item(self.frames_input)
        
        # Animation strength input
        self.strength_input = discord.ui.TextInput(
            label="Animation Strength (0.1-1.0)",
            placeholder="Default: 0.7",
            default="0.7",
            max_length=4,
            required=False
        )
        self.add_item(self.strength_input)
        
        # Sampling steps input
        self.steps_input = discord.ui.TextInput(
            label="Sampling Steps (4-12)",
            placeholder="Default: 6",
            default="6",
            max_length=2,
            required=False
        )
        self.add_item(self.steps_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle animation parameters and start animation process."""
        try:
            # Validate animation prompt
            animation_prompt = self.animation_prompt_input.value.strip()
            if not animation_prompt:
                await interaction.response.send_message(
                    "❌ Animation prompt cannot be empty!",
                    ephemeral=True
                )
                return
            
            # Parse and validate frame count
            frames = 81  # Default
            if self.frames_input.value.strip():
                try:
                    frames = int(self.frames_input.value.strip())
                    if frames not in [81, 121, 161]:
                        await interaction.response.send_message(
                            "❌ Invalid frame count! Must be 81, 121, or 161",
                            ephemeral=True
                        )
                        return
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid frame count! Must be 81, 121, or 161",
                        ephemeral=True
                    )
                    return
            
            # Parse and validate strength
            strength = 0.7  # Default
            if self.strength_input.value.strip():
                try:
                    strength = float(self.strength_input.value.strip())
                    if not (0.1 <= strength <= 1.0):
                        await interaction.response.send_message(
                            "❌ Invalid strength! Must be between 0.1 and 1.0",
                            ephemeral=True
                        )
                        return
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid strength! Must be a number between 0.1 and 1.0",
                        ephemeral=True
                    )
                    return
            
            # Parse and validate steps
            steps = 6  # Default
            if self.steps_input.value.strip():
                try:
                    steps = int(self.steps_input.value.strip())
                    if not (4 <= steps <= 12):
                        await interaction.response.send_message(
                            "❌ Invalid steps! Must be between 4 and 12",
                            ephemeral=True
                        )
                        return
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid steps! Must be between 4 and 12",
                        ephemeral=True
                    )
                    return
            
            # Start animation process
            prompt_preview = animation_prompt[:80] + "..." if len(animation_prompt) > 80 else animation_prompt
            await interaction.response.send_message(
                f"🎬 **{interaction.user.display_name}** is animating image...\n"
                f"*Prompt: {prompt_preview} | Frames: {frames} | Strength: {strength} | Steps: {steps}*",
                ephemeral=False
            )
            
            try:
                # Progress callback for video generation
                progress_callback = await self.post_gen_view.bot._create_unified_progress_callback(
                    interaction,
                    "Video Generation",
                    animation_prompt,
                    f"Resolution: 720x720 | Frames: {frames} | Steps: {steps} | CFG: 1.0 | Strength: {strength}"
                )
                
                # Generate video using ComfyUI with custom prompt
                video_data, filename, video_info = await self.post_gen_view.bot.video_generator.generate_video(
                    prompt=animation_prompt,
                    negative_prompt=self.post_gen_view.generation_info.get('negative_prompt', ''),
                    workflow_name=None,  # Use default video workflow
                    width=720,
                    height=720,
                    steps=steps,
                    cfg=1.0,
                    length=frames,
                    strength=strength,
                    seed=None,
                    input_image_data=self.post_gen_view.original_image_data,
                    progress_callback=progress_callback
                )
                
                # Create success embed
                video_embed = discord.Embed(
                    title="✅ Video Generated Successfully!",
                    description=f"Your image has been animated into a video",
                    color=discord.Color.green()
                )
                
                video_embed.add_field(
                    name="Video Details",
                    value=f"**Format:** MP4\n**Frames:** {frames}\n**Resolution:** 720x720\n**Strength:** {strength}\n**Steps:** {steps}",
                    inline=True
                )
                
                video_embed.add_field(
                    name="Animation Prompt",
                    value=f"{animation_prompt[:150]}{'...' if len(animation_prompt) > 150 else ''}",
                    inline=False
                )
                
                video_embed.add_field(
                    name="Original Prompt",
                    value=f"{self.post_gen_view.generation_info.get('prompt', '')[:100]}{'...' if len(self.post_gen_view.generation_info.get('prompt', '')) > 100 else ''}",
                    inline=False
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
                
                self.post_gen_view.bot.logger.info(f"Successfully animated image for {interaction.user}")
                        
            except Exception as e:
                self.post_gen_view.bot.logger.error(f"Animation error: {e}")
                await interaction.followup.send("❌ Animation failed. Please try again later.", ephemeral=True)
            
        except Exception as e:
            self.post_gen_view.bot.logger.error(f"Error in animation modal submit: {e}")
            try:
                await interaction.response.send_message(
                    "❌ Error processing animation request. Please try again.",
                    ephemeral=True
                )
            except:
                await interaction.followup.send(
                    "❌ Error processing animation request. Please try again.",
                    ephemeral=True
                )

# Help command
@app_commands.command(name="help", description="Show help information about the bot")
async def help_command(interaction: discord.Interaction):
    """Show help information about the bot."""
    embed = discord.Embed(
        title="🎨 ComfyUI Discord Bot Help",
        description="Generate amazing AI images directly in Discord with interactive model and LoRA selection!",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📖 Available Commands",
        value="• `/generate` - Generate AI images or videos\n"
              "• `/edit` - Edit images using natural language prompts\n"
              "• `/help` - Show this help message\n"
              "• `/status` - Check bot and ComfyUI status\n"
              "• `/loras` - List available LoRA models",
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
        name="🎯 Interactive LoRA Selection",
        value="**New User-Friendly Interface!**\n"
              "• After using `/generate`, you'll see an **interactive dropdown menu**\n"
              "• **No more typing long filenames!** Just select from the list\n"
              "• **Flux LoRAs:** General-purpose styles and effects\n"
              "• **HiDream LoRAs:** Must contain 'hidream' in filename\n"
              "• **Adjust Strength:** Use the button to set LoRA intensity (0.0-2.0)\n"
              "• **Generate Options:** With LoRA or without LoRA - your choice!",
        inline=False
    )
    
    embed.add_field(
        name="⚙️ Command Parameters",
        value="• **prompt** - What you want to generate (required)\n"
              "• **model** - Choose Flux or HiDream (default: Flux)\n"
              "• **negative_prompt** - What to avoid in the image\n"
              "• **width/height** - Image dimensions (256-2048)\n"
              "• **steps** - Quality vs speed (auto-defaults per model)\n"
              "• **cfg** - How closely to follow prompt (1.0-30.0)\n"
              "• **batch_size** - Number of images (1-4)\n"
              "• **seed** - For reproducible results",
        inline=False
    )
    
    embed.add_field(
        name="🎬 Post-Generation Actions",
        value="After generating an image, use the action buttons:\n"
              "• **🔍 Upscale** - Interactive upscaling (2x/4x/8x, custom denoise & steps)\n"
              "• **✏️ Edit** - Edit the image using Flux Kontext with custom prompts\n"
              "• **🎬 Animate** - Convert to MP4 video with **custom animation prompts**\n"
              "  ⭐ *New: Animation prompts are pre-filled but fully customizable!*\n"
              "*(Anyone can use these buttons on any generation)*",
        inline=False
    )
    
    embed.add_field(
        name="💡 Pro Tips",
        value="• Use `/loras` to browse available LoRAs before generating\n"
              "• Start with `/generate prompt:your idea` and customize from there\n"
              "• **Flux:** Great for photorealistic and general images\n"
              "• **HiDream:** Excellent for artistic and stylized images\n"
              "• The interactive interface shows you exactly what's available\n"
              "• Try different LoRA strengths - usually 0.5-1.5 works best\n"
              "• Higher steps = better quality but slower generation",
        inline=False
    )
    
    embed.add_field(
        name="🔧 Workflow Examples",
        value="**Step 1:** `/generate prompt:cyberpunk city at night model:flux`\n"
              "**Step 2:** Select a LoRA from the dropdown (or skip)\n"
              "**Step 3:** Adjust strength if needed\n"
              "**Step 4:** Click 'Generate Image'\n"
              "**Step 5:** Use 🔍 Upscale or 🎬 Animate buttons on the result!\n\n"
              "**Quick commands:**\n"
              "`/loras model:flux` - Browse Flux LoRAs\n"
              "`/status` - Check if everything is running",
        inline=False
    )
    
    embed.add_field(
        name="🎨 Image Generation",
        value="Use `/generate` with a text prompt to create images:\n"
              "• Choose between **Flux** (fast) or **HiDream** (detailed)\n"
              "• Customize size, steps, CFG, batch size, and LoRA\n"
              "• Generate multiple images at once\n"
              "• Interactive parameter selection before generation",
        inline=False
    )
    
    embed.add_field(
        name="✏️ Image Editing",
        value="Use `/edit` to modify existing images:\n"
              "• Upload any image file (PNG, JPG, WebP)\n"
              "• Describe your desired changes in natural language\n"
              "• Powered by **Flux Kontext** for precise edits\n"
              "• Example: `/edit image:photo.jpg prompt:add sunglasses`",
        inline=False
    )
    
    embed.add_field(
        name="🎬 Video Generation & Animation",
        value="**Two ways to create videos:**\n"
              "• **Direct**: `/generate` with uploaded image for video generation\n"
              "• **Post-Generation**: Use 🎬 Animate button on any generated image\n\n"
              "**New Animation Features:**\n"
              "• **Custom Animation Prompts** - Modify how your image animates\n"
              "• **Interactive Settings** - Choose frames (81/121/161), strength, steps\n"
              "• **Pre-filled Prompts** - Original prompt auto-filled, edit as needed\n"
              "• **Example**: Change 'mountain landscape' → 'mountain landscape with flowing clouds'",
        inline=False
    )
    
    embed.set_footer(text="Powered by ComfyUI | Phase 4: Interactive LoRA Selection | Made with ❤️")
    
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
        comfyui_online = await bot.image_generator.test_connection()
        
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
        app_commands.Choice(name="Flux Krea ✨ NEW", value="flux_krea"),
        app_commands.Choice(name="HiDream", value="hidream")
    ]
)
async def loras_command(interaction: discord.Interaction, model: str = "all"):
    """List available LoRAs for each model."""
    bot: ComfyUIBot = interaction.client
    
    await interaction.response.defer()
    
    try:
        # Fetch LoRAs from ComfyUI
        all_loras = await bot.image_generator.get_available_loras()
        
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
                    name=f"🚀 Flux & Flux Krea LoRAs ({len(flux_loras)})",
                    value=flux_list + "\n\n*Compatible with both Flux and Flux Krea models*",
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

class ModelSelectMenu(discord.ui.Select):
    """Select menu for choosing AI model."""
    
    def __init__(self, selected_model: Optional[str] = None):
        # Default to flux if no model selected yet
        if selected_model is None:
            selected_model = "flux"
        
        options = [
            discord.SelectOption(
                label="Flux (Default)",
                value="flux",
                description="High-quality, fast generation - 1024x1024, 30 steps",
                emoji="🚀",
                default=(selected_model == "flux")
            ),
            discord.SelectOption(
                label="Flux Krea ✨ NEW",
                value="flux_krea",
                description="Enhanced Flux Krea model - creative, high-quality generation",
                emoji="✨",
                default=(selected_model == "flux_krea")
            ),
            discord.SelectOption(
                label="HiDream",
                value="hidream", 
                description="Detailed, artistic images - 1216x1216, 50 steps",
                emoji="🎨",
                default=(selected_model == "hidream")
            )
        ]
        
        # Set placeholder to show current selection or default
        current_label = "Flux (Default)"  # Default
        for option in options:
            if option.default:
                current_label = option.label
                break
        
        super().__init__(
            placeholder=f"🤖 {current_label}",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Handle model selection."""
        view: CompleteSetupView = self.view
        
        # Check if user is authorized
        if interaction.user.id != view.user_id:
            await interaction.response.send_message(
                "❌ Only the person who started this generation can use these controls.",
                ephemeral=True
            )
            return
        
        selected_model = self.values[0]
        
        # Respond immediately to avoid timeout
        await interaction.response.defer()
        
        try:
            # Update model and apply defaults
            view.model = selected_model
            
            # Apply model-specific defaults
            if selected_model == "flux":
                view.width = 1024
                view.height = 1024
                view.steps = 30
                view.cfg = 5.0
                view.negative_prompt = ""
            elif selected_model == "flux_krea":
                view.width = 1024
                view.height = 1024
                view.steps = 30
                view.cfg = 5.0
                view.negative_prompt = ""
            elif selected_model == "hidream":
                view.width = 1216
                view.height = 1216
                view.steps = 50
                view.cfg = 7.0
                view.negative_prompt = "bad ugly jpeg artifacts"
            
            # Fetch LoRAs for this model
            try:
                all_loras = await view.bot.image_generator.get_available_loras()
                view.loras = view.bot.image_generator.filter_loras_by_model(all_loras, selected_model)
            except Exception as e:
                view.bot.logger.error(f"Failed to fetch LoRAs: {e}")
                view.loras = []
            
            # Clear existing items and rebuild view
            view.clear_items()
            view.add_item(ModelSelectMenu(selected_model))
            
            # Add LoRA selection if available
            if view.loras:
                view.add_item(LoRASelectMenu(view.loras, view.selected_lora))
                if view.selected_lora:
                    view.add_item(LoRAStrengthButton())
            
            view.add_item(ParameterSettingsButton())
            view.add_item(GenerateNowButton())
            
            # Update the embed
            if selected_model == "flux":
                model_display = "Flux"
            elif selected_model == "flux_krea":
                model_display = "Flux Krea ✨ NEW"
            else:
                model_display = "HiDream"
            updated_embed = discord.Embed(
                title="🎨 Image Generation Setup",
                description=f"**Prompt:** {view.prompt[:200]}{'...' if len(view.prompt) > 200 else ''}\n\n" +
                           f"**Model:** {model_display}\n" +
                           f"**Size:** {view.width}x{view.height} | **Steps:** {view.steps} | **CFG:** {view.cfg}",
                color=discord.Color.blue()
            )
            
            status_text = f"✅ **Model Selected:** {model_display}\n"
            if view.loras:
                status_text += f"📋 **Available LoRAs:** {len(view.loras)}\n"
            else:
                status_text += f"📋 **LoRAs:** None available\n"
            status_text += f"⚙️ **Settings:** Ready (click 'Adjust Settings' to customize)\n"
            status_text += f"🚀 **Ready to generate!**"
            
            updated_embed.add_field(
                name="📊 Current Configuration",
                value=status_text,
                inline=False
            )
            
            updated_embed.set_footer(text=f"Requested by {interaction.user.display_name}")
            
            await interaction.edit_original_response(embed=updated_embed, view=view)
            
        except Exception as e:
            view.bot.logger.error(f"Error in model selection: {e}")
            try:
                await interaction.followup.send(
                    f"❌ Error updating model: {str(e)[:100]}...",
                    ephemeral=True
                )
            except:
                pass


class ParameterSettingsButton(discord.ui.Button):
    """Button to open parameter settings modal."""
    
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="⚙️ Adjust Settings",
            emoji="🔧"
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Show parameter settings modal."""
        view: CompleteSetupView = self.view
        
        # Check if user is authorized
        if interaction.user.id != view.user_id:
            await interaction.response.send_message(
                "❌ Only the person who started this generation can use these controls.",
                ephemeral=True
            )
            return
        
        modal = ParameterSettingsModal(view)
        await interaction.response.send_modal(modal)


class ParameterSettingsModal(discord.ui.Modal):
    """Modal for adjusting all generation parameters."""
    
    def __init__(self, view: 'CompleteSetupView'):
        super().__init__(title="🔧 Generation Settings")
        self.view = view
        
        # Add input fields for all parameters
        self.negative_prompt_input = discord.ui.TextInput(
            label="Negative Prompt",
            placeholder="Things to avoid in the image...",
            default=view.negative_prompt,
            required=False,
            max_length=500
        )
        
        self.dimensions_input = discord.ui.TextInput(
            label="Dimensions (WIDTHxHEIGHT)",
            placeholder="1024x1024",
            default=f"{view.width}x{view.height}",
            required=False,
            max_length=20
        )
        
        self.steps_input = discord.ui.TextInput(
            label="Steps (1-150)",
            placeholder="30",
            default=str(view.steps),
            required=False,
            max_length=3
        )
        
        self.cfg_input = discord.ui.TextInput(
            label="CFG Scale (1.0-30.0)",
            placeholder="5.0",
            default=str(view.cfg),
            required=False,
            max_length=5
        )
        
        self.batch_seed_input = discord.ui.TextInput(
            label="Batch Size | Seed (1-4 | number or empty)",
            placeholder="1 | (empty for random)",
            default=f"{view.batch_size} | {view.seed if view.seed else ''}",
            required=False,
            max_length=20
        )
        
        self.add_item(self.negative_prompt_input)
        self.add_item(self.dimensions_input)
        self.add_item(self.steps_input)
        self.add_item(self.cfg_input)
        self.add_item(self.batch_seed_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle parameter updates."""
        try:
            # Parse and validate dimensions
            if self.dimensions_input.value.strip():
                try:
                    dims = self.dimensions_input.value.strip().lower().replace('x', 'x').split('x')
                    if len(dims) == 2:
                        width = int(dims[0])
                        height = int(dims[1])
                        if 256 <= width <= 2048 and 256 <= height <= 2048:
                            self.view.width = width
                            self.view.height = height
                        else:
                            raise ValueError("Dimensions out of range")
                    else:
                        raise ValueError("Invalid format")
                except:
                    await interaction.response.send_message(
                        "❌ Invalid dimensions! Use format like '1024x1024' (256-2048)",
                        ephemeral=True
                    )
                    return
            
            # Parse and validate steps
            if self.steps_input.value.strip():
                try:
                    steps = int(self.steps_input.value.strip())
                    if 1 <= steps <= 150:
                        self.view.steps = steps
                    else:
                        raise ValueError("Steps out of range")
                except:
                    await interaction.response.send_message(
                        "❌ Invalid steps! Must be between 1 and 150",
                        ephemeral=True
                    )
                    return
            
            # Parse and validate CFG
            if self.cfg_input.value.strip():
                try:
                    cfg = float(self.cfg_input.value.strip())
                    if 1.0 <= cfg <= 30.0:
                        self.view.cfg = cfg
                    else:
                        raise ValueError("CFG out of range")
                except:
                    await interaction.response.send_message(
                        "❌ Invalid CFG! Must be between 1.0 and 30.0",
                        ephemeral=True
                    )
                    return
            
            # Parse batch size and seed
            if self.batch_seed_input.value.strip():
                try:
                    parts = self.batch_seed_input.value.strip().split('|')
                    if len(parts) >= 1:
                        batch_size = int(parts[0].strip())
                        if 1 <= batch_size <= 4:
                            self.view.batch_size = batch_size
                        else:
                            raise ValueError("Batch size out of range")
                    
                    if len(parts) >= 2 and parts[1].strip():
                        seed = int(parts[1].strip())
                        self.view.seed = seed
                    elif len(parts) >= 2:
                        self.view.seed = None
                except:
                    await interaction.response.send_message(
                        "❌ Invalid batch/seed! Use format like '2 | 12345' or '1 |' for random seed",
                        ephemeral=True
                    )
                    return
            
            # Update negative prompt
            self.view.negative_prompt = self.negative_prompt_input.value.strip()
            
            await interaction.response.send_message(
                "✅ **Settings Updated!**\n" +
                f"📏 **Size:** {self.view.width}x{self.view.height}\n" +
                f"🔧 **Steps:** {self.view.steps} | **CFG:** {self.view.cfg}\n" +
                f"📦 **Batch:** {self.view.batch_size} | **Seed:** {self.view.seed if self.view.seed else 'Random'}\n" +
                f"🚫 **Negative:** {self.view.negative_prompt[:50]}{'...' if len(self.view.negative_prompt) > 50 else '(none)' if not self.view.negative_prompt else ''}",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                "❌ Error updating settings. Please check your input format.",
                ephemeral=True
            )


class GenerateNowButton(discord.ui.Button):
    """Button to start image generation with current settings."""
    
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.success,
            label="🎨 Generate Image",
            emoji="✨"
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Start image generation."""
        view: CompleteSetupView = self.view
        
        # Check if user is authorized
        if interaction.user.id != view.user_id:
            await interaction.response.send_message(
                "❌ Only the person who started this generation can use these controls.",
                ephemeral=True
            )
            return
        
        try:
            # Respond immediately to avoid timeout
            await interaction.response.defer()
            
            # Get the setup message for potential deletion
            setup_message = interaction.message
            
            # Determine workflow based on model
            workflow_name = f"{view.model}_lora"
            workflow_config = view.bot.config.workflows.get(workflow_name)
            
            if not workflow_config or not workflow_config.enabled:
                await interaction.edit_original_response(
                    content="❌ Selected model is not available.",
                    view=None
                )
                return
            
            # Show initial progress
            if view.model == "flux":
                model_display = "Flux"
            elif view.model == "flux_krea":
                model_display = "Flux Krea ✨ NEW"
            else:
                model_display = "HiDream"
            progress_embed = discord.Embed(
                title="🎨 Starting Image Generation...",
                description=f"**Prompt:** {view.prompt[:150]}{'...' if len(view.prompt) > 150 else ''}",
                color=discord.Color.blue()
            )
            
            await interaction.edit_original_response(embed=progress_embed, view=None)
            
            # Progress callback for updates
            settings_text = f"Model: {model_display} | Size: {view.width}x{view.height} | " + \
                           f"Steps: {view.steps} | CFG: {view.cfg} | " + \
                           f"Batch: {view.batch_size}"
            if view.selected_lora:
                settings_text += f" | LoRA: {view.selected_lora} ({view.lora_strength})"
            
            progress_callback = await view.bot._create_unified_progress_callback(
                interaction,
                "Image Generation",
                view.prompt,
                settings_text
            )
            
            # Generate images (now returns list of individual images)
            images_list, generation_info = await view.bot.image_generator.generate_image(
                prompt=view.prompt,
                negative_prompt=view.negative_prompt,
                workflow_name=workflow_name,
                width=view.width,
                height=view.height,
                steps=view.steps,
                cfg=view.cfg,
                batch_size=view.batch_size,
                seed=view.seed,
                lora_name=view.selected_lora,
                lora_strength=view.lora_strength,
                progress_callback=progress_callback
            )
            
            # Send final completion status update
            try:
                final_progress = ProgressInfo()
                final_progress.mark_completed()
                await progress_callback(final_progress)
                view.bot.logger.info("✅ Sent final completion status to Discord")
                
                # Small delay to ensure the completion message is visible
                await asyncio.sleep(1)
                
                # Clean up the setup message to avoid chat clutter
                try:
                    await setup_message.delete()
                    view.bot.logger.info("🧹 Cleaned up setup message")
                except Exception as cleanup_error:
                    view.bot.logger.warning(f"Failed to clean up setup message: {cleanup_error}")
                    
            except Exception as progress_error:
                view.bot.logger.warning(f"Failed to send final progress update: {progress_error}")
            
            # Send individual images with individual action buttons
            for i, image_data in enumerate(images_list):
                # Save image
                filename = get_unique_filename(f"discord_{interaction.user.id}_{i}")
                save_output_image(image_data, filename)
                
                # Create success embed for this image
                success_embed = discord.Embed(
                    title=f"✅ Image {i + 1}/{len(images_list)} Generated - {model_display}!",
                    description=f"**Prompt:** {view.prompt[:200]}{'...' if len(view.prompt) > 200 else ''}",
                    color=discord.Color.green()
                )
                
                # Add generation details
                details_text = f"**Size:** {view.width}x{view.height}\n" + \
                              f"**Steps:** {view.steps} | **CFG:** {view.cfg}\n" + \
                              f"**Seed:** {generation_info.get('seed', 'Unknown')}\n" + \
                              f"**Batch:** {i + 1} of {generation_info.get('num_images', 1)}"
                
                success_embed.add_field(
                    name="Generation Details",
                    value=details_text,
                    inline=True
                )
                
                # Add model and LoRA info
                model_info = f"**Model:** {model_display}\n"
                if view.selected_lora:
                    model_info += f"**LoRA:** {view.selected_lora}\n**LoRA Strength:** {view.lora_strength}"
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
                
                # Create individual action buttons view for this image
                individual_view = IndividualImageView(
                    bot=view.bot,
                    image_data=image_data,
                    generation_info=generation_info,
                    image_index=i
                )
                
                # Send this individual image
                file = discord.File(BytesIO(image_data), filename=filename)
                
                try:
                    if i == 0:
                        # Edit the original response for the first image
                        await interaction.edit_original_response(
                            embed=success_embed,
                            attachments=[file],
                            view=individual_view
                        )
                        view.bot.logger.info(f"Successfully sent image {i + 1} via edit_original_response for {interaction.user}")
                    else:
                        # Send followup messages for additional images
                        await interaction.followup.send(
                            embed=success_embed,
                            file=file,
                            view=individual_view
                        )
                        view.bot.logger.info(f"Successfully sent image {i + 1} via followup for {interaction.user}")
                        
                except Exception as send_error:
                    view.bot.logger.error(f"Error sending image {i + 1}: {send_error}")
                    # Try sending as followup if edit fails
                    try:
                        await interaction.followup.send(
                            embed=success_embed,
                            file=discord.File(BytesIO(image_data), filename=filename),  # Create new file object
                            view=individual_view
                        )
                        view.bot.logger.info(f"Successfully sent image {i + 1} via fallback followup for {interaction.user}")
                    except Exception as followup_error:
                        view.bot.logger.error(f"Failed to send followup image {i + 1}: {followup_error}")
            
            view.bot.logger.info(f"Image generation process completed for {interaction.user} (ID: {interaction.user.id}) with model: {view.model}")
            
            # Clean up old outputs
            cleanup_old_outputs(view.bot.config.generation.output_limit)
            
        except Exception as e:
            view.bot.logger.error(f"Unexpected error in generation: {e}")
            view.bot.logger.error(f"Traceback: {traceback.format_exc()}")
            
            try:
                error_embed = discord.Embed(
                    title="❌ Generation Failed",
                    description=f"An error occurred during generation: {str(e)[:200]}{'...' if len(str(e)) > 200 else ''}",
                    color=discord.Color.red()
                )
                await interaction.edit_original_response(embed=error_embed, view=None)
            except:
                # If we can't edit, try followup
                try:
                    await interaction.followup.send("❌ Generation failed. Please try again.", ephemeral=True)
                except:
                    view.bot.logger.error("Failed to send error response to user")

class IndividualImageView(discord.ui.View):
    """View for individual images with action buttons."""
    
    def __init__(self, bot: ComfyUIBot, image_data: bytes, generation_info: Dict[str, Any], image_index: int):
        super().__init__(timeout=None)  # No timeout for post-generation actions
        self.bot = bot
        self.image_data = image_data
        self.generation_info = generation_info
        self.image_index = image_index
        
        # Create buttons with dynamic labels
        upscale_button = discord.ui.Button(
            label=f"🔍 Upscale #{image_index + 1}",
            style=discord.ButtonStyle.secondary,
            custom_id=f"upscale_{image_index}"
        )
        upscale_button.callback = self.upscale_button_callback
        
        flux_edit_button = discord.ui.Button(
            label=f"✏️ Flux Edit #{image_index + 1}",
            style=discord.ButtonStyle.secondary,
            custom_id=f"flux_edit_{image_index}"
        )
        flux_edit_button.callback = self.flux_edit_button_callback
        
        qwen_edit_button = discord.ui.Button(
            label=f"⚡ Qwen Edit #{image_index + 1}",
            style=discord.ButtonStyle.secondary,
            custom_id=f"qwen_edit_{image_index}"
        )
        qwen_edit_button.callback = self.qwen_edit_button_callback
        
        animate_button = discord.ui.Button(
            label=f"🎬 Animate #{image_index + 1}",
            style=discord.ButtonStyle.secondary,
            custom_id=f"animate_{image_index}"
        )
        animate_button.callback = self.animate_button_callback
        
        # Add the buttons to the view
        self.add_item(upscale_button)
        self.add_item(flux_edit_button)
        self.add_item(qwen_edit_button)
        self.add_item(animate_button)
    
    async def upscale_button_callback(self, interaction: discord.Interaction):
        """Show upscale parameter selection modal."""
        try:
            # Check rate limiting
            if not self.bot._check_rate_limit(interaction.user.id):
                await interaction.response.send_message(
                    "❌ **Rate Limited!** Please wait before making another request.",
                    ephemeral=True
                )
                return
            
            # Show upscale parameter modal
            modal = UpscaleParameterModal(self)
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            self.bot.logger.error(f"Error showing upscale modal: {e}")
            try:
                await interaction.response.send_message(
                    "❌ Error opening upscale settings. Please try again.",
                    ephemeral=True
                )
            except:
                pass
    
    async def flux_edit_button_callback(self, interaction: discord.Interaction):
        """Show Flux edit parameter selection modal."""
        try:
            # Check rate limiting
            if not self.bot._check_rate_limit(interaction.user.id):
                await interaction.response.send_message(
                    "❌ **Rate Limited!** Please wait before making another request.",
                    ephemeral=True
                )
                return
            
            # Show Flux edit parameter modal
            modal = EditParameterModal(self, workflow_type="flux")
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            self.bot.logger.error(f"Error showing Flux edit modal: {e}")
            try:
                await interaction.response.send_message(
                    "❌ Error opening Flux edit settings. Please try again.",
                    ephemeral=True
                )
            except:
                pass
    
    async def qwen_edit_button_callback(self, interaction: discord.Interaction):
        """Show Qwen edit parameter selection modal."""
        try:
            # Check rate limiting
            if not self.bot._check_rate_limit(interaction.user.id):
                await interaction.response.send_message(
                    "❌ **Rate Limited!** Please wait before making another request.",
                    ephemeral=True
                )
                return
            
            # Show Qwen edit parameter modal
            modal = EditParameterModal(self, workflow_type="qwen")
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            self.bot.logger.error(f"Error showing Qwen edit modal: {e}")
            try:
                await interaction.response.send_message(
                    "❌ Error opening Qwen edit settings. Please try again.",
                    ephemeral=True
                )
            except:
                pass
    
    async def animate_button_callback(self, interaction: discord.Interaction):
        """Show animation parameter selection modal."""
        try:
            # Check rate limiting
            if not self.bot._check_rate_limit(interaction.user.id):
                await interaction.response.send_message(
                    "❌ **Rate Limited!** Please wait before making another request.",
                    ephemeral=True
                )
                return
            
            # Show animation parameter modal
            modal = AnimationParameterModal(self)
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            self.bot.logger.error(f"Error showing animation modal: {e}")
            try:
                await interaction.response.send_message(
                    "❌ Error opening animation settings. Please try again.",
                    ephemeral=True
                )
            except:
                pass

    async def _perform_upscale(self, interaction: discord.Interaction, upscale_factor: int, denoise: float, steps: int):
        """Perform the actual upscaling with user-selected parameters."""
        try:
            # Show public status that someone is upscaling
            await interaction.response.send_message(
                f"🔍 **{interaction.user.display_name}** is upscaling image #{self.image_index + 1}...\n"
                f"*Factor: {upscale_factor}x | Denoise: {denoise} | Steps: {steps}*",
                ephemeral=False  # Public message
            )
            
            # Extract original parameters for better upscaling
            original_prompt = self.generation_info.get('prompt', '')
            original_negative = self.generation_info.get('negative_prompt', '')
            
            # Create progress callback for upscaling
            progress_callback = await self.bot._create_unified_progress_callback(
                interaction,
                "Image Upscaling",
                original_prompt,
                f"Factor: {upscale_factor}x | Method: AI Super-Resolution | Original: {self.generation_info.get('width', 'Unknown')}x{self.generation_info.get('height', 'Unknown')}"
            )
            
            # Perform upscaling
            upscaled_data, upscale_info = await self.bot.image_generator.generate_upscale(
                input_image_data=self.image_data,
                prompt=original_prompt,
                negative_prompt=original_negative,
                upscale_factor=float(upscale_factor),
                denoise=denoise,
                steps=steps,
                cfg=7.0,
                progress_callback=progress_callback
            )
            
            # Send final completion status
            try:
                final_progress = ProgressInfo()
                final_progress.mark_completed()
                await progress_callback(final_progress)
                self.bot.logger.info("✅ Successfully sent completion status to Discord for Image Upscaling")
            except Exception as progress_error:
                self.bot.logger.warning(f"Failed to send final upscale progress: {progress_error}")
            
            # Save upscaled image
            filename = get_unique_filename(f"upscaled_{upscale_factor}x_{interaction.user.id}")
            save_output_image(upscaled_data, filename)
            
            # Create success embed
            success_embed = discord.Embed(
                title="✅ Image Upscaled Successfully!",
                description=f"**Original Image #{self.image_index + 1}** has been upscaled {upscale_factor}x",
                color=discord.Color.green()
            )
            
            success_embed.add_field(
                name="Upscale Details",
                value=f"**Factor:** {upscale_factor}x\n**Method:** AI Super-Resolution\n**Denoise:** {denoise}\n**Steps:** {steps}",
                inline=True
            )
            
            success_embed.add_field(
                name="Original Prompt",
                value=f"{original_prompt[:100]}{'...' if len(original_prompt) > 100 else ''}",
                inline=False
            )
            
            success_embed.set_footer(text=f"Upscaled by {interaction.user.display_name}")
            
            # Create new view for the upscaled image
            upscaled_view = IndividualImageView(
                bot=self.bot,
                image_data=upscaled_data,
                generation_info=upscale_info,
                image_index=0  # Upscaled images are standalone
            )
            
            # Send upscaled image
            file = discord.File(BytesIO(upscaled_data), filename=filename)
            await interaction.followup.send(
                embed=success_embed,
                file=file,
                view=upscaled_view
            )
            
            self.bot.logger.info(f"Successfully generated upscaled image for {interaction.user}")
            
        except Exception as e:
            self.bot.logger.error(f"Error in upscale: {e}")
            try:
                error_embed = discord.Embed(
                    title="❌ Upscaling Failed",
                    description=f"Failed to upscale image: {str(e)[:200]}{'...' if len(str(e)) > 200 else ''}",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            except:
                pass

    async def _perform_edit(self, interaction: discord.Interaction, edit_prompt: str, steps: int, workflow_type: str = "flux"):
        """Perform the actual image editing with user-selected parameters."""
        try:
            # Show public status that someone is editing
            workflow_emoji = "⚡" if workflow_type == "qwen" else "✏️"
            workflow_name = "Qwen" if workflow_type == "qwen" else "Flux"
            await interaction.response.send_message(
                f"{workflow_emoji} **{interaction.user.display_name}** is editing image #{self.image_index + 1} with {workflow_name}...\n"
                f"*Edit: {edit_prompt[:100]}{'...' if len(edit_prompt) > 100 else ''} | Steps: {steps}*",
                ephemeral=False  # Public message
            )
            
            # Create progress callback for editing
            if workflow_type == "qwen":
                progress_callback = await self.bot._create_unified_progress_callback(
                    interaction,
                    "Image Editing",
                    edit_prompt,
                    f"Method: Qwen 2.5 VL | Steps: {steps} | CFG: 1.0"
                )
                cfg = 1.0
            else:
                progress_callback = await self.bot._create_unified_progress_callback(
                    interaction,
                    "Image Editing",
                    edit_prompt,
                    f"Method: Flux Kontext | Steps: {steps} | CFG: 2.5"
                )
                cfg = 2.5
            
            # Perform editing
            edited_data, edit_info = await self.bot.image_generator.generate_edit(
                input_image_data=self.image_data,
                edit_prompt=edit_prompt,
                width=1024,
                height=1024,
                steps=steps,
                cfg=cfg,
                workflow_type=workflow_type,
                progress_callback=progress_callback
            )
            
            # Send final completion status
            try:
                from image_gen import ProgressInfo
                final_progress = ProgressInfo()
                final_progress.mark_completed()
                await progress_callback(final_progress)
                self.bot.logger.info("✅ Successfully sent completion status to Discord for Image Editing")
            except Exception as progress_error:
                self.bot.logger.warning(f"Failed to send final edit progress: {progress_error}")
            
            # Save edited image
            from image_gen import save_output_image, get_unique_filename
            filename = get_unique_filename(f"edited_{interaction.user.id}")
            save_output_image(edited_data, filename)
            
            # Create success embed
            success_embed = discord.Embed(
                title="✅ Image Edited Successfully!",
                description=f"**Image #{self.image_index + 1}** has been edited using Flux Kontext",
                color=discord.Color.green()
            )
            
            success_embed.add_field(
                name="Edit Details",
                value=f"**Method:** Flux Kontext\n**Edit Prompt:** {edit_prompt[:100]}{'...' if len(edit_prompt) > 100 else ''}\n**Steps:** {steps}",
                inline=False
            )
            
            success_embed.set_footer(text=f"Edited by {interaction.user.display_name}")
            
            # Create new view for the edited image
            edited_view = IndividualImageView(
                bot=self.bot,
                image_data=edited_data,
                generation_info=edit_info,
                image_index=0  # Edited images are standalone
            )
            
            # Send edited image
            from io import BytesIO
            file = discord.File(BytesIO(edited_data), filename=filename)
            await interaction.followup.send(
                embed=success_embed,
                file=file,
                view=edited_view
            )
            
            self.bot.logger.info(f"Successfully generated edited image for {interaction.user}")
            
        except Exception as e:
            self.bot.logger.error(f"Error in editing: {e}")
            try:
                error_embed = discord.Embed(
                    title="❌ Image Editing Failed",
                    description=f"Failed to edit image: {str(e)[:200]}{'...' if len(str(e)) > 200 else ''}",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            except:
                pass

    async def _perform_animation(self, interaction: discord.Interaction, animation_prompt: str, frames: int, strength: float, steps: int):
        """Perform the actual animation with user-selected parameters and custom prompt."""
        try:
            # Show public status that someone is animating
            prompt_preview = animation_prompt[:80] + "..." if len(animation_prompt) > 80 else animation_prompt
            await interaction.response.send_message(
                f"🎬 **{interaction.user.display_name}** is animating image #{self.image_index + 1}...\n"
                f"*Prompt: {prompt_preview} | Frames: {frames} | Strength: {strength} | Steps: {steps} | This will take 2-5 minutes.*",
                ephemeral=False  # Public message
            )
            
            # Create progress callback for video generation
            progress_callback = await self.bot._create_unified_progress_callback(
                interaction,
                "Video Generation",
                animation_prompt,
                f"Resolution: 720x720 | Frames: {frames} | Steps: {steps} | CFG: 1.0 | Strength: {strength}"
            )
            
            # Perform video generation using the custom animation prompt
            video_data, filename, video_info = await self.bot.video_generator.generate_video(
                prompt=animation_prompt,
                negative_prompt=self.generation_info.get('negative_prompt', ''),
                workflow_name=None,  # Use default video workflow
                width=720,
                height=720,
                steps=steps,
                cfg=1.0,
                length=frames,
                strength=strength,
                seed=None,
                input_image_data=self.image_data,
                progress_callback=progress_callback
            )
            
            # Send final completion status
            try:
                from image_gen import ProgressInfo
                final_progress = ProgressInfo()
                final_progress.mark_completed()
                await progress_callback(final_progress)
                self.bot.logger.info("✅ Successfully sent completion status to Discord for Video Generation")
            except Exception as progress_error:
                self.bot.logger.warning(f"Failed to send final video progress: {progress_error}")
            
            # Save video
            from video_gen import save_output_video, get_unique_video_filename
            filename = get_unique_video_filename(f"animated_{frames}f_{interaction.user.id}")
            save_output_video(video_data, filename)
            
            # Create success embed
            success_embed = discord.Embed(
                title="✅ Video Generated Successfully!",
                description=f"**Image #{self.image_index + 1}** has been animated into a video",
                color=discord.Color.purple()
            )
            
            success_embed.add_field(
                name="Video Details",
                value=f"**Format:** MP4\n**Frames:** {frames}\n**Resolution:** 720x720\n**Strength:** {strength}\n**Steps:** {steps}",
                inline=True
            )
            
            success_embed.add_field(
                name="Animation Prompt",
                value=f"{animation_prompt[:150]}{'...' if len(animation_prompt) > 150 else ''}",
                inline=False
            )
            
            success_embed.add_field(
                name="Original Prompt", 
                value=f"{self.generation_info.get('prompt', '')[:100]}{'...' if len(self.generation_info.get('prompt', '')) > 100 else ''}",
                inline=False
            )
            
            success_embed.set_footer(text=f"Animated by {interaction.user.display_name}")
            
            # Send video file
            from io import BytesIO
            file = discord.File(BytesIO(video_data), filename=filename)
            await interaction.followup.send(
                embed=success_embed,
                file=file
            )
            
            self.bot.logger.info(f"Successfully generated video for {interaction.user}")
            
        except Exception as e:
            self.bot.logger.error(f"Error in video generation: {e}")
            try:
                error_embed = discord.Embed(
                    title="❌ Video Generation Failed",
                    description=f"Failed to generate video: {str(e)[:200]}{'...' if len(str(e)) > 200 else ''}",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            except:
                pass


class UpscaleParameterModal(discord.ui.Modal):
    """Modal for selecting upscale parameters."""
    
    def __init__(self, image_view):
        super().__init__(title="🔍 Upscale Settings")
        self.image_view = image_view
        
        # Add upscale factor dropdown (we'll handle this in the view)
        self.upscale_factor = discord.ui.TextInput(
            label="Upscale Factor",
            placeholder="Enter: 2, 4, or 8 (default: 2)",
            default="2",
            max_length=1,
            required=True
        )
        self.add_item(self.upscale_factor)
        
        # Add denoise strength
        self.denoise = discord.ui.TextInput(
            label="Denoise Strength",
            placeholder="0.1 - 1.0 (default: 0.35)",
            default="0.35",
            max_length=4,
            required=False
        )
        self.add_item(self.denoise)
        
        # Add steps
        self.steps = discord.ui.TextInput(
            label="Steps",
            placeholder="10-50 (default: 20)",
            default="20",
            max_length=2,
            required=False
        )
        self.add_item(self.steps)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Parse upscale factor
            try:
                upscale_factor = int(self.upscale_factor.value)
                if upscale_factor not in [2, 4, 8]:
                    raise ValueError("Upscale factor must be 2, 4, or 8")
            except (ValueError, TypeError):
                await interaction.response.send_message(
                    "❌ Invalid upscale factor! Must be 2, 4, or 8.",
                    ephemeral=True
                )
                return
            
            # Parse denoise strength
            try:
                denoise = float(self.denoise.value) if self.denoise.value else 0.35
                if not (0.1 <= denoise <= 1.0):
                    raise ValueError("Denoise must be between 0.1 and 1.0")
            except (ValueError, TypeError):
                await interaction.response.send_message(
                    "❌ Invalid denoise strength! Must be between 0.1 and 1.0.",
                    ephemeral=True
                )
                return
            
            # Parse steps
            try:
                steps = int(self.steps.value) if self.steps.value else 20
                if not (10 <= steps <= 50):
                    raise ValueError("Steps must be between 10 and 50")
            except (ValueError, TypeError):
                await interaction.response.send_message(
                    "❌ Invalid steps! Must be between 10 and 50.",
                    ephemeral=True
                )
                return
            
            # Start upscaling with selected parameters
            await self.image_view._perform_upscale(interaction, upscale_factor, denoise, steps)
            
        except Exception as e:
            self.image_view.bot.logger.error(f"Error in upscale modal submit: {e}")
            try:
                await interaction.response.send_message(
                    "❌ Error processing upscale settings. Please try again.",
                    ephemeral=True
                )
            except:
                pass


class AnimationParameterModal(discord.ui.Modal):
    """Modal for selecting animation parameters."""
    
    def __init__(self, image_view):
        super().__init__(title="🎬 Animation Settings")
        self.image_view = image_view
        
        # Get original prompt for pre-filling
        original_prompt = image_view.generation_info.get('prompt', '')
        
        # Add animation prompt input (pre-filled with original)
        self.animation_prompt = discord.ui.TextInput(
            label="Animation Prompt",
            placeholder="Describe the animation or leave as original...",
            default=original_prompt[:500],  # Limit to modal max length
            style=discord.TextStyle.paragraph,
            max_length=500,
            required=True
        )
        self.add_item(self.animation_prompt)
        
        # Add frame count dropdown
        self.frames = discord.ui.TextInput(
            label="Frame Count",
            placeholder="Enter: 81, 121, or 161 (default: 81)",
            default="81",
            max_length=3,
            required=True
        )
        self.add_item(self.frames)
        
        # Add strength
        self.strength = discord.ui.TextInput(
            label="Animation Strength",
            placeholder="0.1 - 1.0 (default: 0.7)",
            default="0.7",
            max_length=4,
            required=False
        )
        self.add_item(self.strength)
        
        # Add steps
        self.steps = discord.ui.TextInput(
            label="Steps",
            placeholder="4-12 (default: 6)",
            default="6",
            max_length=2,
            required=False
        )
        self.add_item(self.steps)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Validate animation prompt
            animation_prompt = self.animation_prompt.value.strip()
            if not animation_prompt:
                await interaction.response.send_message(
                    "❌ Animation prompt cannot be empty!",
                    ephemeral=True
                )
                return
            
            # Parse frame count
            try:
                frames = int(self.frames.value)
                if frames not in [81, 121, 161]:
                    raise ValueError("Frame count must be 81, 121, or 161")
            except (ValueError, TypeError):
                await interaction.response.send_message(
                    "❌ Invalid frame count! Must be 81, 121, or 161.",
                    ephemeral=True
                )
                return
            
            # Parse strength
            try:
                strength = float(self.strength.value) if self.strength.value else 0.7
                if not (0.1 <= strength <= 1.0):
                    raise ValueError("Strength must be between 0.1 and 1.0")
            except (ValueError, TypeError):
                await interaction.response.send_message(
                    "❌ Invalid strength! Must be between 0.1 and 1.0.",
                    ephemeral=True
                )
                return
            
            # Parse steps
            try:
                steps = int(self.steps.value) if self.steps.value else 6
                if not (4 <= steps <= 12):
                    raise ValueError("Steps must be between 4 and 12")
            except (ValueError, TypeError):
                await interaction.response.send_message(
                    "❌ Invalid steps! Must be between 4 and 12.",
                    ephemeral=True
                )
                return
            
            # Start animation with selected parameters and custom prompt
            await self.image_view._perform_animation(interaction, animation_prompt, frames, strength, steps)
            
        except Exception as e:
            self.image_view.bot.logger.error(f"Error in animation modal submit: {e}")
            try:
                await interaction.response.send_message(
                    "❌ Error processing animation settings. Please try again.",
                    ephemeral=True
                )
            except:
                pass


class EditParameterModal(discord.ui.Modal):
    """Modal for configuring image edit parameters."""
    
    def __init__(self, image_view, workflow_type="flux"):
        self.workflow_type = workflow_type
        if workflow_type == "qwen":
            super().__init__(title="⚡ Configure Qwen Edit")
        else:
            super().__init__(title="✏️ Configure Flux Edit")
        self.image_view = image_view
        
        # Edit prompt input (main field)
        self.edit_prompt_input = discord.ui.TextInput(
            label="Edit Prompt",
            placeholder="Describe what you want to change in the image...",
            style=discord.TextStyle.paragraph,
            min_length=1,
            max_length=500,
            required=True
        )
        self.add_item(self.edit_prompt_input)
        
        # Sampling steps input (different ranges for different workflows)
        if workflow_type == "qwen":
            self.steps_input = discord.ui.TextInput(
                label="Sampling Steps (4-20)",
                placeholder="Default: 8",
                default="8",
                min_length=1,
                max_length=2,
                required=False
            )
        else:
            self.steps_input = discord.ui.TextInput(
                label="Sampling Steps (10-50)",
                placeholder="Default: 20",
                default="20",
                min_length=1,
                max_length=2,
                required=False
            )
        self.add_item(self.steps_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle edit parameters and start editing process."""
        try:
            # Validate edit prompt
            edit_prompt = self.edit_prompt_input.value.strip()
            if not edit_prompt:
                await interaction.response.send_message(
                    "❌ Edit prompt cannot be empty!",
                    ephemeral=True
                )
                return
            
            # Parse and validate steps based on workflow type
            if self.workflow_type == "qwen":
                steps = 8  # Default for Qwen
                min_steps, max_steps = 4, 20
            else:
                steps = 20  # Default for Flux
                min_steps, max_steps = 10, 50
            
            if self.steps_input.value.strip():
                try:
                    steps = int(self.steps_input.value.strip())
                    if not (min_steps <= steps <= max_steps):
                        await interaction.response.send_message(
                            f"❌ Invalid steps! Must be between {min_steps} and {max_steps}",
                            ephemeral=True
                        )
                        return
                except ValueError:
                    await interaction.response.send_message(
                        f"❌ Invalid steps! Must be a number between {min_steps} and {max_steps}",
                        ephemeral=True
                    )
                    return
            
            # Start the editing process with workflow type
            await self.image_view._perform_edit(interaction, edit_prompt, steps, self.workflow_type)
            
        except Exception as e:
            self.image_view.bot.logger.error(f"Error in edit modal submit: {e}")
            try:
                await interaction.response.send_message(
                    "❌ Error processing edit request. Please try again.",
                    ephemeral=True
                )
            except:
                await interaction.followup.send(
                    "❌ Error processing edit request. Please try again.",
                    ephemeral=True
                )


class PostGenerationEditModal(discord.ui.Modal):
    """Modal for editing images from PostGenerationView."""
    
    def __init__(self, post_gen_view, user, workflow_type="flux"):
        self.workflow_type = workflow_type
        if workflow_type == "qwen":
            super().__init__(title="⚡ Qwen Edit Image")
        else:
            super().__init__(title="✏️ Flux Edit Image")
        self.post_gen_view = post_gen_view
        self.user = user
        
        # Edit prompt input (main field)
        self.edit_prompt_input = discord.ui.TextInput(
            label="Edit Prompt",
            placeholder="Describe what you want to change in the image...",
            style=discord.TextStyle.paragraph,
            min_length=1,
            max_length=500,
            required=True
        )
        self.add_item(self.edit_prompt_input)
        
        # Sampling steps input (different ranges for different workflows)
        if workflow_type == "qwen":
            self.steps_input = discord.ui.TextInput(
                label="Sampling Steps (4-20)",
                placeholder="Default: 8",
                default="8",
                min_length=1,
                max_length=2,
                required=False
            )
        else:
            self.steps_input = discord.ui.TextInput(
                label="Sampling Steps (10-50)",
                placeholder="Default: 20",
                default="20",
            min_length=1,
            max_length=2,
            required=False
        )
        self.add_item(self.steps_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle edit parameters and start editing process."""
        try:
            # Validate edit prompt
            edit_prompt = self.edit_prompt_input.value.strip()
            if not edit_prompt:
                await interaction.response.send_message(
                    "❌ Edit prompt cannot be empty!",
                    ephemeral=True
                )
                return
            
            # Parse and validate steps based on workflow type
            if self.workflow_type == "qwen":
                steps = 8  # Default for Qwen
                min_steps, max_steps = 4, 20
            else:
                steps = 20  # Default for Flux
                min_steps, max_steps = 10, 50
            
            if self.steps_input.value.strip():
                try:
                    steps = int(self.steps_input.value.strip())
                    if not (min_steps <= steps <= max_steps):
                        await interaction.response.send_message(
                            f"❌ Invalid steps! Must be between {min_steps} and {max_steps}",
                            ephemeral=True
                        )
                        return
                except ValueError:
                    await interaction.response.send_message(
                        f"❌ Invalid steps! Must be a number between {min_steps} and {max_steps}",
                        ephemeral=True
                    )
                    return
            
            # Start editing process
            workflow_emoji = "⚡" if self.workflow_type == "qwen" else "✏️"
            workflow_name = "Qwen" if self.workflow_type == "qwen" else "Flux"
            await interaction.response.send_message(f"{workflow_emoji} Starting {workflow_name} image editing process...", ephemeral=True)
            
            try:
                # Progress callback for editing
                if self.workflow_type == "qwen":
                    progress_callback = await self.post_gen_view.bot._create_unified_progress_callback(
                        interaction,
                        "Image Editing",
                        edit_prompt,
                        f"Method: Qwen 2.5 VL | Steps: {steps} | CFG: 1.0"
                    )
                    cfg = 1.0
                else:
                    progress_callback = await self.post_gen_view.bot._create_unified_progress_callback(
                        interaction,
                        "Image Editing",
                        edit_prompt,
                        f"Method: Flux Kontext | Steps: {steps} | CFG: 2.5"
                    )
                    cfg = 2.5
                
                # Generate edited image using ComfyUI
                edited_data, edit_info = await self.post_gen_view.bot.image_generator.generate_edit(
                    input_image_data=self.post_gen_view.original_image_data,
                    edit_prompt=edit_prompt,
                    width=1024,
                    height=1024,
                    steps=steps,
                    cfg=cfg,
                    workflow_type=self.workflow_type,
                    progress_callback=progress_callback
                )
                
                # Create success embed
                edit_embed = discord.Embed(
                    title="✅ Image Edited Successfully!",
                    description=f"**Original Prompt:** {self.post_gen_view.generation_info.get('prompt', 'Unknown')[:100]}{'...' if len(self.post_gen_view.generation_info.get('prompt', '')) > 100 else ''}",
                    color=discord.Color.green()
                )
                
                edit_embed.add_field(
                    name="Edit Details",
                    value=f"**Method:** {workflow_name}\n**Edit Prompt:** {edit_prompt[:100]}{'...' if len(edit_prompt) > 100 else ''}\n**Steps:** {steps}",
                    inline=False
                )
                
                edit_embed.add_field(
                    name="Requested by",
                    value=interaction.user.display_name,
                    inline=True
                )
                
                # Send edited image file
                edited_filename = f"edited_{int(__import__('time').time())}.png"
                file = discord.File(BytesIO(edited_data), filename=edited_filename)
                
                # Create new view for the edited image
                edited_view = IndividualImageView(
                    bot=self.post_gen_view.bot,
                    image_data=edited_data,
                    generation_info=edit_info,
                    image_index=0  # Edited images are standalone
                )
                
                await interaction.followup.send(
                    embed=edit_embed,
                    file=file,
                    view=edited_view,
                    ephemeral=False  # Make it visible to everyone
                )
                
                self.post_gen_view.bot.logger.info(f"Successfully edited image for {interaction.user}")
                        
            except Exception as e:
                self.post_gen_view.bot.logger.error(f"Edit error: {e}")
                await interaction.followup.send("❌ Image editing failed. Please try again later.", ephemeral=True)
            
        except Exception as e:
            self.post_gen_view.bot.logger.error(f"Error in edit modal submit: {e}")
            try:
                await interaction.response.send_message(
                    "❌ Error processing edit request. Please try again.",
                    ephemeral=True
                )
            except:
                await interaction.followup.send(
                    "❌ Error processing edit request. Please try again.",
                    ephemeral=True
                )

async def main():
    """Main function to run the bot."""
    # Set up logging with strict filtering
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/bot.log', encoding='utf-8')
        ]
    )
    
    # Completely disable debug logging globally - very restrictive
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger('image_gen').setLevel(logging.INFO)
    logging.getLogger('video_gen').setLevel(logging.INFO)
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Completely disable all debug logging - this should stop all monitoring spam
    logging.disable(logging.DEBUG)
    
    # Also silence specific loggers that might cause spam
    logging.getLogger('comfyui').setLevel(logging.WARNING)
    logging.getLogger('websocket').setLevel(logging.WARNING)
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    logger = logging.getLogger(__name__)
    
    try:
        # Create and configure bot
        bot = ComfyUIBot()
        
        # Add commands to the bot
        bot.tree.add_command(generate_command)
        bot.tree.add_command(editflux_command)
        bot.tree.add_command(editqwen_command)
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