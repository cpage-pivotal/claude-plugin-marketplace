# Tanzu Platform Plugin Marketplace

A curated plugin marketplace for Claude Code featuring productivity and integration plugins for Tanzu Platform.

## Overview

This marketplace provides Claude Code plugins for enhancing development workflows with Tanzu Platform integrations and creative tools.

## Available Plugins

### CF Space Auditor

Audit Cloud Foundry spaces for compliance with organizational standards. This plugin performs:

- **Memory allocation compliance** checks (Java apps: 1024M, Non-Java apps: 512M)
- **Instance count monitoring** to identify multi-instance deployments
- **Deployment staleness detection** for apps not updated in 180+ days
- **Detailed compliance reports** with specific findings for each app

**Perfect for:** Cloud Foundry compliance audits, space governance, identifying configuration drift, maintaining deployment standards

### Mailgun

Send emails via the Mailgun API directly from Claude Code. This plugin enables:

- **Email sending** to single or multiple recipients
- **Context-aware content** with dynamically generated subjects and bodies
- **Professional formatting** with proper greetings and closings
- **Environment-based authentication** using MAILGUN_API_KEY

**Perfect for:** Automated notifications, team communications, workflow integrations, email automation

### Google Chat Poster

Post messages to Google Chat Spaces using the Google Chat API. This plugin provides:

- **Direct posting** to Google Chat Spaces
- **Text and formatted messages** with markdown support
- **Webhook-based authentication** for easy integration
- **Error handling** with clear feedback

**Perfect for:** Team notifications, build status updates, CI/CD integrations, workflow alerts

### Topical Limerick

Write entertaining limericks that blend any requested topic with current news and events. This plugin adds an AI skill that:

- **Searches recent news** automatically for topical references
- **Follows proper limerick structure** (AABBA rhyme scheme, anapestic meter)
- **Incorporates specific details** from current events
- **Maintains humor and wit** with surprising, clever endings

**Perfect for:** Creative writing, entertainment, making technical topics fun, social media content, presentations

## 🚀 Quick Start

### Installation

1. **Add this marketplace to Claude Code:**

```bash
/plugin marketplace add cpage-pivotal/claude-plugin-marketplace
```

Or if you've cloned this repository locally:

```bash
/plugin marketplace add /path/to/claude-plugin-marketplace
```

2. **Install one or more plugins:**

```bash
# Install all plugins
/plugin install cf-space-auditor@claude-plugin-marketplace
/plugin install mailgun@claude-plugin-marketplace
/plugin install google-chat-poster@claude-plugin-marketplace
/plugin install topical-limerick@claude-plugin-marketplace
```

3. **Restart Claude Code** to activate the plugins

4. **Verify installation:**

```bash
/plugin
```

### Usage Examples

**CF Space Auditor:**
```
Audit the development space in our production org
Check compliance for the staging space
```

**Mailgun:**
```
Send an email to team@example.com about the deployment being complete
```

**Google Chat Poster:**
```
Post "Build completed successfully" to Google Chat
Send a message to Google Chat about the deployment status
```

**Topical Limerick:**
```
Create a limerick about SpaceX
Limerick about the latest AI news
```

## How the Plugins Work

Each plugin provides specialized skills that Claude Code automatically activates based on your requests:

- **CF Space Auditor** activates when you mention "audit" with a CF space and performs compliance checks against organizational standards
- **Mailgun** activates when you request to send emails and handles API communication with proper formatting
- **Google Chat Poster** activates when you mention posting to Google Chat and manages the API integration
- **Topical Limerick** activates when you mention "limerick" and searches for current news to create topical poetry

The plugins seamlessly integrate into your Claude Code workflow, requiring no special syntax or commands once installed.

## 🔧 For Plugin Developers

### Repository Structure

```
tanzu-platform-plugins/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace configuration
├── plugins/
│   ├── topical-limerick/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json       # Plugin metadata
│   │   └── skills/
│   │       └── topical-limerick/
│   │           └── SKILL.md      # Skill definition
│   ├── mailgun/
│   │   └── ...
│   └── google-chat-poster/
│       └── ...
└── README.md
```

### Testing Locally

1. Clone this repository
2. Add as a local marketplace: `/plugin marketplace add ./tanzu-platform-plugins`
3. Install a plugin: `/plugin install topical-limerick@tanzu-platform-plugins`
4. Test the plugin functionality

### Contributing

To add more plugins to this marketplace:

1. Create a new plugin directory under `plugins/`
2. Add proper `.claude-plugin/plugin.json` manifest
3. Include skills, commands, or agents as needed
4. Update `marketplace.json` with the new plugin entry
5. Submit a pull request

## Use Cases

**Cloud Foundry Governance:**
- Audit CF spaces for compliance with organizational standards
- Identify configuration drift across applications
- Monitor deployment hygiene and detect stale applications
- Enforce memory allocation policies across environments

**Development & Operations:**
- Automate deployment notifications via email or Google Chat
- Send build status updates to team channels
- Notify stakeholders of system events
- Integrate CI/CD pipelines with team communication tools

**Team Communication:**
- Quickly send formatted emails without leaving your development environment
- Post updates to Google Chat Spaces from Claude Code
- Automate routine notifications and reminders

**Creative & Content:**
- Generate entertaining limericks for technical topics
- Create memorable content for presentations and documentation
- Add humor to technical discussions and social media

## 🛠️ Marketplace Management

### List all marketplaces
```bash
/plugin marketplace list
```

### Update marketplace metadata
```bash
/plugin marketplace update tanzu-platform-plugins
```

### Remove marketplace
```bash
/plugin marketplace remove tanzu-platform-plugins
```

## 📋 Plugin Management

### List installed plugins
```bash
/plugin
```

### Enable/disable plugin
```bash
/plugin enable topical-limerick@tanzu-platform-plugins
/plugin disable topical-limerick@tanzu-platform-plugins
```

### Uninstall plugin
```bash
/plugin uninstall topical-limerick@tanzu-platform-plugins
```

## 🔗 Resources

- [Claude Code Plugin Documentation](https://code.claude.com/docs/en/plugins)
- [Plugin Marketplaces Guide](https://code.claude.com/docs/en/plugin-marketplaces)
- [Agent Skills Documentation](https://code.claude.com/docs/en/agent-skills)

## 📄 License

MIT License - See plugin manifests for individual plugin licenses

## 👤 Author

**Corby**

---

**Built for Claude Code** - Extend your AI development experience with creative writing capabilities!

