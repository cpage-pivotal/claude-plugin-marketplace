---
name: tanzu-agent-deploy
description: Deploy AI agents to Tanzu Platform for Cloud Foundry using the Agent Buildpack (GA in Tanzu AI Services 11.0) and MCP Gateway. Use this skill whenever the user wants to push/deploy an agent app with `cf push`, create or edit AGENTS.md (the agent's system prompt) or manifest.yaml for an agent buildpack app, bind/configure/troubleshoot a chat model or LLM connection for an agent (ai-models service binding, user-provided service, TANZU_AGENT_DEFAULT_MODEL, or TANZU_AGENT_OPENAI_*/TANZU_AGENT_GENAI_*/TANZU_AGENT_GCP_*/TANZU_AGENT_ANTHROPIC_* env vars), put Tanzu SSO in front of an agent, add Agent Memory Service or Credential Store to an agent, or create/configure/register servers with/connect an agent to an MCP Gateway (on-platform or off-platform MCP servers, auth bindings like OIDC/OAUTH/GITHUB_ENTERPRISE/USER_INFO, tool filtering). Trigger even if the user doesn't say "Tanzu" explicitly but mentions cf push for an agent, Cloud Foundry agent deployment, agent buildpack, Tanzu Agent, or MCP gateway.
---

# Tanzu Platform AI Agent Deployment

Deploy AI agents on Tanzu Platform for Cloud Foundry via the
[Agent Buildpack](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/ai-services/11-0/ai/app-dev-guide-agent-buildpack-deploy-an-ai-agent.html)
and [MCP Gateway](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/ai-services/11-0/ai/app-dev-guide-mcp-gateway-mcp-gateway-guide.html).
The buildpack is **generally available as of Tanzu AI Services 11.0** (it installs the
Tanzu Agent runtime); everything below is written against that release. The full
variable list is in
[AI Agent Environment Variables](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/ai-services/11-0/ai/app-dev-guide-agent-buildpack-ai-agent-environment-variables.html).

This skill is self-sufficient for the common workflows below. To scaffold an MCP
server to deploy alongside the agent, use the `spring-ai-mcp-server` skill; for
agent-to-agent (A2A) delegation between agent apps, use the `tanzu-agent-a2a`
skill.

## 0. Check the foundation first

```bash
cf buildpacks | grep -E '^\S+\s+agent_buildpack\b'   # GA buildpack name, and its stacks
cf marketplace | grep -E 'ai-models|mcp-gateway|p-identity|agent-memory|credential-store'
```

- Use **`agent_buildpack`**. A foundation upgraded from 10.x may still carry
  `agent_buildpack_beta` (the technical preview) — don't use it for new work.
- If the operator left the tile's *Install Agent Buildpack* errand off, upgrading the
  tile does **not** update the buildpack. The version that matters is the one in the
  staged droplet, not the tile:
  ```bash
  cf curl "/v3/apps/$(cf app my-agent --guid)/droplets/current" | jq '.buildpacks, .stack'
  ```
- `agent-memory` and `credential-store` are new 11.0 offerings (§5, §6). If they are
  missing from the marketplace, the foundation isn't on 11.0 yet.

## 1. Agent Buildpack basics

An agent buildpack app needs only two files:

```
my-agent/
├── AGENTS.md       # system prompt (required; any letter case)
└── manifest.yaml   # CF manifest (optional but recommended)
```

Optional additions: `skills/<name>/SKILL.md` (or `.agents/skills/...`) for on-demand
skills, `branding/` (`logo.svg`, `favicon.svg`, `style.css`), and `a2a-peers.yaml`
(see `tanzu-agent-a2a`).

**manifest.yaml**
```yaml
applications:
  - name: my-agent
    path: .                       # relative to this file: push only the agent dir
    buildpacks:
      - agent_buildpack           # name it explicitly if the dir also has
                                  # requirements.txt or package.json
    # stack: tanzucflinuxfs1      # pin if the foundation's default stack may change
    memory: 1G
    health-check-type: http
    health-check-http-endpoint: /health
    health-check-invocation-timeout: 10
    timeout: 180
    env:
      TANZU_AGENT_DISPLAY_NAME: My Agent
      TANZU_AGENT_DEFAULT_MODEL: <model name from the bound plan>   # see §2
```

Why those health-check lines:
- `GET /health` is the runtime's own liveness probe. It returns HTTP 200 with
  `{"status":"healthy"}`, or `{"status":"degraded","reason":"no model configured"}`
  before a model is bound — so the push-before-bind sequence still starts.
- The runtime is a single asyncio process. The first chat request (cold model client
  plus MCP OAuth token exchanges) can stall it for several seconds, and with the
  platform's 1s default invocation timeout Diego kills a healthy app. Give it 10s.
  Health-check settings only apply on restart, so put them in the manifest before the
  first push.
- `path: .` keeps `cf push -f path/to/manifest.yaml` from uploading the working
  directory (build output, `node_modules`) when run from elsewhere.

Deploy with `cf push`. The app starts in **degraded mode** until an AI model is
bound — `curl https://<agent>/health` says so. Bindings are read only at startup, so
**bind everything, then restage once** (§7).

### Writing AGENTS.md

`AGENTS.md` is the agent's system prompt, written in plain markdown. It should
describe:
- The agent's persona and purpose
- What tools/capabilities it has access to
- Behavioral guidelines (e.g., confirm before taking destructive actions)

Example:
```markdown
# My Agent

You are a helpful assistant with access to GitHub via the GitHub MCP server.

When interacting with GitHub, confirm actions with the user before making
any changes (creating issues, pull requests, comments, etc.).
```

Never put secrets in `AGENTS.md` — it is served back to signed-in users in the debug
panel. Skills follow the Agent Skills format (front matter `name` + `description`);
only the name and description enter the prompt, the body loads on demand. MCP servers
that publish `instructions` have them added to the system prompt automatically.

## 2. Binding a chat model

### Option 1: Bind an `ai-models` service instance (recommended)

```bash
cf marketplace -e ai-models
cf create-service ai-models <PLAN> my-agent-model --wait
cf bind-service my-agent my-agent-model
cf restage my-agent
```

**Prefer a single-model plan.** Each plan's `config_url` advertises its models, and
with no explicit choice the agent takes **the first model the first bound plan
advertises**. On multi-model plans that is often an embedding model
(e.g. `nomic-embed-text`): the agent starts, reports healthy, and never answers.

**Pin the model with `TANZU_AGENT_DEFAULT_MODEL`** on any multi-model plan, and as
belt-and-braces on a single-model one. Two things to know:
- The value must match an advertised model name **exactly**. A miss is only a log
  warning (`... is not in the advertised model list ...; falling back to default
  resolution chain`) followed by the first advertised model — the embedding-model
  failure again, silently. After deploy, check the log for
  `Using TANZU_AGENT_DEFAULT_MODEL=...`.
- It replaced the technical preview's `TANZU_AGENT_GENAI_MODEL_NAME`, which the
  runtime still reads only as a fallback (and for the local-tile option below).

Every bound `ai-models` instance adds its models to the chat UI's model picker, so
binding several plans lets users choose. Bindings are found by tag:
`TANZU_AGENT_GENAI_SERVICE_TAG` (default `genai`) and, for Claude on Anthropic API
plans, `TANZU_AGENT_ANTHROPIC_SERVICE_TAG` (default `tanzu-ai-models`).

Model tuning (users can override all four for themselves on the settings dashboard):

| Variable | Values |
|---|---|
| `TANZU_AGENT_DEFAULT_MODEL` | a model name from a bound plan |
| `TANZU_AGENT_REASONING_EFFORT` | `off` `minimal` `low` `medium` `high` `xhigh` — works with Gemini and with Claude on Anthropic plans as of 11.0 |
| `TANZU_AGENT_TEMPERATURE` | `0.0`–`1.0` |
| `TANZU_AGENT_MAX_TOKENS` | max output tokens |

### Option 2: User-provided service (mirrors an ai-models binding)

Create a user-provided service with the `genai` tag and the same credential
shape, and the buildpack treats it like a managed binding:

```bash
cf create-user-provided-service my-model \
  -t "genai,ai-models,llm" \
  -p '{
    "endpoint": {
      "api_base":        "...",
      "api_key":         "...",
      "name":            "my-model-name",
      "openai_api_base": "..."
    }
  }'
cf bind-service my-agent my-model
```

**Important:** `base_url = api_base + "/openai/v1"` — this matches the Tanzu
genai proxy URL structure but does **not** work cleanly for raw OpenAI
endpoints. Use Option 3 for those. With no `config_url` the model name can't be
discovered: set `TANZU_AGENT_DEFAULT_MODEL` (or `TANZU_AGENT_GENAI_MODEL_NAME`).

### Option 3: Environment variables

For any OpenAI-compatible API (including OpenAI itself), remove the `genai`
tag from any bound service and set env vars instead:

```bash
cf set-env my-agent TANZU_AGENT_OPENAI_API_BASE  https://api.openai.com/v1
cf set-env my-agent TANZU_AGENT_OPENAI_API_KEY   <your-api-key>
cf set-env my-agent TANZU_AGENT_OPENAI_MODEL_NAME gpt-4o
cf restage my-agent
```

Use `cf set-env` for keys — never commit them in `manifest.yaml`.

### Provider priority order

1. A bound `ai-models` / `genai`-tagged service (Options 1 & 2)
2. `TANZU_AGENT_GENAI_API_BASE` + `TANZU_AGENT_GENAI_API_KEY` (+ `_MODEL_NAME`) — local GenAI tile
3. `TANZU_AGENT_GCP_PROJECT_ID` + `TANZU_AGENT_GCP_PRIVATE_KEY` + `TANZU_AGENT_GCP_CLIENT_EMAIL` — Vertex AI
4. `TANZU_AGENT_OPENAI_API_BASE` + `TANZU_AGENT_OPENAI_API_KEY` — any OpenAI-compatible endpoint
5. `TANZU_AGENT_ANTHROPIC_API_KEY` + `TANZU_AGENT_ANTHROPIC_MODEL_NAME`, or a bound `tanzu-ai-models` service

If a bound service resolves, the env-var sources are ignored — unbind it (or drop the
tag) to fall back to them.

## 3. Tanzu SSO in front of the agent

Bind a Tanzu SSO (`p-identity`) instance and the agent requires sign-in for its UI,
`/api/*` and `/a2a`, and keeps MCP connections, tokens, model choice and settings
**per user**. Anything that calls a per-user MCP OAuth flow (§4) needs this.

```bash
cf marketplace -e p-identity
cf create-service p-identity <PLAN> my-agent-sso

cf bind-service my-agent my-agent-sso --wait -c '{
  "grant_types":   ["authorization_code"],
  "redirect_uris": ["https://my-agent.apps.<domain>/api/auth/callback"],
  "scopes":        ["openid","profile","email"]}'
cf restage my-agent
```

- **Pass `redirect_uris` explicitly.** The broker registers an SSO client at bind time;
  observed behaviour is that it rejects `authorization_code` without a redirect URI,
  rejects a `name` parameter on an app binding, and accepts only
  `["authorization_code","client_credentials"]` as a multi-grant combination.
- The callback is `<BASE_URL>/api/auth/callback`. 11.0 no longer derives it from request
  headers: `TANZU_AGENT_BASE_URL` defaults to the app's first external route, so set it
  (and register the matching redirect URI) only if users reach the agent at another host.
- Set `TANZU_AGENT_AUTH_OAUTH_SCOPES` to the scopes the client was registered with
  (`openid profile email`). The default is the same, but leaving it unset logs a
  startup WARNING.
- **Verify:** `curl https://my-agent.../api/auth/status` → `"enabled": true`. If the IdP is
  unreachable at startup the agent **runs without auth** and logs
  `Failed to probe OIDC endpoints for SSO binding` — always check this endpoint.
- In the UI, *Sign in with SSO* opens the IdP in a **new tab**. Until sign-in completes
  the input box reads "No model configured" because `/api/configure` returns 401 — it is
  not a missing model binding.
- Other knobs (all `TANZU_AGENT_` prefixed): `AUTH_SESSION_HOURS` (8),
  `AUTH_ENFORCE_API` (true), `AUTH_A2A_PROTECTED` (true), `AUTH_EXCLUDED_PATHS`
  (e.g. `/api/webhooks/github`), `SESSION_SECRET` (`cf set-env` only).

## 4. MCP Gateway

The MCP Gateway brokers access to MCP servers behind a single endpoint with an audit
log (JSON lines on the `mcp.audit` logger: tool name, `enduser.id`, OAuth client, and
arguments/results when payload logging is on).

```bash
# Create a gateway instance; enable the dashboard (off by default as of 11.0)
cf create-service mcp-gateway gateway my-gateway --wait -c '{"env":{"ENABLE_DASHBOARD":"true"}}'
```

The dashboard URL is shown in `cf service my-gateway`. With `ENABLE_DASHBOARD` false
(the default) the gateway's root URL returns 404. Other `env` keys: `LOG_LEVEL`,
`UPSTREAM_TIMEOUT_SECONDS` (60). Instances created before 11.0 need
`cf upgrade-service my-gateway` (or the operator's *Upgrade all MCP Gateway service
instances* errand) before they can use Credential Store.

### Registering an off-platform MCP server

Use the `mcp-servers` config for servers running outside CF. Pass it at
creation or update time:

```bash
cf create-service mcp-gateway gateway my-gateway --wait -c '{
  "mcp-servers": [{
    "name": "my-server",
    "url":  "https://external-mcp-server.example.com/mcp",
    "metadata": {
      "description": "Optional human-readable description"
    }
  }]
}'
```

`mcp-servers` updates are **declarative** — list every server you want to keep:
```bash
cf update-service my-gateway --wait -c '{
  "mcp-servers": [{
    "name": "my-server",
    "url":  "https://external-mcp-server.example.com/mcp"
  }]
}'
```

To remove all off-platform servers: `cf update-service my-gateway --wait -c '{"mcp-servers": []}'`

> **Credentials for upstream servers:** the `mcp-servers` entry itself carries no
> headers or auth. As of 11.0, bind a **Credential Store** (§6) and the gateway injects
> a per-user or shared credential on the upstream call. Alternatively connect the agent
> to the server directly with a user-provided service carrying the credential (§4,
> *Connecting an agent*), at the cost of the gateway's audit log.

### Registering an on-platform CF app as an MCP server

The app needs an internal route (`apps.internal`) — the gateway only binds to
apps via internal networking:

```bash
# Add internal route if not already present
cf map-route my-mcp-app apps.internal --hostname my-mcp-app

# Bind the app to the gateway (~60-70s; run several binds concurrently)
cf bind-service my-mcp-app my-gateway --wait
```

Bind parameters (`-c '{...}'`):
- **`auth`** — `{"service-instance": {"type": ..., "name": ...}}`, instance in the same
  space. Tanzu SSO (`p-identity`) supports only `OIDC`; a user-provided instance
  supports `OIDC`, `OAUTH`, `GITHUB_ENTERPRISE` or `USER_INFO`.
- **`upstream_mcp_path`** — where the app serves MCP; default `/mcp`.
- **`tool_filtering`** — see below.
- **`metadata.description`**.

```bash
# An MCP server that is an OAuth resource server behind Tanzu SSO
cf bind-service my-mcp-app my-gateway --wait \
  -c '{"auth":{"service-instance":{"type":"OIDC","name":"my-agent-sso"}}}'
```

> **The silent failure:** if the MCP server requires a token and you bind it
> *without* an `auth` block, the bind succeeds, the gateway gets a 401 from the app
> over `apps.internal`, and serves an **empty tool list** — which looks like a working
> server. "The backing business API is unauthenticated" is not a reason to omit it;
> what matters is whether the MCP server itself validates tokens.

Binding an app to the gateway does not change anything the app reads — never restage
or restart the MCP server app for it.

### Tool filtering (11.0)

Ordered rules decide which tools each caller can discover and call. First matching
`condition` wins; **if no rule matches, the caller gets no tools**, so end with a
catch-all `""`. Conditions can test only `username` (`==`, `!=`) and `roles`
(`'<role>' in roles`). `include_patterns`/`exclude_patterns` are fnmatch globs;
exclude wins.

```bash
# On an existing binding — no unbind/rebind needed (keys are CF app names)
cf update-service my-gateway --wait -c '{
  "mcp_server_bindings": {
    "my-mcp-app": {
      "tool_filtering": {
        "filter_rules": [
          { "condition": "'\''admin'\'' in roles", "include_patterns": ["*"] },
          { "condition": "", "include_patterns": ["get*", "list*"] }
        ]
      }
    }
  }
}'
cf service my-gateway --params    # inspect current settings
```

The same `tool_filtering` object goes in an `mcp-servers` entry or in a bind's `-c`.
Sending `"filter_rules": []` removes filtering for that app. Check what your IdP
actually puts in `username` before matching on it: a UAA zone federated to an external
IdP can carry a shadow-user GUID there rather than an email.

### Connecting an agent to an MCP server via the gateway

The gateway exposes each registered server at a path taken from the **app name** (or
the `mcp-servers` `name`): `https://<gateway-route>/<server-name>/mcp`.

Create a user-provided service tagged `mcp-server` pointing at that URL, then
bind it to the agent:

```bash
cf create-user-provided-service my-mcp-gateway \
  -p '{"url": "https://my-gateway.apps.example.com/my-mcp-app/mcp"}' \
  -t mcp-server

cf bind-service my-agent my-mcp-gateway
cf restage my-agent
```

Name the UPS differently from the app it points at (e.g. `<app>-gateway`) so
`cf bind-service` lines are unambiguous.

The agent discovers `mcp-server`-tagged bindings (and `data-product` bindings) at
startup. Credential shapes a binding can carry, for servers reached directly or through
the gateway:

| Binding field | Behaviour |
|---|---|
| `api_key` | `Authorization: Bearer <api_key>` on every request |
| `headers` | extra HTTP headers on every request (11.0) |
| `auth_type: bearer` | each user enters a token with *Set token* |
| `client_id` + `client_secret` + `token_url` | OAuth 2.0 client credentials, auto-refreshed |
| `oauth` | same, camelCase or snake_case (11.0) |
| `api_token` | Tanzu Hub API token exchanged for short-lived tokens (11.0) |
| `mcpServers` map + `mcp.oauth` | several servers in one binding, shared credentials (11.0) |
| *(none; server publishes OAuth metadata)* | per-user **Connect** with dynamic client registration |

A server that answers 401/403 to the startup probe is treated as a bearer-token server.

### What a gateway route with OIDC auth looks like to the user

The agent logs `MCP server '<name>' requires OAuth (MCP_OAUTH) — skipping until user
authenticates` and `No MCP toolsets registered`. **That is the correct end state** —
don't chase it. Tools appear per user, after they sign in (§3) and, in the MCP panel,
click **Connect** on each server. Each Connect opens a gateway consent page in a new
tab ("Application Access Request: the application `py-agent-<ups-name>` wants to access
the MCP server ...", naming the agent's `/api/mcp/oauth/callback`); the user clicks
**Allow Access**. Each gateway route is its own OAuth resource, so N servers means N
Connects.

**Per-user MCP tokens are held in memory.** Any `cf restart`, `cf restage` or `cf push`
of the agent drops them and every user must Connect again. Binding a Credential Store
changes this model (§6).

## 5. Agent Memory Service (11.0)

```bash
cf create-service agent-memory memory my-agent-memory    # or plan: session
cf bind-service my-agent my-agent-memory
cf restage my-agent
```

| Plan | The agent gets |
|---|---|
| `session` | durable conversation history (sidebar), survives restarts |
| `memory` | + long-term memory, full-text search, shared namespaces |

- Native tools: `save_memory`, `search_memories`, `list_memories`, `list_namespaces`,
  `update_memory`, `delete_memory`. Nothing moves into long-term memory automatically —
  the agent decides what to save, so say when to in `AGENTS.md`.
- Memory is scoped per user + issuer + agent; shared namespaces are granted to JWT group
  claims. **Every request needs a user**: with SSO (recommended) it is the signed-in user.
  Without SSO, configure a service identity (`TANZU_AGENT_MEMORY_SERVICE_CLIENT_ID` /
  `_SECRET` / `_TOKEN_URL`) or chat requests fail with HTTP 503.
  `TANZU_AGENT_MEMORY_IDENTITY_MODE` = `auto` | `user` | `service`.
- The operator must add the SSO plan's issuer to the memory service's trusted issuers.
- A startup WARNING `ServiceTokenProvider: borrowing p-identity SSO credentials for the
  client_credentials grant` means no dedicated memory client is set; set
  `TANZU_AGENT_MEMORY_SERVICE_*` if memory calls fail.
- UI: `TANZU_AGENT_ENABLE_MEMORY_PANEL=true`; `MEMORY_PROXY_ENABLED` + `ENABLE_ADMIN_UI`
  for the *Memory & Namespaces* settings page.
- Data is never aged out. Reset a demo by deleting memories/namespaces, or the instance.

## 6. Credential Store (11.0) — the agent never handles the secret

```bash
cf create-service credential-store shared my-cred-store   # logical store, space-scoped
cf bind-service my-agent my-cred-store
cf restage my-agent
```

- With a store bound **and** SSO bound, the agent forwards the signed-in user's SSO JWT
  on gateway routes; the gateway asks Credential Store for that user's (or the store's
  shared) credential and adds it to the upstream request. The agent never sees it.
- Credentials are added **only in Tanzu Hub** (no cf CLI): *Connect* in the agent opens a
  dialog pointing at Hub → *Add Credential* → back in the agent, click **Reconnect** (Hub
  does not redirect back). Mid-conversation, an **Authorize** notification opens the same
  dialog. The operator must set *Hub base URL* on the tile's Credential Store tab.
- User-scoped credentials need a space role (Developer/Auditor/Supporter); store-scoped
  (shared) credentials need Space Manager. With Tanzu SSO a **store-scoped credential
  wins over the user's own** for the same server (identity-zone mismatch on `sub`).
- No user token, no credential — not even a shared one.
- Pre-11.0 gateway instances need `cf upgrade-service` first (§4).

## 7. Full deployment example

```bash
# 1. Register on-platform MCP servers with the gateway — concurrently, ~70s each
cf bind-service mcp-a my-gateway --wait -c '{"auth":{"service-instance":{"type":"OIDC","name":"my-agent-sso"}}}' &
cf bind-service mcp-b my-gateway --wait -c '{"auth":{"service-instance":{"type":"OIDC","name":"my-agent-sso"}}}' &
wait

# 2. Gateway routes as user-provided services
cf cups mcp-a-gateway -p '{"url":"https://my-gateway.apps.example.com/mcp-a/mcp"}' -t mcp-server
cf cups mcp-b-gateway -p '{"url":"https://my-gateway.apps.example.com/mcp-b/mcp"}' -t mcp-server

# 3. Model endpoint and the agent (arrives degraded: /health says so)
cf create-service ai-models <SINGLE-MODEL-PLAN> my-agent-model --wait
cf push                                   # from the agent directory

# 4. Bind everything, then restage ONCE (each restart drops users' MCP tokens)
cf bind-service my-agent my-agent-model &
cf bind-service my-agent mcp-a-gateway &
cf bind-service my-agent mcp-b-gateway &
cf bind-service my-agent my-agent-sso --wait -c '{"grant_types":["authorization_code"],"redirect_uris":["https://my-agent.apps.example.com/api/auth/callback"],"scopes":["openid","profile","email"]}' &
wait
cf restage my-agent

# 5. Verify
curl -s https://my-agent.apps.example.com/health            # {"status":"healthy"}
curl -s https://my-agent.apps.example.com/api/auth/status   # "enabled": true
```

Then sign in and Connect each server in the browser — that is the real check.

## 8. Built-in tools, UI and operations

**Built-in tools are off by default.** Turn on only what the agent needs:
`TANZU_AGENT_FILESYSTEM_ACCESS` (`read-only` | `read-write`),
`TANZU_AGENT_SHELL_ACCESS_ENABLED` (restage; bundles Python, uv, `gh`, `rg`),
`TANZU_AGENT_WEB_SEARCH_ENABLED`, `TANZU_AGENT_FILE_UPLOAD_ENABLED`.
`TANZU_AGENT_TOOL_PERMISSION_MODE` = `allow` (default) | `ask` (approval cards for
`write_file`, `edit_file`, `bash`) | `deny`.

**UI:** `TANZU_AGENT_DISPLAY_NAME` (header, tab, agent card — defaults to the app name),
`TANZU_AGENT_DESCRIPTION`, `TANZU_AGENT_WELCOME_SUGGESTION_1`..`_4` (clickable starter
prompts), `branding/` assets, `ENABLE_DEBUG_UI` (default true), `ENABLE_ADMIN_UI`
(settings dashboard), `ENABLE_MCP_SETTINGS`, `ENABLE_MODEL_PICKER`, `ENABLE_SIDEBAR`.

**Logs and traces:** `TANZU_AGENT_LOG_JSON=true` (JSON lines with model, tool name,
token counts, trace/span ids); `TANZU_AGENT_TRACING_ENABLED` + `TRACING_ENDPOINT`
(OTLP/HTTP, OpenInference). `TRACING_INCLUDE_CONTENT` and `LOG_LLM_TRAFFIC` export
prompts — only where the backend may store them.

**Go-live checklist:** SSO bound and `/api/auth/status` checked · `ENABLE_DEBUG_UI=false`
· no secrets in `AGENTS.md` or the manifest (`cf set-env` or bindings) · decide who may
call `/a2a` · shell off, or `TOOL_PERMISSION_MODE=ask` · filesystem only when needed ·
settings dashboard off · trace content off.

## Troubleshooting checklist

- **Agent stuck in degraded mode** (`/health` → `degraded`): no model bound, or bound
  but not restaged — see §2.
- **Agent starts but never answers**: it selected an embedding model. Check the log for
  `Using TANZU_AGENT_DEFAULT_MODEL=` vs `not in the advertised model list`; fix the name
  or use a single-model plan.
- **Model binding ignored**: a bound `genai`/`ai-models` service takes priority over
  all `TANZU_AGENT_*` model env vars; unbind/untag it if you want env vars to apply.
- **App crashes on the first chat with "Liveness check unsuccessful"**: raise
  `health-check-invocation-timeout` (10) in the manifest and restart.
- **Gateway server connected but has no tools**: the gateway bind is missing its `auth`
  block, or a `tool_filtering` rule matched nothing for this caller.
- **`oauth_pending` / "No MCP toolsets registered" after deploy**: correct — tools
  appear per user after sign-in and Connect.
- **Every restart loses the MCP tools**: per-user tokens are in memory; reconnect, or
  bind a Credential Store (§6). Avoid restarts once users are connected.
- **SSO login loops or fails on callback**: the bind's `redirect_uris` doesn't match
  `<BASE_URL>/api/auth/callback`; set `TANZU_AGENT_BASE_URL` if users use another host.
- **`invalid_scope` at login**: set `TANZU_AGENT_AUTH_OAUTH_SCOPES` to the scopes the
  SSO client was registered with.
- **Gateway dashboard URL returns 404**: `ENABLE_DASHBOARD` is false (the 11.0 default);
  `cf update-service my-gateway -c '{"env":{"ENABLE_DASHBOARD":"true"}}'`.
- **Agent not picking up a new binding**: run `cf restage` — bindings are only
  discovered at startup.
