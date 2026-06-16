# Contributing to Claude Plugin Marketplace

Thank you for your interest in contributing to the Marketplace!

## 📦 How to Contribute a Plugin

### 1. Create Your Plugin

Follow the Claude Code plugin structure:

```
your-plugin/
├── .claude-plugin/
│   └── plugin.json          # Required: Plugin metadata
├── skills/                   # Optional: Agent Skills
│   └── your-skill/
│       └── SKILL.md
├── commands/                 # Optional: Custom commands
│   └── command.md
├── agents/                   # Optional: Custom agents
│   └── agent.md
└── README.md                # Recommended: Plugin documentation
```

### 2. Test Your Plugin Locally

Before contributing:

1. Create a local test marketplace
2. Add your plugin to the test marketplace
3. Install and test in Claude Code
4. Verify all features work as expected

```bash
# Test installation
/plugin marketplace add ./your-test-marketplace
/plugin install your-plugin@your-test-marketplace

# Test functionality
# ... use your plugin features ...
```

### 3. Submit Your Plugin

#### Option A: Fork and Pull Request

1. Fork this repository
2. Add your plugin to `plugins/your-plugin-name/`
3. Update `.claude-plugin/marketplace.json` with your plugin entry
4. Update the README.md to list your plugin
5. Create a pull request with:
   - Description of what your plugin does
   - Examples of usage
   - Screenshots/examples of output (if applicable)

#### Option B: Submit an Issue

If you prefer, create an issue with:
- Link to your plugin repository
- Description and usage examples
- Why it belongs in this marketplace

We'll review and add it if it fits!

## 📋 Plugin Manifest Requirements

Your `plugin.json` must include:

```json
{
  "name": "your-plugin",
  "description": "Clear, concise description",
  "version": "1.0.0",
  "author": {
    "name": "Your Name",
    "email": "optional@email.com"
  },
  "keywords": ["relevant", "keywords"],
  "category": "writing",
  "license": "MIT"
}
```

## ✅ Quality Guidelines

### Documentation
- Include a README.md in your plugin directory
- Provide clear usage examples
- Document any configuration options
- List prerequisites or dependencies

### Code Quality
- Follow Claude Code plugin best practices
- Use meaningful names for commands, agents, and skills
- Include error handling where appropriate
- Test edge cases

### Skill Guidelines (if applicable)
- Clear skill descriptions with `---` frontmatter
- Specific workflow instructions
- Examples demonstrating the skill
- Recognition patterns that trigger the skill

### Commands Guidelines (if applicable)
- Use descriptive command names (e.g., `/write-poem`, not `/wp`)
- Include `description` in frontmatter
- Provide clear instructions to Claude
- Consider command namespacing to avoid conflicts

## 🔍 Review Process

1. **Initial Review**: We check that your plugin:
   - Has proper structure and manifest
   - Includes documentation
   - Fits the marketplace theme

2. **Testing**: We test your plugin:
   - Installation works correctly
   - Features function as described
   - No conflicts with existing plugins

3. **Feedback**: We may request:
   - Documentation improvements
   - Naming clarifications
   - Structural changes

4. **Acceptance**: Once approved:
   - Your plugin is added to the marketplace
   - Listed in the README
   - Announced in release notes

## 🚫 What We Don't Accept

- Duplicate functionality of existing plugins (unless significantly improved)
- Plugins unrelated to the marketplace theme (Tanzu Platform, productivity, integrations, creative tools)
- Poorly documented or untested plugins
- Malicious code or security vulnerabilities
- Plugins that violate Anthropic's usage policies

## 🐛 Bug Reports

Found a bug in an existing plugin?

1. Check if it's already reported in Issues
2. Create a new issue with:
   - Plugin name and version
   - Steps to reproduce
   - Expected vs actual behavior
   - Claude Code version
   - Any error messages

## 💡 Feature Requests

Have an idea for a new plugin or feature?

1. Check existing issues and discussions
2. Create an issue with:
   - Clear description of the feature
   - Use cases and examples
   - Why it would benefit users
   - (Optional) Draft implementation approach

## 📜 Code of Conduct

- Be respectful and constructive
- Help others learn and improve
- Give credit where due
- Follow Anthropic's AI safety guidelines
- Respect intellectual property and licenses

## 🔗 Resources

- [Claude Code Plugin Documentation](https://code.claude.com/docs/en/plugins)
- [Plugin Marketplaces Guide](https://code.claude.com/docs/en/plugin-marketplaces)
- [Agent Skills Documentation](https://code.claude.com/docs/en/agent-skills)
- [Plugin Reference](https://code.claude.com/docs/en/plugins-reference)

## 📧 Questions?

- Open a Discussion for general questions
- Check existing Issues for common problems
- Review the main README.md for usage instructions

---

**Thank you for contributing to the Claude Code Plugin Marketplace!**

