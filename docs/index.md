# UniFi Release Announcer

The announcer queries the UniFi Community GraphQL API every ten minutes and posts new releases to a configured Discord text channel or forum.

The runtime is Rust and uses HTTP only. Discord online presence is not a health signal. Use service logs and completed polls to check health.

The migration preserves Python 0.2.14 selection, URLs, labels, Markdown escaping and emoji. It improves history failure handling and duplicate suppression within a poll.

Start with the [quick start](quickstart.md), then read [configuration](configuration.md) and [deployment](deployment.md).
