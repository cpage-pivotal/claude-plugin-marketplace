#!/usr/bin/env python3
"""
Send emails via Mailgun API.

Usage:
    python send_email.py <recipient> <subject> <body> [--api-key KEY]
    python send_email.py <recipient1,recipient2> <subject> <body>
"""

import os
import sys
import argparse
import requests


def send_email(recipients, subject, body, api_key=None):
    """
    Send email via Mailgun API.
    
    Args:
        recipients: Single email address or comma-separated list
        subject: Email subject line
        body: Email body text
        api_key: Mailgun API key (defaults to API_KEY env var)
    
    Returns:
        tuple: (success: bool, message: str, response_data: dict)
    """
    # Get API key
    key = api_key or os.getenv('MAILGUN_API_KEY')
    if not key or key == 'MAILGUN_API_KEY':
        return False, "API key not provided. Set MAILGUN_API_KEY environment variable or use --api-key", {}
    
    # Parse recipients (handle comma-separated list)
    if isinstance(recipients, str):
        recipient_list = [r.strip() for r in recipients.split(',')]
    else:
        recipient_list = recipients
    
    # Mailgun API configuration
    url = "https://api.mailgun.net/v3/mail.corby.page/messages"
    sender = "Tanzu Agent <postmaster@corby.page>"
    
    try:
        # Send request to Mailgun
        response = requests.post(
            url,
            auth=("api", key),
            data={
                "from": sender,
                "to": recipient_list,
                "subject": subject,
                "text": body
            },
            timeout=10
        )
        
        # Check response
        if response.status_code == 200:
            data = response.json()
            message_id = data.get('id', 'unknown')
            return True, f"Email sent successfully to {', '.join(recipient_list)}", data
        else:
            return False, f"Failed to send email: {response.status_code} - {response.text}", {}
            
    except requests.exceptions.RequestException as e:
        return False, f"Network error: {str(e)}", {}
    except Exception as e:
        return False, f"Unexpected error: {str(e)}", {}


def main():
    parser = argparse.ArgumentParser(
        description="Send email via Mailgun API",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('recipients', help='Email recipient(s), comma-separated for multiple')
    parser.add_argument('subject', help='Email subject line')
    parser.add_argument('body', help='Email body text')
    parser.add_argument('--api-key', help='Mailgun API key (or use API_KEY env var)')
    
    args = parser.parse_args()
    
    # Send email
    success, message, data = send_email(
        args.recipients,
        args.subject,
        args.body,
        args.api_key
    )
    
    # Print result
    if success:
        print(f"✓ {message}")
        print(f"Message ID: {data.get('id')}")
        return 0
    else:
        print(f"✗ {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
