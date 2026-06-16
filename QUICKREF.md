# Quick Reference Guide

## 🚀 Installation Commands

### From GitHub
```bash
/plugin marketplace add cpage-pivotal/claude-plugin-marketplace
/plugin install agent-buildpack@claude-plugin-marketplace
/plugin install cf-space-auditor@claude-plugin-marketplace
/plugin install mailgun@claude-plugin-marketplace
/plugin install google-chat-poster@claude-plugin-marketplace
```

### From Local Directory
```bash
/plugin marketplace add /path/to/claude-plugin-marketplace
/plugin install agent-buildpack@claude-plugin-marketplace
```

## 🔧 Plugin Management

```bash
# List all plugins
/plugin

# List all marketplaces
/plugin marketplace list

# Enable/disable plugin
/plugin enable agent-buildpack@claude-plugin-marketplace
/plugin disable agent-buildpack@claude-plugin-marketplace

# Uninstall plugin
/plugin uninstall agent-buildpack@claude-plugin-marketplace

# Update marketplace
/plugin marketplace update claude-plugin-marketplace

# Remove marketplace
/plugin marketplace remove claude-plugin-marketplace
```

## 📂 File Structure

```
claude-plugin-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace configuration
├── plugins/
│   ├── agent-buildpack/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/
│   │       ├── tanzu-agent-deploy/SKILL.md
│   │       ├── spring-ai-mcp-server/SKILL.md
│   │       └── tanzu-agent-a2a/SKILL.md
│   ├── cf-space-auditor/
│   ├── mailgun/
│   └── google-chat-poster/
├── README.md
└── CONTRIBUTING.md
```

## 🎯 Key Files

- **marketplace.json** - Defines the marketplace and lists available plugins
- **plugin.json** - Plugin metadata and skills list
- **SKILL.md** - Agent skill definition with workflow instructions
- **README.md** - User documentation and installation guide

## 🔗 Resources

- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)
- [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Agent Skills](https://code.claude.com/docs/en/agent-skills)

