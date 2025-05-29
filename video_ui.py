"""
Video generation UI components for Discord bot.
"""

import asyncio
import traceback
from io import BytesIO
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from bot import CompleteSetupView


class VideoParameterSettingsButton(discord.ui.Button):
    """Button to configure video generation parameters."""
    
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label="⚙️ Video Settings",
            emoji="🎬"
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Show video parameter settings modal."""
        view = self.view
        
        # Check if user is authorized
        if interaction.user.id != view.user_id:
            await interaction.response.send_message(
                "❌ Only the person who started this generation can use these controls.",
                ephemeral=True
            )
            return
        
        # Show modal with current settings
        modal = VideoParameterSettingsModal(view)
        await interaction.response.send_modal(modal)


class VideoParameterSettingsModal(discord.ui.Modal):
    """Modal for configuring video generation parameters."""
    
    def __init__(self, view):
        super().__init__(title="🎬 Configure Video Settings")
        self.view = view
        
        # Frame count input
        self.frames_input = discord.ui.TextInput(
            label="Frame Count (81/121/161)",
            placeholder=f"Current: {view.frames}",
            default=str(view.frames),
            min_length=2,
            max_length=3,
            required=False
        )
        self.add_item(self.frames_input)
        
        # Animation strength input
        self.strength_input = discord.ui.TextInput(
            label="Animation Strength (0.1 - 1.0)",
            placeholder=f"Current: {view.strength}",
            default=str(view.strength),
            min_length=3,
            max_length=4,
            required=False
        )
        self.add_item(self.strength_input)
        
        # Sampling steps input
        self.steps_input = discord.ui.TextInput(
            label="Sampling Steps (4-50)",
            placeholder=f"Current: {view.steps}",
            default=str(view.steps),
            min_length=1,
            max_length=2,
            required=False
        )
        self.add_item(self.steps_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle video settings update."""
        try:
            # Parse and validate frame count
            if self.frames_input.value.strip():
                try:
                    frames = int(self.frames_input.value.strip())
                    if frames in [81, 121, 161]:
                        self.view.frames = frames
                    else:
                        await interaction.response.send_message(
                            "❌ Invalid frame count! Must be 81, 121, or 161",
                            ephemeral=True
                        )
                        return
                except:
                    await interaction.response.send_message(
                        "❌ Invalid frame count! Must be 81, 121, or 161",
                        ephemeral=True
                    )
                    return
            
            # Parse and validate strength
            if self.strength_input.value.strip():
                try:
                    strength = float(self.strength_input.value.strip())
                    if 0.1 <= strength <= 1.0:
                        self.view.strength = strength
                    else:
                        await interaction.response.send_message(
                            "❌ Invalid strength! Must be between 0.1 and 1.0",
                            ephemeral=True
                        )
                        return
                except:
                    await interaction.response.send_message(
                        "❌ Invalid strength! Must be a number between 0.1 and 1.0",
                        ephemeral=True
                    )
                    return
            
            # Parse and validate steps
            if self.steps_input.value.strip():
                try:
                    steps = int(self.steps_input.value.strip())
                    if 4 <= steps <= 50:
                        self.view.steps = steps
                    else:
                        await interaction.response.send_message(
                            "❌ Invalid steps! Must be between 4 and 50",
                            ephemeral=True
                        )
                        return
                except:
                    await interaction.response.send_message(
                        "❌ Invalid steps! Must be between 4 and 50",
                        ephemeral=True
                    )
                    return
            
            # Calculate approximate video duration
            duration = round(self.view.frames / 32.0, 1)  # 32 FPS
            
            await interaction.response.send_message(
                "✅ **Video Settings Updated!**\n" +
                f"📹 **Frame Count:** {self.view.frames} ({duration}s video)\n" +
                f"💪 **Strength:** {self.view.strength}\n" +
                f"🔧 **Steps:** {self.view.steps}\n" +
                f"⏱️ **Estimated Time:** 5-15 minutes",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                "❌ Error updating video settings. Please check your input format.",
                ephemeral=True
            )


class GenerateVideoButton(discord.ui.Button):
    """Button to start video generation with current settings."""
    
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.success,
            label="🎬 Generate Video",
            emoji="🚀"
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Start video generation."""
        view = self.view
        
        # Check if user is authorized
        if interaction.user.id != view.user_id:
            await interaction.response.send_message(
                "❌ Only the person who started this generation can use these controls.",
                ephemeral=True
            )
            return
        
        try:
            # Import here to avoid circular imports
            from image_gen import ProgressInfo
            from video_gen import save_output_video, get_unique_video_filename
            
            # Respond immediately to avoid timeout
            await interaction.response.defer()
            
            # Get the setup message for potential deletion
            setup_message = interaction.message
            
            # Show initial progress
            duration = round(view.frames / 32.0, 1)  # 32 FPS
            progress_embed = discord.Embed(
                title="🎬 Starting Video Generation - WAN2.1VACE...",
                description=f"**Prompt:** {view.prompt[:150]}{'...' if len(view.prompt) > 150 else ''}",
                color=discord.Color.purple()
            )
            
            await interaction.edit_original_response(embed=progress_embed, view=None)
            
            # Progress callback for updates
            settings_text = f"Frames: {view.frames} ({duration}s) | Strength: {view.strength} | Steps: {view.steps}"
            
            progress_callback = await view.bot._create_unified_progress_callback(
                interaction,
                "Video Generation",
                view.prompt,
                settings_text
            )
            
            # Generate video using the WAN2.1VACE workflow
            async with view.bot.video_generator as gen:
                video_data, video_filename, generation_info = await gen.generate_video(
                    prompt=view.prompt,
                    negative_prompt="",
                    workflow_name="video_wan_vace_14B_i2v",
                    width=720,
                    height=720,
                    steps=view.steps,
                    cfg=1.0,
                    length=view.frames,
                    strength=view.strength,
                    seed=None,
                    input_image_data=view.image_data,
                    progress_callback=progress_callback
                )
            
            # Send final completion status update
            try:
                final_progress = ProgressInfo()
                final_progress.mark_completed()
                await progress_callback(final_progress)
                view.bot.logger.info("✅ Successfully sent completion status to Discord for Video Generation")
                
                # Small delay to ensure the completion message is visible
                await asyncio.sleep(1)
                
                # Clean up the setup message to avoid chat clutter
                try:
                    await setup_message.delete()
                    view.bot.logger.info("🧹 Cleaned up video setup message")
                except Exception as cleanup_error:
                    view.bot.logger.warning(f"Failed to clean up video setup message: {cleanup_error}")
                    
            except Exception as progress_error:
                view.bot.logger.warning(f"Failed to send final video progress update: {progress_error}")
            
            # Save video
            output_filename = get_unique_video_filename(f"video_{interaction.user.id}")
            save_output_video(video_data, output_filename)
            
            # Create success embed
            success_embed = discord.Embed(
                title="✅ Video Generated Successfully - WAN2.1VACE!",
                description=f"**Prompt:** {view.prompt[:200]}{'...' if len(view.prompt) > 200 else ''}",
                color=discord.Color.green()
            )
            
            # Add generation details
            success_embed.add_field(
                name="Video Details",
                value=f"**Model:** WAN2.1VACE\n**Frames:** {view.frames} ({duration}s)\n**Strength:** {view.strength}\n**Steps:** {view.steps}",
                inline=True
            )
            
            success_embed.add_field(
                name="File Info",
                value=f"**Size:** {len(video_data) / (1024*1024):.1f} MB\n**Format:** MP4 (H.265)\n**FPS:** 32",
                inline=True
            )
            
            success_embed.set_footer(text=f"Generated by {interaction.user.display_name}")
            
            # Send video file
            try:
                file = discord.File(BytesIO(video_data), filename=output_filename)
                await interaction.followup.send(
                    embed=success_embed,
                    file=file
                )
                
                view.bot.logger.info(f"Successfully generated video for {interaction.user}")
                
            except discord.HTTPException as e:
                if e.status == 413:  # File too large
                    error_embed = discord.Embed(
                        title="❌ Video Too Large",
                        description="The generated video is too large to upload to Discord. Try reducing the frame count or using a different strength setting.",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=error_embed)
                else:
                    raise
            
        except Exception as e:
            view.bot.logger.error(f"Error in video generation: {e}")
            view.bot.logger.error(f"Traceback: {traceback.format_exc()}")
            
            try:
                error_embed = discord.Embed(
                    title="❌ Video Generation Failed",
                    description=f"An error occurred during video generation: {str(e)[:200]}{'...' if len(str(e)) > 200 else ''}",
                    color=discord.Color.red()
                )
                await interaction.edit_original_response(embed=error_embed, view=None)
            except:
                # If we can't edit, try followup
                try:
                    await interaction.followup.send("❌ Video generation failed. Please try again.", ephemeral=True)
                except:
                    view.bot.logger.error("Failed to send error response to user") 