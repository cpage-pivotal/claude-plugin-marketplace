# Topical Limerick Plugin

Write entertaining limericks that blend any requested topic with current news and events.

## 🎭 Overview

The Topical Limerick plugin adds an AI skill to Claude Code that automatically writes properly-formatted limericks incorporating current news and topical references. Perfect for adding humor and creativity to any topic!

## ✨ Features

- 🔍 **Automatic news search** - Finds recent, relevant news about your topic
- 📝 **Proper limerick structure** - AABBA rhyme scheme with anapestic meter
- 🎯 **Topical references** - Incorporates specific details from current events
- 😄 **Witty and clever** - Aims for surprising, humorous final lines
- 🌍 **Works for any topic** - People, places, events, technology, politics, etc.

## 🚀 Installation

### Via Marketplace

If the limerick-skill marketplace is available on GitHub:

```bash
# Add the marketplace
/plugin marketplace add corby/limerick-skill

# Install this plugin
/plugin install topical-limerick@limerick-skill
```

### Local Installation

If you have the marketplace cloned locally:

```bash
# Add local marketplace
/plugin marketplace add /path/to/limerick-skill

# Install the plugin
/plugin install topical-limerick@limerick-skill
```

### Restart Required

After installation, restart Claude Code to activate the skill.

## 📖 Usage

Once installed, simply mention "limerick" in your request and Claude Code will automatically use this skill.

### Examples

**Request:**
```
Write a limerick about Python programming
```

**Claude will:**
1. Search for recent Python news
2. Craft a limerick incorporating topical details

---

**Request:**
```
Create a limerick about SpaceX
```

**Claude will:**
1. Find recent SpaceX news (e.g., Starship launches)
2. Write a limerick with specific details

---

**Request:**
```
Limerick about quantum computing
```

**Claude will:**
1. Research latest quantum computing developments
2. Create a witty, technically-informed limerick

## 🎯 Recognition Patterns

The skill automatically activates when you use these phrases:

- "Write a limerick about [topic]"
- "Make a limerick about [person]"
- "Create a limerick for [subject]"
- "Can you write me a limerick?"
- "Limerick about [anything]"
- "Give me a limerick on [topic]"

**Key trigger:** The word **"limerick"** activates this skill.

## 📐 Limerick Format

The plugin ensures proper limerick structure:

### Structure
- **Lines 1, 2, 5:** 8-9 syllables, three stressed beats (A rhyme)
- **Lines 3, 4:** 5-6 syllables, two stressed beats (B rhyme)
- **Meter:** Anapestic (da-da-DUM pattern)

### Example Pattern

```
There ONCE was a MAN from PerU     (A - 9 syllables)
Who DREAMED he was EATing his SHOE (A - 9 syllables)
    He WOKE with a FRIGHT             (B - 6 syllables)
    In the MIDdle of NIGHT            (B - 6 syllables)
And FOUND that his DREAM had come TRUE (A - 9 syllables)
```

## 🔧 How It Works

### Workflow

1. **Detect Request**: Recognizes "limerick" keyword in user input
2. **Research Phase**: Uses `web_search` to find recent, relevant news
   - Looks for concrete details, statistics, quotes
   - Focuses on recent events (past week/month preferred)
   - Identifies interesting or amusing developments
3. **Craft Limerick**: Creates verse following proper structure
   - Maintains AABBA rhyme scheme
   - Follows anapestic meter
   - Incorporates topical details naturally
   - Aims for humorous, clever final line

### Best Practices

The skill follows these principles:
- **Be specific** - Uses actual names, numbers, places from news
- **Be timely** - References recent events
- **Be clever** - Surprising or witty final lines
- **Be natural** - Topical references feel integrated, not forced
- **Test rhythm** - Maintains proper meter throughout

## 🎨 Use Cases

### Creative Writing
- Generate entertaining poetry on demand
- Practice limerick composition techniques
- Explore different rhyme and meter patterns

### Technical Content
- Make programming concepts fun and memorable
- Create engaging technical documentation
- Add humor to code comments

### Marketing & Social Media
- Create viral-worthy content
- Engage audiences with clever wordplay
- Make announcements memorable

### Education
- Teach complex topics in fun, memorable ways
- Create study aids and mnemonics
- Engage students with creative content

### Entertainment
- Generate content for blogs and newsletters
- Create witty commentary on current events
- Add humor to presentations

## 📂 Plugin Structure

```
topical-limerick/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata
└── skills/
    └── topical-limerick/
        └── SKILL.md         # Skill definition and workflow
```

## 🐛 Troubleshooting

### Skill Not Activating

**Problem**: Claude doesn't use the limerick skill when requested

**Solutions**:
- Ensure you use the word "limerick" in your request
- Verify plugin is installed: `/plugin`
- Check plugin is enabled: `/plugin enable topical-limerick@limerick-skill`
- Restart Claude Code after installation

### No News Search

**Problem**: Limericks lack topical references

**Solutions**:
- Ensure Claude has web search access
- Try being more specific with your topic
- Check internet connectivity

### Meter/Rhyme Issues

**Problem**: Limerick doesn't follow proper structure

**Solutions**:
- This is inherent to AI poetry generation
- Request revision: "Can you revise that to better match limerick meter?"
- Provide feedback on specific lines that need adjustment

## 🔗 Resources

- [Claude Code Plugin Documentation](https://code.claude.com/docs/en/plugins)
- [Agent Skills Documentation](https://code.claude.com/docs/en/agent-skills)
- [Marketplace Repository](https://github.com/corby/limerick-skill)

## 📄 License

MIT License - See [LICENSE](../../LICENSE) file

## 👤 Author

**Corby**

---

**Enjoy creating topical limericks with Claude Code!** 🎭✨

