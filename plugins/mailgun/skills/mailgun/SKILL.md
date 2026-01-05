---
name: mailgun
description: Send emails via Mailgun API. Use when the user requests to send an email, notify someone via email, or compose and deliver email messages to recipients. Supports single or multiple recipients with dynamically generated subjects and content based on context.
---

# Mailgun Email Sender

Send emails through the Mailgun API with context-aware subject and body generation.

## Configuration

- **API Endpoint**: `https://api.mailgun.net/v3/mail.corby.page/messages`
- **Sender**: `Tanzu Agent <postmaster@corby.page>`
- **Authentication**: API key required via `MAILGUN_API_KEY` environment variable or `--api-key` argument
- **BCC** (optional): Set `MAILGUN_BCC_ADDRESS` environment variable to automatically BCC all sent emails to a specified address

## Workflow

When the user requests sending an email:

1. **Identify recipients**: Extract email addresses from the request
2. **Generate content**: Create an appropriate subject line and email body based on context
3. **Execute script**: Use `scripts/send_email.py` to send the email

## Script Usage

The bundled `send_email.py` script handles all Mailgun API communication:

```bash
python scripts/send_email.py <recipients> <subject> <body>
```

### Arguments

- `recipients`: Single email or comma-separated list (e.g., "user@example.com" or "user1@example.com,user2@example.com")
- `subject`: Email subject line
- `body`: Email body text
- `--api-key KEY`: Optional API key override (defaults to `API_KEY` env var)

## Examples

### Single Recipient

User request: *"Send an email to cepage@gmail.com about the Q4 architecture review meeting tomorrow at 2pm"*

```bash
python scripts/send_email.py \
  "cepage@gmail.com" \
  "Reminder: Q4 Architecture Review Tomorrow" \
  "Hi Corby,

This is a reminder about our Q4 Architecture Review meeting scheduled for tomorrow at 2:00 PM.

We'll be covering:
- Current platform architecture
- Proposed improvements
- Migration strategy
- Q&A session

Looking forward to seeing you there!

Best regards,
Tanzu Agent"
```

### Multiple Recipients

User request: *"Email the team about the deployment being complete"*

```bash
python scripts/send_email.py \
  "cepage@gmail.com,team@example.com,manager@example.com" \
  "Deployment Complete: Production Environment" \
  "Hi Team,

The production deployment has been completed successfully. All services are running normally.

Best regards,
Tanzu Agent"
```

## Content Generation Guidelines

**Subject Lines:**
- Keep concise (under 60 characters)
- Make purpose immediately clear
- Professional but friendly tone
- Examples: "Meeting Reminder: Q4 Planning", "Update: Deployment Status"

**Email Body:**
- Start with appropriate greeting
- State purpose clearly upfront
- Use paragraphs for readability
- Include relevant context from the user's request
- Close professionally
- Keep natural and contextual, not templated

## Notes

- Script handles single recipients or comma-separated lists
- API key via `MAILGUN_API_KEY` environment variable (or `--api-key` argument)
- Script outputs success/failure status and Mailgun message ID
- All emails sent from `Tanzu Agent <postmaster@corby.page>`
- If `MAILGUN_BCC_ADDRESS` is set, all emails are automatically BCC'd to that address
