"""
PostGenerationView for displaying generated images with actions.

Following discord.py View component patterns from Context7.
"""

from typing import List, Dict, Any, Optional
from io import BytesIO

import discord
from discord.ui import View

from bot.ui.image.view import IndividualImageView
from utils.files import get_unique_filename, save_output_image


class PostGenerationView(View):
    """View for post-generation actions on multiple images.
    
    Following discord.py View patterns from Context7:
    - No timeout for post-generation actions
    - Proper callback handling
    - User permission checks
    """
    
    def __init__(
        self,
        bot,
        images: List[bytes],
        generation_info: Dict[str, Any],
        prompt: str,
        settings_text: str
    ):
        super().__init__(timeout=None)  # No timeout for post-generation actions
        self.bot = bot
        self.images = images
        self.generation_info = generation_info
        self.prompt = prompt
        self.settings_text = settings_text
    
    async def send_images(self, interaction: discord.Interaction, model_display: str) -> None:
        """
        Send all generated images with individual action views.
        
        Args:
            interaction: Discord interaction
            model_display: Display name of the model used
        """
        for i, image_data in enumerate(self.images):
            # Save image
            filename = get_unique_filename(f"discord_{interaction.user.id}_{i}")
            save_output_image(image_data, filename)
            
            # Create embed for each image
            embed = discord.Embed(
                title=f"✅ Image {i+1} Generated - {model_display}!",
                description=f"**Prompt:** {self.prompt[:200]}{'...' if len(self.prompt) > 200 else ''}",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="Generation Details",
                value=self.settings_text,
                inline=False
            )
            
            embed.set_footer(text=f"Image {i+1} of {len(self.images)} | Requested by {interaction.user.display_name}")
            
            # Create view with action buttons for this image
            individual_view = IndividualImageView(
                bot=self.bot,
                image_data=image_data,
                generation_info={**self.generation_info, 'image_index': i},
                image_index=i
            )
            
            # Send image
            file = discord.File(BytesIO(image_data), filename=filename)
            
            if i == 0:
                # First image - EDIT THE ORIGINAL RESPONSE (same message throughout!)
                await interaction.edit_original_response(
                    embed=embed,
                    attachments=[file],
                    view=individual_view
                )
                self.bot.logger.info(f"✅ Edited original message with result image")
            else:
                # Additional images - send as followup
                await interaction.followup.send(embed=embed, file=file, view=individual_view)
                self.bot.logger.info(f"✅ Sent additional image {i+1} as followup")
