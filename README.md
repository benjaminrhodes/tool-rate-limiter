# Tool Call Rate Limiter

Rate limit agent tool invocations using the token bucket algorithm.

## Features

- Rate limit by tool
- Token bucket algorithm
- Per-user limits
- CLI interface
- JSON file persistence

## Usage

```bash
# Create a config file (config.json)
{
  "tool1": {"capacity": 10, "refill_rate": 1},
  "tool2": {"capacity": 5, "refill_rate": 0.5}
}

# Check if request is allowed
python -m src.cli check tool1 user1
# Returns: ALLOWED (exit 0) or DENIED (exit 1)

# Set limit for a tool
python -m src.cli set-limit tool1 20 2

# Show status of all buckets
python -m src.cli status

# Reset all buckets
python -m src.cli reset
```

## Configuration

Edit `config.json` to configure rate limits:
- `capacity`: Maximum tokens in bucket
- `refill_rate`: Tokens added per second

Environment variables:
- `RATE_LIMIT_CONFIG`: Path to config file (default: config.json)
- `RATE_LIMIT_STATE`: Path to state file (default: state.json)

## Testing

```bash
pytest tests/ -v
```

## License

MIT
