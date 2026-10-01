# Troubleshooting

Use the JSON logs to find startup errors and failed polls. A bot shown as offline is expected for HTTP-only operation.

- Configuration errors: supply a non-empty token, a positive channel ID and valid case-sensitive tags.
- Discord 401/403: check the existing bot token and channel permissions. Do not print or paste the token.
- History failure: the poll skips posting rather than treating missing history as empty.
- GraphQL failure: the service reports failure and tries again on the next poll. Empty successful feeds are a different result.
- Uncertain send: inspect channel history before retrying. The process suppresses that URL locally to avoid blind replay.
- Missing old announcements: the history window is 200 text messages or 50 archived forum starters plus active starters. It is deliberately bounded.
- Large title: announcements or forum names exceeding Discord limits are rejected.
- Memory test stops: inspect summary.json. Keep Docker running for the complete 24-hour measurement; do not treat a partial result as success.

There is no JSON state file to reset. Do not delete the PVC during the initial migration.
