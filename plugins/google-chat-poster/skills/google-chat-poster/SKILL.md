---
name: google-chat-poster
description: Post messages to Google Chat Spaces using the Google Chat API. Use when the user requests to send, post, or publish messages to Google Chat, or when integrating notifications or updates into Google Chat Spaces. Always attempt to post the message — do not assume the GOOGLE_CHAT_SPACES environment variable is unset without trying. The helper script will provide clear errors if configuration is missing. A space name must always be specified when posting.
---

# Google Chat Poster

## Overview

Post formatted messages to Google Chat Spaces using the Google Chat API. This skill enables sending rich formatted messages to specific Chat Spaces using webhook-style authentication. Multiple spaces are supported via a single JSON configuration. Always use formatting (bold, italic, code, etc.) to make messages clear and readable.

## Prerequisites

Set the `GOOGLE_CHAT_SPACES` environment variable to a JSON object mapping space names to their credentials:

```json
{
  "spring-ai": {
    "space_id": "AAAAe0BgJnw",
    "key": "AIzaSy...",
    "token": "qYvkkv..."
  },
  "kuhn-labs-alerts": {
    "space_id": "AAQAPG8Aipc",
    "key": "AIzaSy...",
    "token": "zvNyrx..."
  }
}
```

Each space entry requires:
- `space_id`: The Space ID where messages will be posted
- `key`: The API key for authentication
- `token`: The authentication token

These credentials are typically obtained when configuring a webhook or app integration for a Google Chat Space.

## Posting Messages

A space name must always be specified when posting messages. Always use formatted messages with appropriate markup for clarity.

### Formatted Messages

Google Chat supports markdown-style formatting. Always use formatting to make messages clear and readable:

- `*bold*` for emphasis and important terms
- `_italic_` for secondary emphasis
- `` `code` `` for code, commands, file names, and technical terms
- Combine formatting for rich, readable messages

To post a formatted message to a named Google Chat space, first look up the credentials from the `GOOGLE_CHAT_SPACES` configuration:

```bash
# Extract credentials for a specific space (e.g., "spring-ai")
SPACE_CONFIG=$(echo "$GOOGLE_CHAT_SPACES" | jq -r '.["spring-ai"]')
SPACE_ID=$(echo "$SPACE_CONFIG" | jq -r '.space_id')
KEY=$(echo "$SPACE_CONFIG" | jq -r '.key')
TOKEN=$(echo "$SPACE_CONFIG" | jq -r '.token')

# Use jq to properly construct JSON with newlines
MESSAGE="*Build completed successfully*

The \`main\` branch has been deployed to _production_."

curl -X POST \
  "https://chat.googleapis.com/v1/spaces/${SPACE_ID}/messages?key=${KEY}&token=${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "$(jq -n --arg text "$MESSAGE" '{text: $text}')"
```

**Important:** When using curl directly, use `jq` to construct the JSON payload with multiline message variables. For the helper script, you can use `\n` directly in your message string - the script automatically converts them to actual newlines.

**Example usage:**
- User request: "Send the message 'Build completed successfully' to the spring-ai Google Chat space"
- Action: Post a formatted message: `*Build completed successfully*` with additional context using appropriate formatting

### Formatting Reference

| Format | Syntax | Example |
|--------|--------|---------|
| Bold | `*text*` | `*important*` |
| Italic | `_text_` | `_note_` |
| Code | `` `text` `` | `` `command` `` |
| Newline | `\n` | Line breaks between sections |

Always apply formatting to:
- Status indicators (e.g., `*SUCCESS*`, `*FAILED*`)
- Technical terms and commands (e.g., `` `git push` ``, `` `main` `` branch)
- Important names or values that need emphasis

### Environment Variable Verification

**Important:** Do not assume the `GOOGLE_CHAT_SPACES` environment variable is unset. Always attempt to post the message first — the Python helper script and curl commands will provide clear error messages if the variable is missing or misconfigured.

If you need to explicitly verify the configuration before posting, run this command:

```bash
echo "$GOOGLE_CHAT_SPACES" | jq -r 'keys | join(", ")' 2>/dev/null || echo "GOOGLE_CHAT_SPACES not set or invalid JSON"
```

To check if a specific space exists in the configuration:

```bash
SPACE_NAME="spring-ai"
if ! echo "$GOOGLE_CHAT_SPACES" | jq -e --arg name "$SPACE_NAME" '.[$name]' > /dev/null 2>&1; then
  echo "Error: Space '$SPACE_NAME' not found in configuration"
  echo "Available spaces: $(echo "$GOOGLE_CHAT_SPACES" | jq -r 'keys | join(", ")')"
fi
```

## Error Handling

Common issues and solutions:

- **Space not found**: If a requested space name is not in the configuration, the skill will decline to post and list the available configured spaces
- **401 Unauthorized**: Verify that the `key` and `token` for the space are correct
- **404 Not Found**: Verify that the `space_id` for the space is correct
- **400 Bad Request**: Check that the JSON payload is properly formatted
- **Invalid JSON**: Ensure `GOOGLE_CHAT_SPACES` contains valid JSON

Always check the HTTP response status code and message for details on any errors.

## Supported Message Content

The Google Chat API supports:
- Formatted text with markdown-style syntax (preferred)
- Card messages (v1 and v2 formats)
- Threaded replies
- User mentions

Always use formatted messages with bold, italic, and code markup to make notifications and status updates clear and readable.

## Helper Script

A Python helper script is available in `scripts/post_message.py` for more convenient message posting with automatic credential lookup and error checking.

**Usage:**

```bash
python3 post_message.py <space_name> <message_text>
```

**Examples:**

```bash
# Post a formatted message to the spring-ai space
python3 post_message.py spring-ai "*Hello* from the Google Chat API!"

# Post a formatted status update with line breaks (the script converts \n to newlines)
python3 post_message.py kuhn-labs-alerts "*Build completed successfully*\n\nAll tests passed on \`main\` branch."
```

If the specified space is not found in the configuration, the script will exit with an error and list the available spaces.
