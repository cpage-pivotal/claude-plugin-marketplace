# Limerick Skill Plugin Marketplace

A curated plugin marketplace for Claude Code featuring the **Topical Limerick** skill - an AI-powered limerick writer that combines classic poetry with current events.

## 🎭 Overview

This marketplace provides Claude Code plugins.

## 📦 Available Plugins

### Topical Limerick

Write entertaining limericks that blend any requested topic with current news and events. This plugin adds an AI skill that:

- ✅ **Searches recent news** automatically for topical references
- ✅ **Follows proper limerick structure** (AABBA rhyme scheme, anapestic meter)
- ✅ **Incorporates specific details** from current events
- ✅ **Maintains humor and wit** with surprising, clever endings

**Perfect for:** Creative writing, entertainment, making technical topics fun, social media content, presentations

## 🚀 Quick Start

### Installation

1. **Add this marketplace to Claude Code:**

```bash
/plugin marketplace add corby/limerick-skill
```

Or if you've cloned this repository locally:

```bash
/plugin marketplace add /path/to/limerick-skill
```

2. **Install the topical-limerick plugin:**

```bash
/plugin install topical-limerick@limerick-skill
```

3. **Restart Claude Code** to activate the plugin

4. **Verify installation:**

```bash
/plugin
```

Look for `topical-limerick` in your installed plugins list.

### Usage

Once installed, Claude Code will automatically use the topical-limerick skill whenever you mention "limerick" in your request:

```
Write a limerick about Python programming
```

```
Create a limerick about SpaceX
```

```
Limerick about the latest AI news
```

The skill will:
1. Automatically search for recent news about the topic
2. Craft a properly-formatted limerick incorporating topical details
3. Ensure proper meter (da-da-DUM pattern) and rhyme scheme (AABBA)

## 📖 How It Works

### Example Interaction

**You:** "Write a limerick about Claude AI"

**Claude Code will:**
1. Search for recent Claude AI news
2. Find topical details (e.g., new Sonnet 4 release)
3. Craft a limerick like:

```
Claude Sonnet Four's making waves in the press,
With reasoning powers that truly impress.
    It can code and create,
    At a lightning-fast rate,
While keeping its hallucinations much less.
```

### Recognition Patterns

The skill automatically activates when you say:
- "Write a limerick about [topic]"
- "Make a limerick about [person]"
- "Create a limerick for [subject]"
- "Limerick about [anything]"
- "Give me a limerick on [topic]"

## 🔧 For Plugin Developers

### Repository Structure

```
limerick-skill/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace configuration
├── plugins/
│   └── topical-limerick/
│       ├── .claude-plugin/
│       │   └── plugin.json       # Plugin metadata
│       └── skills/
│           └── topical-limerick/
│               └── SKILL.md      # Skill definition
└── README.md
```

### Testing Locally

1. Clone this repository
2. Add as a local marketplace: `/plugin marketplace add ./limerick-skill`
3. Install the plugin: `/plugin install topical-limerick@limerick-skill`
4. Test by requesting a limerick

### Contributing

To add more poetry or creative writing plugins to this marketplace:

1. Create a new plugin directory under `plugins/`
2. Add proper `.claude-plugin/plugin.json` manifest
3. Include skills, commands, or agents as needed
4. Update `marketplace.json` with the new plugin entry
5. Submit a pull request

## 📚 Limerick Format Reference

### Structure
- **Lines 1, 2, 5:** Three stressed syllables (8-9 syllables total) - rhyme together (A)
- **Lines 3, 4:** Two stressed syllables (5-6 syllables total) - rhyme together (B)
- **Meter:** Anapestic (da-da-DUM pattern)

### Example Pattern

```
There ONCE was a MAN from PerU     (A - 9 syllables)
Who DREAMED he was EATing his SHOE (A - 9 syllables)
    He WOKE with a FRIGHT             (B - 6 syllables)
    In the MIDdle of NIGHT            (B - 6 syllables)
And FOUND that his DREAM had come TRUE (A - 9 syllables)
```

## 🎯 Use Cases

- **Technical Content:** Make programming concepts entertaining
- **Marketing:** Create memorable taglines and social media content
- **Education:** Teach complex topics in a fun, memorable way
- **Entertainment:** Generate creative content for blogs, newsletters
- **Team Building:** Add humor to presentations and meetings
- **Current Events:** Provide witty commentary on news and trends

## 🛠️ Marketplace Management

### List all marketplaces
```bash
/plugin marketplace list
```

### Update marketplace metadata
```bash
/plugin marketplace update limerick-skill
```

### Remove marketplace
```bash
/plugin marketplace remove limerick-skill
```

## 📋 Plugin Management

### List installed plugins
```bash
/plugin
```

### Enable/disable plugin
```bash
/plugin enable topical-limerick@limerick-skill
/plugin disable topical-limerick@limerick-skill
```

### Uninstall plugin
```bash
/plugin uninstall topical-limerick@limerick-skill
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

