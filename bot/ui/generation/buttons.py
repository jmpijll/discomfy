"""
Generation buttons following discord.py best practices.

Following Context7 discord.py button patterns:
- Proper callback handling
- User permission checks
- Clean interaction responses
"""

from typing import Optional
import discord
from discord.ui import Button

from core.exceptions import ValidationError


class GenerateButton(Button):
    """Button to start generation with selected LoRA.
    
    Following discord.py Button best practices from Context7.
    """
    
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.success,
            label="🎨 Generate Image",
            emoji="✨"
        )
    
    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle button click - start image generation.
        
        Following Context7 interaction response patterns.
        """
        view = self.view
        
        # Check if user is the original requester (via interaction_check)
        # This is handled by the View, but we double-check here for safety
        if hasattr(view, 'user_id') and interaction.user.id != view.user_id:
            await interaction.response.send_message(
                "❌ Only the person who started this generation can use these buttons.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        # Start generation with selected parameters
        if hasattr(view, '_start_generation'):
            await view._start_generation(
                interaction,
                getattr(view, 'selected_lora', None),
                getattr(view, 'lora_strength', 1.0)
            )


class GenerateWithoutLoRAButton(Button):
    """Button to start generation without LoRA."""
    
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label="Generate Without LoRA",
            emoji="🚀"
        )
    
    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle button click - start generation without LoRA."""
        view = self.view
        
        # Permission check
        if hasattr(view, 'user_id') and interaction.user.id != view.user_id:
            await interaction.response.send_message(
                "❌ Only the person who started this generation can use these buttons.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        # Start generation without LoRA
        if hasattr(view, '_start_generation'):
            await view._start_generation(interaction, None, 0.0)


class GenerateNowButton(Button):
    """Button to start image generation with current settings.
    
    Used in CompleteSetupView for immediate generation.
    """
    
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.success,
            label="✨ Generate Now",
            emoji="✨"
        )
    
    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle button click - generate with current settings."""
        view = self.view
        
        # Permission check via View's interaction_check
        if not await view.interaction_check(interaction):
            return
        
        await interaction.response.defer()
        
        # Trigger generation with view's current settings
        if hasattr(view, 'generate_now'):
            await view.generate_now(interaction)
        else:
            await interaction.followup.send(
                "❌ Generation method not available.",
                ephemeral=True
            )


class ParameterSettingsButton(Button):
    """Button to open parameter settings modal."""
    
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="⚙️ Adjust Settings",
            emoji="🔧"
        )
    
    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle button click - show parameter settings modal."""
        view = self.view
        
        # Permission check
        if hasattr(view, 'user_id') and interaction.user.id != view.user_id:
            await interaction.response.send_message(
                "❌ Only the person who started this generation can use these controls.",
                ephemeral=True
            )
            return
        
        # Show parameter settings modal
        from bot.ui.generation.modals import ParameterSettingsModal
        
        current_settings = {
            'width': getattr(view, 'width', 1024),
            'height': getattr(view, 'height', 1024),
            'steps': getattr(view, 'steps', 30),
            'cfg': getattr(view, 'cfg', 5.0),
            'batch_size': getattr(view, 'batch_size', 1),
        }
        
        modal = ParameterSettingsModal(view, current_settings)
        await interaction.response.send_modal(modal)


class LoRAStrengthButton(Button):
    """Button to adjust LoRA strength."""
    
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="⚖️ LoRA Strength",
            emoji="⚖️"
        )
    
    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle button click - show LoRA strength modal."""
        view = self.view
        
        # Permission check
        if hasattr(view, 'user_id') and interaction.user.id != view.user_id:
            await interaction.response.send_message(
                "❌ Only the person who started this generation can use these controls.",
                ephemeral=True
            )
            return
        
        # Show LoRA strength modal
        from bot.ui.generation.modals import LoRAStrengthModal
        
        current_strength = getattr(view, 'lora_strength', 1.0)
        modal = LoRAStrengthModal(current_strength, view)
        await interaction.response.send_modal(modal)
