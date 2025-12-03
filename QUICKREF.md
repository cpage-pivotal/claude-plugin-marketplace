# Quick Reference Guide

## 🚀 Installation Commands

### From GitHub (after publishing)
```bash
/plugin marketplace add corby/limerick-skill
/plugin install topical-limerick@limerick-skill
```

### From Local Directory
```bash
/plugin marketplace add /Users/corby/Projects/claude/limerick-skill
/plugin install topical-limerick@limerick-skill
```

## 📝 Usage

Simply mention "limerick" in your request:

```
Write a limerick about [topic]
```

## 🔧 Plugin Management

```bash
# List all plugins
/plugin

# List all marketplaces
/plugin marketplace list

# Enable/disable plugin
/plugin enable topical-limerick@limerick-skill
/plugin disable topical-limerick@limerick-skill

# Uninstall plugin
/plugin uninstall topical-limerick@limerick-skill

# Update marketplace
/plugin marketplace update limerick-skill

# Remove marketplace
/plugin marketplace remove limerick-skill
```

## 📂 File Structure

```
limerick-skill/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace configuration
├── plugins/
│   └── topical-limerick/
│       ├── .claude-plugin/
│       │   └── plugin.json       # Plugin manifest
│       └── skills/
│           └── topical-limerick/
│               └── SKILL.md      # Skill definition
├── README.md                     # Main documentation
├── CONTRIBUTING.md               # How to contribute
├── LICENSE                       # MIT License
└── VALIDATION.md                 # Structure validation
```

## 🎯 Key Files

- **marketplace.json** - Defines the marketplace and lists available plugins
- **plugin.json** - Plugin metadata and configuration
- **SKILL.md** - Agent skill definition with workflow instructions
- **README.md** - User documentation and installation guide

## 🔗 Resources

- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)
- [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Agent Skills](https://code.claude.com/docs/en/agent-skills)

