---
name: cf-space-auditor
description: Audit Cloud Foundry spaces for compliance with memory allocation standards, instance counts, and deployment staleness. Applies specific audit rules - Java apps must use 1024M memory, non-Java apps must use 512M, identifies multi-instance apps, and flags apps not deployed in 6+ months. Use when the user asks to "audit" a CF space, check space compliance, review space against standards, or evaluate apps for configuration issues. Trigger words include "audit", "compliance", "standards", "check configuration".
---

# Cloud Foundry Space Auditor

## MANDATORY: Apply ONLY These Three Audit Criteria

This skill performs a **compliance audit** using exactly three criteria. Do NOT add any other analysis:

**The Three Criteria:**
1. **Memory Allocation**: Java apps = 1024M, Non-Java apps = 512M (strict equality)
2. **Instance Count**: Flag any app running >1 instance
3. **Deployment Staleness**: Flag running apps not deployed in 180+ days

**DO NOT include in this audit:**
- Routes or orphaned routes
- Service instances or bindings
- Resource optimization suggestions
- Storage/disk analysis
- General space health assessments
- Custom recommendations

**If the user wants general space analysis:** This is the WRONG skill. Use CF MCP tools conversationally without this skill.

**This skill triggers when:** User says "audit" + space name, OR asks to check compliance/standards.

## Prerequisites

Verify the Cloud Foundry MCP server is available before proceeding. If the user hasn't configured the CF MCP server, inform them they need to set it up first.

## Audit Workflow

### Step 1: Gather Required Parameters

**Required Information:**
- Cloud Foundry organization name
- Space name within the organization

**If not provided by the user:**
Ask the user to provide both the organization name and space name before proceeding.

Example: "To audit the space, I need two pieces of information: (1) the Cloud Foundry organization name, and (2) the space name. Could you provide both?"

### Step 2: Retrieve Apps in the Space

Use the Cloud Foundry MCP server tools to get the list of applications in the specified org and space.

**Typical tool calls:**
- List all apps in the space using the appropriate CF MCP tool
- For each app, retrieve detailed information including:
  - App name
  - State (running, stopped, etc.)
  - Buildpack(s) used
  - Memory allocation
  - Number of instances
  - Last uploaded/deployed timestamp

### Step 3: Evaluate Apps Against Audit Criteria

Analyze each app against the following criteria:

#### Memory Allocation Standards

**Java Buildpack Apps:**
- Expected: 1024M (1G) of memory
- Flag if: Memory allocation is not exactly 1024M
- Severity: Configuration inconsistency

**Non-Java Apps (all other buildpacks):**
- Expected: 512M of memory
- Flag if: Memory allocation is not exactly 512M
- Severity: Configuration inconsistency

#### Instance Count

**All Apps:**
- Flag if: App is running more than 1 instance
- Reason: Multi-instance apps may indicate high-availability requirements or potential scaling issues
- Note: This is informational, not necessarily a problem

#### Deployment Staleness

**All Running Apps:**
- Flag if: Last deployed/updated more than 6 months ago (180 days)
- Reason: May be stale, unmaintained, or candidates for review
- Calculate: Compare current date with last uploaded timestamp
- Severity: Potential maintenance risk

### Step 4: Generate Audit Report

**CRITICAL REMINDER - AUDIT SCOPE:**
This audit covers ONLY apps and ONLY three criteria (memory, instances, staleness).
DO NOT include: routes, services, resource optimization, or any recommendations.
If you find yourself analyzing routes, services, or making optimization suggestions, STOP - you are outside the scope of this skill.

**CRITICAL REPORTING REQUIREMENTS:**
- MUST include specific app names for EVERY finding
- MUST include actual values (memory, instance count, dates) for every flagged app
- MUST show expected vs. actual values for memory issues
- MUST calculate and show days since deployment for stale apps
- DO NOT provide vague summaries like "2 apps have issues" without listing which apps

Structure the audit report with the following sections:

**1. Audit Summary**
- Total apps audited (count)
- Apps with memory allocation issues (count + will be listed below)
- Apps running multiple instances (count + will be listed below)
- Apps potentially stale (count + will be listed below)
- Apps fully compliant (count)

**2. Memory Allocation Issues**

For EACH app that doesn't meet memory standards, list:
- App name
- Buildpack type (Java or other)
- Expected memory (1024M for Java, 512M for others)
- Actual memory allocation
- State (running/stopped)

Example format:
```
Memory Allocation Issues (3 apps):

Java Apps - Expected 1024M:
- app-name-1: 512M (should be 1024M) - RUNNING
- app-name-2: 2048M (should be 1024M) - STOPPED

Non-Java Apps - Expected 512M:
- app-name-3: 1024M (should be 512M) - RUNNING
```

**3. Multi-Instance Apps**

For EACH app running more than 1 instance, list:
- App name
- Current instance count
- Buildpack type
- State

Example format:
```
Multi-Instance Apps (2 apps):

- app-name-1: 3 instances (Java buildpack) - RUNNING
- app-name-2: 2 instances (Python buildpack) - RUNNING
```

**4. Potentially Stale Apps**

For EACH running app not deployed in 6+ months, list:
- App name
- Last deployed date (YYYY-MM-DD format)
- Days since last deployment (calculated)
- Buildpack type

Example format:
```
Potentially Stale Apps (2 apps):

- app-name-1: Last deployed 2024-03-15 (274 days ago) - Java buildpack
- app-name-2: Last deployed 2024-01-10 (339 days ago) - Python buildpack
```

**5. Compliant Apps** (optional, can be summary)

Either list compliant apps OR provide count:
- "3 apps are fully compliant with all standards"
- Or list specific app names if count is small

**VERIFICATION CHECKLIST BEFORE RESPONDING:**
- [ ] Did I list specific app names for every issue found?
- [ ] Did I include actual values (memory, instances, dates) for each flagged app?
- [ ] Did I calculate days since deployment for stale apps?
- [ ] Did I show expected vs. actual for memory issues?
- [ ] If I said "2 apps have X issue," did I name both apps?

## Example Interactions

**User request:** "Audit the development space in our production org"

**Response flow:**
1. Confirm org is "production" and space is "development"
2. Use CF MCP tools to list apps in production/development
3. Retrieve details for each app
4. Evaluate against all criteria
5. Generate structured audit report with findings

**Example of GOOD audit output:**
```
Cloud Foundry Space Audit: development (production org)

Audit Summary:
- Total apps audited: 8
- Memory allocation issues: 2 apps
- Multi-instance apps: 1 app
- Potentially stale apps: 2 apps
- Fully compliant: 3 apps

Memory Allocation Issues (2 apps):

Java Apps - Expected 1024M:
- legacy-api: 512M (should be 1024M) - RUNNING

Non-Java Apps - Expected 512M:
- python-worker: 1024M (should be 512M) - RUNNING

Multi-Instance Apps (1 app):

- critical-service: 3 instances (Java buildpack) - RUNNING

Potentially Stale Apps (2 apps):

- legacy-api: Last deployed 2024-03-15 (274 days ago) - Java buildpack
- old-processor: Last deployed 2024-02-01 (316 days ago) - Python buildpack

Compliant Apps: 3 apps are fully compliant with all standards.
```

**Example of BAD audit output (DO NOT DO THIS):**
```
The audit found several issues. There are 2 apps with memory problems and 2 apps that haven't been updated recently.
```
*This is bad because it doesn't name the apps or provide specific details.*

**Example of VERY BAD audit output - SCOPE VIOLATION (NEVER DO THIS):**
```
Cloud Foundry Space Audit: corbyp (solution-architects org)

Applications Summary: 11 total, 5 running, 6 stopped

Service Instances (15)
- User-Provided Services: 12
- Managed Services: 3

Routes (14)
- Orphaned Routes: 3

Recommendations:
1. Clean up orphaned routes
2. Review stopped applications
3. Optimize resource allocation
```
*This is VERY BAD because it analyzes routes, services, and provides recommendations - all OUTSIDE the scope of this audit. This skill should ONLY analyze apps against the three criteria.*

**User request:** "Check my CF space"

**Response flow:**
1. Ask: "To audit your space, I need the organization name and space name. Could you provide both?"
2. Wait for user to provide details
3. Proceed with audit workflow

## Important Notes

**Data Requirements:**
- Only running apps should be evaluated for deployment staleness
- Stopped apps can be noted separately if relevant
- Memory standards are strict equality checks (not ranges)
- Be precise with buildpack identification - check for "java" in buildpack name (case-insensitive)
- When calculating staleness, use current date and clear date arithmetic

**Reporting Requirements:**
- ALWAYS list specific app names for every finding
- NEVER provide summaries without details (e.g., "2 apps have issues" without naming them)
- ALWAYS include actual values: memory amounts, instance counts, deployment dates
- ALWAYS show expected vs. actual for memory issues
- ALWAYS calculate and show days since deployment for stale apps

**Error Handling:**
- If any MCP tool calls fail, report the error clearly to the user
- If buildpack information is null/missing, note this as a configuration issue
- If deployment timestamp is unavailable, note this limitation
