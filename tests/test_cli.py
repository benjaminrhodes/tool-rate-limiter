"""Tests for CLI."""

import json
import os
import tempfile
from unittest.mock import patch


from src import cli


class TestCLI:
    """Test CLI commands."""

    def test_check_allows_request(self):
        """check command should allow when tokens available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "state.json")
            config_file = os.path.join(tmpdir, "config.json")
            with open(config_file, "w") as f:
                json.dump({"tool1": {"capacity": 5, "refill_rate": 1}}, f)

            with patch.object(cli, "DEFAULT_CONFIG_FILE", config_file):
                with patch.object(cli, "DEFAULT_STATE_FILE", state_file):
                    code = cli.main(["check", "tool1", "user1"])

            assert code == 0

    def test_check_denies_request(self):
        """check command should deny when tokens exhausted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "state.json")
            config_file = os.path.join(tmpdir, "config.json")
            with open(config_file, "w") as f:
                json.dump({"tool1": {"capacity": 1, "refill_rate": 0}}, f)

            with patch.object(cli, "DEFAULT_CONFIG_FILE", config_file):
                with patch.object(cli, "DEFAULT_STATE_FILE", state_file):
                    cli.main(["check", "tool1", "user1"])
                    code = cli.main(["check", "tool1", "user1"])

            assert code == 1

    def test_set_limit_updates_config(self):
        """set-limit command should update config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "state.json")
            config_file = os.path.join(tmpdir, "config.json")
            with open(config_file, "w") as f:
                json.dump({"tool1": {"capacity": 5, "refill_rate": 1}}, f)

            with patch.object(cli, "DEFAULT_CONFIG_FILE", config_file):
                with patch.object(cli, "DEFAULT_STATE_FILE", state_file):
                    code = cli.main(["set-limit", "tool1", "10", "2"])

            assert code == 0

            with open(config_file) as f:
                config = json.load(f)
            assert config["tool1"]["capacity"] == 10
            assert config["tool1"]["refill_rate"] == 2

    def test_status_shows_buckets(self):
        """status command should display bucket info."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "state.json")
            config_file = os.path.join(tmpdir, "config.json")
            with open(config_file, "w") as f:
                json.dump({"tool1": {"capacity": 5, "refill_rate": 1}}, f)

            with patch.object(cli, "DEFAULT_CONFIG_FILE", config_file):
                with patch.object(cli, "DEFAULT_STATE_FILE", state_file):
                    code = cli.main(["status"])

            assert code == 0

    def test_reset_clears_buckets(self):
        """reset command should clear all buckets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "state.json")
            config_file = os.path.join(tmpdir, "config.json")
            with open(config_file, "w") as f:
                json.dump({"tool1": {"capacity": 5, "refill_rate": 1}}, f)

            with patch.object(cli, "DEFAULT_CONFIG_FILE", config_file):
                with patch.object(cli, "DEFAULT_STATE_FILE", state_file):
                    cli.main(["check", "tool1", "user1"])
                    code = cli.main(["reset"])

            assert code == 0

    def test_unknown_tool_check_returns_error(self):
        """check with unknown tool returns error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "state.json")
            config_file = os.path.join(tmpdir, "config.json")
            with open(config_file, "w") as f:
                json.dump({}, f)

            with patch.object(cli, "DEFAULT_CONFIG_FILE", config_file):
                with patch.object(cli, "DEFAULT_STATE_FILE", state_file):
                    code = cli.main(["check", "unknown", "user1"])

            assert code == 2
