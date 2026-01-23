# Troubleshooting

This guide helps you diagnose and fix common issues with the UniFi Release Announcer.

## Common Issues

### Bot Not Posting to Discord

#### Symptoms
- The bot runs without errors but doesn't post messages to Discord
- No error messages in the logs

#### Possible Causes & Solutions

1. **Missing Permissions**

   The bot needs the "Send Messages" permission in the target channel.

   **Solution:**
   - Go to your Discord server settings
   - Navigate to Roles
   - Find your bot's role
   - Ensure "Send Messages" permission is enabled
   - Check channel-specific permissions as well

2. **Incorrect Channel ID**

   The channel ID might be wrong or the bot doesn't have access to that channel.

   **Solution:**
   - Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
   - Right-click on the channel and select "Copy ID"
   - Verify the ID matches your `DISCORD_CHANNEL_ID` environment variable
   - Ensure the bot has been invited to the server and can see the channel

3. **No New Releases**

   The bot only posts when it detects a new release.

   **Solution:**
   - Check the cache file at `/cache/release_state.json`
   - Delete this file to force the bot to post the latest release again
   - Wait for the next check cycle (10 minutes by default)

### Environment Variable Issues

#### Symptoms
- Bot fails to start
- Error messages about missing configuration

#### Solutions

1. **Check .env file exists**

   ```bash
   ls -la .env
   ```

2. **Verify environment variables are set**

   ```bash
   # For local development
   cat .env

   # For Docker
   docker compose config

   # For Kubernetes
   kubectl get secret unifi-release-announcer-secrets -o yaml
   ```

3. **Ensure proper format**

   The `.env` file should look like:
   ```env
   DISCORD_BOT_TOKEN=your_token_here
   DISCORD_CHANNEL_ID=123456789012345678
   SCRAPER_BACKEND=graphql
   TAGS=unifi-protect,unifi-network
   ```

   - No spaces around `=`
   - No quotes needed for values
   - Channel ID should be a number

### Scraper Backend Issues

#### GraphQL Backend Fails

**Symptoms:**
- Errors about GraphQL queries
- Connection timeouts

**Solutions:**

1. **Check network connectivity**

   ```bash
   curl -I https://community.ui.com
   ```

2. **Try the RSS backend instead**

   Update your `.env`:
   ```env
   SCRAPER_BACKEND=rss
   ```

3. **Check for API changes**

   The Ubiquiti Community API might have changed. Check the logs for specific error messages.

#### RSS Backend Fails

**Symptoms:**
- Errors parsing RSS feed
- No releases detected

**Solutions:**

1. **Verify RSS feed is accessible**

   ```bash
   curl https://community.ui.com/releases.rss
   ```

2. **Switch to GraphQL backend**

   Update your `.env`:
   ```env
   SCRAPER_BACKEND=graphql
   ```

### Docker Issues

#### Container Won't Start

**Symptoms:**
- Container exits immediately
- Error messages in logs

**Solutions:**

1. **Check logs**

   ```bash
   docker compose logs announcer
   ```

2. **Verify image built correctly**

   ```bash
   task build
   # or
   docker compose build announcer
   ```

3. **Check environment variables**

   ```bash
   docker compose config
   ```

4. **Ensure cache directory exists**

   ```bash
   mkdir -p cache
   chmod 755 cache
   ```

#### Permission Issues with Cache

**Symptoms:**
- Errors writing to `/cache/release_state.json`
- Permission denied errors

**Solutions:**

1. **Fix cache directory permissions**

   ```bash
   chmod 755 cache
   chmod 644 cache/release_state.json  # if file exists
   ```

2. **Check volume mount**

   Verify in `docker-compose.yml`:
   ```yaml
   volumes:
     - ./cache:/cache
   ```

### Kubernetes Issues

#### Pod Won't Start

**Symptoms:**
- Pod in CrashLoopBackOff state
- Pod shows errors in describe

**Solutions:**

1. **Check pod status**

   ```bash
   kubectl get pods
   kubectl describe pod <pod-name>
   ```

2. **View logs**

   ```bash
   kubectl logs <pod-name>
   ```

3. **Verify secrets are created**

   ```bash
   kubectl get secrets
   kubectl describe secret unifi-release-announcer-secrets
   ```

4. **Check image pull**

   ```bash
   kubectl describe pod <pod-name> | grep -A 5 Events
   ```

#### Secret Not Found

**Symptoms:**
- Error about missing secrets
- Environment variables not set

**Solutions:**

1. **Create the secret**

   ```bash
   cd k8s
   kubectl apply -f secret.yaml
   ```

2. **Verify secret exists**

   ```bash
   kubectl get secret unifi-release-announcer-secrets
   ```

### Tag Filtering Issues

#### Wrong Releases Being Announced

**Symptoms:**
- Releases that don't match your configured tags are being announced
- Getting announcements for products you didn't configure

**Solutions:**

1. **Verify TAGS environment variable**

   Check your configuration:
   ```bash
   # For Docker
   docker compose config | grep TAGS

   # For Kubernetes
   kubectl get deployment unifi-release-announcer -o yaml | grep -A 5 TAGS
   ```

2. **Check tag matching logic**

   The bot matches releases based on tags in the release metadata. Some releases may have multiple tags.

3. **Review available tags**

   See the [Configuration](configuration.md#available-tags) page for a complete list of available tags.

4. **Debug tag matching**

   You can use the debug script to see what tags are being matched:
   ```bash
   uv run python debug_tags.py
   ```

## Debugging Tips

### Enable Verbose Logging

Add logging configuration to see more details:

```python
# In main.py, add at the top
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Release State

The bot stores the last announced release in `/cache/release_state.json`:

```bash
# View current state
cat cache/release_state.json

# Reset state (will re-announce latest release)
rm cache/release_state.json
```

### Test Scraper Backends

You can test each backend independently:

```bash
# Test GraphQL backend
uv run python -c "from scraper_backends.graphql_backend import GraphQLBackend; backend = GraphQLBackend(); print(backend.get_latest_release())"

# Test RSS backend
uv run python -c "from scraper_backends.rss_backend import RSSBackend; backend = RSSBackend(); print(backend.get_latest_release())"
```

### Verify Discord Bot Token

Test if your bot token is valid:

```bash
# Using curl
curl -H "Authorization: Bot YOUR_BOT_TOKEN" https://discord.com/api/v10/users/@me
```

## Getting Help

If you're still experiencing issues:

1. **Check the logs** - Most issues will show error messages in the logs
2. **Review the configuration** - Double-check all environment variables
3. **Search existing issues** - Someone may have encountered the same problem
4. **Open an issue** - Provide:
   - Error messages from logs
   - Your configuration (without sensitive data)
   - Steps to reproduce the issue
   - Environment details (Docker version, Kubernetes version, etc.)

## Performance Issues

### Bot Using Too Much Memory

**Solutions:**

1. **Check for memory leaks**

   Monitor memory usage:
   ```bash
   # Docker
   docker stats

   # Kubernetes
   kubectl top pods
   ```

2. **Reduce check frequency**

   The bot checks every 10 minutes by default. This is configured in `main.py`.

### Slow Response Times

**Solutions:**

1. **Use GraphQL backend**

   GraphQL is generally faster than RSS:
   ```env
   SCRAPER_BACKEND=graphql
   ```

2. **Check network latency**

   ```bash
   ping community.ui.com
   ```
