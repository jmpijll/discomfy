"""
Image action modals (upscale, edit, animation parameters).

Following discord.py Modal patterns from Context7.
"""

from typing import Optional
import discord
from discord.ui import Modal, TextInput

from core.validators.image import StepParameters
from core.exceptions import ValidationError


class UpscaleParameterModal(Modal):
    """Modal for configuring upscale parameters."""
    
    def __init__(self, view, image_data: bytes):
        super().__init__(title="🔍 Upscale Parameters")
        self.view = view
        self.image_data = image_data
        
        # Upscale factor input
        self.factor_input = TextInput(
            label="Upscale Factor",
            placeholder="2, 4, or 8 (default: 4)",
            default="4",
            min_length=1,
            max_length=1,
            required=False
        )
        self.add_item(self.factor_input)
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle upscale parameter submission."""
        try:
            factor = int(self.factor_input.value) if self.factor_input.value else 4
            
            # Validate factor
            if factor not in [2, 4, 8]:
                await interaction.response.send_message(
                    "❌ Upscale factor must be 2, 4, or 8.",
                    ephemeral=True
                )
                return
            
            await interaction.response.defer()
            
            # Start upscaling with separate progress message (for concurrent operations)
            progress_embed = discord.Embed(
                title="🔍 Image Upscaling - Starting...",
                description=f"**Upscale Factor:** {factor}x",
                color=discord.Color.blue()
            )
            progress_message = await interaction.followup.send(embed=progress_embed, wait=True)
            
            # Create progress callback that updates the separate message
            async def progress_callback(tracker):
                try:
                    from core.progress.tracker import ProgressTracker, ProgressStatus
                    if isinstance(tracker, ProgressTracker):
                        title_text, _, color = tracker.state.to_user_friendly()
                        percentage = tracker.state.metrics.percentage
                        phase = tracker.state.phase
                        
                        # Create progress bar
                        filled = int(percentage / 5)
                        empty = 20 - filled
                        progress_bar = "█" * filled + "░" * empty
                        
                        embed = discord.Embed(
                            title=f"🔍 Image Upscaling - {title_text}",
                            description=f"**Upscale Factor:** {factor}x",
                            color=color
                        )
                        embed.add_field(
                            name="Progress",
                            value=f"{progress_bar} {percentage:.1f}%",
                            inline=False
                        )
                        
                        await progress_message.edit(embed=embed)
                except Exception as e:
                    pass  # Silently fail to avoid interrupting generation
            
            
            # Perform upscale using new architecture
            from core.generators.base import UpscaleGenerationRequest
            
            request = UpscaleGenerationRequest(
                input_image_data=self.image_data,
                upscale_factor=factor,
                progress_callback=progress_callback
            )
            
            result = await self.view.bot.image_generator.generate(request)
            upscaled_data = result.output_data
            upscale_info = result.generation_info
            
            # Delete progress message since we're sending the final result
            try:
                await progress_message.delete()
            except:
                pass  # Message might already be deleted
            
            # Save and send result
            from utils.files import get_unique_filename, save_output_image
            from io import BytesIO
            
            filename = get_unique_filename(f"upscaled_{interaction.user.id}")
            save_output_image(upscaled_data, filename)
            
            success_embed = discord.Embed(
                title="✅ Image Upscaled Successfully!",
                description=f"Upscaled by **{factor}x**",
                color=discord.Color.green()
            )
            
            file = discord.File(BytesIO(upscaled_data), filename=filename)
            
            # Create new view for upscaled image
            from bot.ui.image.view import IndividualImageView
            upscaled_view = IndividualImageView(
                bot=self.view.bot,
                image_data=upscaled_data,
                generation_info=upscale_info,
                image_index=0
            )
            
            await interaction.followup.send(
                embed=success_embed,
                file=file,
                view=upscaled_view
            )
            
        except (ValueError, ValidationError) as e:
            # Delete progress message on error
            try:
                await progress_message.delete()
            except:
                pass
            await interaction.response.send_message(
                f"❌ Invalid parameter: {str(e)}",
                ephemeral=True
            )
        except Exception as e:
            # Delete progress message on error
            try:
                await progress_message.delete()
            except:
                pass
            self.view.bot.logger.error(f"Error in upscale: {e}")
            await interaction.followup.send(
                f"❌ Failed to upscale image: {str(e)[:200]}",
                ephemeral=True
            )
    
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """Handle modal errors."""
        await interaction.response.send_message(
            "❌ An error occurred while processing your upscale request.",
            ephemeral=True
        )


class EditParameterModal(Modal):
    """Modal for configuring image edit parameters."""
    
    def __init__(self, view, image_data: bytes, edit_type: str = "flux"):
        super().__init__(title=f"✏️ Edit Parameters ({edit_type.title()})")
        self.view = view
        self.image_data = image_data
        self.edit_type = edit_type
        
        # Edit prompt input
        self.prompt_input = TextInput(
            label="Edit Prompt",
            placeholder="Describe what you want to change...",
            required=True,
            max_length=500
        )
        self.add_item(self.prompt_input)
        
        # Steps input
        if edit_type == "flux":
            default_steps = "20"
            steps_range = "10-50"
        else:
            default_steps = "8"
            steps_range = "4-20"
        
        self.steps_input = TextInput(
            label=f"Steps ({steps_range})",
            placeholder=f"Default: {default_steps}",
            default=default_steps,
            min_length=1,
            max_length=2,
            required=False
        )
        self.add_item(self.steps_input)
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle edit parameter submission."""
        try:
            prompt = self.prompt_input.value.strip()
            if not prompt:
                await interaction.response.send_message(
                    "❌ Edit prompt cannot be empty.",
                    ephemeral=True
                )
                return
            
            # Validate steps
            if self.edit_type == "flux":
                min_steps, max_steps = 10, 50
                default_steps = 20
            else:
                min_steps, max_steps = 4, 20
                default_steps = 8
            
            steps = int(self.steps_input.value) if self.steps_input.value else default_steps
            
            try:
                step_params = StepParameters(steps=steps, min_steps=min_steps, max_steps=max_steps)
                steps = step_params.steps
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ Invalid steps: {str(e)}",
                    ephemeral=True
                )
                return
            
            await interaction.response.defer()
            
            # Start editing with separate progress message (for concurrent operations)
            progress_embed = discord.Embed(
                title=f"✏️ Image Editing ({self.edit_type.title()}) - Starting...",
                description=f"**Edit Prompt:** {prompt[:200]}{'...' if len(prompt) > 200 else ''}\n**Steps:** {steps}",
                color=discord.Color.blue()
            )
            progress_message = await interaction.followup.send(embed=progress_embed, wait=True)
            
            # Create progress callback that updates the separate message
            async def progress_callback(tracker):
                try:
                    from core.progress.tracker import ProgressTracker, ProgressStatus
                    if isinstance(tracker, ProgressTracker):
                        title_text, _, color = tracker.state.to_user_friendly()
                        percentage = tracker.state.metrics.percentage
                        phase = tracker.state.phase
                        
                        # Create progress bar
                        filled = int(percentage / 5)
                        empty = 20 - filled
                        progress_bar = "█" * filled + "░" * empty
                        
                        embed = discord.Embed(
                            title=f"✏️ Image Editing ({self.edit_type.title()}) - {title_text}",
                            description=f"**Edit Prompt:** {prompt[:200]}{'...' if len(prompt) > 200 else ''}\n**Steps:** {steps}",
                            color=color
                        )
                        embed.add_field(
                            name="Progress",
                            value=f"{progress_bar} {percentage:.1f}%",
                            inline=False
                        )
                        
                        await progress_message.edit(embed=embed)
                except Exception as e:
                    pass  # Silently fail to avoid interrupting generation
            
            
            # Perform edit using new architecture
            from core.generators.base import EditGenerationRequest
            
            # Set CFG based on edit type
            cfg_value = 2.5 if self.edit_type == "flux" else 1.0
            
            request = EditGenerationRequest(
                input_image_data=self.image_data,
                edit_prompt=prompt,
                workflow_type=self.edit_type,
                width=1024,
                height=1024,
                steps=steps,
                cfg=cfg_value,
                progress_callback=progress_callback
            )
            
            result = await self.view.bot.image_generator.generate(request)
            edited_data = result.output_data
            edit_info = result.generation_info
            
            # Delete progress message since we're sending the final result
            try:
                await progress_message.delete()
            except:
                pass  # Message might already be deleted
            
            # Save and send result
            from utils.files import get_unique_filename, save_output_image
            from io import BytesIO
            
            filename = get_unique_filename(f"edited_{interaction.user.id}")
            save_output_image(edited_data, filename)
            
            success_embed = discord.Embed(
                title=f"✅ Image Edited Successfully ({self.edit_type.title()})!",
                description=f"**Edit Prompt:** {prompt[:200]}{'...' if len(prompt) > 200 else ''}",
                color=discord.Color.green()
            )
            
            file = discord.File(BytesIO(edited_data), filename=filename)
            
            # Create new view for edited image
            from bot.ui.image.view import IndividualImageView
            edited_view = IndividualImageView(
                bot=self.view.bot,
                image_data=edited_data,
                generation_info=edit_info,
                image_index=0
            )
            
            await interaction.followup.send(
                embed=success_embed,
                file=file,
                view=edited_view
            )
            
        except (ValueError, ValidationError) as e:
            # Delete progress message on error
            try:
                await progress_message.delete()
            except:
                pass
            await interaction.response.send_message(
                f"❌ Invalid parameter: {str(e)}",
                ephemeral=True
            )
        except Exception as e:
            # Delete progress message on error
            try:
                await progress_message.delete()
            except:
                pass
            self.view.bot.logger.error(f"Error in edit: {e}")
            await interaction.followup.send(
                f"❌ Failed to edit image: {str(e)[:200]}",
                ephemeral=True
            )
    
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """Handle modal errors."""
        await interaction.response.send_message(
            "❌ An error occurred while processing your edit request.",
            ephemeral=True
        )


class AnimationParameterModal(Modal):
    """Modal for configuring animation parameters."""
    
    def __init__(self, view, image_data: bytes):
        super().__init__(title="🎬 Animation Parameters")
        self.view = view
        self.image_data = image_data
        
        # Frame count input
        self.frames_input = TextInput(
            label="Frame Count (81/121/161)",
            placeholder="81 (2.5s), 121 (3.8s), 161 (5.0s)",
            default="121",
            min_length=2,
            max_length=3,
            required=False
        )
        self.add_item(self.frames_input)
        
        # Animation strength input
        self.strength_input = TextInput(
            label="Animation Strength (0.1-1.0)",
            placeholder="Default: 0.7",
            default="0.7",
            min_length=3,
            max_length=4,
            required=False
        )
        self.add_item(self.strength_input)
        
        # Steps input
        self.steps_input = TextInput(
            label="Sampling Steps (4-50)",
            placeholder="Default: 4",
            default="4",
            min_length=1,
            max_length=2,
            required=False
        )
        self.add_item(self.steps_input)
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle animation parameter submission."""
        try:
            # Validate frames
            frames = int(self.frames_input.value) if self.frames_input.value else 121
            if frames not in [81, 121, 161]:
                await interaction.response.send_message(
                    "❌ Frame count must be 81, 121, or 161.",
                    ephemeral=True
                )
                return
            
            # Validate strength
            strength = float(self.strength_input.value) if self.strength_input.value else 0.7
            if not (0.1 <= strength <= 1.0):
                await interaction.response.send_message(
                    "❌ Animation strength must be between 0.1 and 1.0.",
                    ephemeral=True
                )
                return
            
            # Validate steps
            steps = int(self.steps_input.value) if self.steps_input.value else 4
            if not (4 <= steps <= 50):
                await interaction.response.send_message(
                    "❌ Steps must be between 4 and 50.",
                    ephemeral=True
                )
                return
            
            await interaction.response.defer()
            
            # Start animation with separate progress message (for concurrent operations)
            duration = round(frames / 32.0, 1)  # 32 FPS
            
            # Send initial progress message
            progress_embed = discord.Embed(
                title="🎬 Video Animation - Starting...",
                description=f"**Frames:** {frames} ({duration}s) | **Strength:** {strength} | **Steps:** {steps}",
                color=discord.Color.blue()
            )
            progress_message = await interaction.followup.send(embed=progress_embed, wait=True)
            
            # Create progress callback that updates the separate message
            async def progress_callback(tracker):
                try:
                    from core.progress.tracker import ProgressTracker, ProgressStatus
                    if isinstance(tracker, ProgressTracker):
                        title_text, _, color = tracker.state.to_user_friendly()
                        percentage = tracker.state.metrics.percentage
                        phase = tracker.state.phase
                        
                        # Create progress bar
                        filled = int(percentage / 5)
                        empty = 20 - filled
                        progress_bar = "█" * filled + "░" * empty
                        
                        embed = discord.Embed(
                            title=f"🎬 Video Animation - {title_text}",
                            description=f"**Frames:** {frames} ({duration}s) | **Strength:** {strength} | **Steps:** {steps}",
                            color=color
                        )
                        embed.add_field(
                            name="Progress",
                            value=f"{progress_bar} {percentage:.1f}%",
                            inline=False
                        )
                        
                        await progress_message.edit(embed=embed)
                except Exception as e:
                    pass  # Silently fail to avoid interrupting generation
            
            
            # Perform animation
            if not self.view.bot.video_generator:
                await interaction.followup.send(
                    "❌ Video generator not available.",
                    ephemeral=True
                )
                return
            
            video_data, video_filename, video_info = await self.view.bot.video_generator.generate_video(
                prompt="Animated from image",
                negative_prompt="",
                workflow_name="video_wan_vace_14B_i2v",
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
            
            # Delete progress message since we're sending the final result
            try:
                await progress_message.delete()
            except:
                pass  # Message might already be deleted
            
            # Save and send result
            from utils.files import get_unique_video_filename, save_output_video
            from io import BytesIO
            
            filename = get_unique_video_filename(f"animated_{interaction.user.id}")
            save_output_video(video_data, filename)
            
            success_embed = discord.Embed(
                title="✅ Animation Created Successfully!",
                description=f"**Frames:** {frames} ({duration}s video)",
                color=discord.Color.green()
            )
            
            file = discord.File(BytesIO(video_data), filename=filename)
            await interaction.followup.send(
                embed=success_embed,
                file=file
            )
            
        except (ValueError, ValidationError) as e:
            # Delete progress message on error
            try:
                await progress_message.delete()
            except:
                pass
            await interaction.response.send_message(
                f"❌ Invalid parameter: {str(e)}",
                ephemeral=True
            )
        except Exception as e:
            # Delete progress message on error
            try:
                await progress_message.delete()
            except:
                pass
            self.view.bot.logger.error(f"Error in animation: {e}")
            await interaction.followup.send(
                f"❌ Failed to animate image: {str(e)[:200]}",
                ephemeral=True
            )
    
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """Handle modal errors."""
        await interaction.response.send_message(
            "❌ An error occurred while processing your animation request.",
            ephemeral=True
        )


