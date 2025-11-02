"""
Status and help command handlers.

Following discord.py app_commands best practices from Context7.
"""

import discord
from discord import app_commands


async def status_command_handler(
    interaction: discord.Interaction,
    bot
) -> None:
    """
    Handle /status command.
    
    Following Context7 discord.py interaction patterns.
    """
    try:
        # Test ComfyUI connection
        is_connected = await bot.image_generator.test_connection() if bot.image_generator else False
        
        # Get queue status
        queue_info = "Unknown"
        try:
            if bot.image_generator and bot.image_generator.session:
                async with bot.image_generator.session.get(
                    f"{bot.image_generator.base_url}/queue"
                ) as response:
                    if response.status == 200:
                        queue_data = await response.json()
                        pending = len(queue_data.get('queue_pending', []))
                        running = len(queue_data.get('queue_running', []))
                        queue_info = f"{pending} pending, {running} running"
        except Exception:
            queue_info = "Unable to fetch"
        
        status_embed = discord.Embed(
            title="🤖 DisComfy Bot Status",
            color=discord.Color.green() if is_connected else discord.Color.red()
        )
        
        status_embed.add_field(
            name="ComfyUI Connection",
            value="✅ Connected" if is_connected else "❌ Disconnected",
            inline=True
        )
        
        status_embed.add_field(
            name="Queue Status",
            value=queue_info,
            inline=True
        )
        
        status_embed.add_field(
            name="Bot Version",
            value="v2.0 (Refactoring)",
            inline=True
        )
        
        await interaction.response.send_message(embed=status_embed, ephemeral=True)
        
    except Exception as e:
        bot.logger.error(f"Error in status command: {e}")
        try:
            await interaction.response.send_message(
                "❌ An error occurred while checking status.",
                ephemeral=True
            )
        except:
            pass


async def help_command_handler(
    interaction: discord.Interaction,
    bot
) -> None:
    """
    Handle /help command.
    
    Following Context7 discord.py interaction patterns.
    """
    try:
        help_embed = discord.Embed(
            title="📚 DisComfy Bot Help",
            description="Commands and features available in this bot.",
            color=discord.Color.blue()
        )
        
        help_embed.add_field(
            name="/generate",
            value="Generate images or videos with interactive setup",
            inline=False
        )
        
        help_embed.add_field(
            name="/editflux",
            value="Edit images using Flux Kontext AI",
            inline=False
        )
        
        help_embed.add_field(
            name="/editqwen",
            value="Edit images using Qwen AI (supports 1-3 images)",
            inline=False
        )
        
        help_embed.add_field(
            name="/status",
            value="Check bot and ComfyUI connection status",
            inline=False
        )
        
        help_embed.add_field(
            name="/loras",
            value="List available LoRAs for image generation",
            inline=False
        )
        
        help_embed.set_footer(text="Use /generate to start creating!")
        
        await interaction.response.send_message(embed=help_embed, ephemeral=True)
        
    except Exception as e:
        bot.logger.error(f"Error in help command: {e}")
        try:
            await interaction.response.send_message(
                "❌ An error occurred while displaying help.",
                ephemeral=True
            )
        except:
            pass


