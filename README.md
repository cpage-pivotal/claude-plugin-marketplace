# Developer Plugin Marketplace

A curated plugin marketplace for Claude Code featuring productivity and integration plugins for AI Developers.

## Overview

This marketplace provides Claude Code plugins for enhancing development workflows with Tanzu Platform integrations and productivity tools.

## Available Plugins

### Agent Buildpack

Build and deploy AI agent demos on Tanzu Platform for Cloud Foundry using the Agent Buildpack and MCP Gateway. This plugin bundles three complementary skills:

- **`tanzu-agent-deploy`** — push agent apps with `cf push`, write/edit `AGENTS.md` and `manifest.yaml`, bind a chat model (GenAI service, user-provided service, or `TANZU_AGENT_*` env vars), and register MCP servers behind an MCP Gateway
- **`spring-ai-mcp-server`** — scaffold a Spring AI 2.0 / Spring Boot 4 MCP server (Streamable-HTTP, `@McpTool`-annotated tools) ready to build, run, and deploy
- **`tanzu-agent-a2a`** — wire up native agent-to-agent (A2A) communication so one agent app can delegate to another as a peer (`a2a-peers.yaml`, `list_a2a_peers` / `call_a2a_peer`)

**Perfect for:** Tanzu Solution Architects building agentic application demos, standing up MCP tool servers, and showcasing multi-agent delegation on Cloud Foundry

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
/plugin install agent-buildpack@claude-plugin-marketplace
/plugin install mailgun@claude-plugin-marketplace
/plugin install google-chat-poster@claude-plugin-marketplace
```

3. **Restart Claude Code** to activate the plugins

4. **Verify installation:**

```bash
/plugin
```

### Usage Examples

**Agent Buildpack:**
```
Deploy this agent with the agent buildpack and bind it to our GenAI service
Scaffold an MCP server exposing weather lookup tools
Set up A2A so the orchestrator agent can delegate to the data agent
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

## How the Plugins Work

Each plugin provides specialized skills that Claude Code automatically activates based on your requests:

- **Agent Buildpack** activates when you mention deploying an agent, `cf push` for an agent buildpack app, scaffolding an MCP server, the MCP Gateway, or agent-to-agent (A2A) delegation
- **Mailgun** activates when you request to send emails and handles API communication with proper formatting
- **Google Chat Poster** activates when you mention posting to Google Chat and manages the API integration

The plugins seamlessly integrate into your Claude Code workflow, requiring no special syntax or commands once installed.

## 🔧 For Plugin Developers

### Repository Structure

```
claude-plugin-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace configuration
├── plugins/
│   ├── agent-buildpack/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/               # three bundled skills
│   │       ├── tanzu-agent-deploy/
│   │       ├── spring-ai-mcp-server/
│   │       └── tanzu-agent-a2a/
│   ├── mailgun/
│   │   └── ...
│   └── google-chat-poster/
│       └── ...
└── README.md
```

### Testing Locally

1. Clone this repository
2. Add as a local marketplace: `/plugin marketplace add ./claude-plugin-marketplace`
3. Install a plugin: `/plugin install agent-buildpack@claude-plugin-marketplace`
4. Test the plugin functionality

### Contributing

To add more plugins to this marketplace:

1. Create a new plugin directory under `plugins/`
2. Add proper `.claude-plugin/plugin.json` manifest
3. Include skills, commands, or agents as needed
4. Update `marketplace.json` with the new plugin entry
5. Submit a pull request

## Use Cases

**Development & Operations:**
- Automate deployment notifications via email or Google Chat
- Send build status updates to team channels
- Notify stakeholders of system events
- Integrate CI/CD pipelines with team communication tools

**Team Communication:**
- Quickly send formatted emails without leaving your development environment
- Post updates to Google Chat Spaces from Claude Code
- Automate routine notifications and reminders

## 🛠️ Marketplace Management

### List all marketplaces
```bash
/plugin marketplace list
```

### Update marketplace metadata
```bash
/plugin marketplace update claude-plugin-marketplace
```

### Remove marketplace
```bash
/plugin marketplace remove claude-plugin-marketplace
```

## 📋 Plugin Management

### List installed plugins
```bash
/plugin
```

### Enable/disable plugin
```bash
/plugin enable agent-buildpack@claude-plugin-marketplace
/plugin disable agent-buildpack@claude-plugin-marketplace
```

### Uninstall plugin
```bash
/plugin uninstall agent-buildpack@claude-plugin-marketplace
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

**Built for Claude Code** - Extend your AI development experience with Tanzu Platform integrations!

