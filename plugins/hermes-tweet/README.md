# Hermes Tweet Plugin

Guide Hermes Agent setup and X/Twitter workflows through the current Hermes Tweet plugin.

## Installation

```bash
/plugin marketplace add cpage-pivotal/claude-plugin-marketplace
/plugin install hermes-tweet@claude-plugin-marketplace
```

## What It Covers

- Install and enable Hermes Tweet on the Hermes host.
- Discover supported routes locally with `tweet_explore`.
- Route catalog-listed reads through `tweet_read`.
- Keep private reads and mutations behind `tweet_action`.
- Keep `XQUIK_API_KEY` in runtime configuration.
- Require `HERMES_TWEET_ENABLE_ACTIONS=true` for action workflows.

The Claude Code plugin provides guidance. Hermes Tweet executes on the Hermes Agent host.

## Source

- https://github.com/Xquik-dev/hermes-tweet
- https://pypi.org/project/hermes-tweet/

Xquik is an independent third-party service. Not affiliated with X Corp. "Twitter" and "X" are trademarks of X Corp.
