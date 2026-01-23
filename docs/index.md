# UniFi Release Announcer

A Discord bot that monitors UniFi community releases and posts announcements to a Discord channel.

## Features

- **Modular Scraper Architecture**: Swappable backends for different scraping needs
- **GraphQL API**: Direct API access for reliable data fetching
- **Docker Ready**: Optimized Alpine-based container (157MB)
- **Environment Configuration**: Easy backend switching via environment variables
- 🔍 **Automatic Monitoring**: Checks for new UniFi releases every 10 minutes
- 📱 **Platform Detection**: Automatically tags releases with platform-specific emojis (iOS 📱, Android 🤖, Desktop 💻)
- 🎯 **Smart Filtering**: Only posts new releases, avoiding duplicates
- ☸️ **Kubernetes Support**: Ready for deployment on k3s/Kubernetes clusters

## How It Works

1. **Scraping**: The bot scrapes the Ubiquiti Community forums for the latest UniFi releases
2. **Comparison**: It compares the latest release URL with the previously posted one (stored in `/cache/release_state.json`)
3. **Posting**: If a new release is found, it formats a message with platform tags and posts to Discord
4. **State Management**: Updates the stored URL to prevent duplicate posts (stored in `/cache/release_state.json`)

## Message Format

The bot posts messages in this format:

```markdown
🎉 **New UniFi Release Posted**

🔗 [UniFi Protect iOS 2.13.1](https://community.ui.com/releases/...) 📱
```

Platform tags:

- 📱 for iOS releases
- 🤖 for Android releases
- 💻 for Desktop/Application releases
- 🔧 UniFi for other releases
