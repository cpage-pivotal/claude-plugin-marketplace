#!/usr/bin/env python3
"""
Google Chat Message Poster

Posts messages to Google Chat Spaces using the Google Chat API.
Requires environment variable: GOOGLE_CHAT_SPACES (JSON mapping space names to credentials)
"""

import os
import sys
import json
import urllib.request
import urllib.error


def get_spaces_config():
    """Get and parse the GOOGLE_CHAT_SPACES configuration."""
    spaces_json = os.environ.get('GOOGLE_CHAT_SPACES')
    
    if not spaces_json:
        print("Error: GOOGLE_CHAT_SPACES environment variable not set", file=sys.stderr)
        print("Please set GOOGLE_CHAT_SPACES to a JSON object mapping space names to credentials.", file=sys.stderr)
        print('Example: {"my-space": {"space_id": "...", "key": "...", "token": "..."}}', file=sys.stderr)
        sys.exit(1)
    
    try:
        config = json.loads(spaces_json)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in GOOGLE_CHAT_SPACES: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not isinstance(config, dict) or not config:
        print("Error: GOOGLE_CHAT_SPACES must be a non-empty JSON object", file=sys.stderr)
        sys.exit(1)
    
    return config


def get_space_credentials(space_name):
    """Get credentials for a specific space by name."""
    config = get_spaces_config()
    
    if space_name not in config:
        available = ', '.join(sorted(config.keys()))
        print(f"Error: Space '{space_name}' not found in configuration", file=sys.stderr)
        print(f"Available spaces: {available}", file=sys.stderr)
        sys.exit(1)
    
    space_config = config[space_name]
    
    required_keys = ['space_id', 'key', 'token']
    missing = [k for k in required_keys if k not in space_config]
    
    if missing:
        print(f"Error: Space '{space_name}' is missing required keys: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
    
    return space_config['space_id'], space_config['key'], space_config['token']


def post_message(space_name, text):
    """
    Post a text message to a named Google Chat space.
    
    Args:
        space_name: The name of the space (as defined in GOOGLE_CHAT_SPACES)
        text: The message text to post
        
    Returns:
        dict: The response from the Google Chat API
    """
    space_id, key, token = get_space_credentials(space_name)
    
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
            print(f"Message posted successfully to '{space_name}'!")
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
    if len(sys.argv) < 3:
        print("Usage: python post_message.py <space_name> <message_text>", file=sys.stderr)
        print("Example: python post_message.py spring-ai 'Hello from the Google Chat API!'", file=sys.stderr)
        sys.exit(1)
    
    space_name = sys.argv[1]
    message_text = ' '.join(sys.argv[2:])
    post_message(space_name, message_text)


if __name__ == '__main__':
    main()
