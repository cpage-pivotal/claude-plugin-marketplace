# Tanzu Cost Report

Generate a **cost optimization report** for a Tanzu Platform estate, driven by
Tanzu Hub's entity graph and Telemetry pricing data. The output is a single
self-contained HTML artifact: fleet summary, live-metering coverage, three
tiers of findings (broken apps, stale apps, orphaned service instances), and
top spenders by space and org.

Ask for it in plain language — Claude Code activates the skill automatically:

> *"Generate a cost optimization report for our Tanzu foundations."*
>
> *"Refresh the Tanzu cost report with a 90-day staleness threshold."*

## Skill in this plugin

- **`cost-optimization-report`** — pulls the raw inventory and pricing data
  from Tanzu Hub, validates it, computes every figure, and renders the report.

## Prerequisites

- **A `tanzu-hub` MCP server**, connected and authenticated in your Claude Code
  session. This plugin does **not** configure it — set it up separately:

  ```bash
  claude mcp add --transport http tanzu-hub https://<your-hub-host>/hub/mcp
  # then authenticate interactively with /mcp
  ```

  Verify with `claude mcp list` — it should show `tanzu-hub` as Connected. The
  skill's queries are read-only (`gql_execute_safe`); nothing in the report
  workflow mutates platform state.
- **Python 3** on PATH, for the bundled scripts. No third-party packages.

## How it works

Two phases, deliberately split:

1. **Pull** — Claude runs a fixed set of GraphQL queries through the MCP
   server's session auth (a script can't hold that auth) and saves each raw
   response to disk verbatim.
2. **Compute + render** — bundled Python scripts do every transformation. A
   validator (`validate_inputs.py`) runs between the two phases and exits
   non-zero on the specific input problems that have previously shipped wrong
   numbers.

Nothing is transcribed or reshaped by hand. That's the point: each check in the
validator maps to a real wrong figure this report published at some stage.

## What's bundled

```
skills/cost-optimization-report/
├── SKILL.md                            # the workflow
├── scripts/
│   ├── gen_stats_queries.py            # emit batched queryStats queries
│   ├── resolve_plan_group_coverage.py  # which (offering, plan) pairs have a rate card
│   ├── parse_stats_results.py          # responses -> price_series.json
│   ├── validate_inputs.py              # preflight; fails loudly
│   ├── compute_report_data.py          # all report figures -> report_data.json
│   └── build_report_html.py            # report_data.json -> report.html
└── references/
    └── hub-graphql.md                  # Tanzu Hub querying notes
```

`references/hub-graphql.md` is field notes from building this report — how Hub's
GraphQL API and Telemetry namespace actually behave, including the
`sum by (...)` 5-series cap that silently undercounts priced entities, and a
worked example for creating and attaching a Service Rate Card to close a
"no cost visibility" gap.

## Environment notes

The skill and its reference were developed against one specific Tanzu Hub
install. Concrete numbers in the prose (instance counts, rate card names like
`Production Standard`, example prices) are that environment's, not yours — they
are kept because they illustrate the failure modes, not because they're
universal. Substitute your own Hub hostname for `<your-hub-host>` throughout.

## Installation

```bash
/plugin marketplace add cpage-pivotal/claude-plugin-marketplace
/plugin install tanzu-cost-report@claude-plugin-marketplace
```

## License

MIT
