"""
Generation modals following discord.py best practices.

Following Context7 discord.py Modal patterns:
- Proper TextInput usage
- Validation in on_submit
- Clean error handling
"""

import discord
from discord.ui import Modal, TextInput

from core.validators.image import StepParameters
from core.exceptions import ValidationError


class LoRAStrengthModal(Modal):
    """Modal for adjusting LoRA strength.
    
    Following discord.py Modal patterns from Context7.
    """
    
    def __init__(self, current_strength: float, view):
        super().__init__(title="Adjust LoRA Strength")
        self.view = view
        self.strength_input = TextInput(
            label="LoRA Strength",
            placeholder="Enter a value between 0.0 and 2.0",
            default=str(current_strength),
            min_length=1,
            max_length=5
        )
        self.add_item(self.strength_input)
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle modal submission with validation."""
        try:
            strength = float(self.strength_input.value)
            
            # Validate strength range
            if not (0.0 <= strength <= 2.0):
                await interaction.response.send_message(
                    "❌ **Invalid strength!** Please enter a value between 0.0 and 2.0.",
                    ephemeral=True
                )
                return
            
            # Update the view's lora_strength
            self.view.lora_strength = strength
            
            # Silently dismiss the modal without showing extra message
            await interaction.response.defer()
            
        except ValueError:
            await interaction.response.send_message(
                "❌ **Invalid input!** Please enter a valid number between 0.0 and 2.0.",
                ephemeral=True
            )
    
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """Handle modal errors following discord.py patterns."""
        await interaction.response.send_message(
            "❌ An error occurred while processing your input. Please try again.",
            ephemeral=True
        )


class ParameterSettingsModal(Modal):
    """Modal for adjusting generation parameters."""
    
    def __init__(self, view, current_settings: dict):
        super().__init__(title="⚙️ Generation Settings")
        self.view = view
        self.current_settings = current_settings

        # Check if this is DyPE model
        is_dype = hasattr(view, 'model') and view.model == 'dype_flux_krea'

        # Width input
        max_dimension = "4096" if is_dype else "2048"
        self.width_input = TextInput(
            label="Width",
            placeholder=f"512-{max_dimension}",
            default=str(current_settings.get('width', 2560 if is_dype else 1024)),
            min_length=3,
            max_length=4,
            required=False
        )
        self.add_item(self.width_input)

        # Height input
        self.height_input = TextInput(
            label="Height",
            placeholder=f"512-{max_dimension}",
            default=str(current_settings.get('height', 2560 if is_dype else 1024)),
            min_length=3,
            max_length=4,
            required=False
        )
        self.add_item(self.height_input)

        # Steps input
        self.steps_input = TextInput(
            label="Steps",
            placeholder="1-150",
            default=str(current_settings.get('steps', 30)),
            min_length=1,
            max_length=3,
            required=False
        )
        self.add_item(self.steps_input)

        # CFG input
        self.cfg_input = TextInput(
            label="CFG Scale",
            placeholder="1.0-20.0",
            default=str(current_settings.get('cfg', 1.0 if is_dype else 5.0)),
            min_length=1,
            max_length=4,
            required=False
        )
        self.add_item(self.cfg_input)

        # For DyPE model, add dype_exponent instead of batch size
        if is_dype:
            self.dype_exponent_input = TextInput(
                label="DyPE Exponent (0.5-4.0)",
                placeholder="Resolution scaling (default: 2.0)",
                default=str(current_settings.get('dype_exponent', 2.0)),
                min_length=1,
                max_length=4,
                required=False
            )
            self.add_item(self.dype_exponent_input)
            self.batch_input = None
        else:
            # Batch size input (not for DyPE)
            self.batch_input = TextInput(
                label="Batch Size",
                placeholder="1-10",
                default=str(current_settings.get('batch_size', 1)),
                min_length=1,
                max_length=2,
                required=False
            )
            self.add_item(self.batch_input)
            self.dype_exponent_input = None
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Validate and update parameters."""
        try:
            # Determine max dimension based on model
            is_dype = hasattr(self.view, 'model') and self.view.model == 'dype_flux_krea'
            max_dimension = 4096 if is_dype else 2048

            # Validate and update width
            if self.width_input.value:
                width = int(self.width_input.value)
                if not (512 <= width <= max_dimension):
                    raise ValidationError(f"Width must be between 512 and {max_dimension}")
                self.view.width = width

            # Validate and update height
            if self.height_input.value:
                height = int(self.height_input.value)
                if not (512 <= height <= max_dimension):
                    raise ValidationError(f"Height must be between 512 and {max_dimension}")
                self.view.height = height

            # Validate steps
            if self.steps_input.value:
                steps = int(self.steps_input.value)
                params = StepParameters(steps=steps)
                self.view.steps = params.steps

            # Validate CFG
            if self.cfg_input.value:
                cfg = float(self.cfg_input.value)
                if not (1.0 <= cfg <= 20.0):
                    raise ValidationError("CFG must be between 1.0 and 20.0")
                self.view.cfg = cfg

            # Validate batch size or dype_exponent
            if self.batch_input and self.batch_input.value:
                batch_size = int(self.batch_input.value)
                if not (1 <= batch_size <= 10):
                    raise ValidationError("Batch size must be between 1 and 10")
                self.view.batch_size = batch_size

            # Validate dype_exponent for DyPE model
            if self.dype_exponent_input and self.dype_exponent_input.value:
                dype_exponent = float(self.dype_exponent_input.value)
                if not (0.5 <= dype_exponent <= 4.0):
                    raise ValidationError("DyPE exponent must be between 0.5 and 4.0")
                self.view.dype_exponent = dype_exponent
            
            # Silently dismiss the modal without showing extra message
            await interaction.response.defer()
            
        except (ValueError, ValidationError) as e:
            await interaction.response.send_message(
                f"❌ **Invalid input:** {str(e)}",
                ephemeral=True
            )
    
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """Handle modal errors."""
        await interaction.response.send_message(
            "❌ An error occurred while processing your settings. Please try again.",
            ephemeral=True
        )


