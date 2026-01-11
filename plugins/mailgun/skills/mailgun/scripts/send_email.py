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
import subprocess
import json


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
    
    # Get optional BCC address
    bcc_address = os.getenv('MAILGUN_BCC_ADDRESS')
    if bcc_address:
        print(f"[DEBUG] MAILGUN_BCC_ADDRESS is set: {bcc_address}")
    else:
        print("[DEBUG] MAILGUN_BCC_ADDRESS is not set")
    
    # Mailgun API configuration
    url = "https://api.mailgun.net/v3/mail.corby.page/messages"
    sender = "Tanzu Agent <postmaster@corby.page>"
    
    # Build request data
    request_data = {
        "from": sender,
        "to": recipient_list,
        "subject": subject,
        "text": body
    }
    
    # Add BCC if configured
    if bcc_address:
        request_data["bcc"] = bcc_address
    
    try:
        # Build curl command
        curl_cmd = [
            "curl",
            "-s",  # Silent mode
            "-w", "\n%{http_code}",  # Write HTTP status code at the end
            "-u", f"api:{key}",  # Basic auth
            "--max-time", "10"  # Timeout
        ]

        # Add form data for each field
        curl_cmd.extend(["-F", f"from={request_data['from']}"])
        curl_cmd.extend(["-F", f"subject={subject}"])
        curl_cmd.extend(["-F", f"text={body}"])

        # Add recipients (multiple -F flags for each recipient)
        for recipient in recipient_list:
            curl_cmd.extend(["-F", f"to={recipient}"])

        # Add BCC if configured
        if bcc_address:
            curl_cmd.extend(["-F", f"bcc={bcc_address}"])

        # Add URL
        curl_cmd.append(url)

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
            return False, f"Failed to parse curl response: {result.stdout}", {}

        # Check response
        if status_code == 200:
            try:
                data = json.loads(response_body)
                message_id = data.get('id', 'unknown')
                return True, f"Email sent successfully to {', '.join(recipient_list)}", data
            except json.JSONDecodeError:
                return False, f"Failed to parse JSON response: {response_body}", {}
        else:
            return False, f"Failed to send email: {status_code} - {response_body}", {}

    except subprocess.SubprocessError as e:
        return False, f"Curl execution error: {str(e)}", {}
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
        bcc = os.getenv('MAILGUN_BCC_ADDRESS')
        if bcc:
            print(f"BCC: {bcc}")
        return 0
    else:
        print(f"✗ {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
