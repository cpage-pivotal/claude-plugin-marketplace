---
name: cost-optimization-report
description: Regenerate the Tanzu Hub cost optimization report (broken/wasted apps, stale apps, orphaned service instances, top spenders) as a self-contained HTML artifact. Use when the user asks to refresh, regenerate, re-run, or update the Tanzu Hub cost report, or asks for a new cost optimization report across Tanzu foundations.
---

# Tanzu Hub cost optimization report

Regenerates the cost-optimization report built in this project: entity-graph-derived
findings (broken apps, stale apps, orphaned service instances) plus modeled and
live-metered cost, rendered as a single HTML artifact.

Two phases: **pull** (you, via the `tanzu-hub` MCP tools — a script can't hold the
session's auth) and **compute+render** (deterministic, via the bundled scripts).
See `references/hub-graphql.md` for background on querying Hub.

## Scripts

Everything either side of an MCP call is scripted. The calls themselves need the
session's auth, so an agent still pastes queries and saves responses — but it
should never construct a query or transform a value by hand.

| Script | Phase | Does |
|---|---|---|
| `gen_stats_queries.py` | 1 | emits `queryStats` batches (≤20 ids, aliased) for the three price metrics |
| `resolve_plan_group_coverage.py` | 1 | `emit-hop1` / `emit-hop2` / `assemble` → which `(offering, plan)` pairs have a rate card |
| `parse_stats_results.py` | 1 | saved responses + rate cards + coverage → `price_series.json` |
| `validate_inputs.py` | 1.5 | preflight; exits 1 on any input problem that has previously shipped a wrong number |
| `compute_report_data.py` | 2 | all report figures → `report_data.json` |
| `build_report_html.py` | 2 | `report_data.json` → self-contained `report.html` |

## Prerequisites

- `tanzu-hub` MCP server connected (`claude mcp list` should show it Connected). If
  not, see `references/hub-graphql.md` for how it's registered/authenticated.
- A working directory to hold raw pulls — create `<scratch>/data/` (use the
  session's scratchpad dir if available; anything else the user points at works too).

## Phase 1 — pull raw data (MCP tool calls, not scriptable)

Run each query below and save the **raw tool result** to the named file under
`<scratch>/data/`. Large results auto-save to a `tool-results/*.txt` file (per the
tool's own error message) — copy that file to the target name rather than
re-fetching. `gql_execute_safe` is read-only; nothing here mutates state.

**Save every response to disk before moving on, even the small ones that come
back inline.** Only the MCP call itself needs the session; everything either side
of it is scripted (`gen_stats_queries.py`, `parse_stats_results.py`,
`resolve_plan_group_coverage.py`). Writing the raw JSON out verbatim and letting
those scripts read it removes the step where numbers get re-typed or reshaped by
hand — which is where every wrong figure this report has published came from.
Never hand-build a compact dict of prices from what you see in tool output.

1. **Foundations in scope** — `get_foundations(first: 10)`. Build
   `foundations.json` as `{"<GUID>": "<entityName>", ...}` for every foundation to
   include (ask the user which foundations if not already clear from context).

2. **Orgs** — for compactness, this typed query (adjust `first` if >100 orgs):
   ```graphql
   query { entityQuery { typed { tanzu { tas { organization {
     query(first: 200) { totalCount entities {
       entityId entityName properties { foundation }
     } } } } } } } }
   ```
   Save as `orgs.json` in the shape `{"entities": [{entityId, entityName,
   properties:{foundation}}, ...]}` — flatten `properties.foundation` to a
   top-level `foundation` key to match what `compute_report_data.py` expects, e.g.
   via `jq '.result.entityQuery.typed.tanzu.tas.organization.query | {entities: [.entities[] | {entityId, entityName, foundation: .properties.foundation}]}'`.

3. **Applications** — first get `totalCount` with `first: 1`, then pull all of
   them in one shot with that count:
   ```graphql
   query { entityQuery { typed { tanzu { tas { application {
     query(first: <totalCount>) { totalCount pageInfo { endCursor hasNextPage }
       entities { entityId entityName properties {
         foundation spaceGUID instanceCount runningInstanceCount crashedInstanceCount
         totalMemoryLimitMB state systemApp routes createdAt updatedAt stack
         runtimeVersion springApp
       } }
     } } } } } } }
   ```
   Save the full tool result (not just `entities`) as `apps.json` — the compute
   script reads `.result.entityQuery.typed.tanzu.tas.application.query.entities`.
   Check `pageInfo.hasNextPage`; if true, page with `after` and merge `entities`.

4. **Service instances** — same pattern:
   ```graphql
   query { entityQuery { typed { tanzu { tas { serviceinstance {
     query(first: <totalCount>) { totalCount pageInfo { endCursor hasNextPage }
       entities { entityId entityName properties {
         foundation spaceGUID boundAppCount plan serviceOfferingName serviceType
         type createdAt updatedAt lastOperationState lastOperationUpdatedAt
         sharedSpacesGUIDs
       } }
     } } } } } } }
   ```
   Save as `services.json`.

5. **Spaces**:
   ```graphql
   query { entityQuery { typed { tanzu { tas { space {
     query(first: <totalCount>) { totalCount pageInfo { endCursor hasNextPage }
       entities { entityId entityName properties {
         foundation organizationGUID totalAppCount totalMemoryLimitMB
         totalServiceInstanceCount
       } }
     } } } } } } }
   ```
   Save as `spaces.json`.

6. **Rate cards** — pull both cards *and* each service card's attached
   `ServicePlanGroup`s in one query, and save it as `<scratch>/rate_cards.json`.
   `parse_stats_results.py` and `resolve_plan_group_coverage.py` both read this
   exact file, so do not trim the `relationshipsOut` block:
   ```graphql
   query { entityQuery { typed { tanzu { platform {
     applicationratecard { query(first: 20) { entities { entityId entityName properties {
       appInstanceHours { unitPrice } appMemoryGbHours { unitPrice } } } } }
     serviceratecard { query(first: 50) { entities { entityId entityName
       properties { serviceInstanceHours { unitPrice } }
       relationshipsOut { isAssociatedWith { tanzu_platform_serviceplangroup(first: 50) {
         totalCount entities { entityId entityName } } } } } } }
   } } } } }
   ```
   There is typically exactly one application rate card platform-wide; if there
   are several, `parse_stats_results.py` warns and uses the first — ask the user
   which applies, or note the ambiguity in the report.

   Then resolve which `(offering, plan)` pairs those cards actually cover. **Do
   not match on plan name** — see the warning in step 7's coverage note. Three
   commands, two of which emit queries for you to run:
   ```bash
   python3 scripts/resolve_plan_group_coverage.py emit-hop1 \
       --data-dir <scratch>/data --out-dir <scratch>/cov
   # run each cov/hop1_NN.gql, save responses as cov/hop1_NN.json
   python3 scripts/resolve_plan_group_coverage.py emit-hop2 --out-dir <scratch>/cov
   # run each cov/hop2_NN.gql, save responses as cov/hop2_NN.json
   python3 scripts/resolve_plan_group_coverage.py assemble --out-dir <scratch>/cov \
       --rate-cards <scratch>/rate_cards.json --out <scratch>/coverage.json
   ```
   Two hops because `ServiceInstance → ServicePlan → ServicePlanGroup` in one
   query returns `INTERNAL` (3 levels of nesting), and batching ids into the
   ServicePlan hop errors intermittently — hop 2 therefore uses one id per alias.
   Aliases that come back empty are reported as `unresolved`, never silently
   counted as uncovered.

7. **Live price series** — **do NOT use `stats_query_metrics` or any `sum by (...)`
   group-by query for this.** That query shape silently caps at 5 returned series no
   matter how many entities actually have data — a prior run of this report measured
   "5 of 76 orgs priced" this way and it was wrong by a wide margin (the real number,
   measured correctly, was 34 of 76). Full story and the exact failure mode in
   `references/hub-graphql.md` under "CRITICAL: `sum by (...)` / `tags`-filtered group-by queries
   silently cap at 5 series" — read it before touching this step.

   Instead, use raw `gql_execute_safe` with `queryStats`'s top-level `entityId`
   argument, batched at **≤20 entity IDs per call** (a clean `BAD_REQUEST` above 20,
   not silent truncation — safe to rely on getting everything back at or under that).
   **Don't hand-write these.** Generate them:
   ```bash
   python3 scripts/gen_stats_queries.py --data-dir <scratch>/data \
       --out-dir <scratch>/stats --services paid
   # run each stats/<metric>_NN.gql, save each response as stats/<metric>_NN.json
   python3 scripts/parse_stats_results.py --results <scratch>/stats \
       --out <scratch>/data/price_series.json \
       --rate-cards <scratch>/rate_cards.json --coverage <scratch>/coverage.json
   ```
   That produces `price_series.json` complete and correctly shaped. Keep the
   generated basenames when saving responses — the parser infers the metric from
   the filename. `--services paid` covers all non-`user-provided` instances (~321
   here); `--services orphaned` is the smaller scope SKILL.md once called the
   minimum, but it understates the metering-coverage tile, so prefer `paid`.

   Doing this by hand cost one session ~76,000 characters of pasted VRNs and ~570
   hand-transcribed floats. Don't.

   **Telemetry quirks the generator already encodes** (all verified 2026-07-27):
   values are DAILY totals, not monthly and not cumulative (a $6.24/day series is
   `$0.26/hr × 24h`, a Postgres Medium rate); `intervalMins` is **ignored** —
   Telemetry always returns daily points; a time window is **required** (omitting
   `startTime`/`endTime`, or using a sub-day window, returns `[]`); a 1-day window
   yields 2 points and the **last** one is today's total. Resist widening the
   window to force large responses: series for deleted or newly created entities
   are ragged, so `data[-1]` stops meaning "today" once the window is long.

   **What "coverage" actually means, now that the query bug is fixed:** virtually
   every org and space returns *some* value (real `$0` if it has no priced
   apps/services running, a positive number otherwise) — because the Application Rate
   Card is typically attached at the Foundation scope, covering everything under it.
   So org/space "coverage" is really a **nonzero-spend count**, not a
   priced-vs-unpriced split — report it as "N of M orgs show nonzero live spend
   today," not "N of M orgs are priced." **Service instances are different and
   genuinely can be unpriced**: an offering with no Service Rate Card at all (not
   just an unattached one) will never return data regardless of query method — cross-
   reference against the rate-card → `ServicePlanGroup` mapping (step 6) to tell
   "zero because idle" apart from "zero because no rate card exists for this
   offering." That second case is the real, fixable finding — see `references/hub-graphql.md`'s
   "Worked example: creating and attaching a Service Rate Card" for how to close it.

   `parse_stats_results.py` assembles `price_series.json` in this shape — the
   contract `compute_report_data.py` reads. Shown for reference; don't build it
   by hand:
   ```json
   {
     "space_total_price": {"<entityId>": <daily_$>, ...},
     "org_total_price": {"<entityId>": <daily_$>, ...},
     "service_instance_price": {"<entityId>": <daily_$>, ...},
     "app_rate_card": {"appInstanceHours": <unitPrice>, "appMemoryGbHours": <unitPrice>},
     "service_rate_cards": {"<rate card entityName>": <unitPrice>, ...},
     "service_plan_group_coverage": {
       "covered_offering_plan_pairs": [["<serviceOfferingName>", "<plan>"], ...],
       "note": "every (offering, plan) pair whose ServicePlanGroup has an attached Service Rate Card"
     }
   }
   ```

   **Do NOT key `service_plan_group_coverage` by plan name alone** (e.g. a flat
   list of `"standard"`, `"proxy"`) — this was a real bug, caught and fixed
   2026-07-27. Plan names like `standard` and `proxy` are reused across many
   *unrelated* offerings, each backed by a different `ServicePlanGroup` entity
   (confirmed: ~18 separate `standard`-named groups exist platform-wide). Matching
   by bare plan name means giving one offering a rate card silently marks every
   *other* offering sharing that generic plan name as "covered" too, even ones with
   no rate card at all — `compute_report_data.py` had exactly this bug until it was
   caught by a user spot-checking the published number. **Always key by the
   `(serviceOfferingName, plan)` tuple**, as in the schema above. Names that are
   already globally distinctive (`on-demand-postgres-db`, `uaa`, `db-small`,
   `tanzu-gpt-oss-120b`, etc.) are safe to match on plan name alone in principle,
   but there's no cost to using the tuple everywhere, so just always do that — one
   matching rule, no special-casing which names happen to be ambiguous today.

   `resolve_plan_group_coverage.py` (step 6) builds this list the only reliable
   way — resolving each offering's actual `ServicePlanGroup` through
   `ServiceInstance → ServicePlan → ServicePlanGroup` and intersecting with the
   groups a rate card is attached to. It never matches on names.

   Include `$0` entries for entities that returned data (don't drop them) — the
   compute script uses presence-in-dict to mean "queryable," and value to mean
   "spend," which are now two different things per the note above.
   `parse_stats_results.py` preserves them; anything you assemble by hand won't.

## Phase 1.5 — validate before computing

```bash
python3 scripts/validate_inputs.py --data-dir <scratch>/data
```

**Run this every time; it is cheap and it fails loudly.** Every wrong number this
report has published came from an input problem that looked fine downstream, and
each check maps to one that actually shipped: a partial `service_instance_price`
pull (`E1`), orphaned instances that were never queried (`E2`), bare plan names
used as coverage keys (`E3`), a missing application rate card (`E4`), plus
warnings for entity/price snapshot drift and orgs/spaces absent from a price dict
(the 5-series cap's signature). Exit status is 1 if any error fires.

If `E2` reports instances that *have* a rate card but no reading, that is a
missing query, not a platform gap — re-run the relevant `gen_stats_queries.py`
batch rather than publishing and explaining it away.

## Phase 2 — compute and render

```bash
python3 scripts/compute_report_data.py \
  --data-dir <scratch>/data \
  --out <scratch>/report_data.json \
  --stale-days 120           # ask the user; 120 is the current default (changed from 90)
  # --now 2026-07-26          # optional override, defaults to real today

python3 scripts/build_report_html.py \
  --data <scratch>/report_data.json \
  --out <scratch>/report.html
```

`compute_report_data.py` produces every number in the report: fleet summary,
live-metering coverage, three finding tiers (broken apps / stale apps / orphaned
services — deduplicated, so an app that's both routeless and crash-looping counts
once), top spaces/orgs by modeled cost, and the rate cards used. Read the
docstring at the top of that file for the exact expected shape of each input
file if a query above needs adjusting for a schema change.

## Phase 3 — publish

Publish `report.html` via the `Artifact` tool (`favicon: "💰"`, keep the same
file path across regenerations if the user wants the same URL updated).

## Visual design

`build_report_html.py`'s template is ported from a Claude Design mockup
("FinOps Report Redesign", file `Cost Optimization Report.dc.html`). **That
mockup is private to the skill's original author — you can't open it, and you
don't need to.** `build_report_html.py` is self-contained; the notes below
exist so the port is understandable if you want to restyle it.

Two things changed porting it into `build_report_html.py`, both required
because this has to run as a self-contained `Artifact`, not inside Claude
Design's editor:
- The `.dc.html` / `<x-dc>` / `support.js` component runtime is Claude
  Design–editor-only. The layout/CSS carried over exactly; the `{{ }}` /
  `<sc-for>` template holes became plain client-side JS (`RENDER_JS` in the
  script) that computes the same bars/tables/derived values from the
  embedded `DATA` blob.
- The mockup's Google Fonts (`Newsreader`, `Public Sans`) are dropped —
  Artifacts block outside network requests including font CDNs. The template
  keeps those font-family names first in the stack so they'll be picked up
  automatically if the user later embeds them as `data:` URIs, but falls
  back to system serif/sans-serif today. Sizes/weights/spacing are
  unchanged, only the exact typeface.

To restyle: edit the inline HTML/CSS in `build_report_html.py` directly.
State literals are Python f-string interpolations from `data`; anything
repeated or derived is computed in `RENDER_JS` from the embedded `DATA`
blob. There is no automated sync with any design tool.

If validating colors for a *new* palette (not this ported one), load the
`dataviz` skill and run its `scripts/validate_palette.js` before adopting
new hex values.

## Notes for future changes

- **`service_instance_price` in `price_series.json` only has data for instances you
  actually queried — a partial pull silently persists as "unmetered" in the report,
  even for instances that genuinely have a rate card and real live pricing.** Caught
  2026-07-27: earlier in this project, only 5 sample instances were ever pulled
  (from the very first pricing probe), and that stale 5-entry dict kept getting
  carried forward through several regenerations — including after adding brand-new
  rate cards — so dozens of instances that *did* have live prices sat mislabeled as
  "unmetered" in the published report. If the user asks "why is X unmetered" and X's
  offering/plan has a rate card (check `service_plan_group_coverage`), the answer is
  almost always "we never queried it," not a real platform gap — re-pull
  `service_instance_price` for the full paid population (or at minimum every
  instance appearing in `tier1_orphaned_services`) via the `entityId`-batched method
  before trusting the number. Cheap to do: ~326 paid instances is 17 calls of ≤20
  each, or as small as 5 calls (~83) if scoped to just orphaned instances.
  **`validate_inputs.py` now catches this as `E1`/`E2` before publish** — it was
  re-verified against a fixture reproducing the exact 5-entry stale dict. The
  remaining risk is skipping the validator, not missing the bug.
- **A `$0.00` price is a REAL metered reading, not a missing one — never test it
  for truthiness.** Caught 2026-07-27, a *second* distinct cause of the same
  "why is X unmetered" complaint as the note above, and it survived the fix for
  that one. Several offerings are deliberately priced at `$0.00/instance-hr`
  (the `AI Models on Tanzu Platform` and `Zero-Cost MCP Servers` rate cards), so
  Telemetry legitimately returns `0` for their instances. Both scripts collapsed
  that into "no data": `compute_report_data.py` had
  `round(live_price * 30, 2) if live_price else None` and
  `build_report_html.py` had `const metered = !!d.monthly_cost;`. Result: 23
  orphaned AI-Models instances were reported as "outside today's metering" when
  they were fully metered at zero — and it masked the fact that only **4**
  instances genuinely sat behind an offering with no rate card at all, which is
  the actual actionable finding. **Always decide "metered" by presence in the
  `service_instance_price` dict (`eid in prices[...]`), never by the value.**
  The compute script now emits per-item `metered` / `has_rate_card` flags plus
  `metered_count` / `zero_priced_count` / `no_rate_card_count`; keep the three
  display states distinct — a dollar figure, `$0.00`, `no rate card`, and
  `no reading` mean four different things to a reader deciding what to spin down.
  Note this was invisible in the orphaned-services table itself (it shows the top
  25 by cost, so `$0` rows sort off the end) — the damage was entirely in the
  section's summary sentence and counts. Check prose, not just tables.
- **Rate cards can change or multiply.** The report assumes one application
  rate card platform-wide. If Hub later has per-foundation or per-org rate
  cards, `compute_report_data.py`'s `app_monthly_cost()` needs the entity's
  applicable card looked up, not a single global constant.
- **"Modeled" vs "live-metered" is the report's central framing** — don't
  collapse the two into one number. Modeled cost is provisioned capacity ×
  the platform's own unit price; live-metered is what Hub's Telemetry
  namespace actually reports today, which may cover only a fraction of the
  estate. If metering coverage improves, the coverage tiles will naturally
  show it.
- **Staleness/scaled-instance findings depend on the environment.** In the
  environment this was built against, no stale app ran more than 1 instance,
  so "stale AND multi-instance" was empty and got folded into a plain
  "stale" tier. Re-check whether that split is worth restoring if a future
  run finds stale multi-instance apps.
