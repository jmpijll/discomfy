"""
Generation setup view for image/video generation.

Following discord.py View component patterns from Context7:
- Proper timeout handling
- User permission checks
- Component state management
"""

from typing import Optional
import discord
from discord.ui import View

from core.generators.base import GeneratorType


class GenerationSetupView(View):
    """Unified setup view for generation with proper discord.py patterns.
    
    Based on discord.py View component patterns:
    - Proper timeout handling
    - User permission checks
    - Component state management
    """
    
    def __init__(
        self,
        bot,
        prompt: str,
        user_id: int,
        generator_type: GeneratorType = GeneratorType.IMAGE,
        **kwargs
    ):
        # Standard discord.py View timeout (300s = 5 minutes)
        super().__init__(timeout=300)
        self.bot = bot
        self.prompt = prompt
        self.user_id = user_id
        self.generator_type = generator_type
        self.settings = self._get_default_settings(generator_type, **kwargs)
        
        # Add UI components
        self._initialize_components()
    
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
    
    def _get_default_settings(self, generator_type: GeneratorType, **kwargs) -> dict:
        """Get default settings based on generator type."""
        if generator_type == GeneratorType.VIDEO:
            return {
                'frames': kwargs.get('frames', 121),
                'strength': kwargs.get('strength', 0.7),
                'steps': kwargs.get('steps', 4),
            }
        else:
            # Image generation defaults
            return {
                'model': kwargs.get('model', 'flux'),
                'selected_lora': kwargs.get('selected_lora'),
                'lora_strength': kwargs.get('lora_strength', 1.0),
                'negative_prompt': kwargs.get('negative_prompt', ''),
                'width': kwargs.get('width', 1024),
                'height': kwargs.get('height', 1024),
                'steps': kwargs.get('steps', 30),
                'cfg': kwargs.get('cfg', 5.0),
                'batch_size': kwargs.get('batch_size', 1),
                'seed': kwargs.get('seed'),
            }
    
    def _initialize_components(self) -> None:
        """Initialize UI components based on generator type."""
        # This will be populated with actual components in separate files
        pass


