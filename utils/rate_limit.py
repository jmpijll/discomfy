"""
Rate limiting utilities for DisComfy v2.0.

Following best practices for in-memory rate limiting.
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    per_user: int = 10  # Requests per user per window
    global_limit: int = 100  # Global requests per window
    window_seconds: int = 60  # Time window in seconds


class RateLimiter:
    """Rate limiter with per-user and global limits.
    
    Uses sliding window approach with in-memory storage.
    """
    
    def __init__(self, config: RateLimitConfig):
        """
        Initialize rate limiter.
        
        Args:
            config: Rate limiting configuration
        """
        self.config = config
        self.user_limits: Dict[int, List[float]] = {}
        self.global_limit: List[float] = []
    
    def check_rate_limit(self, user_id: int) -> bool:
        """
        Check if user is within rate limit.
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if within limit, False if rate limited
        """
        current_time = time.time()
        window_start = current_time - self.config.window_seconds
        
        # Check global limit first
        self.global_limit = [t for t in self.global_limit if t > window_start]
        
        if len(self.global_limit) >= self.config.global_limit:
            return False
        
        # Check per-user limit
        if user_id not in self.user_limits:
            self.user_limits[user_id] = []
        
        # Remove old timestamps
        self.user_limits[user_id] = [
            t for t in self.user_limits[user_id] if t > window_start
        ]
        
        if len(self.user_limits[user_id]) >= self.config.per_user:
            return False
        
        # Record this request
        self.user_limits[user_id].append(current_time)
        self.global_limit.append(current_time)
        
        return True
    
    def get_user_remaining(self, user_id: int) -> int:
        """
        Get remaining requests for a user in current window.
        
        Args:
            user_id: User ID to check
            
        Returns:
            Number of remaining requests
        """
        current_time = time.time()
        window_start = current_time - self.config.window_seconds
        
        if user_id not in self.user_limits:
            return self.config.per_user
        
        # Remove old timestamps
        self.user_limits[user_id] = [
            t for t in self.user_limits[user_id] if t > window_start
        ]
        
        return max(0, self.config.per_user - len(self.user_limits[user_id]))
    
    def reset_user(self, user_id: int) -> None:
        """
        Reset rate limit for a specific user.
        
        Args:
            user_id: User ID to reset
        """
        if user_id in self.user_limits:
            del self.user_limits[user_id]
    
    def reset_all(self) -> None:
        """Reset all rate limits."""
        self.user_limits.clear()
        self.global_limit.clear()


