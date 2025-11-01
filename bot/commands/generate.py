"""
/generate command handler.

Following discord.py app_commands best practices from Context7.
"""

from typing import Optional
import discord
from discord import app_commands

from core.validators.image import ImageValidator, PromptParameters
from core.exceptions import ValidationError
from core.generators.base import GeneratorType
from bot.ui.generation.complete_setup_view import CompleteSetupView


async def generate_command_handler(
    interaction: discord.Interaction,
    bot,
    prompt: str,
    image: Optional[discord.Attachment] = None
) -> None:
    """
    Handle /generate command.
    
    Following Context7 discord.py interaction patterns:
    - Proper interaction response
    - Clean error handling
    - User-friendly messages
    """
    try:
        # Validate rate limit
        if not bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message(
                "❌ You're sending requests too quickly. Please wait a moment.",
                ephemeral=True
            )
            return
        
        # Validate prompt using Pydantic
        try:
            prompt_params = PromptParameters(prompt=prompt)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Invalid prompt: {str(e)}",
                ephemeral=True
            )
            return
        
        # Check if image provided (for video generation)
        if image:
            # Validate image
            validator = ImageValidator(bot.config.discord.max_file_size_mb)
            validation = validator.validate(image)
            
            if not validation.is_valid:
                await interaction.response.send_message(
                    validation.error_message,
                    ephemeral=True
                )
                return
            
            # Video generation mode
            await interaction.response.send_message(
                "🎬 Video generation mode starting...",
                ephemeral=True
            )
        else:
            # Image generation mode - show setup view
            setup_view = CompleteSetupView(
                bot=bot,
                prompt=prompt_params.prompt,
                user_id=interaction.user.id,
                video_mode=False
            )
            
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
            
            await interaction.response.send_message(
                embed=setup_embed,
                view=setup_view
            )
            
            # Initialize default LoRAs and update the message to show them
            await setup_view.initialize_default_loras()
            
            # Update the message with LoRA menu visible
            if setup_view.loras:
                await interaction.edit_original_response(view=setup_view)
            
    except Exception as e:
        bot.logger.error(f"Error in generate command: {e}")
        try:
            if interaction.response.is_done():
                await interaction.followup.send(
                    "❌ An error occurred. Please try again.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ An error occurred. Please try again.",
                    ephemeral=True
                )
        except:
            pass

