---
name: topical-limerick
description: Write limericks with current news and topical references. ALWAYS use this skill when the user asks to "write a limerick", "make a limerick", "create a limerick", "limerick about", or mentions "limerick" in their request. Works for any topic - people, places, events, sports, technology, politics, celebrities, etc.
---

# Topical Limerick

Write entertaining limericks that blend the requested topic with current news and events.

## Workflow

When the user requests a limerick:

### 1. Research Current News (REQUIRED)

ALWAYS use web_search to find recent, relevant news about the requested topic:

```
web_search("Chauncey Billups recent news")
```

Look for newsworthy, interesting, or amusing recent developments. Focus on:
- Concrete details, numbers, statistics
- Recent quotes or statements
- Current role, position, or activities
- Recent events (past week/month preferred)

**Important:** Do NOT skip the web search step. Fresh, topical details make the limerick more engaging and relevant.

### 2. Craft the Limerick

Create a limerick that:
- Follows proper limerick structure (see format below)
- Incorporates specific topical details from the news search
- Maintains a humorous, playful tone
- Weaves the news naturally into the verse (not forced)

### 3. Limerick Format Requirements

**Meter:** Anapestic meter (da-da-DUM pattern)
- Lines 1, 2, 5: Three stressed syllables (8-9 syllables total)
- Lines 3, 4: Two stressed syllables (5-6 syllables total)

**Rhyme scheme:** AABBA
- Lines 1, 2, 5 rhyme with each other
- Lines 3, 4 rhyme with each other

**Structure example:**
```
There ONCE was a MAN from PerU     (A - 9 syllables)
Who DREAMED he was EATing his SHOE (A - 9 syllables)
    He WOKE with a FRIGHT             (B - 6 syllables)
    In the MIDdle of NIGHT            (B - 6 syllables)
And FOUND that his DREAM had come TRUE (A - 9 syllables)
```

## Best Practices

- **Be specific:** Use actual names, numbers, places from the news search
- **Be timely:** Reference events from recent weeks or months
- **Be clever:** The best limericks have a surprising or witty final line
- **Be natural:** The topical reference should feel integrated, not shoehorned
- **Test the rhythm:** Read aloud mentally to ensure proper meter

## Example

**User request:** "Write a limerick about Chauncey Billups"

**Step 1 - Web search:**
```
web_search("Chauncey Billups recent news coaching")
```

**Step 2 - After finding news (e.g., coaching Portland Trail Blazers):**

```
There once was a coach named Chauncey,
Whose Portland squad looked rather fancy.
    With plays sharp and clean,
    Best backcourt they've seen,
His Blazers now dance like they're prancy!
```

---

**Another example:** "limerick about AI"

**Step 1 - Web search:**
```
web_search("Claude AI Sonnet recent news")
```

**Step 2 - After finding news:**

```
Claude Sonnet Four's making waves in the press,
With reasoning powers that truly impress.
    It can code and create,
    At a lightning-fast rate,
While keeping its hallucinations much less.
```

---

## Recognition Patterns

This Skill activates when users say things like:
- "Write a limerick about [topic]"
- "Make a limerick about [person]"
- "Create a limerick for [subject]"
- "Can you write me a limerick?"
- "Limerick about [anything]"
- "Give me a limerick on [topic]"

The key trigger word is **"limerick"** - always use this Skill when that word appears.
