"""
IndividualImageView for post-generation image actions.

Following discord.py View component patterns from Context7.
"""

from typing import Dict, Any
from io import BytesIO

import discord
from discord.ui import View, Button

from core.validators.image import ImageValidator
from core.exceptions import ValidationError
from utils.files import get_unique_filename, save_output_image


class IndividualImageView(View):
    """View for individual images with action buttons.
    
    Following discord.py View patterns from Context7:
    - No timeout for post-generation actions
    - Proper callback handling
    - User permission checks
    """
    
    def __init__(self, bot, image_data: bytes, generation_info: Dict[str, Any], image_index: int):
        super().__init__(timeout=None)  # No timeout for post-generation actions
        self.bot = bot
        self.image_data = image_data
        self.generation_info = generation_info
        self.image_index = image_index
        
        # Create buttons using the extracted button classes
        from bot.ui.image.buttons import (
            UpscaleButton, FluxEditButton, QwenEditButton, AnimateButton
        )
        
        upscale_btn = UpscaleButton(label=f"🔍 Upscale #{image_index + 1}")
        upscale_btn.callback = self.upscale_button_callback
        
        flux_edit_btn = FluxEditButton(label=f"✏️ Flux Edit #{image_index + 1}")
        flux_edit_btn.callback = self.flux_edit_button_callback
        
        qwen_edit_btn = QwenEditButton(label=f"⚡ Qwen Edit #{image_index + 1}")
        qwen_edit_btn.callback = self.qwen_edit_button_callback
        
        animate_btn = AnimateButton(label=f"🎬 Animate #{image_index + 1}")
        animate_btn.callback = self.animate_button_callback
        
        self.add_item(upscale_btn)
        self.add_item(flux_edit_btn)
        self.add_item(qwen_edit_btn)
        self.add_item(animate_btn)
    
    async def upscale_button_callback(self, interaction: discord.Interaction) -> None:
        """Handle upscale button click."""
        # Check rate limiting
        if not self.bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message(
                "❌ You're sending requests too quickly. Please wait a moment.",
                ephemeral=True
            )
            return
        
        # Show upscale parameter modal
        from bot.ui.image.modals import UpscaleParameterModal
        modal = UpscaleParameterModal(self, self.image_data)
        await interaction.response.send_modal(modal)
    
    async def flux_edit_button_callback(self, interaction: discord.Interaction) -> None:
        """Handle Flux edit button click."""
        # Check rate limiting
        if not self.bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message(
                "❌ You're sending requests too quickly. Please wait a moment.",
                ephemeral=True
            )
            return
        
        # Show edit modal
        from bot.ui.image.modals import EditParameterModal
        modal = EditParameterModal(self, self.image_data, edit_type="flux")
        await interaction.response.send_modal(modal)
    
    async def qwen_edit_button_callback(self, interaction: discord.Interaction) -> None:
        """Handle Qwen edit button click."""
        # Check rate limiting
        if not self.bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message(
                "❌ You're sending requests too quickly. Please wait a moment.",
                ephemeral=True
            )
            return
        
        # Show edit modal
        from bot.ui.image.modals import EditParameterModal
        modal = EditParameterModal(self, self.image_data, edit_type="qwen")
        await interaction.response.send_modal(modal)
    
    async def animate_button_callback(self, interaction: discord.Interaction) -> None:
        """Handle animate button click."""
        # Check rate limiting
        if not self.bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message(
                "❌ You're sending requests too quickly. Please wait a moment.",
                ephemeral=True
            )
            return
        
        # Show animation modal
        from bot.ui.image.modals import AnimationParameterModal
        modal = AnimationParameterModal(self, self.image_data)
        await interaction.response.send_modal(modal)


