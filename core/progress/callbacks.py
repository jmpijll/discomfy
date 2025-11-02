"""
Progress callback creators for Discord integration.

Following discord.py interaction patterns from Context7.
"""

from typing import Callable, Optional
import discord
import asyncio

from core.progress.tracker import ProgressTracker, ProgressStatus
from core.exceptions import DisComfyError

# Import old ProgressInfo for backward compatibility (lazy import)
# ProgressInfo will be imported only when needed


async def create_discord_progress_callback(
    interaction: discord.Interaction,
    title: str,
    prompt: str,
    settings: str,
    tracker: Optional[ProgressTracker] = None
) -> Callable:
    """
    Create a progress callback that updates Discord messages.
    
    Following Context7 discord.py interaction response patterns.
    Progress message is automatically deleted when generation completes.
    
    Args:
        interaction: Discord interaction to respond to
        title: Title for progress embed
        prompt: Generation prompt
        settings: Settings description
        tracker: Optional progress tracker (creates one if not provided)
        
    Returns:
        Async callback function that accepts progress updates
    """
    tracker = tracker or ProgressTracker()
    last_update_time = 0  # Start at 0 to allow immediate first update
    update_interval = 1.0  # Update every 1 second minimum
    
    # NOTE: We don't send an initial message here!
    # The caller (complete_setup_view) already edited the original response.
    # We'll just keep editing that same message.
    
    async def progress_callback(progress) -> None:
        """
        Update Discord message with progress by editing the original response.
        
        Args:
            progress: ProgressInfo or ProgressTracker instance
        """
        nonlocal last_update_time
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔔 PROGRESS CALLBACK INVOKED! Type: {type(progress).__name__}")
        
        try:
            # Handle both old ProgressInfo and new ProgressTracker
            is_completed = False
            try:
                # Try new ProgressTracker first
                if isinstance(progress, ProgressTracker):
                    title_text, description, color = progress.state.to_user_friendly()
                    percentage = progress.state.metrics.percentage
                    phase = progress.state.phase
                    is_completed = progress.state.status == ProgressStatus.COMPLETED
                elif hasattr(progress, 'get_user_friendly_status'):
                    # Old ProgressInfo (lazy import)
                    title_text, description, color = progress.get_user_friendly_status()
                    percentage = progress.percentage
                    phase = progress.phase
                    is_completed = getattr(progress, 'status', '') == 'completed'
                else:
                    # Unknown type, skip
                    import logging
                    logging.getLogger(__name__).warning(f"Unknown progress type: {type(progress)}")
                    return
            except Exception as e:
                # If anything fails, skip update
                import logging
                logging.getLogger(__name__).error(f"Error parsing progress: {e}", exc_info=True)
                return
            
            # Check update interval for regular updates  
            current_time = asyncio.get_event_loop().time()
            if current_time - last_update_time < update_interval:
                return
            
            # Create updated embed
            embed = discord.Embed(
                title=f"{title} - {title_text}",
                description=f"**Prompt:** {prompt[:150]}{'...' if len(prompt) > 150 else ''}",
                color=color
            )
            
            # Create progress bar (like old code)
            filled = int(percentage / 5)  # 20 blocks for 100%
            empty = 20 - filled
            progress_bar = "█" * filled + "░" * empty
            
            embed.add_field(
                name="Progress",
                value=f"{progress_bar} {percentage:.1f}%",
                inline=False
            )
            
            # Always edit the original response (like old working code)
            try:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"📤 Attempting to update Discord: {percentage:.1f}% - {phase}")
                logger.debug(f"   Interaction.response.is_done()={interaction.response.is_done()}")
                logger.debug(f"   Interaction.type={interaction.type}")
                
                await interaction.edit_original_response(embed=embed)
                last_update_time = current_time
                logger.info(f"✅ Updated Discord progress: {percentage:.1f}% - {phase}")
            except discord.NotFound as e:
                # Interaction expired - this shouldn't happen if we update frequently enough
                import logging
                logging.getLogger(__name__).error(f"❌ Interaction expired: {e}")
            except discord.HTTPException as e:
                # Other Discord error
                import logging
                logging.getLogger(__name__).error(f"❌ Failed to update Discord message: {e}")
                
        except Exception as e:
            # Silently fail to avoid spamming errors
            pass
    
    return progress_callback

