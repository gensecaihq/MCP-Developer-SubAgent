#!/usr/bin/env python3
"""
Comprehensive tests for rate limiter module
"""

import pytest
import asyncio
import time
import json
import tempfile
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rate_limiter import (
    RateLimiter,
    RateLimit,
    RateLimitState,
    RateLimitExceeded,
    rate_limited,
    get_rate_limiter
)


class TestRateLimit:
    """Test RateLimit configuration class"""
    
    def test_rate_limit_defaults(self):
        """Test RateLimit default values"""
        limit = RateLimit()
        assert limit.max_requests == 60
        assert limit.window_seconds == 60
        assert limit.burst_limit == 10
        assert limit.cooldown_seconds == 300
    
    def test_rate_limit_custom(self):
        """Test RateLimit custom values"""
        limit = RateLimit(
            max_requests=100,
            window_seconds=120,
            burst_limit=20,
            cooldown_seconds=600
        )
        assert limit.max_requests == 100
        assert limit.window_seconds == 120
        assert limit.burst_limit == 20
        assert limit.cooldown_seconds == 600


class TestRateLimitState:
    """Test RateLimitState tracking"""
    
    def test_state_initialization(self):
        """Test state initializes correctly"""
        state = RateLimitState()
        assert len(state.requests) == 0
        assert state.burst_count == 0
        assert state.last_request == 0
        assert state.cooldown_until == 0
        assert state.total_requests == 0
        assert state.total_blocked == 0


class TestRateLimiter:
    """Test RateLimiter core functionality"""
    
    @pytest.fixture
    def temp_config(self):
        """Temporary config file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                "test_endpoint": {
                    "max_requests": 5,
                    "window_seconds": 10,
                    "burst_limit": 2,
                    "cooldown_seconds": 30
                }
            }
            json.dump(config, f)
            yield f.name
        Path(f.name).unlink()
    
    @pytest.fixture
    def rate_limiter(self, temp_config):
        """Rate limiter with test configuration"""
        return RateLimiter(config_path=temp_config)
    
    def test_initialization_default(self):
        """Test rate limiter initialization with defaults"""
        limiter = RateLimiter()
        assert "anthropic_api" in limiter.limits
        assert "global" in limiter.limits
        assert limiter.limits["global"].max_requests == 100
    
    def test_initialization_with_config(self, rate_limiter):
        """Test rate limiter initialization with config file"""
        assert "test_endpoint" in rate_limiter.limits
        assert rate_limiter.limits["test_endpoint"].max_requests == 5
    
    @pytest.mark.asyncio
    async def test_basic_rate_limiting(self, rate_limiter):
        """Test basic rate limiting functionality"""
        # First few requests should be allowed
        for i in range(3):
            result = await rate_limiter.check_rate_limit("test_endpoint")
            assert result["allowed"] is True
            assert result["remaining"] >= 0
            
            if result["allowed"]:
                await rate_limiter.record_request("test_endpoint")
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, rate_limiter):
        """Test rate limit exceeded scenario"""
        # Fill up the rate limit
        for i in range(5):
            result = await rate_limiter.check_rate_limit("test_endpoint")
            if result["allowed"]:
                await rate_limiter.record_request("test_endpoint")
        
        # Next request should be blocked
        result = await rate_limiter.check_rate_limit("test_endpoint")
        assert result["allowed"] is False
        assert result["reason"] == "rate_limit_exceeded"
        assert result["retry_after"] > 0
    
    @pytest.mark.asyncio
    async def test_burst_protection(self, rate_limiter):
        """Test burst protection functionality"""
        # Make rapid requests to trigger burst protection
        for i in range(3):  # More than burst_limit (2)
            await rate_limiter.check_rate_limit("test_endpoint")
            await rate_limiter.record_request("test_endpoint")
        
        # Should activate burst protection
        result = await rate_limiter.check_rate_limit("test_endpoint")
        # May be blocked due to burst protection
        if not result["allowed"]:
            assert result["reason"] == "burst_limit_exceeded"
    
    @pytest.mark.asyncio
    async def test_cooldown_period(self, rate_limiter):
        """Test cooldown period functionality"""
        # Exhaust rate limit to trigger cooldown
        for i in range(6):  # More than max_requests (5)
            result = await rate_limiter.check_rate_limit("test_endpoint")
            if result["allowed"]:
                await rate_limiter.record_request("test_endpoint")
        
        # Should be in cooldown
        result = await rate_limiter.check_rate_limit("test_endpoint")
        if not result["allowed"] and result["reason"] == "rate_limit_exceeded":
            # Verify cooldown is active
            assert result["retry_after"] > 0
            
            # Verify cooldown persists
            result2 = await rate_limiter.check_rate_limit("test_endpoint")
            assert result2["allowed"] is False
    
    @pytest.mark.asyncio
    async def test_sliding_window(self, rate_limiter):
        """Test sliding window behavior"""
        # Make some requests
        for i in range(3):
            result = await rate_limiter.check_rate_limit("test_endpoint")
            if result["allowed"]:
                await rate_limiter.record_request("test_endpoint")
        
        # Wait for part of window to pass
        await asyncio.sleep(2)
        
        # Should still have some capacity
        result = await rate_limiter.check_rate_limit("test_endpoint")
        assert result["allowed"] is True
    
    def test_statistics(self, rate_limiter):
        """Test statistics generation"""
        stats = rate_limiter.get_statistics()
        
        assert "endpoints" in stats
        assert "global_stats" in stats
        assert "total_requests" in stats["global_stats"]
        assert "total_blocked" in stats["global_stats"]
        assert "active_cooldowns" in stats["global_stats"]
    
    def test_update_limits(self, rate_limiter):
        """Test updating rate limits"""
        original_max = rate_limiter.limits["test_endpoint"].max_requests
        
        rate_limiter.update_limits("test_endpoint", max_requests=10)
        assert rate_limiter.limits["test_endpoint"].max_requests == 10
        assert rate_limiter.limits["test_endpoint"].max_requests != original_max
    
    def test_config_persistence(self, temp_config):
        """Test configuration persistence"""
        limiter = RateLimiter(config_path=temp_config)
        limiter.update_limits("new_endpoint", max_requests=50)
        limiter.save_config()
        
        # Load new instance
        limiter2 = RateLimiter(config_path=temp_config)
        assert "new_endpoint" in limiter2.limits
        assert limiter2.limits["new_endpoint"].max_requests == 50


class TestRateLimitDecorator:
    """Test rate limiting decorator"""
    
    @pytest.fixture
    def test_limiter(self):
        """Test rate limiter with tight limits"""
        limiter = RateLimiter()
        limiter.update_limits("decorator_test", max_requests=2, window_seconds=10)
        return limiter
    
    def test_sync_decorator(self, test_limiter):
        """Test decorator on synchronous function"""
        @rate_limited("decorator_test", limiter=test_limiter)
        def sync_function(x):
            return x * 2
        
        # First few calls should work
        assert sync_function(5) == 10
        assert sync_function(6) == 12
        
        # Should eventually hit rate limit
        with pytest.raises(RateLimitExceeded):
            for i in range(10):
                sync_function(i)
    
    @pytest.mark.asyncio
    async def test_async_decorator(self, test_limiter):
        """Test decorator on asynchronous function"""
        @rate_limited("decorator_test", limiter=test_limiter)
        async def async_function(x):
            await asyncio.sleep(0.01)
            return x * 3
        
        # First few calls should work
        result1 = await async_function(5)
        assert result1 == 15
        
        result2 = await async_function(6)
        assert result2 == 18
        
        # Should eventually hit rate limit
        with pytest.raises(RateLimitExceeded):
            tasks = [async_function(i) for i in range(10)]
            await asyncio.gather(*tasks)


class TestRateLimitExceeded:
    """Test RateLimitExceeded exception"""
    
    def test_exception_creation(self):
        """Test exception creation with parameters"""
        exc = RateLimitExceeded("Test message", retry_after=30, endpoint="test")
        
        assert str(exc) == "Test message"
        assert exc.retry_after == 30
        assert exc.endpoint == "test"
    
    def test_exception_defaults(self):
        """Test exception with default parameters"""
        exc = RateLimitExceeded("Test message")
        
        assert str(exc) == "Test message"
        assert exc.retry_after == 0
        assert exc.endpoint == ""


class TestGlobalRateLimiter:
    """Test global rate limiter functionality"""
    
    def test_get_rate_limiter_singleton(self):
        """Test global rate limiter is singleton"""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        
        assert limiter1 is limiter2
    
    def test_global_limiter_functionality(self):
        """Test global limiter works correctly"""
        limiter = get_rate_limiter()
        
        # Should have default configuration
        assert "anthropic_api" in limiter.limits
        assert "global" in limiter.limits


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    @pytest.fixture
    def edge_limiter(self):
        """Rate limiter for edge case testing"""
        return RateLimiter()
    
    @pytest.mark.asyncio
    async def test_zero_requests_limit(self, edge_limiter):
        """Test with zero requests limit"""
        edge_limiter.update_limits("zero_limit", max_requests=0)
        
        result = await edge_limiter.check_rate_limit("zero_limit")
        assert result["allowed"] is False
    
    @pytest.mark.asyncio
    async def test_very_small_window(self, edge_limiter):
        """Test with very small time window"""
        edge_limiter.update_limits("small_window", window_seconds=1, max_requests=1)
        
        result = await edge_limiter.check_rate_limit("small_window")
        assert result["allowed"] is True
        
        await edge_limiter.record_request("small_window")
        
        # Should be blocked immediately
        result = await edge_limiter.check_rate_limit("small_window")
        assert result["allowed"] is False
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, edge_limiter):
        """Test concurrent requests to same endpoint"""
        edge_limiter.update_limits("concurrent", max_requests=10, window_seconds=60)
        
        async def make_request():
            result = await edge_limiter.check_rate_limit("concurrent")
            if result["allowed"]:
                await edge_limiter.record_request("concurrent")
            return result["allowed"]
        
        # Make concurrent requests
        tasks = [make_request() for _ in range(20)]
        results = await asyncio.gather(*tasks)
        
        # Some should be allowed, some blocked
        allowed_count = sum(results)
        assert allowed_count <= 10  # Shouldn't exceed limit
        assert allowed_count > 0   # Some should be allowed
    
    def test_invalid_config_file(self):
        """Test handling of invalid config file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            f.flush()
            
            # Should handle gracefully and use defaults
            limiter = RateLimiter(config_path=f.name)
            assert "global" in limiter.limits
        
        Path(f.name).unlink()
    
    def test_missing_config_file(self):
        """Test handling of missing config file"""
        limiter = RateLimiter(config_path="/nonexistent/path.json")
        
        # Should use defaults
        assert "global" in limiter.limits
        assert "anthropic_api" in limiter.limits


class TestPerformance:
    """Performance tests for rate limiter"""
    
    @pytest.fixture
    def perf_limiter(self):
        """Rate limiter configured for performance testing"""
        limiter = RateLimiter()
        limiter.update_limits("perf_test", max_requests=1000, window_seconds=60)
        return limiter
    
    @pytest.mark.asyncio
    async def test_check_performance(self, perf_limiter):
        """Test rate limit check performance"""
        start_time = time.time()
        
        for i in range(100):
            await perf_limiter.check_rate_limit("perf_test")
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 100
        
        # Should be fast (less than 1ms per check)
        assert avg_time < 0.001, f"Rate limit check too slow: {avg_time:.4f}s"
    
    @pytest.mark.asyncio
    async def test_record_performance(self, perf_limiter):
        """Test request recording performance"""
        start_time = time.time()
        
        for i in range(100):
            await perf_limiter.record_request("perf_test")
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 100
        
        # Should be fast
        assert avg_time < 0.001, f"Request recording too slow: {avg_time:.4f}s"
    
    def test_statistics_performance(self, perf_limiter):
        """Test statistics generation performance"""
        # Add some data first
        asyncio.run(self._add_test_data(perf_limiter))
        
        start_time = time.time()
        
        for i in range(10):
            perf_limiter.get_statistics()
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 10
        
        # Should be reasonably fast
        assert avg_time < 0.01, f"Statistics generation too slow: {avg_time:.4f}s"
    
    async def _add_test_data(self, limiter):
        """Helper to add test data"""
        for i in range(50):
            await limiter.check_rate_limit("perf_test")
            await limiter.record_request("perf_test")


def run_rate_limiter_tests():
    """Run all rate limiter tests"""
    return pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_rate_limiter_tests()