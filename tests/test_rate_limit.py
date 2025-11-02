"""
Unit tests for rate limiting.

Following pytest best practices.
"""

import pytest
import time
from utils.rate_limit import RateLimiter, RateLimitConfig


class TestRateLimiter:
    """Test RateLimiter class."""
    
    def test_initial_check_passes(self, rate_limiter):
        """Test that initial rate limit check passes."""
        assert rate_limiter.check_rate_limit(12345) is True
    
    def test_per_user_limit_enforced(self, rate_limiter):
        """Test that per-user rate limit is enforced."""
        user_id = 12345
        config = RateLimitConfig(per_user=5, global_limit=100, window_seconds=60)
        limiter = RateLimiter(config)
        
        # Make 5 requests (should all pass)
        for _ in range(5):
            assert limiter.check_rate_limit(user_id) is True
        
        # 6th request should fail
        assert limiter.check_rate_limit(user_id) is False
    
    def test_global_limit_enforced(self):
        """Test that global rate limit is enforced."""
        config = RateLimitConfig(per_user=100, global_limit=5, window_seconds=60)
        limiter = RateLimiter(config)
        
        # Make 5 requests from different users (should all pass)
        for user_id in range(5):
            assert limiter.check_rate_limit(user_id) is True
        
        # 6th request should fail (global limit)
        assert limiter.check_rate_limit(999) is False
    
    def test_window_expires(self):
        """Test that rate limit window expires correctly."""
        config = RateLimitConfig(per_user=2, global_limit=100, window_seconds=1)
        limiter = RateLimiter(config)
        
        user_id = 12345
        
        # Make 2 requests
        assert limiter.check_rate_limit(user_id) is True
        assert limiter.check_rate_limit(user_id) is True
        
        # 3rd should fail
        assert limiter.check_rate_limit(user_id) is False
        
        # Wait for window to expire
        time.sleep(2)
        
        # Should be able to make request again
        assert limiter.check_rate_limit(user_id) is True
    
    def test_get_user_remaining(self, rate_limiter):
        """Test getting remaining requests for a user."""
        user_id = 12345
        
        # Initially should have full limit
        remaining = rate_limiter.get_user_remaining(user_id)
        assert remaining == 10  # Default config per_user=10
        
        # Make a request
        rate_limiter.check_rate_limit(user_id)
        
        # Should have one less remaining
        remaining = rate_limiter.get_user_remaining(user_id)
        assert remaining == 9
    
    def test_reset_user(self, rate_limiter):
        """Test resetting rate limit for a user."""
        user_id = 12345
        
        # Make some requests
        for _ in range(3):
            rate_limiter.check_rate_limit(user_id)
        
        # Reset
        rate_limiter.reset_user(user_id)
        
        # Should have full limit again
        remaining = rate_limiter.get_user_remaining(user_id)
        assert remaining == 10
    
    def test_reset_all(self, rate_limiter):
        """Test resetting all rate limits."""
        # Make requests from multiple users
        for user_id in range(5):
            rate_limiter.check_rate_limit(user_id)
        
        # Reset all
        rate_limiter.reset_all()
        
        # All users should have full limit
        for user_id in range(5):
            remaining = rate_limiter.get_user_remaining(user_id)
            assert remaining == 10


