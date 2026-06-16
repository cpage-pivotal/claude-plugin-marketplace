# Mailgun Plugin

Send HTML emails via the Mailgun API directly from Claude Code.

## Installation

```bash
/plugin marketplace add cpage-pivotal/claude-plugin-marketplace
/plugin install mailgun@claude-plugin-marketplace
```

## Configuration

### Required: API Key

Set your Mailgun API key as an environment variable:

```bash
export MAILGUN_API_KEY=key-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Find your API key in the [Mailgun Dashboard](https://app.mailgun.com/) under **Settings → API Keys**. Use your **Private API key**.

### Optional: BCC Address

To automatically BCC every sent email to a fixed address (useful for logging or archiving):

```bash
export MAILGUN_BCC_ADDRESS=archive@example.com
```

### Persisting Environment Variables

Add the exports to your shell profile (`~/.zshrc`, `~/.bashrc`, etc.) so they survive restarts:

```bash
export MAILGUN_API_KEY=key-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export MAILGUN_BCC_ADDRESS=archive@example.com   # optional
```

Or set them in your Claude Code environment configuration.

## Mailgun Domain Setup

> **Note:** The plugin script is preconfigured for the domain `mail.corby.page` with sender `Tanzu Agent <postmaster@corby.page>`. If you use a different Mailgun domain, edit the `url` and `sender` variables at the top of `skills/mailgun/scripts/send_email.py`:
>
> ```python
> url = "https://api.mailgun.net/v3/YOUR-DOMAIN/messages"
> sender = "Your Name <postmaster@YOUR-DOMAIN>"
> ```
>
> Your Mailgun domain must be verified before sending. See [Mailgun domain verification docs](https://documentation.mailgun.com/docs/mailgun/user-manual/sending-domains/).

## Usage

Once installed and configured, just ask Claude Code to send an email naturally:

```
Send an email to alice@example.com about the deployment being complete
Email the team at team@example.com with a summary of today's changes
Notify bob@example.com and carol@example.com that the meeting is rescheduled to 3pm
```

Claude will generate an appropriate subject line and HTML body based on the context of your request.

## What It Does

- Sends rich HTML emails with proper formatting
- Supports single or multiple recipients (comma-separated)
- Generates context-aware subject lines and email bodies
- Optionally BCCs a fixed address for every email sent
- Reports the Mailgun message ID on success

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `API key not provided` | `MAILGUN_API_KEY` not set | Export the variable and restart Claude Code |
| `HTTP 401` | Invalid API key | Verify the key in Mailgun Dashboard → API Keys |
| `HTTP 403` | Domain not authorized | Check that your sending domain is verified in Mailgun |
| `HTTP 400` | Bad request | Usually a malformed recipient address |
