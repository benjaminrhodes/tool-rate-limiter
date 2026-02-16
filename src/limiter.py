"""Rate limiter using token bucket algorithm."""

import json
import os
import time
from dataclasses import dataclass


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    pass


@dataclass
class Bucket:
    """Token bucket state."""

    tokens: float
    last_refill: float


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, config_file: str, state_file: str):
        self.config_file = config_file
        self.state_file = state_file
        self.config = self._load_config()
        self.state = self._load_state()

    def _load_config(self) -> dict:
        """Load config from file."""
        if os.path.exists(self.config_file):
            with open(self.config_file) as f:
                return json.load(f)
        return {}

    def _save_config(self):
        """Save config to file."""
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2)

    def _load_state(self) -> dict:
        """Load state from file."""
        if os.path.exists(self.state_file):
            with open(self.state_file) as f:
                return json.load(f)
        return {}

    def _save_state(self):
        """Save state to file."""
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def _get_bucket_key(self, tool: str, user: str) -> str:
        """Get bucket key."""
        return f"{tool}:{user}"

    def _refill_bucket(self, tool: str, user: str):
        """Refill bucket based on elapsed time."""
        bucket_key = self._get_bucket_key(tool, user)
        tool_config = self.config.get(tool)

        if not tool_config:
            return

        capacity = tool_config["capacity"]
        refill_rate = tool_config["refill_rate"]

        if bucket_key not in self.state:
            self.state[bucket_key] = {"tokens": capacity, "last_refill": time.time()}
            return

        bucket = self.state[bucket_key]
        now = time.time()
        elapsed = now - bucket["last_refill"]

        new_tokens = bucket["tokens"] + (elapsed * refill_rate)
        bucket["tokens"] = min(new_tokens, capacity)
        bucket["last_refill"] = now

    def check(self, tool: str, user: str) -> bool:
        """Check if request is allowed. Returns True if allowed, False if denied."""
        if tool not in self.config:
            raise RateLimitExceeded(f"Unknown tool: {tool}")

        self._refill_bucket(tool, user)

        bucket_key = self._get_bucket_key(tool, user)
        bucket = self.state[bucket_key]

        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            self._save_state()
            return True

        return False

    def set_limit(self, tool: str, capacity: int, refill_rate: float):
        """Set limit for a tool."""
        self.config[tool] = {"capacity": capacity, "refill_rate": refill_rate}
        self._save_config()

    def status(self) -> dict:
        """Get status of all buckets."""
        result = {}
        for tool, tool_config in self.config.items():
            result[tool] = {
                "capacity": tool_config["capacity"],
                "refill_rate": tool_config["refill_rate"],
                "users": {},
            }

        for bucket_key, bucket_data in self.state.items():
            tool, user = bucket_key.split(":", 1)
            if tool in result:
                result[tool]["users"][user] = bucket_data["tokens"]

        return result

    def reset(self):
        """Reset all buckets to full."""
        self.state = {}
        self._save_state()
