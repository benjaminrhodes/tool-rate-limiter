"""CLI interface."""

import argparse
import json
import os
import sys

from src.limiter import RateLimitExceeded, RateLimiter

DEFAULT_CONFIG_FILE = "config.json"
DEFAULT_STATE_FILE = "state.json"


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(description="Rate limiting for agent tools")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    check_parser = subparsers.add_parser("check", help="Check if request is allowed")
    check_parser.add_argument("tool", help="Tool name")
    check_parser.add_argument("user", help="User identifier")

    set_limit_parser = subparsers.add_parser("set-limit", help="Set limit for a tool")
    set_limit_parser.add_argument("tool", help="Tool name")
    set_limit_parser.add_argument("capacity", type=int, help="Bucket capacity")
    set_limit_parser.add_argument("refill_rate", type=float, help="Refill rate (tokens/second)")

    subparsers.add_parser("status", help="Show status of all buckets")
    subparsers.add_parser("reset", help="Reset all buckets")

    return parser


def cmd_check(args, limiter: RateLimiter) -> int:
    """Handle check command."""
    try:
        allowed = limiter.check(args.tool, args.user)
        if allowed:
            print(f"ALLOWED: {args.tool} for {args.user}")
            return 0
        else:
            print(f"DENIED: {args.tool} for {args.user}")
            return 1
    except RateLimitExceeded as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


def cmd_set_limit(args, limiter: RateLimiter) -> int:
    """Handle set-limit command."""
    limiter.set_limit(args.tool, args.capacity, args.refill_rate)
    print(f"Set limit for {args.tool}: capacity={args.capacity}, refill_rate={args.refill_rate}")
    return 0


def cmd_status(args, limiter: RateLimiter) -> int:
    """Handle status command."""
    status = limiter.status()
    print(json.dumps(status, indent=2))
    return 0


def cmd_reset(args, limiter: RateLimiter) -> int:
    """Handle reset command."""
    limiter.reset()
    print("All buckets reset")
    return 0


def main(argv=None):
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    config_file = os.environ.get("RATE_LIMIT_CONFIG", DEFAULT_CONFIG_FILE)
    state_file = os.environ.get("RATE_LIMIT_STATE", DEFAULT_STATE_FILE)

    limiter = RateLimiter(config_file, state_file)

    commands = {
        "check": cmd_check,
        "set-limit": cmd_set_limit,
        "status": cmd_status,
        "reset": cmd_reset,
    }

    return commands[args.command](args, limiter)


if __name__ == "__main__":
    sys.exit(main())
