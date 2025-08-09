#!/usr/bin/env python3
"""
Rate Limiting for API Calls
Prevents abuse and manages API quota efficiently
"""

import time
import asyncio
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import os
from pathlib import Path


@dataclass
class RateLimit:
    """Rate limit configuration"""
    max_requests: int = 60      # Max requests per window
    window_seconds: int = 60    # Time window in seconds
    burst_limit: int = 10       # Burst allowance
    cooldown_seconds: int = 300 # Cooldown after limit exceeded


@dataclass 
class RateLimitState:
    """Track rate limiting state"""
    requests: deque = field(default_factory=deque)
    burst_count: int = 0
    last_request: float = 0
    cooldown_until: float = 0
    total_requests: int = 0
    total_blocked: int = 0


class RateLimiter:
    """
    Intelligent rate limiter with multiple strategies:
    - Token bucket for burst handling
    - Sliding window for sustained rate limiting
    - Adaptive cooling for abuse prevention
    - Per-endpoint and global limits
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or ".claude/rate_limits.json"
        self.limits = self._load_config()
        self.state: Dict[str, RateLimitState] = defaultdict(RateLimitState)
        self.global_state = RateLimitState()
        
    def _load_config(self) -> Dict[str, RateLimit]:
        """Load rate limiting configuration"""
        default_limits = {
            "anthropic_api": RateLimit(
                max_requests=50,    # Anthropic's typical limit
                window_seconds=60,
                burst_limit=5,
                cooldown_seconds=120
            ),
            "global": RateLimit(
                max_requests=100,   # Global limit across all APIs
                window_seconds=60,
                burst_limit=15,
                cooldown_seconds=180
            ),
            "webhook": RateLimit(
                max_requests=20,    # Conservative for webhooks
                window_seconds=60,
                burst_limit=3,
                cooldown_seconds=60
            )
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                
                # Convert dict to RateLimit objects
                loaded_limits = {}
                for key, data in config_data.items():
                    loaded_limits[key] = RateLimit(**data)
                
                # Merge with defaults
                default_limits.update(loaded_limits)
                
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Warning: Failed to load rate limits config: {e}")
        
        return default_limits
    
    def save_config(self):
        """Save current rate limiting configuration"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Convert RateLimit objects to dicts
        config_data = {}
        for key, limit in self.limits.items():
            config_data[key] = {
                "max_requests": limit.max_requests,
                "window_seconds": limit.window_seconds,
                "burst_limit": limit.burst_limit,
                "cooldown_seconds": limit.cooldown_seconds
            }
        
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    async def check_rate_limit(self, endpoint: str = "global") -> Dict[str, Any]:
        """
        Check if request is allowed under rate limits
        Returns: {
            "allowed": bool,
            "reason": str,
            "retry_after": int,
            "remaining": int,
            "reset_time": float
        }
        """
        current_time = time.time()
        
        # Get rate limit config
        limit_config = self.limits.get(endpoint, self.limits["global"])
        state = self.state[endpoint]
        
        # Check global limits too (unless this IS the global check)
        if endpoint != "global":
            global_check = await self.check_rate_limit("global")
            if not global_check["allowed"]:
                return global_check
        
        # Check cooldown period
        if current_time < state.cooldown_until:
            return {
                "allowed": False,
                "reason": "cooldown_active",
                "retry_after": int(state.cooldown_until - current_time),
                "remaining": 0,
                "reset_time": state.cooldown_until
            }
        
        # Clean old requests from sliding window
        window_start = current_time - limit_config.window_seconds
        while state.requests and state.requests[0] < window_start:
            state.requests.popleft()
        
        # Check burst limit
        if state.last_request > 0:
            time_since_last = current_time - state.last_request
            if time_since_last < 1.0:  # Less than 1 second
                state.burst_count += 1
                if state.burst_count > limit_config.burst_limit:
                    # Activate short cooldown for burst protection
                    state.cooldown_until = current_time + 10
                    return {
                        "allowed": False,
                        "reason": "burst_limit_exceeded",
                        "retry_after": 10,
                        "remaining": 0,
                        "reset_time": current_time + 10
                    }
            else:
                # Reset burst counter if enough time has passed
                state.burst_count = max(0, state.burst_count - 1)
        
        # Check sliding window limit
        if len(state.requests) >= limit_config.max_requests:
            # Rate limit exceeded - activate cooldown
            state.cooldown_until = current_time + limit_config.cooldown_seconds
            state.total_blocked += 1
            
            return {
                "allowed": False,
                "reason": "rate_limit_exceeded", 
                "retry_after": limit_config.cooldown_seconds,
                "remaining": 0,
                "reset_time": state.cooldown_until
            }
        
        # Request is allowed
        remaining = limit_config.max_requests - len(state.requests) - 1
        reset_time = window_start + limit_config.window_seconds
        
        return {
            "allowed": True,
            "reason": "allowed",
            "retry_after": 0,
            "remaining": remaining,
            "reset_time": reset_time
        }
    
    async def record_request(self, endpoint: str = "global"):
        """Record a successful request"""
        current_time = time.time()
        state = self.state[endpoint]
        
        state.requests.append(current_time)
        state.last_request = current_time
        state.total_requests += 1
        
        # Also record in global state if not global
        if endpoint != "global":
            await self.record_request("global")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        stats = {
            "endpoints": {},
            "global_stats": {
                "total_requests": self.global_state.total_requests,
                "total_blocked": self.global_state.total_blocked,
                "active_cooldowns": 0
            }
        }
        
        current_time = time.time()
        
        for endpoint, state in self.state.items():
            # Clean old requests for accurate stats
            limit_config = self.limits.get(endpoint, self.limits["global"])
            window_start = current_time - limit_config.window_seconds
            while state.requests and state.requests[0] < window_start:
                state.requests.popleft()
            
            is_in_cooldown = current_time < state.cooldown_until
            if is_in_cooldown:
                stats["global_stats"]["active_cooldowns"] += 1
            
            stats["endpoints"][endpoint] = {
                "current_requests_in_window": len(state.requests),
                "max_requests": limit_config.max_requests,
                "utilization_percent": (len(state.requests) / limit_config.max_requests) * 100,
                "total_requests": state.total_requests,
                "total_blocked": state.total_blocked,
                "burst_count": state.burst_count,
                "in_cooldown": is_in_cooldown,
                "cooldown_remaining": max(0, state.cooldown_until - current_time)
            }
        
        return stats
    
    def update_limits(self, endpoint: str, **kwargs):
        """Update rate limits for an endpoint"""
        if endpoint not in self.limits:
            self.limits[endpoint] = RateLimit()
        
        limit = self.limits[endpoint]
        
        for key, value in kwargs.items():
            if hasattr(limit, key):
                setattr(limit, key, value)
        
        self.save_config()


# Decorator for rate limiting functions
def rate_limited(endpoint: str = "global", limiter: Optional[RateLimiter] = None):
    """Decorator to add rate limiting to functions"""
    if limiter is None:
        limiter = RateLimiter()
    
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # Check rate limit
            check_result = await limiter.check_rate_limit(endpoint)
            
            if not check_result["allowed"]:
                raise RateLimitExceeded(
                    f"Rate limit exceeded for {endpoint}: {check_result['reason']}",
                    retry_after=check_result["retry_after"],
                    endpoint=endpoint
                )
            
            # Record the request
            await limiter.record_request(endpoint)
            
            # Call the function
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            # For sync functions, run async operations in event loop
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    
    def __init__(self, message: str, retry_after: int = 0, endpoint: str = ""):
        super().__init__(message)
        self.retry_after = retry_after
        self.endpoint = endpoint


# Global rate limiter instance
_global_limiter = None

def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = RateLimiter()
    return _global_limiter


# Example usage and testing
async def example_usage():
    """Example of how to use the rate limiter"""
    limiter = RateLimiter()
    
    # Configure rate limits
    limiter.update_limits("anthropic_api", max_requests=30, window_seconds=60)
    
    # Check if request is allowed
    result = await limiter.check_rate_limit("anthropic_api")
    print(f"Request allowed: {result}")
    
    if result["allowed"]:
        # Record the request
        await limiter.record_request("anthropic_api")
        print("Request recorded")
    
    # Get statistics
    stats = limiter.get_statistics()
    print(f"Stats: {json.dumps(stats, indent=2)}")


# Rate limited function example
@rate_limited("anthropic_api")
async def make_api_call(prompt: str):
    """Example rate-limited API call"""
    print(f"Making API call with prompt: {prompt}")
    # Simulate API call
    await asyncio.sleep(0.1)
    return {"response": f"Response to: {prompt}"}


if __name__ == "__main__":
    asyncio.run(example_usage())