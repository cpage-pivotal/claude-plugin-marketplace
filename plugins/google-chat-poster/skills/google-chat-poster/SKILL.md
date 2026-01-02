---
name: google-chat-poster
description: Post messages to Google Chat Spaces using the Google Chat API. Use when the user requests to send, post, or publish messages to Google Chat, or when integrating notifications or updates into Google Chat Spaces. Requires environment variables GOOGLE_CHAT_SPACE_ID, GOOGLE_CHAT_KEY, and GOOGLE_CHAT_TOKEN for authentication.
---

# Google Chat Poster

## Overview

Post messages to Google Chat Spaces using the Google Chat API. This skill enables sending plain text messages and formatted messages with cards to specific Chat Spaces using webhook-style authentication.

## Prerequisites

Ensure the following environment variables are set:

- `GOOGLE_CHAT_SPACE_ID`: The Space ID where messages will be posted
- `GOOGLE_CHAT_KEY`: The API key for authentication
- `GOOGLE_CHAT_TOKEN`: The authentication token

These credentials are typically obtained when configuring a webhook or app integration for a Google Chat Space.

## Posting Messages

### Basic Text Messages

To post a plain text message to Google Chat:

```bash
curl -X POST \
  "https://chat.googleapis.com/v1/spaces/${GOOGLE_CHAT_SPACE_ID}/messages?key=${GOOGLE_CHAT_KEY}&token=${GOOGLE_CHAT_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Your message text here"
  }'
```

**Example usage:**
- User request: "Send the message 'Build completed successfully' to Google Chat"
- Action: Post the message using the curl command above with the appropriate text

### Messages with Formatting

Google Chat supports basic markdown-style formatting in text messages:

```bash
curl -X POST \
  "https://chat.googleapis.com/v1/spaces/${GOOGLE_CHAT_SPACE_ID}/messages?key=${GOOGLE_CHAT_KEY}&token=${GOOGLE_CHAT_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "*Bold text*, _italic text_, and `code formatting`"
  }'
```

### Environment Variable Verification

Before posting messages, verify that the required environment variables are set:

```bash
if [ -z "$GOOGLE_CHAT_SPACE_ID" ] || [ -z "$GOOGLE_CHAT_KEY" ] || [ -z "$GOOGLE_CHAT_TOKEN" ]; then
  echo "Error: Required environment variables not set"
  echo "Please set: GOOGLE_CHAT_SPACE_ID, GOOGLE_CHAT_KEY, GOOGLE_CHAT_TOKEN"
  exit 1
fi
```

## Error Handling

Common issues and solutions:

- **401 Unauthorized**: Verify that GOOGLE_CHAT_KEY and GOOGLE_CHAT_TOKEN are correct
- **404 Not Found**: Verify that GOOGLE_CHAT_SPACE_ID is correct
- **400 Bad Request**: Check that the JSON payload is properly formatted

Always check the HTTP response status code and message for details on any errors.

## Supported Message Content

The Google Chat API supports:
- Plain text messages
- Formatted text with basic markdown
- Card messages (v1 and v2 formats)
- Threaded replies
- User mentions

For simple notifications and status updates, plain text messages are typically sufficient.

## Helper Script

A Python helper script is available in `scripts/post_message.py` for more convenient message posting with automatic environment variable handling and error checking.
