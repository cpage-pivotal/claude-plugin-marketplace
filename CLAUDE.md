# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **Claude Code Plugin Marketplace** that distributes plugins for productivity and integration with Tanzu Platform. The marketplace currently includes four plugins:

- **cf-space-auditor**: Audits Cloud Foundry spaces for compliance (memory allocation, instance counts, deployment staleness)
- **mailgun**: Sends emails via Mailgun API
- **google-chat-poster**: Posts messages to Google Chat Spaces
- **topical-limerick**: Generates entertaining limericks with current news references

## Architecture

### Marketplace Structure

The marketplace follows the Claude Code plugin marketplace specification:

```
.
├── .claude-plugin/
│   └── marketplace.json        # Marketplace manifest defining available plugins
└── plugins/
    ├── plugin-name/
    │   ├── .claude-plugin/
    │   │   └── plugin.json     # Plugin manifest (name, version, author, keywords)
    │   └── skills/             # Optional: Agent Skills directory
    │       └── skill-name/
    │           ├── SKILL.md    # Skill definition and workflow
    │           └── scripts/    # Optional: Helper scripts
```

### Key Files

**`.claude-plugin/marketplace.json`** - Defines the marketplace itself:
- Marketplace name: `tanzu-platform-plugins`
- Owner information
- List of available plugins with metadata (name, source path, description, version, keywords, category)

**`plugins/*/plugin.json`** - Each plugin's manifest:
- Plugin name, description, version
- Author information
- Keywords for discoverability
- Reference to skills directories

**`plugins/*/skills/*/SKILL.md`** - Agent skill definitions:
- Frontmatter with skill name and description
- Workflow instructions for Claude Code
- Recognition patterns (when to activate)
- Best practices and examples

### Plugin Types

This marketplace includes three types of plugins:

1. **Integration Skills** (mailgun, google-chat-poster, cf-space-auditor):
   - Use external APIs or tools
   - Often include Python helper scripts in `scripts/` subdirectories
   - Require environment variables for authentication

2. **AI Skills** (topical-limerick):
   - Pure agent skills without external dependencies
   - Use Claude Code's built-in tools (WebSearch)
   - Teach Claude specific workflows or formats

## Common Tasks

### Testing Plugins Locally

```bash
# Add this marketplace from local path
/plugin marketplace add /Users/corby/Projects/claude/claude-plugin-marketplace

# Install a specific plugin
/plugin install plugin-name@tanzu-platform-plugins

# Verify installation
/plugin

# Test the plugin functionality by using it in conversation
```

### Adding a New Plugin

1. Create plugin directory: `plugins/new-plugin/`
2. Create manifest: `plugins/new-plugin/.claude-plugin/plugin.json`
3. Add plugin content (skills, commands, or agents)
4. Update `.claude-plugin/marketplace.json` to include the new plugin
5. Test locally before committing

### Modifying a Skill

1. Read the existing SKILL.md file in `plugins/*/skills/*/SKILL.md`
2. Understand the frontmatter (name, description, recognition patterns)
3. Update the workflow section with clear, step-by-step instructions
4. Test the skill by triggering it in Claude Code
5. Increment the version in the plugin's `plugin.json`

## Plugin-Specific Details

### cf-space-auditor

- **Dependency**: Requires Cloud Foundry MCP server to be configured
- **Audit Criteria**: Exactly three checks (memory allocation, instance count, deployment staleness)
- **Scope**: ONLY audits apps, NOT routes, services, or other CF resources
- **Memory Standards**: Java apps = 1024M, Non-Java apps = 512M (strict equality)
- **Staleness Threshold**: 180 days (6 months)

### mailgun

- **API Endpoint**: `https://api.mailgun.net/v3/mail.corby.page/messages`
- **Authentication**: Requires `MAILGUN_API_KEY` environment variable
- **Sender**: `Tanzu Agent <postmaster@corby.page>`
- **Helper Script**: `plugins/mailgun/skills/mailgun/scripts/send_email.py`
- **Usage**: `python send_email.py <recipients> <subject> <body>`

### google-chat-poster

- **Authentication**: Requires three environment variables:
  - `GOOGLE_CHAT_SPACE_ID`
  - `GOOGLE_CHAT_KEY`
  - `GOOGLE_CHAT_TOKEN`
- **API**: Google Chat API v1
- **Helper Script**: `plugins/google-chat-poster/skills/google-chat-poster/scripts/post_message.py`
- **Supports**: Plain text, markdown formatting, card messages

### topical-limerick

- **No external dependencies** - uses WebSearch tool
- **Workflow**: Always search for recent news → craft limerick with topical references
- **Format**: AABBA rhyme scheme, anapestic meter
- **Structure**: Lines 1,2,5 have 8-9 syllables; lines 3,4 have 5-6 syllables
- **Trigger**: Activates when user mentions "limerick"

## Important Conventions

### Skill Definition Format

All SKILL.md files must include:
- Frontmatter with `name` and `description` fields
- Clear workflow section with numbered steps
- Recognition patterns explaining when the skill activates
- Examples demonstrating proper usage
- Best practices section

### Plugin Manifest Requirements

All plugin.json files must include:
- `name`: Matches directory name
- `description`: Clear explanation of plugin purpose
- `version`: Semantic versioning (e.g., "1.0.0")
- `author`: Name (email optional)
- `keywords`: Array of relevant search terms
- `category`: Plugin category (e.g., "writing", "integration", "cloud-foundry")
- `license`: "MIT" or other license identifier

### Marketplace Manifest

The `.claude-plugin/marketplace.json` must:
- Define a unique marketplace `name`
- Include `owner` information
- List all plugins in `plugins` array
- Use `./plugins/plugin-name` as the `source` path
- Set `strict: true` for all plugins to enforce schema validation

## File Locations

- Marketplace manifest: `.claude-plugin/marketplace.json`
- Plugin manifests: `plugins/*/plugin.json`
- Skills: `plugins/*/skills/*/SKILL.md`
- Helper scripts: `plugins/*/skills/*/scripts/*.py`
- Documentation: `README.md`, `STRUCTURE.md`, `CONTRIBUTING.md`

## References

- Main documentation: `README.md` - Installation and usage instructions
- Structure guide: `STRUCTURE.md` - Detailed explanation of marketplace architecture
- Contribution guide: `CONTRIBUTING.md` - Guidelines for adding new plugins
