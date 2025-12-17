"""
CompleteSetupView for interactive generation setup with all parameters.

Following discord.py View component patterns from Context7.
This is the full implementation that replaces the old CompleteSetupView from bot.py.
"""

from typing import Optional, List, Dict, Any
import discord
from discord.ui import View

from bot.ui.generation.select_menus import ModelSelectMenu, LoRASelectMenu
from bot.ui.generation.buttons import GenerateNowButton, ParameterSettingsButton, LoRAStrengthButton
from bot.ui.generation.modals import ParameterSettingsModal


class CompleteSetupView(View):
    """Complete interactive setup view for all generation parameters.
    
    Following discord.py View patterns from Context7:
    - Proper timeout handling
    - User permission checks
    - Component state management
    """
    
    def __init__(
        self,
        bot,
        prompt: str,
        user_id: int,
        video_mode: bool = False,
        image_data: Optional[bytes] = None
    ):
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
            
            # Add video controls
            from video_ui import VideoParameterSettingsButton, GenerateVideoButton
            self.add_item(VideoParameterSettingsButton())
            self.add_item(GenerateVideoButton())
        else:
            # Image generation parameters - default to flux
            self.model = "flux"
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
            self.dype_exponent = 2.0  # Default for DyPE models
            
            # Add image generation controls
            self.add_item(ModelSelectMenu(self.model))
            # LoRA selector will be added during async initialization if LoRAs are available
            self.add_item(ParameterSettingsButton())
            self.add_item(GenerateNowButton())
            
            # Note: LoRASelectMenu and LoRAStrengthButton will be added dynamically in initialize_default_loras()
        
        # Track setup message for cleanup
        self.setup_message = None
    
    async def initialize_default_loras(self) -> None:
        """Initialize LoRAs for the default flux model."""
        try:
            all_loras = await self.bot.image_generator.get_available_loras()
            self.loras = self.bot.image_generator.filter_loras_by_model(all_loras, self.model)
            
            # Rebuild view completely with LoRAs (like model selection does)
            if self.loras:
                self.clear_items()
                self.add_item(ModelSelectMenu(self.model))
                self.add_item(LoRASelectMenu(self.loras, self.selected_lora))
                if self.selected_lora:
                    self.add_item(LoRAStrengthButton())
                self.add_item(ParameterSettingsButton())
                self.add_item(GenerateNowButton())
                        
        except Exception as e:
            self.bot.logger.error(f"Failed to initialize LoRAs: {e}")
            self.loras = []
    
    async def on_timeout(self) -> None:
        """Discord.py View timeout handler - disable all buttons."""
        for item in self.children:
            item.disabled = True
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Discord.py interaction permission check."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Only the command author can use these controls.",
                ephemeral=True
            )
            return False
        return True
    
    async def generate_now(self, interaction: discord.Interaction) -> None:
        """
        Start generation with current settings.
        
        This method handles the actual generation logic.
        """
        try:
            # Defer interaction to prevent timeout
            if not interaction.response.is_done():
                await interaction.response.defer()
            
            # Get setup message for cleanup later
            setup_message = interaction.message
            
            # Determine workflow based on model
            # Map model names to actual workflow files
            workflow_name = None
            if self.model == "flux":
                workflow_name = "flux_lora"  # flux_lora.json
            elif self.model == "flux_krea":
                workflow_name = "flux_krea_lora"  # flux_krea_lora.json
            elif self.model == "dype_flux_krea":
                workflow_name = "dype_flux_krea_lora"  # dype-flux-krea-lora.json
            elif self.model == "hidream":
                workflow_name = "hidream_lora"  # hidream_lora.json
            elif self.model == "ziturbo":
                workflow_name = "ziturbo"  # ZITURBO1.json

            if not workflow_name:
                await interaction.followup.send(
                    "❌ Selected model is not available.",
                    ephemeral=True
                )
                return

            # Remove the setup view immediately and show starting progress
            model_display = {
                "flux": "Flux",
                "flux_krea": "Flux Krea ✨",
                "dype_flux_krea": "DyPE Flux Krea 🚀",
                "hidream": "HiDream",
                "ziturbo": "ZI Turbo ⚡ NEW"
            }.get(self.model, self.model)
            
            progress_embed = discord.Embed(
                title="🎨 Starting Image Generation...",
                description=f"**Prompt:** {self.prompt[:150]}{'...' if len(self.prompt) > 150 else ''}",
                color=discord.Color.blue()
            )
            
            # Remove view from setup message (like old code)
            await interaction.edit_original_response(embed=progress_embed, view=None)
            
            # Progress callback for updates
            settings_text = (
                f"Model: {model_display} | Size: {self.width}x{self.height} | "
                f"Steps: {self.steps} | CFG: {self.cfg} | Batch: {self.batch_size}"
            )
            if self.selected_lora:
                settings_text += f" | LoRA: {self.selected_lora} ({self.lora_strength})"
            
            progress_callback = await self.bot._create_unified_progress_callback(
                interaction,
                "Image Generation",
                self.prompt,
                settings_text
            )
            
            # Prepare generation parameters
            gen_params = {
                'prompt': self.prompt,
                'negative_prompt': self.negative_prompt,
                'workflow_name': workflow_name,
                'width': self.width,
                'height': self.height,
                'steps': self.steps,
                'cfg': self.cfg,
                'batch_size': self.batch_size,
                'seed': self.seed,
                'lora_name': self.selected_lora,
                'lora_strength': self.lora_strength,
                'progress_callback': progress_callback
            }

            # Add dype_exponent for DyPE models
            if self.model == 'dype_flux_krea':
                gen_params['dype_exponent'] = self.dype_exponent

            # Generate images
            images_list, generation_info = await self.bot.image_generator.generate_image(**gen_params)
            
            # Show result in THE SAME MESSAGE (cleaner UX)
            from bot.ui.generation.post_view import PostGenerationView
            from utils.files import get_unique_filename, save_output_image
            from io import BytesIO
            
            post_view = PostGenerationView(
                bot=self.bot,
                images=images_list,
                generation_info={
                    **generation_info,
                    'model': self.model,
                    'width': self.width,
                    'height': self.height,
                    'steps': self.steps,
                    'cfg': self.cfg,
                    'lora_name': self.selected_lora,
                    'lora_strength': self.lora_strength
                },
                prompt=self.prompt,
                settings_text=settings_text
            )
            
            await post_view.send_images(interaction, model_display)
            
        except Exception as e:
            self.bot.logger.error(f"Error in generate_now: {e}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred during generation. Please try again.",
                    ephemeral=True
                )
            except:
                pass
    
    async def update_model_embed(
        self,
        interaction: discord.Interaction,
        selected_model: str
    ) -> None:
        """Update the embed when model selection changes."""
        try:
            model_display = {
                "flux": "Flux",
                "flux_krea": "Flux Krea ✨",
                "dype_flux_krea": "DyPE Flux Krea 🚀",
                "hidream": "HiDream",
                "ziturbo": "ZI Turbo ⚡ NEW"
            }.get(selected_model, selected_model)
            
            updated_embed = discord.Embed(
                title="🎨 Image Generation Setup",
                description=f"**Prompt:** {self.prompt[:200]}{'...' if len(self.prompt) > 200 else ''}\n\n" +
                           f"**Model:** {model_display}\n" +
                           f"**Size:** {self.width}x{self.height} | **Steps:** {self.steps} | **CFG:** {self.cfg}",
                color=discord.Color.blue()
            )
            
            status_text = f"✅ **Model Selected:** {model_display}\n"
            if self.loras:
                status_text += f"📋 **Available LoRAs:** {len(self.loras)}\n"
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
            
            await interaction.edit_original_response(embed=updated_embed, view=self)
            
        except Exception as e:
            self.bot.logger.error(f"Error updating model embed: {e}")

