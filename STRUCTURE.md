# Repository Structure

This repository is a **Claude Code Plugin Marketplace** for Tanzu Platform and productivity plugins.

## 📁 Complete Directory Tree

```
claude-plugin-marketplace/
├── .claude-plugin/
│   └── marketplace.json              # Marketplace manifest
│
├── plugins/
│   ├── agent-buildpack/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json           # Plugin manifest
│   │   ├── skills/
│   │   │   ├── tanzu-agent-deploy/
│   │   │   │   └── SKILL.md
│   │   │   ├── spring-ai-mcp-server/
│   │   │   │   └── SKILL.md
│   │   │   └── tanzu-agent-a2a/
│   │   │       └── SKILL.md
│   │   └── README.md
│   ├── tanzu-cost-report/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── skills/
│   │   │   └── cost-optimization-report/
│   │   │       ├── SKILL.md
│   │   │       ├── scripts/          # pull, validate, compute, render
│   │   │       └── references/       # Tanzu Hub GraphQL notes
│   │   └── README.md
│   ├── cf-space-auditor/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/
│   │       └── cf-space-auditor/
│   │           └── SKILL.md
│   ├── google-chat-poster/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/
│   │       └── google-chat-poster/
│   │           └── SKILL.md
│   ├── mailgun/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/
│   │       └── mailgun/
│   │           └── SKILL.md
│
├── .gitignore                        # Git ignore rules
├── CONTRIBUTING.md                   # Contribution guidelines
├── LICENSE                           # MIT License
├── README.md                         # Main marketplace documentation
├── QUICKREF.md                       # Quick reference guide
└── STRUCTURE.md                      # This file
```

## 📄 File Descriptions

### Root Level Files

#### `.claude-plugin/marketplace.json`
The marketplace manifest that defines this repository as a Claude Code plugin marketplace. Contains:
- Marketplace name and owner information
- List of available plugins with their metadata
- Plugin sources and installation information

#### `README.md`
Main documentation for the marketplace including:
- Overview of the marketplace and available plugins
- Installation instructions for users
- Usage examples
- Plugin management commands
- Resource links

#### `CONTRIBUTING.md`
Guidelines for contributing new plugins to this marketplace including:
- What types of plugins are welcome
- How to structure a plugin properly
- Testing requirements
- Submission process
- Quality guidelines

#### `LICENSE`
MIT License for the marketplace and its contents.

#### `.gitignore`
Git ignore rules for editor files, OS files, logs, and temporary files.

#### `QUICKREF.md`
Quick reference guide with common commands and file structure.

### Plugin Files

Each plugin under `plugins/` follows this structure:

```
<plugin-name>/
├── .claude-plugin/
│   └── plugin.json     # Plugin manifest (name, description, version, skills list)
├── skills/
│   └── <skill-name>/
│       └── SKILL.md    # Skill instructions for Claude Code
└── README.md           # Optional plugin documentation
```

## 🔄 How It Works

### Marketplace Flow

1. **User adds marketplace:**
   ```bash
   /plugin marketplace add cpage-pivotal/claude-plugin-marketplace
   ```
   Claude Code reads `.claude-plugin/marketplace.json`

2. **User installs a plugin:**
   ```bash
   /plugin install agent-buildpack@claude-plugin-marketplace
   ```
   Claude Code reads the plugin source path from marketplace.json, copies plugin files, loads plugin.json, and registers all skills.

3. **Claude activates skills automatically** based on recognition patterns defined in each SKILL.md.

## 🎯 Key Concepts

### Marketplace vs Plugin vs Skill

- **Marketplace**: A catalog (this repo) listing available plugins
- **Plugin**: A package that extends Claude Code (e.g., `agent-buildpack`)
- **Skill**: A capability Claude learns from a SKILL.md file

### File Roles

- **marketplace.json**: "Here are the plugins I offer and where to find them"
- **plugin.json**: "I am a plugin that provides these skills"
- **SKILL.md**: "Here's how to perform this specific task"

## 📦 Adding New Plugins

1. Create `plugins/new-plugin/` directory
2. Add `.claude-plugin/plugin.json` manifest
3. Add skills under `skills/<skill-name>/SKILL.md`
4. Update `.claude-plugin/marketplace.json` with new plugin entry
5. Add `plugins/new-plugin/README.md` documentation

See CONTRIBUTING.md for detailed guidelines.

## 🚀 Publishing

Push to GitHub, then users can install with:

```bash
/plugin marketplace add cpage-pivotal/claude-plugin-marketplace
/plugin install agent-buildpack@claude-plugin-marketplace
```

## 🔗 Resources

- [Claude Code Plugin Documentation](https://code.claude.com/docs/en/plugins)
- [Plugin Marketplaces Guide](https://code.claude.com/docs/en/plugin-marketplaces)
- [Agent Skills Documentation](https://code.claude.com/docs/en/agent-skills)
- [Plugins Reference](https://code.claude.com/docs/en/plugins-reference)
