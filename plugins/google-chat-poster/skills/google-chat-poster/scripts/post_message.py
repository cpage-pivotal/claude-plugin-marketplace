#!/usr/bin/env python3
"""
Google Chat Message Poster

Posts messages to Google Chat Spaces using the Google Chat API.
Requires environment variable: GOOGLE_CHAT_SPACES (JSON mapping space names to credentials)
"""

import os
import sys
import json
import subprocess


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
    data = json.dumps(payload)

    try:
        # Build curl command
        curl_cmd = [
            "curl",
            "-s",  # Silent mode
            "-w", "\n%{http_code}",  # Write HTTP status code at the end
            "-X", "POST",
            "-H", "Content-Type: application/json",
            "-d", data,
            url
        ]

        # Execute curl command
        result = subprocess.run(
            curl_cmd,
            capture_output=True,
            text=True,
            check=False
        )

        # Parse response - split output and status code
        output_lines = result.stdout.strip().rsplit('\n', 1)
        if len(output_lines) == 2:
            response_body, status_code = output_lines
            status_code = int(status_code)
        else:
            print(f"Error: Failed to parse curl response: {result.stdout}", file=sys.stderr)
            sys.exit(1)

        # Check response
        if status_code == 200:
            try:
                response_data = json.loads(response_body)
                print(f"Message posted successfully to '{space_name}'!")
                print(f"Message name: {response_data.get('name', 'Unknown')}")
                return response_data
            except json.JSONDecodeError:
                print(f"Error: Failed to parse JSON response: {response_body}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Error posting message (HTTP {status_code})", file=sys.stderr)
            print(f"Details: {response_body}", file=sys.stderr)
            sys.exit(1)

    except subprocess.SubprocessError as e:
        print(f"Curl execution error: {str(e)}", file=sys.stderr)
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
