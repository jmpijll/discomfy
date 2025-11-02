"""
LoRAs command handler.

Following discord.py app_commands best practices from Context7.
"""

import discord
from discord import app_commands


async def loras_command_handler(
    interaction: discord.Interaction,
    bot
) -> None:
    """
    Handle /loras command.
    
    Following Context7 discord.py interaction patterns.
    """
    try:
        if not bot.image_generator:
            await interaction.response.send_message(
                "❌ Image generator not initialized.",
                ephemeral=True
            )
            return
        
        # Get available LoRAs
        try:
            all_loras = await bot.image_generator.get_available_loras()
        except Exception as e:
            bot.logger.error(f"Error fetching LoRAs: {e}")
            await interaction.response.send_message(
                "❌ Failed to fetch LoRAs. Please try again later.",
                ephemeral=True
            )
            return
        
        if not all_loras:
            await interaction.response.send_message(
                "❌ No LoRAs found. Please check your ComfyUI setup.",
                ephemeral=True
            )
            return
        
        # Organize LoRAs by model
        loras_by_model = {
            'flux': [],
            'flux_krea': [],
            'hidream': []
        }
        
        for lora in all_loras:
            model_type = lora.get('model_type', 'flux')
            if model_type in loras_by_model:
                loras_by_model[model_type].append(lora)
        
        # Create embed
        loras_embed = discord.Embed(
            title="🎨 Available LoRAs",
            description="LoRAs organized by compatible model",
            color=discord.Color.purple()
        )
        
        # Add LoRAs for each model
        for model, loras in loras_by_model.items():
            if loras:
                model_display = {
                    'flux': 'Flux',
                    'flux_krea': 'Flux Krea',
                    'hidream': 'HiDream'
                }.get(model, model)
                
                lora_list = '\n'.join([
                    f"• {lora.get('display_name', lora.get('filename', 'Unknown'))}"
                    for lora in loras[:10]  # Limit to 10 per model
                ])
                
                if len(loras) > 10:
                    lora_list += f"\n*...and {len(loras) - 10} more*"
                
                loras_embed.add_field(
                    name=f"{model_display} LoRAs ({len(loras)})",
                    value=lora_list or "None",
                    inline=False
                )
        
        loras_embed.set_footer(text="Select a LoRA when generating images with /generate")
        
        await interaction.response.send_message(embed=loras_embed, ephemeral=True)
        
    except Exception as e:
        bot.logger.error(f"Error in loras command: {e}")
        try:
            await interaction.response.send_message(
                "❌ An error occurred while fetching LoRAs.",
                ephemeral=True
            )
        except:
            pass


