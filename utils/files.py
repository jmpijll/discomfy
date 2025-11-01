"""
File operation utilities for DisComfy v2.0.

Handles saving, cleanup, and unique filename generation.
"""

import time
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_unique_filename(prefix: str, extension: str = ".png") -> str:
    """
    Generate a unique filename with timestamp.
    
    Args:
        prefix: Filename prefix
        extension: File extension (default: .png)
        
    Returns:
        Unique filename string
    """
    timestamp = int(time.time() * 1000)  # Milliseconds for uniqueness
    return f"{prefix}_{timestamp}{extension}"


def save_output_image(image_data: bytes, filename: str, output_dir: str = "output") -> Path:
    """
    Save image data to file.
    
    Args:
        image_data: Image data as bytes
        filename: Filename to save as
        output_dir: Output directory (default: "output")
        
    Returns:
        Path to saved file
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    file_path = output_path / filename
    
    try:
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        logger.debug(f"Saved image: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Failed to save image {filename}: {e}")
        raise


def save_output_video(video_data: bytes, filename: str, output_dir: str = "output") -> Path:
    """
    Save video data to file.
    
    Args:
        video_data: Video data as bytes
        filename: Filename to save as
        output_dir: Output directory (default: "output")
        
    Returns:
        Path to saved file
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    file_path = output_path / filename
    
    try:
        with open(file_path, 'wb') as f:
            f.write(video_data)
        
        logger.debug(f"Saved video: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Failed to save video {filename}: {e}")
        raise


def cleanup_old_outputs(
    output_dir: str = "output",
    max_files: int = 50,
    file_extension: Optional[str] = None
) -> int:
    """
    Clean up old output files, keeping only the most recent ones.
    
    Args:
        output_dir: Output directory to clean
        max_files: Maximum number of files to keep
        file_extension: Optional file extension filter (e.g., ".png", ".mp4")
        
    Returns:
        Number of files deleted
    """
    output_path = Path(output_dir)
    
    if not output_path.exists():
        return 0
    
    # Get all files
    if file_extension:
        files = list(output_path.glob(f"*{file_extension}"))
    else:
        files = [f for f in output_path.iterdir() if f.is_file()]
    
    if len(files) <= max_files:
        return 0
    
    # Sort by modification time (oldest first)
    files.sort(key=lambda f: f.stat().st_mtime)
    
    # Delete oldest files
    files_to_delete = files[:-max_files]
    deleted_count = 0
    
    for file_path in files_to_delete:
        try:
            file_path.unlink()
            deleted_count += 1
            logger.debug(f"Deleted old file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete {file_path}: {e}")
    
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} old output files")
    
    return deleted_count


def get_unique_video_filename(prefix: str) -> str:
    """
    Generate a unique video filename.
    
    Args:
        prefix: Filename prefix
        
    Returns:
        Unique video filename with .mp4 extension
    """
    return get_unique_filename(prefix, extension=".mp4")


