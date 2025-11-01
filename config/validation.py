"""
Configuration validation functions.
"""

import re


def validate_discord_token(token: str) -> bool:
    """
    Validate Discord bot token format.
    
    Args:
        token: Discord bot token to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not token or len(token) < 50:
        return False
    # Basic format check for Discord bot tokens
    return token.count('.') >= 2


def validate_comfyui_url(url: str) -> bool:
    """
    Validate ComfyUI URL format.
    
    Args:
        url: ComfyUI URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Handle None or empty
    if not url:
        return False
        
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None

