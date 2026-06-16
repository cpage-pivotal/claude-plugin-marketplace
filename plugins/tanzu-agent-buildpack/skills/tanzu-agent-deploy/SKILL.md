---
name: tanzu-agent-deploy
description: Deploy AI agents to Tanzu Platform for Cloud Foundry using the Agent Buildpack and MCP Gateway. Use this skill whenever the user wants to push/deploy an agent app with `cf push`, create or edit AGENTS.md (the agent's system prompt) or manifest.yaml for an agent buildpack app, bind/configure/troubleshoot a chat model or LLM connection for an agent (Tanzu GenAI service binding, user-provided service, or TANZU_AGENT_OPENAI_*/TANZU_AGENT_GENAI_*/TANZU_AGENT_GCP_* env vars), or create/configure/register servers with/connect an agent to an MCP Gateway (on-platform or off-platform MCP servers, auth bindings like GITHUB_ENTERPRISE/OAUTH/OIDC). Trigger even if the user doesn't say "Tanzu" explicitly but mentions cf push for an agent, Cloud Foundry agent deployment, agent buildpack, or MCP gateway.
---

# Tanzu Platform AI Agent Deployment

Deploy AI agents on Tanzu Platform for Cloud Foundry via the
[Agent Buildpack](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/ai-services/10-4/ai/tutorials-deploy-an-ai-agent.html)
and [MCP Gateway](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/ai-services/10-4/ai/tutorials-mcp-gateway.html).

This skill is self-sufficient for the common workflows below. To scaffold an MCP
server to deploy alongside the agent, use the `spring-ai-mcp-server` skill; for
agent-to-agent (A2A) delegation between agent apps, use the `tanzu-agent-a2a`
skill.

## 1. Agent Buildpack basics

An agent buildpack app needs only two files:

```
my-agent/
├── AGENTS.md       # system prompt (required)
└── manifest.yaml   # CF manifest (optional but recommended)
```

**manifest.yaml**
```yaml
applications:
  - name: my-agent
    buildpacks:
      - agent_buildpack
```

Deploy with `cf push`. The app starts in **degraded mode** until an AI model is
bound — if a freshly pushed agent isn't responding, check whether a model has
been bound yet (see §2).

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

## 2. Binding a chat model

Pick one of three approaches. They are tried in priority order at startup, and
**a `genai`-tagged VCAP_SERVICES binding always wins** over env vars.

### Option 1: Bind a Tanzu GenAI service instance (recommended)

```bash
cf bind-service my-agent my-model-service
cf restage my-agent
```

The buildpack discovers any service binding tagged `genai` in `VCAP_SERVICES`
and reads credentials from its `endpoint` object:
- `endpoint.api_base` — used to construct the proxy URL (`api_base + /openai/v1`)
- `endpoint.api_key` — authentication token
- `endpoint.openai_api_base` — OpenAI-compatible base URL
- `endpoint.config_url` — queried at startup to discover available model names

### Option 2: User-provided service (mirrors a GenAI binding)

Create a user-provided service with the `genai` tag and the same credential
shape, and the buildpack treats it like a managed GenAI binding:

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
endpoints. Use Option 3 for those.

If `config_url` is absent, the buildpack can't auto-discover the model name. Fix:
```bash
cf set-env my-agent TANZU_AGENT_GENAI_MODEL_NAME <model-name>
```

### Option 3: Environment variables for OpenAI-compatible endpoints

For any OpenAI-compatible API (including OpenAI itself), remove the `genai`
tag from any bound service and set env vars instead:

```bash
cf set-env my-agent TANZU_AGENT_OPENAI_API_BASE  https://api.openai.com/v1
cf set-env my-agent TANZU_AGENT_OPENAI_API_KEY   <your-api-key>
cf set-env my-agent TANZU_AGENT_OPENAI_MODEL_NAME gpt-4o
cf restage my-agent
```

### Provider priority order

1. `genai`-tagged VCAP binding (Options 1 & 2 above)
2. `TANZU_AGENT_GENAI_API_BASE` + `TANZU_AGENT_GENAI_API_KEY` (local GenAI tile)
3. `TANZU_AGENT_GCP_PROJECT_ID` + `TANZU_AGENT_GCP_PRIVATE_KEY` + `TANZU_AGENT_GCP_CLIENT_EMAIL` (Vertex AI)
4. `TANZU_AGENT_OPENAI_API_BASE` + `TANZU_AGENT_OPENAI_API_KEY` (Option 3, any OpenAI-compatible)

If a `genai`-tagged service is bound, env vars in 2-4 are ignored — remove the
tag (or unbind the service) to fall back to env vars.

## 3. MCP Gateway

The MCP Gateway brokers access to MCP servers behind a single observable
endpoint with usage metrics and audit logs.

```bash
# Create a gateway instance
cf create-service mcp-gateway gateway my-gateway --wait
```

The dashboard URL is shown in `cf service my-gateway`.

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

To add/change servers later:
```bash
cf update-service my-gateway --wait -c '{
  "mcp-servers": [{
    "name": "my-server",
    "url":  "https://external-mcp-server.example.com/mcp"
  }]
}'
```

To remove all off-platform servers: `cf update-service my-gateway --wait -c '{"mcp-servers": []}'`

> **Limitation:** The `mcp-servers` schema does not support custom headers or
> auth. If the off-platform server requires a bearer token, deploy a proxy app
> or use the on-platform approach below instead.

### Registering an on-platform CF app as an MCP server

The app needs an internal route (`apps.internal`) — the gateway only binds to
apps via internal networking:

```bash
# Add internal route if not already present
cf map-route my-mcp-app apps.internal --hostname my-mcp-app

# Bind the app to the gateway
cf bind-service my-mcp-app my-gateway --wait
```

For servers requiring auth, pass binding parameters:
```bash
cf bind-service my-mcp-app my-gateway --wait -c '{
  "auth": {
    "service-instance": {
      "type": "GITHUB_ENTERPRISE",
      "name": "github-enterprise-auth-credentials"
    }
  },
  "metadata": {
    "description": "GitHub MCP server"
  }
}'
```

Supported auth types: `GITHUB_ENTERPRISE`, `OAUTH`, `OIDC`.

### Connecting an agent to an MCP server via the gateway

The gateway exposes each registered server at a path based on its name:
`https://<gateway-app>.apps.<domain>/<server-name>/mcp`

Create a user-provided service tagged `mcp-server` pointing at that URL, then
bind it to the agent:

```bash
cf create-user-provided-service my-mcp \
  -p '{"url": "https://my-gateway.apps.example.com/my-server/mcp"}' \
  -t mcp-server

cf bind-service my-agent my-mcp
cf restage my-agent
```

The agent buildpack discovers all `mcp-server`-tagged bindings at startup and
connects to them automatically.

## 4. Full deployment example

```bash
# 1. Deploy the agent
cf push my-agent

# 2. Bind an AI model
cf bind-service my-agent my-model-service

# 3. Create MCP Gateway with an off-platform server
cf create-service mcp-gateway gateway my-gateway --wait -c '{
  "mcp-servers": [{
    "name": "time-server",
    "url":  "https://time-mcp.example.com/mcp"
  }]
}'

# 4. Or bind an on-platform CF app
cf map-route my-mcp-app apps.internal --hostname my-mcp-app
cf bind-service my-mcp-app my-gateway --wait

# 5. Wire the gateway into the agent
cf create-user-provided-service my-mcp \
  -p '{"url": "https://my-gateway.apps.example.com/time-server/mcp"}' \
  -t mcp-server
cf bind-service my-agent my-mcp

# 6. Restage once to pick everything up
cf restage my-agent
```

## Troubleshooting checklist

- **Agent stuck in degraded mode**: no model bound yet — see §2.
- **Model binding ignored**: a `genai`-tagged VCAP binding takes priority over
  all `TANZU_AGENT_*` env vars; unbind/untag it if you want env vars to apply.
- **Model name not discovered**: `endpoint.config_url` missing — set
  `TANZU_AGENT_GENAI_MODEL_NAME` explicitly.
- **MCP server needs auth headers but is off-platform**: the `mcp-servers`
  schema can't carry auth — deploy a proxy app, or move the server on-platform
  and use `cf bind-service ... -c '{"auth": {...}}'`.
- **Agent not picking up a new MCP binding**: run `cf restage` — bindings are
  only discovered at startup.
