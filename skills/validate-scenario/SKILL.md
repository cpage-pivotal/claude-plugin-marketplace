# validate-scenario

Validate a Jira Scenario ticket against the gold standard format. The Scenario ticket ID will be passed as the first argument (e.g., TNZ-XXXXX).

**Important** Running validations should just return the results. It should never modify the scenario.

## Steps

### Step 1: Fetch the Scenario ticket
Use `jira_get_issue` with `issueIdOrKey` to fetch the Scenario ticket. Extract:
- **Description** (full text) — contains narrative sections (Objective, Why, Customers, Success, User Personas & Roles, Out of Scope, Dependencies & Risks, References / Prior Art, Scale & Performance Targets)
- **Acceptance Criteria field** (`customfield_45430`, checklist content) — contains User Flow headers (with narrative descriptions) and the structured ACs grouped under them.
- **Basic fields**: assignee, component, status, priority

**Important: Description vs. AC field separation**
The Description and the Acceptance Criteria checklist field have distinct responsibilities:
- The **Description** contains 9 narrative sections. It does NOT contain User Flows or individual ACs.
- The **AC checklist field** contains User Flow headers with narrative descriptions (purpose, persona, journey), Impact tags, and UX Design links, plus the structured ACs grouped under them. Each User Flow header includes a `>>` block with a narrative paragraph, Impact tag, and UX Design link. Each individual AC is just a one-line description (no `>>` block, no ID prefix).

### Step 2: Run Validation Checks
Run every check in the checklist below against the ticket content. For each check, record one of:
- **PASS**: The check is satisfied
- **FAIL**: The check is not satisfied — include a specific explanation of what's missing or wrong
- **WARN**: Partially satisfied or could be improved — include a suggestion

### Step 3: Present Results
Present the results as a structured report with three sections:

1. **Summary**: X passed, Y failed, Z warnings out of N total checks
2. **Failures** (must fix): List each FAIL with the check name, what's wrong, and what a fix looks like
3. **Warnings** (should fix): List each WARN with the check name and improvement suggestion
4. **Passed**: List the check names that passed (collapsed/brief)

Use a severity indicator: FAIL items are blockers for epic generation, WARN items are quality improvements.

---

## Validation Checklist

### Section Presence Checks
These verify that all 9 required sections exist in the Description field.

| Check ID | Check | What to look for |
|----------|-------|------------------|
| S1 | Objective exists | A clearly labeled section describing the high level outcome that the users of this scenario will be able to achieve. It should be customer outcome centric and can be brief. |
| S2 | Why exists | A section explaining why this matters in business terms (MTTR, developer experience, support burden, competitive parity, etc.) |
| S3 | Customers exists | A section with specific customer names/references, interview quotes or support ticket references, competitive pressure, and cost of inaction |
| S4 | Success exists | A section that defines success in a sentence or two for both customers and the product |
| S5 | User Personas & Roles exists | A section defining at least 2 distinct personas/roles with their responsibilities and how they interact with the feature |
| S6 | Out of Scope exists | A section (or explicitly-skipped placeholder) for what is NOT included |
| S7 | Dependencies & Risks exists | A section (or explicitly-skipped placeholder) for dependencies and risks |
| S8 | References / Prior Art exists | A section (or explicitly-skipped placeholder) for references and prior art |
| S9 | Scale & Performance Targets exists | A section (or explicitly-skipped placeholder) for scale and performance targets |

*Explicitly skipped:* A section is "explicitly skipped" when its body contains only (or predominantly) a short statement that the section is intentionally omitted, e.g. "Explicitly skipped.", "N/A — explicitly skipped.", "Not applicable for this scenario.", or "Skipped for this scenario." The section header must still exist; the content is minimal and declares the skip.

### Optional Sections (Skippable)
The following sections (S6–S9) may be **explicitly skipped** as above: **Out of Scope**, **Dependencies & Risks**, **References / Prior Art**, **Scale & Performance Targets**. For each of these sections:

1. If the section is **explicitly skipped**: Report **WARN** (one per skipped section), e.g. "Out of Scope is explicitly skipped." Do *not* run the section-specific quality checks (Q8, Q9, Q10, Q11) for that section.
2. If the section is **present with real content**: Run the usual quality checks for that section (Q8, Q9, Q10, Q11 as applicable). Do not report a skip warning.

| Section | When skipped → WARN | Quality checks to skip when skipped |
|---------|---------------------|--------------------------------------|
| Out of Scope (S6) | SK1 Out of Scope explicitly skipped | Q9 |
| Dependencies & Risks (S7) | SK2 Dependencies & Risks explicitly skipped | Q10, Q11 |
| References / Prior Art (S8) | SK3 References / Prior Art explicitly skipped | (none) |
| Scale & Performance Targets (S9) | SK4 Scale & Performance Targets explicitly skipped | Q8; also skip XR2 if Scale is skipped |

### Section Quality Checks
These verify that sections contain meaningful content, not just headers. **Q8, Q9, Q10, Q11** apply only when the corresponding section is *not* explicitly skipped.

| Check ID | Check | What to look for |
|----------|-------|------------------|
| Q1 | Why has affected personas | The why explicitly names which personas/roles are affected |
| Q2 | Customers has cost of inaction | The Customers section includes an explicit "cost of inaction" or equivalent explaining what happens if we don't do this |
| Q3 | Customers has real customer references | At least 2 specific customer names, interview dates, support ticket IDs, or advisory board references (not generic statements like "customers want this") |
| Q4 | Customers has competitive analysis | At least 1 named competitor with specific capabilities they have. *Explicitly skippable:* if the Customers section contains an explicit skip statement for competitive analysis (e.g. "Competitive analysis: N/A", "No competitive analysis."), report **WARN**. If competitive analysis is simply absent with no skip statement, report **FAIL**. |
| Q5 | Customers has quantified impact | At least 1 quantified impact statement (e.g., "15-20% of support tickets", "4 hours/week", "6 hours lost"). *Report **WARN** (not FAIL) when missing.* |
| Q6 | Success covers customers and product | Success section defines what success looks like in a sentence or two for both customers and the product |
| Q7 | User Personas are distinct and actionable | Each persona has a clear name/role, specific responsibilities listed, and is meaningfully different from other personas |
| Q8 | Scale targets are quantified | Every scale target has a specific number (not vague like "fast" or "scalable") with units. *Only when Scale & Performance Targets is not explicitly skipped.* |
| Q9 | Out of Scope has at least 2 items | At least 2 explicit exclusions are listed (prevents scope creep). *Report **WARN** (not FAIL) when fewer than 2 items. Only when Out of Scope is not explicitly skipped.* |
| Q10 | Dependencies list specific systems | If dependencies are listed, they must name specific systems/services (not vague references). PMs only need to list dependencies on capabilities that do not yet exist in the product. *Explicitly skippable:* if the section contains an explicit skip statement for dependencies (e.g. "No dependencies.", "Dependencies: N/A"), report **WARN**. If dependencies are simply absent with no skip statement, report **FAIL**. *Only when Dependencies & Risks is not explicitly skipped.* |
| Q11 | Risks have mitigations | Each identified risk has a corresponding mitigation strategy. *Only when Dependencies & Risks is not explicitly skipped.* |

### User Flow Checks (AC checklist field)
These verify that the User Flow headers in the AC checklist field are complete. User Flows (including their narratives) live entirely in the AC field, not in the Description.

| Check ID | Check | What to look for |
|----------|-------|------------------|
| AC1 | At least 2 User Flows defined | There are at least 2 distinct User Flow headers (`### User Flow N: ...`) in the AC checklist field |
| AC2 | Every User Flow header has a narrative description | Each User Flow header item in the AC field has a `>>` block containing a narrative paragraph that explains the flow's purpose, persona, and context. This is the header item's description — it is separate from the individual AC items beneath it. |
| AC10 | User Flow headers have Impact tags and UX Design links | Each User Flow header item in the AC field has an Impact tag in its `>>` block (e.g. `[UI]`, `[BE]`, `[UX]`, `[CLI]`, `[UI + BE]`, `[CLI + BE]`, etc.) indicating the primary impact area of the flow. If the flow is tagged with `[UI]` or `[UX]`, the header must also include a UX Design link (or "Pending UX" — flag "Pending" as WARN). |

### Acceptance Criteria Structure Checks (AC checklist field)
These verify that the AC checklist field structure is complete and suitable for automated epic generation. ACs live exclusively in the AC checklist field, NOT in the Description.

| Check ID | Check | What to look for |
|----------|-------|------------------|
| AC3 | Every User Flow has at least 1 AC | No user flow group in the AC checklist is empty — each has at least 1 acceptance criteria |
| AC8 | ACs that reference scale have Scale targets | If an AC mentions performance, throughput, latency, or concurrency, it should reference specific numbers from the Scale section |
| AC9 | AC text is self-contained | Each AC's text is specific enough to create an Epic from it without needing to read other ACs (no "same as above" or "see above") |

### Acceptance Criteria Field Checks (Checklist Format)
These verify that the dedicated Acceptance Criteria checklist field (`customfield_45430`) follows the correct checklist syntax. This is where all ACs live.

| Check ID | Check | What to look for |
|----------|-------|------------------|
| CL1 | AC field is populated | The Acceptance Criteria field is not empty — it should contain the structured checklist |
| CL2 | Headers use ### syntax | User flow groupings use `###` header syntax |
| CL3 | Items use [ ] syntax | Each AC item uses `[ ]` checklist item syntax |
| CL4 | Headers have description blocks | Each User Flow header has a `>>` description block with a narrative paragraph, an Impact tag, and a UX Design link (when applicable). Individual AC items do NOT have `>>` blocks. |
| CL5 | Header descriptions include Impact | Every User Flow header `>>` block includes an Impact line with a valid tag (`[UI]`, `[BE]`, `[UX]`, `[CLI]`, or combinations) |

### Cross-Reference Checks
These verify consistency between sections.

| Check ID | Check | What to look for |
|----------|-------|------------------|
| XR1 | Personas referenced in ACs match User Personas section | The personas/roles mentioned in AC text (e.g., "Platform Operator can...") match the personas defined in the User Personas section |
| XR2 | Scale targets in ACs match Scale section | Scale numbers referenced in individual ACs are consistent with the global targets in the Scale & Performance Targets section. *Skip this check (PASS) when Scale & Performance Targets is explicitly skipped.* |
| XR3 | User Flow personas match User Personas section | The personas/roles named in each User Flow header (e.g. "Platform Operator", "All Roles") in the AC field correspond to personas defined in the User Personas & Roles section in the Description — no unrecognized personas |

### Sample Data Checks
These verify that the author has replaced or removed template placeholders and sample data before the scenario is treated as ready.

| Check ID | Check | What to look for |
|----------|-------|------------------|
| SD1 | No unreplaced sample data | The Description and Acceptance Criteria field (customfield_45430) do not contain placeholder or sample text left for the author to replace. Search for: *[REPLACE: ...]* (e.g. `[REPLACE: Customer/segment name]`, `[REPLACE: ticket ID]`, `[REPLACE: fill in once known]`, `[REPLACE: replace with approved list or remove]`); the phrase *Sample data* in a note instructing the author to replace content; or similar template placeholders. If any such text appears in either field, report **WARN** and list each occurrence (e.g. "Description, Customers section: [REPLACE: ticket ID]") so the author can replace or remove before publishing. PASS only when no unreplaced sample-data markers are found. |

---

## Output Format

Present the report in this format:

```
h2. Scenario Validation Report: <TICKET_KEY>

h3. Summary
* Total checks: N
* Passed: X
* Failed: Y
* Warnings: Z

h3. Failures (Must Fix)

*F1. [Check ID] Check Name*
Issue: <what's wrong>
Fix: <what needs to change>

*F2. [Check ID] Check Name*
Issue: <what's wrong>
Fix: <what needs to change>

(... repeat for all failures ...)

h3. Warnings (Should Fix)

*W1. [Check ID] Check Name*
Issue: <what could be improved>
Suggestion: <how to improve>

(... repeat for all warnings ...)

h3. Passed Checks
<comma-separated list of passed check IDs>
```

If there are 0 failures, congratulate the author and note any warnings as optional improvements.

## Important Notes

- **Description vs. AC field**: The Description contains 9 narrative sections (Objective through Scale & Performance Targets). The AC checklist field (`customfield_45430`) contains User Flow headers (with narrative descriptions, Impact tags, and UX Design links) and the structured ACs grouped under them. Individual ACs are just a one-line description — no IDs, no `>>` blocks. User Flows live entirely in the AC field — the Description does not have a User Flows section.
- **Jira MCP tool**: Use `jira_get_issue` with parameter `issueIdOrKey` (e.g., `{"issueIdOrKey": "TNZ-82898"}`).
- Be strict on FAIL checks — the goal is to catch issues before engineering starts work.
- Be constructive in WARN suggestions — explain why the improvement matters.
- If the Description is completely empty or clearly not a Scenario (e.g., it's a Bug or Story), stop immediately and report that this ticket does not appear to be a Scenario.
- Do NOT modify the ticket. This command is read-only.

This command will be available in chat with /validate-scenario
