"""
Image action buttons following discord.py best practices.

Following Context7 discord.py button patterns for post-generation actions.
"""

import discord
from discord.ui import Button

from core.validators.image import ImageValidator
from core.exceptions import ValidationError


class UpscaleButton(Button):
    """Button to upscale an image."""
    
    def __init__(self, label: str = "🔍 Upscale"):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=label
        )
    
    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle upscale button click."""
        view = self.view
        
        # Check rate limiting
        if not view.bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message(
                "❌ You're sending requests too quickly. Please wait a moment.",
                ephemeral=True
            )
            return
        
        # Show upscale parameter modal if view has one
        if hasattr(view, 'show_upscale_modal'):
            await view.show_upscale_modal(interaction)
        else:
            await interaction.response.send_message(
                "🔍 Starting upscaling process...",
                ephemeral=True
            )


class FluxEditButton(Button):
    """Button to edit image with Flux Kontext."""
    
    def __init__(self, label: str = "✏️ Flux Edit"):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=label
        )
    
    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle Flux edit button click."""
        view = self.view
        
        # Check rate limiting
        if not view.bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message(
                "❌ You're sending requests too quickly. Please wait a moment.",
                ephemeral=True
            )
            return
        
        # Show edit modal
        if hasattr(view, 'show_flux_edit_modal'):
            await view.show_flux_edit_modal(interaction)
        else:
            await interaction.response.send_message(
                "Feature not yet implemented",
                ephemeral=True
            )


class QwenEditButton(Button):
    """Button to edit image with Qwen."""
    
    def __init__(self, label: str = "⚡ Qwen Edit"):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=label
        )
    
    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle Qwen edit button click."""
        view = self.view
        
        # Check rate limiting
        if not view.bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message(
                "❌ You're sending requests too quickly. Please wait a moment.",
                ephemeral=True
            )
            return
        
        # Show edit modal
        if hasattr(view, 'show_qwen_edit_modal'):
            await view.show_qwen_edit_modal(interaction)
        else:
            await interaction.response.send_message(
                "Feature not yet implemented",
                ephemeral=True
            )


class AnimateButton(Button):
    """Button to animate an image."""
    
    def __init__(self, label: str = "🎬 Animate"):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=label
        )
    
    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle animate button click."""
        view = self.view
        
        # Check rate limiting
        if not view.bot._check_rate_limit(interaction.user.id):
            await interaction.response.send_message(
                "❌ You're sending requests too quickly. Please wait a moment.",
                ephemeral=True
            )
            return
        
        # Show animation modal
        if hasattr(view, 'show_animation_modal'):
            await view.show_animation_modal(interaction)
        else:
            await interaction.response.send_message(
                "Feature not yet implemented",
                ephemeral=True
            )


