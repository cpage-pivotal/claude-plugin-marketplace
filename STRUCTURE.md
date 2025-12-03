# Repository Structure

This repository is now a **Claude Code Plugin Marketplace** that distributes the Topical Limerick plugin.

## 📁 Complete Directory Tree

```
limerick-skill/
├── .claude-plugin/
│   └── marketplace.json              # Marketplace manifest
│
├── plugins/
│   └── topical-limerick/
│       ├── .claude-plugin/
│       │   └── plugin.json           # Plugin manifest
│       ├── skills/
│       │   └── topical-limerick/
│       │       └── SKILL.md          # Skill definition
│       └── README.md                 # Plugin documentation
│
├── .gitignore                        # Git ignore rules
├── CONTRIBUTING.md                   # Contribution guidelines
├── LICENSE                           # MIT License
├── README.md                         # Main marketplace documentation
├── QUICKREF.md                       # Quick reference guide
├── STRUCTURE.md                      # This file
└── VALIDATION.md                     # Structure validation report
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

#### `VALIDATION.md`
Validation report confirming the marketplace structure is correct.

### Plugin Files

#### `plugins/topical-limerick/.claude-plugin/plugin.json`
Plugin manifest containing:
- Plugin name, description, and version
- Author information
- Keywords and category
- Skills directory reference

#### `plugins/topical-limerick/skills/topical-limerick/SKILL.md`
Agent skill definition that teaches Claude Code how to:
- Write properly-formatted limericks
- Search for current news about topics
- Incorporate topical references
- Follow limerick structure (AABBA rhyme, anapestic meter)

#### `plugins/topical-limerick/README.md`
Plugin-specific documentation including:
- Feature overview
- Installation instructions
- Usage examples
- Troubleshooting guide

## 🔄 How It Works

### Marketplace Flow

1. **User adds marketplace:**
   ```bash
   /plugin marketplace add corby/limerick-skill
   ```
   Claude Code reads `.claude-plugin/marketplace.json`

2. **User installs plugin:**
   ```bash
   /plugin install topical-limerick@limerick-skill
   ```
   Claude Code:
   - Reads the plugin source path from marketplace.json
   - Copies plugin files to Claude's plugin directory
   - Loads the plugin.json manifest
   - Registers the skills directory

3. **User requests a limerick:**
   ```
   Write a limerick about AI
   ```
   Claude Code:
   - Recognizes "limerick" keyword
   - Activates the topical-limerick skill
   - Follows SKILL.md workflow
   - Searches web for AI news
   - Crafts limerick with topical references

### Plugin Structure

```
topical-limerick/
├── .claude-plugin/          # Configuration
│   └── plugin.json          # Tells Claude what this plugin provides
└── skills/                  # Skills directory
    └── topical-limerick/    # Individual skill
        └── SKILL.md         # Skill instructions for Claude
```

The plugin uses **Agent Skills** - Claude reads SKILL.md and learns:
- When to activate (recognition patterns)
- What workflow to follow (research → craft → format)
- Best practices (be specific, timely, clever)
- Format requirements (AABBA rhyme, meter)

## 🎯 Key Concepts

### Marketplace vs Plugin vs Skill

- **Marketplace**: A catalog (this repo) that lists available plugins
- **Plugin**: A package (topical-limerick) that extends Claude Code
- **Skill**: A capability (writing limericks) that Claude learns from SKILL.md

### File Roles

- **marketplace.json**: "Here are the plugins I offer and where to find them"
- **plugin.json**: "I am a plugin that provides these capabilities"
- **SKILL.md**: "Here's how to perform this specific task"

## 📦 Adding New Plugins

To add more plugins to this marketplace:

1. Create `plugins/new-plugin/` directory
2. Add `.claude-plugin/plugin.json` manifest
3. Add plugin components (skills, commands, agents, etc.)
4. Update `.claude-plugin/marketplace.json` with new plugin entry
5. Add documentation in `plugins/new-plugin/README.md`

See CONTRIBUTING.md for detailed guidelines.

## 🚀 Publishing

To make this marketplace available to others:

1. **Commit to Git:**
   ```bash
   git add .
   git commit -m "Convert to plugin marketplace structure"
   ```

2. **Push to GitHub:**
   ```bash
   git push origin main
   ```

3. **Share with others:**
   They can now use:
   ```bash
   /plugin marketplace add corby/limerick-skill
   /plugin install topical-limerick@limerick-skill
   ```

## 🔗 Resources

- [Claude Code Plugin Documentation](https://code.claude.com/docs/en/plugins)
- [Plugin Marketplaces Guide](https://code.claude.com/docs/en/plugin-marketplaces)
- [Agent Skills Documentation](https://code.claude.com/docs/en/agent-skills)
- [Plugins Reference](https://code.claude.com/docs/en/plugins-reference)
