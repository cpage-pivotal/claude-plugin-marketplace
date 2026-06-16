# Google Chat Poster Plugin

Post messages to Google Chat Spaces using the Google Chat API directly from Claude Code.

## Installation

```bash
/plugin marketplace add cpage-pivotal/claude-plugin-marketplace
/plugin install google-chat-poster@claude-plugin-marketplace
```

## Configuration

### Required: Space Credentials

Set the `GOOGLE_CHAT_SPACES` environment variable to a JSON object mapping space names to their credentials:

```bash
export GOOGLE_CHAT_SPACES='{
  "my-space": {
    "space_id": "AAAAe0BgJnw",
    "key": "AIzaSy...",
    "token": "qYvkkv..."
  },
  "alerts": {
    "space_id": "AAQAPG8Aipc",
    "key": "AIzaSy...",
    "token": "zvNyrx..."
  }
}'
```

Each entry requires:
- **`space_id`** — the ID of the Google Chat Space (e.g. `AAAAe0BgJnw`)
- **`key`** — the Google API key
- **`token`** — the authentication token

You can configure as many spaces as you like. The name you give each entry (e.g. `"my-space"`) is how you'll refer to it when asking Claude to post a message.

### Getting Credentials

Credentials come from configuring an **Incoming Webhook** or **App** integration on a Google Chat Space:

1. Open [Google Chat](https://chat.google.com) and go to the Space
2. Click the Space name at the top → **Apps & Integrations** → **Add webhooks**
3. Create a new webhook — Google will give you a webhook URL in this format:
   ```
   https://chat.googleapis.com/v1/spaces/{space_id}/messages?key={key}&token={token}
   ```
4. Extract the three values from that URL and add them to `GOOGLE_CHAT_SPACES`

### Persisting Environment Variables

Because the value is JSON, it's easiest to store it in a file and source it:

```bash
# ~/.config/google-chat-spaces.env
export GOOGLE_CHAT_SPACES='{
  "my-space": {
    "space_id": "AAAAe0BgJnw",
    "key": "AIzaSy...",
    "token": "qYvkkv..."
  }
}'
```

Then add to your shell profile (`~/.zshrc`, `~/.bashrc`):

```bash
source ~/.config/google-chat-spaces.env
```

Or set it in your Claude Code environment configuration.

## Usage

Once installed and configured, ask Claude Code to post naturally — always name the target space:

```
Post "Deployment complete" to the my-space Google Chat space
Send a build status update to alerts
Post a formatted message to my-space summarizing today's changes
```

Claude will apply appropriate Google Chat formatting (bold, italic, code) to make messages clear and readable.

## What It Does

- Posts formatted text messages to any configured Google Chat Space
- Supports Google Chat markdown: `*bold*`, `_italic_`, `` `code` ``
- Lists available spaces when a requested space is not found
- Reports the message name on success

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `GOOGLE_CHAT_SPACES not set` | Variable not exported | Export it and restart Claude Code |
| `Space 'x' not found` | Name not in config | Check available names: `echo "$GOOGLE_CHAT_SPACES" \| jq 'keys'` |
| `HTTP 401 Unauthorized` | Wrong `key` or `token` | Regenerate the webhook in Google Chat and update the values |
| `HTTP 404 Not Found` | Wrong `space_id` | Verify the space ID from the webhook URL |
| `Invalid JSON` | Malformed `GOOGLE_CHAT_SPACES` | Validate with `echo "$GOOGLE_CHAT_SPACES" \| jq .` |
