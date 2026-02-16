"""Tests for rate limiter."""

import json
import os
import tempfile

import pytest

from src.limiter import RateLimitExceeded, RateLimiter


class TestRateLimiter:
    """Test RateLimiter class."""

    def test_check_allows_request_when_bucket_has_tokens(self):
        """Request should be allowed when bucket has tokens."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "state.json")
            config_file = os.path.join(tmpdir, "config.json")
            with open(config_file, "w") as f:
                json.dump({"tool1": {"capacity": 5, "refill_rate": 1}}, f)

            limiter = RateLimiter(config_file, state_file)
            result = limiter.check("tool1", "user1")

            assert result is True

    def test_check_rejects_request_when_bucket_empty(self):
        """Request should be denied when bucket is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "state.json")
            config_file = os.path.join(tmpdir, "config.json")
            with open(config_file, "w") as f:
                json.dump({"tool1": {"capacity": 1, "refill_rate": 0}}, f)

            limiter = RateLimiter(config_file, state_file)
            limiter.check("tool1", "user1")  # First request uses the token
            result = limiter.check("tool1", "user1")  # Second should fail

            assert result is False

    def test_different_users_have_separate_buckets(self):
        """Each user should have their own bucket."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "state.json")
            config_file = os.path.join(tmpdir, "config.json")
            with open(config_file, "w") as f:
                json.dump({"tool1": {"capacity": 1, "refill_rate": 0}}, f)

            limiter = RateLimiter(config_file, state_file)
            limiter.check("tool1", "user1")
            result = limiter.check("tool1", "user2")

            assert result is True

    def test_different_tools_have_separate_buckets(self):
        """Each tool should have its own bucket."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "state.json")
            config_file = os.path.join(tmpdir, "config.json")
            with open(config_file, "w") as f:
                json.dump(
                    {
                        "tool1": {"capacity": 1, "refill_rate": 0},
                        "tool2": {"capacity": 1, "refill_rate": 0},
                    },
                    f,
                )

            limiter = RateLimiter(config_file, state_file)
            limiter.check("tool1", "user1")
            result = limiter.check("tool2", "user1")

            assert result is True

    def test_set_limit_updates_tool_limit(self):
        """set_limit should update the limit for a tool."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "state.json")
            config_file = os.path.join(tmpdir, "config.json")
            with open(config_file, "w") as f:
                json.dump({"tool1": {"capacity": 5, "refill_rate": 1}}, f)

            limiter = RateLimiter(config_file, state_file)
            limiter.set_limit("tool1", 10, 2)

            assert limiter.config["tool1"]["capacity"] == 10
            assert limiter.config["tool1"]["refill_rate"] == 2

    def test_set_limit_creates_new_tool_if_not_exists(self):
        """set_limit should create new tool if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "state.json")
            config_file = os.path.join(tmpdir, "config.json")
            with open(config_file, "w") as f:
                json.dump({}, f)

            limiter = RateLimiter(config_file, state_file)
            limiter.set_limit("newtool", 5, 1)

            assert limiter.config["newtool"]["capacity"] == 5
            assert limiter.config["newtool"]["refill_rate"] == 1

    def test_status_returns_all_buckets(self):
        """status should return all bucket states."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "state.json")
            config_file = os.path.join(tmpdir, "config.json")
            with open(config_file, "w") as f:
                json.dump(
                    {
                        "tool1": {"capacity": 5, "refill_rate": 1},
                        "tool2": {"capacity": 10, "refill_rate": 2},
                    },
                    f,
                )

            limiter = RateLimiter(config_file, state_file)
            limiter.check("tool1", "user1")

            status = limiter.status()

            assert "tool1" in status
            assert "tool2" in status
            assert status["tool1"]["capacity"] == 5

    def test_reset_clears_all_user_buckets(self):
        """reset should clear all user buckets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "state.json")
            config_file = os.path.join(tmpdir, "config.json")
            with open(config_file, "w") as f:
                json.dump({"tool1": {"capacity": 5, "refill_rate": 1}}, f)

            limiter = RateLimiter(config_file, state_file)
            limiter.check("tool1", "user1")
            limiter.check("tool1", "user1")
            limiter.check("tool1", "user1")

            limiter.reset()

            # After reset, should be able to make requests again
            result = limiter.check("tool1", "user1")
            assert result is True

    def test_state_persists_to_file(self):
        """State should persist to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "state.json")
            config_file = os.path.join(tmpdir, "config.json")
            with open(config_file, "w") as f:
                json.dump({"tool1": {"capacity": 3, "refill_rate": 0}}, f)

            limiter = RateLimiter(config_file, state_file)
            limiter.check("tool1", "user1")  # tokens: 3->2
            limiter.check("tool1", "user1")  # tokens: 2->1
            limiter.check("tool1", "user1")  # tokens: 1->0

            # Create new limiter instance - should load persisted state
            limiter2 = RateLimiter(config_file, state_file)
            result = limiter2.check("tool1", "user1")  # tokens: 0, should fail

            assert result is False  # Should be limited

    def test_unknown_tool_raises_exception(self):
        """Unknown tool should raise exception."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "state.json")
            config_file = os.path.join(tmpdir, "config.json")
            with open(config_file, "w") as f:
                json.dump({}, f)

            limiter = RateLimiter(config_file, state_file)

            with pytest.raises(RateLimitExceeded):
                limiter.check("unknown_tool", "user1")
