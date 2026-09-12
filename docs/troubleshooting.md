# Troubleshooting
## Connection refused
- Check `base_url` in config.yaml
- Ensure Ollama / API server is running

## HTTP 401/403
- Verify `api_key_env` points to a valid env var
- Run `harness-ui` and check key management panel

## HTTP 429 (rate limit)
- Tool calls are rate-limited automatically; retry with backoff
- Reduce `num_results` in tool params

## Timeout
- Increase `timeout` in config.yaml
- Check network connectivity

## Empty results
- Verify the endpoint URL is correct
- Check `custom_endpoints` enabled flag

## Keys visible in logs
- Never commit `.env`; it is gitignored
- UI masks keys (last 4 chars only)
