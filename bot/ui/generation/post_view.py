"""
PostGenerationView for displaying generated images with actions.

Following discord.py View component patterns from Context7.
"""

from typing import List, Dict, Any, Optional
from io import BytesIO

import discord
from discord.ui import View
from PIL import Image

from bot.ui.image.view import IndividualImageView
from utils.files import get_unique_filename, save_output_image


class PostGenerationView(View):
    """View for post-generation actions on multiple images.
    
    Following discord.py View patterns from Context7:
    - No timeout for post-generation actions
    - Proper callback handling
    - User permission checks
    """
    
    def __init__(
        self,
        bot,
        images: List[bytes],
        generation_info: Dict[str, Any],
        prompt: str,
        settings_text: str
    ):
        super().__init__(timeout=None)  # No timeout for post-generation actions
        self.bot = bot
        self.images = images
        self.generation_info = generation_info
        self.prompt = prompt
        self.settings_text = settings_text
        self.MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB Discord limit for regular users

    def _compress_image_if_needed(self, image_data: bytes, filename: str) -> tuple[bytes, str]:
        """
        Compress image if it exceeds Discord's 10MB file size limit.
        Uses lossless PNG optimization first, then falls back to high-quality JPEG if needed.

        Args:
            image_data: Original image data (PNG from ComfyUI)
            filename: Original filename

        Returns:
            Tuple of (compressed_data, new_filename)
        """
        original_size_mb = len(image_data) / 1024 / 1024

        # Only compress if image exceeds 10MB
        if len(image_data) <= self.MAX_FILE_SIZE:
            self.bot.logger.debug(f"Image size {original_size_mb:.1f}MB is within Discord's 10MB limit, no compression needed")
            return image_data, filename

        # Image is too large, attempt lossless compression
        self.bot.logger.warning(f"Image size {original_size_mb:.1f}MB exceeds Discord's 10MB limit, compressing...")

        try:
            # Load image
            img = Image.open(BytesIO(image_data))

            # Try PNG optimization first (lossless)
            # PNG compression levels: 0 (no compression) to 9 (max compression)
            for compress_level in [9, 6, 3]:  # Try maximum, medium, low compression
                output = BytesIO()
                img.save(output, format='PNG', optimize=True, compress_level=compress_level)
                compressed_data = output.getvalue()
                compressed_size_mb = len(compressed_data) / 1024 / 1024

                if len(compressed_data) <= self.MAX_FILE_SIZE:
                    self.bot.logger.info(f"✅ Lossless PNG compression: {original_size_mb:.1f}MB → {compressed_size_mb:.1f}MB (level {compress_level})")
                    return compressed_data, filename

            # If PNG optimization didn't work, fall back to high-quality JPEG
            self.bot.logger.warning(f"PNG optimization insufficient, converting to JPEG...")

            # Convert to RGB if necessary (JPEG doesn't support alpha)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background

            # Progressive quality reduction for JPEG
            for quality in [98, 95, 92, 88, 85, 82, 78, 75, 70, 65, 60]:
                output = BytesIO()
                img.save(output, format='JPEG', quality=quality, optimize=True, subsampling=0)
                compressed_data = output.getvalue()
                compressed_size_mb = len(compressed_data) / 1024 / 1024

                if len(compressed_data) <= self.MAX_FILE_SIZE:
                    new_filename = filename.replace('.png', '.jpg')
                    self.bot.logger.info(f"✅ JPEG compression: {original_size_mb:.1f}MB → {compressed_size_mb:.1f}MB at quality {quality}")
                    return compressed_data, new_filename

            # If still too large at quality 60, use that anyway (extremely rare)
            self.bot.logger.warning(f"⚠️ Image still {compressed_size_mb:.1f}MB after aggressive compression")
            return compressed_data, filename.replace('.png', '.jpg')

        except Exception as e:
            self.bot.logger.error(f"❌ Failed to compress image: {e}, sending original (may fail upload)")
            return image_data, filename

    async def send_images(self, interaction: discord.Interaction, model_display: str) -> None:
        """
        Send all generated images with individual action views.
        
        Args:
            interaction: Discord interaction
            model_display: Display name of the model used
        """
        for i, image_data in enumerate(self.images):
            # Compress image if needed (for large DyPE generations)
            original_size_mb = len(image_data) / 1024 / 1024
            compressed_data, filename = self._compress_image_if_needed(
                image_data,
                get_unique_filename(f"discord_{interaction.user.id}_{i}")
            )

            # Save the original (uncompressed) image to disk
            save_output_image(image_data, filename.replace('.jpg', '.png'))

            # Create embed for each image
            embed = discord.Embed(
                title=f"✅ Image {i+1} Generated - {model_display}!",
                description=f"**Prompt:** {self.prompt[:200]}{'...' if len(self.prompt) > 200 else ''}",
                color=discord.Color.green()
            )

            # Truncate settings_text to Discord's 1024 character field limit
            settings_value = self.settings_text[:1020] + "..." if len(self.settings_text) > 1020 else self.settings_text

            # Add compression notice if image was compressed
            if len(compressed_data) != len(image_data):
                compressed_size_mb = len(compressed_data) / 1024 / 1024
                format_type = "PNG (lossless)" if filename.endswith('.png') else "JPEG"
                settings_value += f"\n\n⚠️ Compressed ({format_type}): {original_size_mb:.1f}MB → {compressed_size_mb:.1f}MB"

            embed.add_field(
                name="Generation Details",
                value=settings_value,
                inline=False
            )

            embed.set_footer(text=f"Image {i+1} of {len(self.images)} | Requested by {interaction.user.display_name}")

            # Create view with action buttons for this image (use original uncompressed data)
            individual_view = IndividualImageView(
                bot=self.bot,
                image_data=image_data,
                generation_info={**self.generation_info, 'image_index': i},
                image_index=i
            )

            # Send compressed image to Discord
            file = discord.File(BytesIO(compressed_data), filename=filename)
            
            if i == 0:
                # First image - EDIT THE ORIGINAL RESPONSE (same message throughout!)
                await interaction.edit_original_response(
                    embed=embed,
                    attachments=[file],
                    view=individual_view
                )
                self.bot.logger.info(f"✅ Edited original message with result image")
            else:
                # Additional images - send as followup
                await interaction.followup.send(embed=embed, file=file, view=individual_view)
                self.bot.logger.info(f"✅ Sent additional image {i+1} as followup")
