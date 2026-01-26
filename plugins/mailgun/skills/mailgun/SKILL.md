---
name: mailgun
description: Send HTML emails via Mailgun API. Use when the user requests to send an email, notify someone via email, or compose and deliver email messages to recipients. Supports single or multiple recipients with dynamically generated subjects and HTML content based on context.
---

# Mailgun Email Sender

Send HTML emails through the Mailgun API with context-aware subject and body generation. All emails are sent as HTML for rich formatting support.

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

The bundled `send_email.py` script handles all Mailgun API communication and sends HTML emails:

```bash
python3 scripts/send_email.py <recipients> <subject> <html_body>
```

### Arguments

- `recipients`: Single email or comma-separated list (e.g., "user@example.com" or "user1@example.com,user2@example.com")
- `subject`: Email subject line
- `html_body`: Email body in HTML format (supports full HTML markup)
- `--api-key KEY`: Optional API key override (defaults to `API_KEY` env var)

## Examples

### Single Recipient

User request: *"Send an email to cepage@gmail.com about the Q4 architecture review meeting tomorrow at 2pm"*

```bash
python3 scripts/send_email.py \
  "cepage@gmail.com" \
  "Reminder: Q4 Architecture Review Tomorrow" \
  "<html>
<body>
<p>Hi Corby,</p>

<p>This is a reminder about our <strong>Q4 Architecture Review</strong> meeting scheduled for tomorrow at <strong>2:00 PM</strong>.</p>

<p>We'll be covering:</p>
<ul>
  <li>Current platform architecture</li>
  <li>Proposed improvements</li>
  <li>Migration strategy</li>
  <li>Q&amp;A session</li>
</ul>

<p>Looking forward to seeing you there!</p>

<p>Best regards,<br>
Tanzu Agent</p>
</body>
</html>"
```

### Multiple Recipients

User request: *"Email the team about the deployment being complete"*

```bash
python3 scripts/send_email.py \
  "cepage@gmail.com,team@example.com,manager@example.com" \
  "Deployment Complete: Production Environment" \
  "<html>
<body>
<p>Hi Team,</p>

<p>The production deployment has been completed successfully. All services are running normally.</p>

<p>Best regards,<br>
Tanzu Agent</p>
</body>
</html>"
```

## Content Generation Guidelines

**Subject Lines:**
- Keep concise (under 60 characters)
- Make purpose immediately clear
- Professional but friendly tone
- Examples: "Meeting Reminder: Q4 Planning", "Update: Deployment Status"

**HTML Email Body:**
- Always wrap content in `<html><body>...</body></html>` tags
- Use `<p>` tags for paragraphs
- Use `<strong>` for bold and `<em>` for italic text
- Use `<ul>` and `<li>` for bullet lists, `<ol>` for numbered lists
- Use `<br>` for line breaks within paragraphs
- Use `<a href="...">` for hyperlinks
- Escape special characters (e.g., `&amp;` for &)
- Start with appropriate greeting
- State purpose clearly upfront
- Include relevant context from the user's request
- Close professionally

## Notes

- Script handles single recipients or comma-separated lists
- API key via `MAILGUN_API_KEY` environment variable (or `--api-key` argument)
- Script outputs success/failure status and Mailgun message ID
- All emails sent from `Tanzu Agent <postmaster@corby.page>`
- If `MAILGUN_BCC_ADDRESS` is set, all emails are automatically BCC'd to that address
