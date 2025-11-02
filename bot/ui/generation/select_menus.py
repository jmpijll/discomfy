"""
Generation select menus following discord.py best practices.

Following Context7 discord.py Select patterns:
- Proper option handling
- Clean callback implementation
"""

from typing import List, Optional
import discord
from discord.ui import Select
from discord import SelectOption


class ModelSelectMenu(Select):
    """Select menu for choosing generation model.
    
    Following discord.py Select best practices from Context7.
    """
    
    def __init__(self, current_model: str = "flux"):
        options = [
            SelectOption(
                label="Flux (Fast)",
                description="Fast high-quality generation",
                value="flux",
                emoji="⚡",
                default=(current_model == "flux")
            ),
            SelectOption(
                label="Flux Krea ✨ NEW",
                description="Enhanced creative generation",
                value="flux_krea",
                emoji="✨",
                default=(current_model == "flux_krea")
            ),
            SelectOption(
                label="HiDream",
                description="High-dream quality generation",
                value="hidream",
                emoji="🎨",
                default=(current_model == "hidream")
            ),
        ]
        
        super().__init__(
            placeholder="Select Model...",
            options=options,
            min_values=1,
            max_values=1
        )
    
    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle model selection.
        
        Following Context7 interaction response patterns.
        """
        view = self.view
        
        # Permission check
        if hasattr(view, 'user_id') and interaction.user.id != view.user_id:
            await interaction.response.send_message(
                "❌ Only the person who started this generation can use these controls.",
                ephemeral=True
            )
            return
        
        selected_model = self.values[0]
        
        # Defer interaction first
        await interaction.response.defer()
        
        try:
            # Update view's model and apply model-specific defaults
            view.model = selected_model
            
            # Apply model-specific defaults (from old working code)
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
            
            # Clear ALL items and rebuild view (like old code)
            view.clear_items()
            
            # Add model select menu with correct default
            view.add_item(ModelSelectMenu(current_model=selected_model))
            
            # Add LoRA selection if available
            if view.loras:
                view.add_item(LoRASelectMenu(view.loras, view.selected_lora))
                # Add LoRA strength button if a LoRA is selected
                if view.selected_lora:
                    from bot.ui.generation.buttons import LoRAStrengthButton
                    view.add_item(LoRAStrengthButton())
            
            # Add parameter settings and generate buttons
            from bot.ui.generation.buttons import ParameterSettingsButton, GenerateNowButton
            view.add_item(ParameterSettingsButton())
            view.add_item(GenerateNowButton())
            
            view.bot.logger.info(f"✅ Updated view for model '{selected_model}' with {len(view.loras)} LoRAs")
            
            # Update embed if view has method to do so
            if hasattr(view, 'update_model_embed'):
                await view.update_model_embed(interaction, selected_model)
                
        except Exception as e:
            view.bot.logger.error(f"Error in model selection: {e}")
            try:
                await interaction.followup.send(
                    f"❌ Error updating model: {str(e)[:100]}...",
                    ephemeral=True
                )
            except:
                pass


class LoRASelectMenu(Select):
    """Select menu for choosing LoRA.
    
    Following discord.py Select best practices from Context7.
    """
    
    def __init__(self, loras: List[dict], current_lora: Optional[str] = None):
        if loras:
            options = []
            for lora in loras[:25]:  # Discord limit: 25 options
                # LoRAs have 'filename' and 'display_name' keys
                lora_filename = lora.get('filename', 'Unknown')
                lora_display = lora.get('display_name', lora_filename)
                options.append(
                    SelectOption(
                        label=lora_display[:100],  # Discord label limit
                        description=f"LoRA: {lora_filename[:100]}",
                        value=lora_filename,
                        default=(current_lora == lora_filename)
                    )
                )
            
            # Add "None" option
            options.insert(0, SelectOption(
                label="None",
                description="No LoRA",
                value="none",
                default=(current_lora is None)
            ))
        else:
            options = [
                SelectOption(
                    label="No LoRAs Available",
                    description="No LoRAs found for this model",
                    value="none",
                    disabled=True
                )
            ]
        
        super().__init__(
            placeholder="Select LoRA...",
            options=options,
            min_values=1,
            max_values=1
        )
    
    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle LoRA selection."""
        view = self.view
        
        # Permission check
        if hasattr(view, 'user_id') and interaction.user.id != view.user_id:
            await interaction.response.send_message(
                "❌ Only the person who started this generation can use these controls.",
                ephemeral=True
            )
            return
        
        selected_lora = self.values[0]
        
        # Defer the interaction
        await interaction.response.defer()
        
        # Update view's selected LoRA
        if hasattr(view, 'selected_lora'):
            if selected_lora == "none":
                view.selected_lora = None
            else:
                view.selected_lora = selected_lora
        
        # Rebuild view to add/remove LoRA strength button
        if hasattr(view, 'bot') and hasattr(view.bot, 'image_generator'):
            try:
                # Clear and rebuild
                view.clear_items()
                
                # Add model select menu
                from bot.ui.generation.select_menus import ModelSelectMenu
                view.add_item(ModelSelectMenu(current_model=view.model if hasattr(view, 'model') else 'flux'))
                
                # Add LoRA select menu
                if hasattr(view, 'loras') and view.loras:
                    view.add_item(LoRASelectMenu(view.loras, view.selected_lora))
                    
                    # Add LoRA strength button if a LoRA is selected
                    if view.selected_lora:
                        from bot.ui.generation.buttons import LoRAStrengthButton
                        view.add_item(LoRAStrengthButton())
                
                # Add parameter settings and generate buttons
                from bot.ui.generation.buttons import ParameterSettingsButton, GenerateNowButton
                view.add_item(ParameterSettingsButton())
                view.add_item(GenerateNowButton())
                
                # Update the message with new view
                await interaction.edit_original_response(view=view)
                
            except Exception as e:
                if hasattr(view, 'bot'):
                    view.bot.logger.error(f"Error updating LoRA selection: {e}")

