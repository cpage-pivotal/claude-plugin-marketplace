#!/usr/bin/env python3
"""
Google Chat Message Poster

Posts messages to Google Chat Spaces using the Google Chat API.
Requires environment variables: GOOGLE_CHAT_SPACE_ID, GOOGLE_CHAT_KEY, GOOGLE_CHAT_TOKEN
"""

import os
import sys
import json
import urllib.request
import urllib.error


def get_env_vars():
    """Get required environment variables."""
    space_id = os.environ.get('GOOGLE_CHAT_SPACE_ID')
    key = os.environ.get('GOOGLE_CHAT_KEY')
    token = os.environ.get('GOOGLE_CHAT_TOKEN')
    
    if not all([space_id, key, token]):
        print("Error: Missing required environment variables", file=sys.stderr)
        print("Please set: GOOGLE_CHAT_SPACE_ID, GOOGLE_CHAT_KEY, GOOGLE_CHAT_TOKEN", file=sys.stderr)
        sys.exit(1)
    
    return space_id, key, token


def post_message(text):
    """
    Post a text message to Google Chat.
    
    Args:
        text: The message text to post
        
    Returns:
        dict: The response from the Google Chat API
    """
    space_id, key, token = get_env_vars()
    
    # Construct the API URL
    url = f"https://chat.googleapis.com/v1/spaces/{space_id}/messages?key={key}&token={token}"
    
    # Prepare the request payload
    payload = {"text": text}
    data = json.dumps(payload).encode('utf-8')
    
    # Create the request
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        # Send the request
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            print(f"Message posted successfully!")
            print(f"Message name: {response_data.get('name', 'Unknown')}")
            return response_data
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"Error posting message (HTTP {e.code}): {e.reason}", file=sys.stderr)
        print(f"Details: {error_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python post_message.py <message_text>", file=sys.stderr)
        print("Example: python post_message.py 'Hello from the Google Chat API!'", file=sys.stderr)
        sys.exit(1)
    
    message_text = ' '.join(sys.argv[1:])
    post_message(message_text)


if __name__ == '__main__':
    main()
