"""
Edit command handlers (/editflux, /editqwen).

Following discord.py app_commands best practices from Context7.
"""

from typing import Optional
import discord
from discord import app_commands
from io import BytesIO

from core.validators.image import ImageValidator, PromptParameters, StepParameters
from core.exceptions import ValidationError
from bot.ui.image.buttons import FluxEditButton, QwenEditButton


async def editflux_command_handler(
    interaction: discord.Interaction,
    bot,
    image: discord.Attachment,
    prompt: str,
    steps: Optional[int] = 20
) -> None:
    """
    Handle /editflux command.
    
    Following Context7 discord.py interaction patterns.
    """
    try:
        # Validate rate limit
        if not bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message(
                "❌ You're making requests too quickly. Please wait a moment.",
                ephemeral=True
            )
            return
        
        # Validate image using validator
        validator = ImageValidator(bot.config.discord.max_file_size_mb)
        validation = validator.validate(image)
        
        if not validation.is_valid:
            await interaction.response.send_message(
                validation.error_message,
                ephemeral=True
            )
            return
        
        # Validate prompt
        try:
            prompt_params = PromptParameters(prompt=prompt)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Invalid prompt: {str(e)}",
                ephemeral=True
            )
            return
        
        # Validate steps
        if steps is not None:
            try:
                step_params = StepParameters(steps=steps, min_steps=10, max_steps=50)
                steps = step_params.steps
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ Invalid steps: {str(e)}",
                    ephemeral=True
                )
                return
        else:
            steps = 20
        
        # Send initial response
        initial_embed = discord.Embed(
            title="✏️ Starting Image Edit - Flux Kontext",
            description=f"**Edit Prompt:** {prompt[:150]}{'...' if len(prompt) > 150 else ''}",
            color=discord.Color.orange()
        )
        
        initial_embed.add_field(
            name="Settings",
            value=f"**Model:** Flux Kontext\n**Steps:** {steps}\n**CFG:** 2.5",
            inline=True
        )
        
        await interaction.response.send_message(embed=initial_embed)
        
        # Download image
        image_data = await image.read()
        
        # Create progress callback
        progress_callback = await bot._create_unified_progress_callback(
            interaction,
            "Image Editing",
            prompt_params.prompt,
            f"Method: Flux Kontext | Steps: {steps} | CFG: 2.5"
        )
        
        # Perform edit using new architecture
        from core.generators.base import EditGenerationRequest
        
        request = EditGenerationRequest(
            input_image_data=image_data,
            edit_prompt=prompt_params.prompt,
            workflow_type="flux",
            width=1024,
            height=1024,
            steps=steps,
            cfg=2.5,
            progress_callback=progress_callback
        )
        
        result = await bot.image_generator.generate(request)
        edited_data = result.output_data
        edit_info = result.generation_info
        
        # Delete progress message since we're sending the final result
        try:
            await interaction.delete_original_response()
        except:
            pass  # Message might already be deleted
        
        # Save and send result
        from utils.files import save_output_image, get_unique_filename
        filename = get_unique_filename(f"edited_{interaction.user.id}", extension=".png")
        save_output_image(edited_data, filename)
        
        success_embed = discord.Embed(
            title="✅ Image Edited Successfully!",
            description="Your image has been edited using **Flux Kontext**",
            color=discord.Color.green()
        )
        
        success_embed.add_field(
            name="Edit Details",
            value=f"**Prompt:** {prompt[:200]}{'...' if len(prompt) > 200 else ''}\n**Steps:** {steps}",
            inline=False
        )
        
        # Send edited image
        file = discord.File(BytesIO(edited_data), filename=filename)
        await interaction.followup.send(
            embed=success_embed,
            file=file
        )
        
    except Exception as e:
        bot.logger.error(f"Error in editflux command: {e}")
        # Delete progress message on error
        try:
            await interaction.delete_original_response()
        except:
            pass
        try:
            await interaction.followup.send(
                f"❌ Error: {str(e)[:200]}",
                ephemeral=True
            )
        except:
            pass


async def editqwen_command_handler(
    interaction: discord.Interaction,
    bot,
    image: discord.Attachment,
    prompt: str,
    image2: Optional[discord.Attachment] = None,
    image3: Optional[discord.Attachment] = None,
    steps: Optional[int] = 8
) -> None:
    """
    Handle /editqwen command.
    
    Following Context7 discord.py interaction patterns.
    """
    try:
        # Validate rate limit
        if not bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message(
                "❌ You're making requests too quickly. Please wait a moment.",
                ephemeral=True
            )
            return
        
        # Validate images
        validator = ImageValidator(bot.config.discord.max_file_size_mb)
        
        # Primary image
        validation = validator.validate(image)
        if not validation.is_valid:
            await interaction.response.send_message(
                validation.error_message,
                ephemeral=True
            )
            return
        
        # Additional images
        additional_images = []
        if image2:
            validation = validator.validate(image2)
            if not validation.is_valid:
                await interaction.response.send_message(
                    f"Image 2: {validation.error_message}",
                    ephemeral=True
                )
                return
            additional_images.append(image2)
        
        if image3:
            if not image2:
                await interaction.response.send_message(
                    "❌ Cannot provide image3 without image2!",
                    ephemeral=True
                )
                return
            validation = validator.validate(image3)
            if not validation.is_valid:
                await interaction.response.send_message(
                    f"Image 3: {validation.error_message}",
                    ephemeral=True
                )
                return
            additional_images.append(image3)
        
        # Validate prompt
        try:
            prompt_params = PromptParameters(prompt=prompt)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Invalid prompt: {str(e)}",
                ephemeral=True
            )
            return
        
        # Validate steps
        if steps is not None:
            try:
                step_params = StepParameters(steps=steps, min_steps=4, max_steps=20)
                steps = step_params.steps
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ Invalid steps: {str(e)}",
                    ephemeral=True
                )
                return
        else:
            steps = 8
        
        # Download images
        image_data = await image.read()
        additional_image_data = []
        for img in additional_images:
            additional_image_data.append(await img.read())
        
        # Send initial response
        initial_embed = discord.Embed(
            title="✏️ Starting Qwen Image Edit",
            description=f"**Edit Prompt:** {prompt[:150]}{'...' if len(prompt) > 150 else ''}",
            color=discord.Color.blue()
        )
        
        initial_embed.add_field(
            name="Input Images",
            value=f"**Primary:** {image.filename}\n**Additional:** {len(additional_images)}",
            inline=True
        )
        
        initial_embed.add_field(
            name="Settings",
            value=f"**Model:** Qwen\n**Steps:** {steps}\n**CFG:** 1.0",
            inline=True
        )
        
        await interaction.response.send_message(embed=initial_embed)
        
        # Create progress callback
        progress_callback = await bot._create_unified_progress_callback(
            interaction,
            "Qwen Image Editing",
            prompt_params.prompt,
            f"Images: {1 + len(additional_image_data)} | Steps: {steps}"
        )
        
        # Perform edit using new architecture
        from core.generators.base import EditGenerationRequest
        
        request = EditGenerationRequest(
            input_image_data=image_data,
            edit_prompt=prompt_params.prompt,
            workflow_type="qwen",
            steps=steps,
            cfg=1.0,  # Qwen uses CFG=1.0
            progress_callback=progress_callback
        )
        
        result = await bot.image_generator.generate(request)
        edited_data = result.output_data
        edit_info = result.generation_info
        
        # Delete progress message since we're sending the final result
        try:
            await interaction.delete_original_response()
        except:
            pass  # Message might already be deleted
        
        # Save and send result
        from utils.files import save_output_image, get_unique_filename
        filename = get_unique_filename(f"qwen_edited_{interaction.user.id}", extension=".png")
        save_output_image(edited_data, filename)
        
        success_embed = discord.Embed(
            title="✅ Image Edited Successfully!",
            description="Your image has been edited using **Qwen Image Edit**",
            color=discord.Color.green()
        )
        
        file = discord.File(BytesIO(edited_data), filename=filename)
        await interaction.followup.send(
            embed=success_embed,
            file=file
        )
        
    except Exception as e:
        bot.logger.error(f"Error in editqwen command: {e}")
        # Delete progress message on error
        try:
            await interaction.delete_original_response()
        except:
            pass
        try:
            await interaction.followup.send(
                f"❌ Error: {str(e)[:200]}",
                ephemeral=True
            )
        except:
            pass

