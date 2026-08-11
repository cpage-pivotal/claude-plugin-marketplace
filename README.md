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

### Tanzu Cost Report

Generate a cost optimization report for a Tanzu Platform estate from Tanzu Hub's entity graph and Telemetry pricing data, rendered as a self-contained HTML artifact:

- **Findings in three tiers** — broken/wasted apps, stale apps, and orphaned service instances, deduplicated so an app that's both routeless and crash-looping counts once
- **Modeled vs. live-metered cost** kept as distinct numbers, with explicit metering-coverage tiles
- **Rate card coverage** resolved through `ServiceInstance → ServicePlan → ServicePlanGroup`, so "unpriced because no rate card exists" is separated from "$0 because idle"
- **Top spenders** by space and org
- **A preflight validator** that fails loudly on the input problems that have previously shipped wrong figures

Requires a `tanzu-hub` MCP server connected in your session — configure that separately (see the plugin README). All queries are read-only.

**Perfect for:** Platform teams and FinOps reviews that need a defensible picture of what a Tanzu foundation is spending and what can be safely reclaimed

### Mailgun

Send emails via the Mailgun API directly from Claude Code. This plugin enables:

- **Email sending** to single or multiple recipients
- **Context-aware content** with dynamically generated subjects and bodies
- **Professional formatting** with proper greetings and closings
- **Environment-based authentication** using MAILGUN_API_KEY

**Perfect for:** Automated notifications, team communications, workflow integrations, email automation

### Application Advisor

Automate Spring dependency upgrades using [Broadcom Application Advisor](https://techdocs.broadcom.com/us/en/vmware-tanzu/spring/application-advisor/1-6/app-advisor/what-is-app-advisor.html). This plugin guides you through the full integration:

- **Registry token setup** — obtain credentials from the Broadcom Support Portal
- **Maven configuration** — add the enterprise repository and credentials to `settings.xml` and `pom.xml`
- **CLI installation** — download the `advisor` binary for your OS/architecture
- **Upgrade plans** — run `advisor upgrade-plan get` and interpret results, including blocked dependency handling
- **GitHub Actions workflow** — CI integration that opens upgrade PRs automatically on every push to `main`
- **OpenRewrite recipes** — run Broadcom's commercial Spring Boot 4.x upgrade recipes directly when the advisor can't orchestrate an upgrade automatically

**Perfect for:** Spring Boot application teams that want incremental, automated dependency upgrades with minimal manual intervention

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
/plugin install tanzu-cost-report@claude-plugin-marketplace
/plugin install application-advisor@claude-plugin-marketplace
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

**Tanzu Cost Report:**
```
Generate a cost optimization report for our Tanzu foundations
Refresh the Tanzu cost report with a 90-day staleness threshold
Which orphaned service instances are costing us the most?
```

**Application Advisor:**
```
Set up Application Advisor for this Spring Boot project
Add a GitHub workflow to automate Spring dependency upgrades
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
- **Tanzu Cost Report** activates when you ask for, refresh, or regenerate a Tanzu cost/FinOps report, or ask about wasted apps, stale apps, or orphaned service instances across foundations
- **Application Advisor** activates when you mention Spring upgrades, Application Advisor, the advisor CLI, Broadcom registry tokens, or automating dependency bumps
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
│   ├── tanzu-cost-report/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/
│   │       └── cost-optimization-report/
│   │           ├── SKILL.md
│   │           ├── scripts/      # pull, validate, compute, render
│   │           └── references/   # Tanzu Hub GraphQL notes
│   ├── application-advisor/
│   │   └── skills/
│   │       └── application-advisor/
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

