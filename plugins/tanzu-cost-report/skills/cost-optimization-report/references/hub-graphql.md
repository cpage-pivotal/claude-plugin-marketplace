# Tanzu Hub — interfacing notes

> **Bundled reference.** Ported from the notes the `cost-optimization-report`
> skill was built against. Everything below was verified against one specific
> Tanzu Hub install in July 2026 — replace `<your-hub-host>` with your own Hub
> hostname, and treat concrete prices/rate-card names as that environment's,
> not yours. The sections the skill links to directly are **"CRITICAL: `sum by
> (...)` ... silently cap at 5 series"** and **"Worked example: creating and
> attaching a Service Rate Card"**.

Working notes on how to query Tanzu Hub for reporting (cost, inventory, vulnerabilities,
etc.), gathered while building initial cost reports. Two ways in: the MCP server and the
raw GraphQL API. Prefer MCP tools when one fits; drop to raw GraphQL (via
`gql_execute_safe`) when you need something the tools don't expose.

## Endpoints

- GraphQL API: `https://<your-hub-host>/hub/graphql`
- MCP server: `https://<your-hub-host>/hub/mcp` (registered locally via
  `claude mcp add --transport http tanzu-hub https://<your-hub-host>/hub/mcp`,
  then authenticated interactively via `/mcp` — OAuth, dynamic client registration,
  authorization server discovered from
  `https://<your-hub-host>/.well-known/oauth-protected-resource/hub/mcp`)

Raw HTTP GraphQL calls without a bearer token only work for schema introspection
(`{__typename}`, `__schema`, `sdl`) — actual data queries (e.g. `entityQuery`) return
`PERMISSION_DENIED` unauthenticated. The MCP session's auth carries through automatically
when using the MCP tools.

## MCP tools available (tanzu-hub server)

Two kinds:

1. **Curated tools** wrapping specific GraphQL operations with a friendlier interface:
   `get_organizations`, `get_foundations`, `get_spaces`, `get_applications`,
   `get_platform_alerts`, `get_platform_usage`, `get_platform_vulnerabilities`,
   `get_marketplace`, `get_services`, `get_foundation_capacity`,
   `get_foundation_capabilities`, `get_foundation_certificates`, `get_foundation_groups`,
   `get_connected_vcenters`, `get_job`, `get_application_logs`,
   `application_service_check`, `list_routes`, `admin_get_licenses`,
   `get_tanzu_hub_health`, `stats_query_metrics`, `get_qa_context`.
2. **Generic GraphQL escape hatches**:
   - `gql_execute_safe(graphql: str)` — executes a raw read-only GraphQL query.
     Mutations are unconditionally blocked (no admin check even attempted). The
     block message reads *"Mutations are not supported by this tool. Use
     gql_execute (requires admin)"* — **that `gql_execute` tool is not actually
     exposed to MCP clients** (confirmed via tool search after an account-level
     permission upgrade; still not there). Don't chase it — the block is
     unconditional regardless of caller privilege, and the working path for
     mutations is the browser-token method below.
   - `gql_generate_safe(user_request: str, ...)` — generates GraphQL from natural
     language, can optionally execute/paginate it.

**Why this matters:** the curated tools are the right choice for expressiveness in
common cases. Fall back to `gql_execute_safe` when you need a field/shape the wrapper
doesn't expose, or when introspecting the schema itself.

## GraphQL schema — top-level query roots

Discovered via `{ __schema { queryType { fields { name description } } } }`. Notable
roots: `entityQuery` (inventory/CMDB, `entity:*:read`), `dashboardQuery`,
`derivedDataQuery` (`deriveddata:Export:read`), `documentQuery`, `fleetManagementQuery`,
`groupQuery`, `hubPolicyQuery`, `hyperlinkQuery`, `libraryList` / `libraryCveList`
(Spring/Java/Python/Node catalogs + CVEs), `licenseQuery`, `managementEndpointQuery`,
`notificationQuery`, `profileQuery`, `tenantManagementQuery`, `upgradePlanner`,
`userQuery`, `warehouseQuery`, `capacityQuery`, `insightQuery`, `metricQuery`,
`observabilityQuery`, `pixieProxyQuery`, `platformObservabilityQuery`, `statsQuery`
(time-series stats/forecasts), `artifactMetadataQuery`, `assessmentQuery`,
`repositoryQuery`, `vulnerabilityQuery`, `conversationalQuery`, `authQuery`,
`queryComplexity`, and **`sdl`** (full schema as SDL string) / `stitchedSdl`.

Many roots carry required API permission scopes in their descriptions (e.g.
`entity:*:read`, `libraries:Enabled:read`) — a `PERMISSION_DENIED` error on a query
usually means the authenticated session/token lacks that scope, not that the query is
malformed.

### Pulling the full SDL

`{ sdl }` returns the entire schema as one string — **over 1M characters**, too large
for a normal tool response (`gql_execute_safe` will error with a token-limit message and
instead save the JSON to a file under `~/.claude/projects/.../tool-results/`). To work
with it:

```python
import json
d = json.load(open("<saved-path>"))
sdl = d["result"]["sdl"]
open("/tmp/hub_sdl.graphql", "w").write(sdl)
```

Then `grep`/inspect specific type definitions rather than reading it all — e.g.
`grep -n "^type StatsQuery" -A 30 /tmp/hub_sdl.graphql`.

## Cost / stats querying (`statsQuery`, `stats_query_metrics`)

`stats_query_metrics` (MCP tool) wraps the `statsQuery.queryStats` GraphQL field.
Signature: `query_strings: list[str]`, `namespace` (default `"Observability"`),
`start_time`/`end_time` (ISO-8601), `interval_mins` (default 15), optional `tags`.
Executes all `query_strings` in parallel, keyed by string, against
`StatsInput { namespace, startTime, endTime, intervalMins/intervalSeconds, queryString,
tags, keys, aggregation, ... }`.

For **cost data**, use `namespace: "Telemetry"` with a PromQL-style `queryString`, e.g.:

```
sum by (_org_entity_id, _foundation_entity_id)(space_total_price offset -1d)
```

Response shape (raw): `statsQuery.queryStats[].stats[]` where each `Stat` has `tags`
(key/value pairs like `_org_entity_id`, `_foundation_entity_id`) and a `data` array of
floats, one per interval — **no explicit timestamps come back**; the caller must derive
dates from `startTime` + `intervalMins`/`intervalSeconds` and array index. Arrays can be
shorter than the full window if a tag combination (e.g. an org) didn't exist for the
whole period (e.g. a deleted org only shows 1 data point).

### CRITICAL: `sum by (...)` / `tags`-filtered group-by queries silently cap at 5 series

**Discovered 2026-07-26, cost this session a materially wrong report finding — read
this before writing any query that aggregates cost/usage across many entities.**

A `queryStats` call using PromQL-style group-by (`sum by (_org_entity_id)(...)`) —
whether unfiltered, or filtered via `stats_query_metrics`'s `tags` parameter — **returns
at most 5 series, no matter how many entities actually have data and no matter how large
the filter's entity list is.** Tested explicitly: an unfiltered call returned 5 orgs; a
`tags` filter naming 25 different org IDs *also* returned exactly 5; a filter naming 8
orgs returned only 5 (silently dropping 3, including some that were later confirmed
nonzero). There's no error, no `hasNextPage`/truncation flag — it just quietly hands
back a subset. **Do not treat an empty or short result from a `sum by (...)` /
`tags`-filtered query as "this entity has no cost data."** A report built on this query
shape will drastically undercount how many orgs/spaces/services are actually priced —
this is exactly what happened here: initial measurement claimed only 5 of 76 orgs had
live pricing, when the real number (checked properly, see below) was 34 of 76.

**The fix:** use the top-level `entityId` argument on `queryStats` instead — a
*different* parameter from `StatsInput.tags`, not exposed by the `stats_query_metrics`
MCP tool (only reachable via raw `gql_execute_safe`). It returns one `Stats` entry per
entity, no group-by cap:
```graphql
query {
  statsQuery {
    queryStats(
      entityId: ["<org-1>", "<org-2>", "..."]
      input: { namespace: "Telemetry", queryString: "org_total_price", startTime: "...", endTime: "...", intervalMins: 1440 }
    ) {
      entity { entityId entityName }
      stats { data }
    }
  }
}
```
Confirmed clean at 8 and 20 entity IDs per call (all returned, including legitimate
`$0` entries). **Hard cap: "Cannot query for more than 20 entity ids when query string
is specified in stats query"** — a clean `BAD_REQUEST` error past 20, not silent
truncation, so batch in chunks of ≤20 and it's safe to rely on getting everything back.
For N entities, that's `ceil(N/20)` calls — e.g. 76 orgs in 4 calls, 254 spaces in 13,
vs. the `tags` approach which would need `ceil(N/5)` calls *and* still risk silent
undercount at the boundary.

### Metric name discovery — does NOT work via GraphQL introspection

The `queryString` field on `StatsInput` is documented in the SDL only as: *"Some stats
providers can support stats query strings, in which case the query syntax is specific to
the provider"* — it's an opaque string, not a GraphQL enum/type. There is no schema path
to enumerate valid PromQL metric names like `space_total_price`.

Tried and failed:
- `statsQuery.statsProviders` only enumerates 5 providers — `aria`, `ariaKubernetes`,
  `aws` (null here), `azure` (null here), `platformHealth`. **`Telemetry` is not one of
  them** — it isn't a self-describing/enumerable provider through this field.
- The "list available keys" trick (call `queryStats` with an `entityId` and no
  `queryString`/`keys` filter, per the SDL hint: *"To list available keys for an entity,
  don't filter on keys and specify only the `key` field in stats"*) does **not** work for
  `Telemetry` — it errored with `cannot perform time-series query without specifying
  keys` (when a time window was given) or `Not Found` (without one). That discovery
  trick only applies to providers using the `keys` filter style (e.g.
  `ariaKubernetes`), not `queryString`-style providers like `Telemetry`.

**To find more Telemetry/cost metric names**, options (untried as of this writing):
1. Product docs for Tanzu Hub's cost/telemetry metrics.
2. Capture the Hub UI's own network calls (its cost dashboards must issue queries like
   the sample above) via browser devtools/HAR.
3. Guess siblings by naming convention (e.g. `org_total_price`,
   `foundation_total_price`, `app_total_price`) and test directly against
   `stats_query_metrics`.
4. Ask a Tanzu Hub admin/vendor for a metric catalog.

## Altair — the built-in GraphQL explorer with example collections

`https://<your-hub-host>/hub/altair` is Hub's embedded Altair GraphQL client.
It ships with a large tree of **pre-loaded, working example queries/mutations**,
organized by domain: Starter (auth + basic queries), Business Applications, Entity
Queries, TAS Services & Applications, Platform Health & Operations, Dashboard
Management, Assessment Center, Export & Reports, Notifications, TAS Foundations,
Management Endpoints, Licenses, Subscription Queries. **Check here before
reverse-engineering a query shape from the SDL by trial and error** — there's a good
chance a working example already exists.

### The sanctioned way to get a bearer token (no browser-session extraction needed)

Altair's welcome text documents a **client-credentials OAuth flow** that's the proper
alternative to the browser-token-extraction workaround described below:

1. In the Hub Web UI: **Administration → Roles and permissions** → create an OAuth
   app → assign it a role/permission set (this is how you'd scope a bot/automation
   credential to exactly what it needs, e.g. `applicationMgmt:Application:update` for
   a cost-automation tool, without borrowing a human session's roles).
2. Exchange the app's ID/secret for an access token with this mutation (no
   Authorization header needed for this one call — it's what produces the header for
   everything else):
   ```graphql
   mutation createToken($OAUTH_APP_ID: String!, $OAUTH_APP_SECRET: String!) {
     authMutation {
       oAuthAppMutation {
         generateAccessTokenForOAuthApp(input: {
           oauthAppId: $OAUTH_APP_ID
           oauthAppSecret: $OAUTH_APP_SECRET
         }) {
           accessToken       # just the token
           authorization     # full "Bearer ..." header value
           expiresInSeconds
         }
       }
     }
   }
   ```
3. Use the returned token as `Authorization: Bearer <accessToken>` on subsequent
   requests — same as the extracted-browser-token approach, but scoped deliberately
   rather than inheriting whatever a human happens to have.

This is the preferred path going forward for any mutation-executing automation — set
up a purpose-scoped OAuth app once, rather than re-extracting a human's session token
per use.

### Entity metric-key discovery — tried, also a dead end for `Telemetry`

The "Entity Queries" collection's "09 - Entity Metrics and Stats" example uses a
**different path than `statsQuery.queryStats`** — it goes through the entity graph:
```graphql
query getAllAvailableMetrics($entityId: [EntityId!]) {
  entityQuery {
    queryEntities(entityId: $entityId) {
      entities {
        entityId
        stats { key }
      }
    }
  }
}
```
**Tried against both an Organization and a Space entity ID — doesn't crack the
`Telemetry` metric-name discovery problem either.** Without a namespace specified, it
returns a fixed 8 `Stat` entries all with `key: ""` (one placeholder per registered
stats provider, presumably `aria`/`ariaKubernetes`/`aws`/`azure`/`platformHealth` plus
a few not exposed via `statsProviders`, `Telemetry` likely among them) — real `key`
values only come back for providers that use `keys`-style filtering (e.g.
`ariaKubernetes`); `queryString`-based providers like `Telemetry` just resolve to an
empty placeholder instead of erroring. Explicitly passing `input: { namespace:
"Telemetry" }` here reproduces the same `Not Found` error as the direct
`statsQuery.queryStats` attempt — so this is the same dead end via a different
resolver path, not a new one. **Metric-name discovery for `Telemetry` remains
unsolved** — still need product docs, a Hub UI network capture of its own cost
dashboards, or naming-convention guessing (see the Cost/telemetry-metrics section
above).

The companion query in the same example (`nameSpaceStats`) does still confirm the
correct field name for fetching an entity by ID is **`queryEntities(entityId:
[EntityId!])`**, not `apps` (the `apps` key seen in `get_applications` MCP tool
responses is that tool's own response envelope, not a literal GraphQL field name —
don't assume MCP tool response keys are real schema fields when hand-writing raw
GraphQL).

## Executing mutations (bypassing the MCP tool's read-only guard)

**Confirmed working end-to-end** (2026-07-26): created a `ShowbackRateCard` and
attached it to entities via this exact flow — see the worked example below.

Both `gql_execute_safe` and `gql_generate_safe` unconditionally block mutations — this
is deliberate, not permission-based, so there's no MCP-level way to run a write through
them regardless of the caller's actual privileges. **Account-level permission changes
don't change this.** `authQuery.hasPermissions` accurately reflects a real permission
grant (verified: flipped from missing to `true` immediately after an admin granted a
user elevated rights, no re-auth needed) — but that only means the *account* can
perform the mutation once you reach the GraphQL endpoint with a real token. It does
**not** unlock any additional MCP tool. The browser-token + `curl` path below is still
required regardless of how privileged the account is — permission level and MCP tool
access are orthogonal.

To run a mutation, extract a real bearer token from an authenticated Hub **browser**
session (not the MCP OAuth session, which Claude Code doesn't expose as a readable
token) and call `/hub/graphql` directly with `curl`. Steps, using `playwright-cli`:

1. Open a **headed** browser and have the human authenticate interactively (SSO/Keycloak
   — Claude driving a headless/scripted login won't work and shouldn't be attempted):
   ```bash
   playwright-cli -s=hub open https://<your-hub-host> --browser=chrome --headed
   ```
2. Wait for the human to confirm they've completed login in that window.
3. Pull the access token out of `sessionStorage` (this is where Hub's Angular frontend
   stores its live OIDC session — `localStorage` also has a similar `tp_app_oauth2_token`
   JSON blob, either works):
   ```bash
   playwright-cli -s=hub sessionstorage-get access_token
   ```
4. Use it as a bearer token directly against the GraphQL endpoint:
   ```bash
   curl -s -X POST https://<your-hub-host>/hub/graphql \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"query": "mutation { ... }"}'
   ```
5. Close the session when done: `playwright-cli -s=hub close`.

**Before attempting any mutation, check permissions first** — cheap and read-only, via
`authQuery.hasPermissions` (works through `gql_execute_safe`, no token extraction
needed, since it's just a read):
```graphql
query {
  authQuery {
    hasPermissions(authPermissions: ["applicationMgmt:Application:update"]) {
      hasPermissions
      missingPermissionNames
    }
  }
}
```

### Verify a mutation's effect via entity relationships, not Telemetry stats

After a mutation, re-query the affected entity read-only to confirm it actually took —
but **don't use `stats_query_metrics`/Telemetry for this**. Telemetry cost data appears
to run on a batch/delayed pipeline: right after attaching a brand-new rate card to a
service's `ServicePlanGroup`, `service_instance_price` for an instance under that plan
still came back empty (`queryStats: []`) the same day, even though the association
itself was already live. Confirm via the entity graph instead — it reflects a write
immediately:
```graphql
query {
  entityQuery {
    typed { tanzu { platform { serviceratecard {
      query(entityId: ["<rateCardId>"]) {
        entities {
          entityName
          properties { serviceInstanceHours }
          relationshipsOut {
            isAssociatedWith { tanzu_platform_serviceplangroup(first: 10) { totalCount entities { entityName } } }
          }
        }
      }
    } } } }
  }
}
```
An empty stats result right after a rate-card mutation is expected, not a sign the
mutation failed — check back the next day (or whenever the metering batch runs) if you
need the dollar figure to actually appear in `space_total_price`/`org_total_price`.

### Worked example: creating and attaching a Service Rate Card

Closes real "no cost visibility" gaps — a service offering with **no rate card at all**
(not just an unattached one) shows zero live price no matter how you query it, since
there's nothing to compute a price from. Steps:

1. **Find the rate card schema id and the target scope's `allowedScopeTypes`** (read-only):
   ```graphql
   query {
     entityQuery { typed { tanzu { platform {
       serviceratecardschema { query(first: 5) { entities { entityId entityName properties { allowedScopeTypes } } } }
     } } } }
   }
   ```
   For the Service schema, `allowedScopeTypes: ["Tanzu.Platform.ServicePlanGroup"]` — so
   entities passed to `attachEntitiesToRateCard` must be `ServicePlanGroup` ids, not
   `ServiceOffering` or `ServicePlan` ids. **A single "offering" name in the UI (e.g.
   "AI Models on Tanzu Platform") can map to several `ServicePlanGroup` entities** — one
   per plan variant. List them all first:
   ```graphql
   query {
     entityQuery { typed { tanzu { platform {
       serviceplangroup { query(first: 100) { totalCount entities { entityId entityName } } }
     } } } }
   }
   ```
   and match by name pattern (plan-group names are the CF plan name, e.g.
   `tanzu-gpt-oss-120b`, not the offering's display name) — there's no direct
   offering→plan-group query path found so far, so this list-and-match is the working
   approach **only when the plan name is globally distinctive**.

   **Warning — generic plan names collide across unrelated offerings.** Names like
   `standard` and `proxy` are not unique: the platform-wide `serviceplangroup` list
   above showed ~18 separate `standard`-named `ServicePlanGroup` entities, one per
   offering, each a distinct entity with its own GUID. Matching on the bare name
   `"standard"` will silently grab the wrong offering's plan group (or several).
   **Caught a real instance of this 2026-07-27**: after pricing 6 offerings that
   happened to use `plan: standard`, a coverage report keyed by plan name alone
   would have also marked 7 *other*, still-unpriced `standard`-plan offerings as
   covered. When the plan name isn't obviously distinctive, resolve the actual
   `ServicePlanGroup` per offering instead of guessing from the name — pick one
   representative `ServiceInstance` for that offering and traverse:
   ```graphql
   query {
     entityQuery { typed { tanzu { tas { serviceinstance {
       query(entityId: ["<a ServiceInstance id for this offering>"]) {
         entities { relationshipsOut { isContainedIn { tanzu_tas_serviceplan { entityId entityName } } } }
       }
     } } } } }
   }
   ```
   then a second hop, `ServicePlan → isContainedIn → ServicePlanGroup`:
   ```graphql
   query {
     entityQuery { typed { tanzu { tas { serviceplan {
       query(entityId: ["<ServicePlan id from the previous step>"]) {
         entities { relationshipsOut { isContainedIn { tanzu_platform_serviceplangroup { entityId entityName } } } }
       }
     } } } } }
   }
   ```
   Two gotchas doing this at scale: (1) chaining both hops in one nested query
   (`serviceinstance → ... → serviceplan → ... → serviceplangroup`, 3 levels) errors
   `INTERNAL` — do it as two separate queries instead. (2) Batching many entity IDs
   into the second hop (`serviceplan.query(entityId: [...])`, plural) also
   intermittently errors `INTERNAL` on specific plans for no apparent
   plan-name-related reason — fall back to one `entityId` per call (still cheap,
   these are point lookups) rather than debugging which one is poisoning the batch.
   Once you have one `(offering, plan) → ServicePlanGroup entityId` mapping, all
   *other* service instances sharing that same `(offering, plan)` pair share the
   same plan group — no need to resolve per-instance, just per distinct pair.

2. **Create the rate card** (mutation, needs a real bearer token per the steps above):
   ```graphql
   mutation {
     showbackMutation { showbackRateCardMutation {
       create(input: [{
         name: "AI Models on Tanzu Platform"
         rateCardType: SERVICE
         rateCardSchemaId: "vrn/provider:Tanzu/ServiceRateCardSchema:service-rate-card-schema"
         componentsPrice: [{ component: "serviceInstanceHours", unitPrice: 0.01 }]
       }]) {
         status { status errorMessage }
         rateCard { entityId entityName }
       }
     } }
   }
   ```
   Returns the new rate card's `entityId` — capture it for step 3.

3. **Attach it to every relevant `ServicePlanGroup`** found in step 1:
   ```graphql
   mutation {
     showbackMutation { showbackRateCardMutation {
       attachEntitiesToRateCard(
         rateCardId: "<entityId from step 2>"
         entityIds: ["<ServicePlanGroup entityId>", "..."]
         canOverride: false
       ) { status { status errorMessage } }
     } }
   }
   ```
   `canOverride: false` is the safe default — it'll fail loudly instead of silently
   replacing an existing association if a plan group is already priced elsewhere.

4. Verify per the entity-relationship query above, not Telemetry stats.

The Application rate card side works the same way but scopes to
`Tanzu.TAS.Foundation` instead (`allowedScopeTypes: ["Tanzu.TAS.Foundation"]`) — one
card can cover an entire foundation's app footprint, confirmed already attached to both
foundations in this environment (`Production Standard`, $0.114/instance-hr +
$0.003/GB-hr).

### Known limitation: token scope vs. Web UI capability

The extracted `tp_app` OAuth token's `scope` claim is minimal (`["openid", "roles"]`);
the actual authorization roles live in the **`id_token`**'s `roles` claim (e.g.
`["opsman.restricted_view", "platform-users"]`), not the access token's `scope`. A
mutation attempt with insufficient permission surfaced as an opaque **502**, not a clean
`PERMISSION_DENIED` — so a 502 on a mutation should be treated as "check
`hasPermissions` first," not assumed to be a transient gateway issue.

Per Hub's RBAC docs, Hub-level roles are only `Administrator` (all operations) and
`Viewer` (read-only) — **application lifecycle permissions
(`applicationMgmt:Application:update`/`delete`) are gated by your synced Cloud Foundry
org/space role** (e.g. `SpaceDeveloper`), not by Hub-level roles. Seeing the Stop/Start
button in the Hub Web UI for a given app is a faster/free way to check whether your CF
space role actually grants this than extracting a token and probing — if the button
isn't visible on the app detail page, the CF space role isn't there yet, and a 502 on
the equivalent mutation is expected, not a bug.

Extracted tokens are short-lived (~30 min per the `exp`/`iat` claims) — re-extract
fresh each time rather than reusing a saved one.

## Resolving entity IDs to names

`stats_query_metrics` results are tagged with VRN-style entity IDs, e.g.:
```
vrn/provider:TAS/instance:p-bosh-da61b5b8f5a5c0050a8f/Organization:3a9fe1ad-9da4-4119-afcc-2feed8a5aaf8
```
Resolve these to names via `get_organizations(orgId: [...])` (accepts a list of VRN
IDs) or `get_foundations`. Note: an org ID that no longer exists in the inventory (e.g.
deleted mid-period) won't be returned by `get_organizations` even if it still appears in
historical stats data — treat it as "unknown/deleted" rather than an error.

## Example known-good queries

Sanity check (no auth needed, schema-only):
```graphql
{ __typename }
```

Org lookup by VRN ID list:
```graphql
# via get_organizations MCP tool, not raw GraphQL
get_organizations(orgId: ["vrn/provider:TAS/instance:.../Organization:..."])
```

Cost by org/foundation for a date range (via `stats_query_metrics`):
```json
{
  "query_strings": ["sum by (_org_entity_id, _foundation_entity_id)(space_total_price offset -1d)"],
  "namespace": "Telemetry",
  "start_time": "2026-05-01T00:00:00.000Z",
  "end_time": "2026-05-31T00:00:00.000Z",
  "interval_mins": 1440
}
```
