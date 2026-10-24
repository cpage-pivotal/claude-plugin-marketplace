---
name: tanzu-agent-a2a
description: Implement native Agent-to-Agent (A2A) communication between Agent Buildpack apps on Tanzu Platform for Cloud Foundry (Tanzu AI Services 11.0 GA). Use this skill whenever the user wants to build an A2A server or A2A client, make one agent call/delegate to another agent (peer), declare peers with `a2a-peers.yaml`, an `a2a`-tagged service binding, or a published agent offering, use the native `list_a2a_peers`/`call_a2a_peer` tools, expose or protect an agent's `/a2a` endpoint and agent card, or write AGENTS.md instructions for invoking peer agents or handling requests from them. Trigger on "A2A", "agent-to-agent", "peer agent", "agent card", "delegate to another agent", or "agents talking to each other" even if Tanzu/CF isn't named explicitly.
---

# Tanzu Agent Buildpack A2A (Agent-to-Agent)

The Agent Buildpack lets two or more agent apps talk to each other directly: one
agent (the **client / requester**) delegates a task to a **peer** agent (the
**server / worker**), which does the work and returns the answer. It speaks the
open [A2A protocol](https://a2a-protocol.org) over plain HTTP between apps — **no
message broker** (no RabbitMQ, no queue). Reference:
[Use Agent-to-Agent Communication with the AI Agent](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/ai-services/11-0/ai/app-dev-guide-agent-buildpack-enable-a2a-for-the-ai-agent.html).

This skill covers only A2A. For pushing the app, binding a chat model, SSO, or
wiring MCP Gateway, use the `tanzu-agent-deploy` skill — A2A agents still need a
chat model bound to leave degraded mode.

## 0. Prerequisite: the GA Agent Buildpack

This skill describes the **GA** buildpack shipped with Tanzu AI Services 11.0
(`agent_buildpack` 0.2.39 on a freshly upgraded foundation; the request/response
behaviour below was read from the 0.2.51 runtime). Technical-preview builds
(`agent_buildpack_beta`, 0.1.x and earlier) were not checked against it — don't
apply this skill to them.

```bash
cf buildpacks | grep -E '^\S+\s+agent_buildpack\b'
ver=$(cf buildpacks | awk '$2=="agent_buildpack"' \
        | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' | head -1 | tr -d v)
echo "agent_buildpack version: ${ver:-NOT FOUND}"
required=0.2.39
if [ -n "$ver" ] && [ "$(printf '%s\n%s\n' "$ver" "$required" | sort -V | head -1)" = "$required" ]; then
  echo "OK — GA A2A"
else
  echo "TOO OLD — needs the GA agent_buildpack (>= $required)"
fi
```

**If the version is older (or only `agent_buildpack_beta` exists), STOP.** Tell the
user something like:

> This skill targets the GA Agent Buildpack from Tanzu AI Services 11.0, but this
> foundation has `<version>`. Ask your platform team to upgrade AI Services and run
> its *Install Agent Buildpack* errand.

After pushing, confirm the version actually staged — the tile version isn't proof:
`cf curl "/v3/apps/$(cf app <agent> --guid)/droplets/current" | jq '.buildpacks'`.

## 1. How native A2A works

**Every agent is an A2A server.** The runtime exposes, with no extra code:
- `POST /a2a/` — A2A JSON-RPC (`message/send`, `tasks/get`).
- `GET /.well-known/agent-card.json` — the **agent card**: `TANZU_AGENT_DISPLAY_NAME`,
  `TANZU_AGENT_DESCRIPTION`, the agent's **skills** (from `skills/`), and its endpoint
  URL (`TANZU_AGENT_BASE_URL`, else `X-Forwarded-Host`, else the app's first route).

**An agent with peers configured is also an A2A client**, and gets two tools:
- `list_a2a_peers` — each peer's alias, URL and (when reachable) its agent-card
  description.
- `call_a2a_peer(alias, message)` — sends `message/send`, polls `tasks/get` until the
  peer finishes, and **returns the peer's reply text** as the tool result.

So A2A is **request/response**. The caller blocks on `call_a2a_peer` and gets the
answer back in the same tool call; the worker simply answers the message it was sent.
The worker must **not** "reply" by calling `call_a2a_peer` back to the caller — that
starts a brand-new task on the caller, duplicating work or looping. Peering is
**directional**: only the caller needs the worker in its peer list.

Each inbound task is its own agent run on the worker, with the worker's own
`AGENTS.md`, model, skills and statically authenticated tools — and **no end-user
session**. Anything that is per user on the worker (MCP servers the user connected
through OAuth *Connect*, personal memory) is not available to an A2A run. Give a
worker the tools it needs through bindings that authenticate on their own.

Peers that publish an A2A **0.3** card are supported (11.0).

## 2. Declaring peers

Three sources, merged into one alias list. **The file wins** on an alias clash.

### a. A user-provided service binding (recommended)

No domain to hard-code in the app's files — the peer URL lives in the binding:

```bash
cf cups peer-beta -t a2a -p '{"uri":"https://agent-a2a-beta.<apps-domain>"}'
cf bind-service agent-a2a-alpha peer-beta
cf restage agent-a2a-alpha
```

Bindings tagged `a2a`, `agent` or `a2a-agent` with a `uri` (the peer's base URL)
become peers; the **binding name is the alias**. Bindings that also carry the model
tag (`genai`) are never treated as peers.

### b. A published agent offering

Binding a service-published A2A agent offering makes every agent in it a peer:
credentials carry `agentCardUrls: [...]` plus an `oauth` block of client credentials.
One peer per card URL; the token is fetched from the card's `oauth2` security scheme
token URL and auto-refreshed.

### c. `a2a-peers.yaml` (or `.yml` / `.json`) at the app root

```yaml
# Peer agents reachable from this app. Replace <apps-domain> before cf push.
peers:
  - alias: beta
    url: https://agent-a2a-beta.<apps-domain>
    # agent_card_url: https://.../.well-known/agent-card.json   # if mounted under a path
    # headers: { X-API-KEY: "..." }                              # forwarded verbatim
    # insecure: false                                            # skip TLS verification
```

`TANZU_AGENT_A2A_PEERS_FILE` points at a file elsewhere. Get the apps domain from
`cf domains`.

### Rules every peer must satisfy

- The peer **must serve an agent card** — from `agent_card_url` if set, else
  `<url>/.well-known/agent-card.json`.
- `agent_card_url` must share the `url`'s scheme, host and port.
- The caller only calls the card's endpoint if it has the **same scheme and host** as
  the configured URL. A peer reached through another host (a gateway, or an internal
  route) must set `TANZU_AGENT_BASE_URL` so its card advertises that address.

## 3. Authentication on `/a2a`

- **No SSO bound:** `/a2a` is open, and the worker logs a WARNING saying so. Fine for a
  demo; not for production.
- **SSO bound:** `TANZU_AGENT_AUTH_A2A_PROTECTED` defaults to `true`, so `/a2a` needs a
  signed-in session and **other agents get 401**. To let agents call it, set
  `TANZU_AGENT_AUTH_A2A_PROTECTED=false` on the worker and restrict who can reach it —
  e.g. call it only over an `apps.internal` route with a network policy
  (`cf add-network-policy <caller> <worker> --port 8080`), with the worker's
  `TANZU_AGENT_BASE_URL` set to that internal URL.
- **Published agent offering:** OAuth client credentials from the binding, issued by
  the platform — the governed option.
- **Static headers** in the peers file are forwarded verbatim (e.g. an API key a
  gateway in front of the peer checks).

**Identity does not flow through A2A.** The worker sees the calling *agent* (or nobody),
never the end user who asked the caller. If the worker can reach data the user
shouldn't see, the caller becomes a confused deputy. Scope what a worker can do to
what any caller may see, or keep user-scoped work in the agent the user signed in to.

## 4. AGENTS.md for an A2A **client** (requester / orchestrator)

````markdown
You are **Research Orchestrator**: you answer questions by delegating to specialist agents.

## Peer agents

- `list_a2a_peers` — lists available peers with their aliases and descriptions.
- `call_a2a_peer(alias, message)` — sends a task to a peer and returns its answer.

Call `list_a2a_peers` before your first delegation to see who is available and what
each peer says it does.

### When to delegate
- The task needs data or tools only the peer has.
- The task matches a skill the peer advertises and you lack.

### When NOT to delegate
- You can answer accurately from context — do it directly.
- The peer's only advantage would be its model's reasoning — use your own.

### How to write a delegation message
The peer has none of this conversation's context. Make the message self-contained:
state the task, the inputs, and the format you want back. Name the skill you expect
it to use and ask for raw results:

> "Using your `<skill-name>` skill, <task with all inputs>. Return the raw result,
> not a summary."

### Using the answer
`call_a2a_peer` returns the peer's reply directly. If it reports it can't do the task
(`NO TOOL AVAILABLE: ...`), don't retry the same peer with the same request — handle it
yourself or tell the user. Say which peer you consulted when you use its answer.
````

## 5. AGENTS.md for an A2A **server** (worker / specialist)

The worker needs no A2A-specific tools. It needs instructions that make its answers
useful to another agent, and its card needs an accurate description.

````markdown
You are **Manifest Doctor**: you review Cloud Foundry manifests for mistakes.

Requests may come from people in the chat UI or from other agents over A2A. Requests
from agents are self-contained tasks: there is no one to ask follow-up questions, so
work from what the message gives you and state any assumption you had to make.

Answer in this structure:

```
TOOL USED: <tool or skill name, or "none">
RESULT:
<the raw result>
SUMMARY:
<one sentence>
```

If you cannot do the task, answer `NO TOOL AVAILABLE: <reason>` so the caller stops
retrying. Your answer is returned to the caller automatically — never call
`call_a2a_peer` to reply.
````

Put the worker's capabilities in `skills/<name>/SKILL.md` as well: skills appear in
the agent card, which is what `list_a2a_peers` shows the caller.

## 6. App layout and manifest

```
agent-a2a-alpha/              agent-a2a-beta/
├── AGENTS.md   (client)      ├── AGENTS.md   (worker)
├── manifest.yaml             ├── manifest.yaml
└── a2a-peers.yaml (optional, └── skills/<name>/SKILL.md (advertised in its card)
    if not using a binding)
```

```yaml
applications:
  - name: agent-a2a-beta
    buildpacks:
      - agent_buildpack
    health-check-type: http
    health-check-http-endpoint: /health
    env:
      TANZU_AGENT_DISPLAY_NAME: Manifest Doctor       # agent card name
      TANZU_AGENT_DESCRIPTION: Reviews Cloud Foundry manifests and explains what is wrong.
```

Use `agent_buildpack` alone — A2A is native, so no extra buildpack is needed.

## 7. Deploying a two-agent A2A demo

```bash
# 1. Push both agents (each with its own AGENTS.md and manifest.yaml)
cf push agent-a2a-alpha
cf push agent-a2a-beta

# 2. Bind a chat model to EACH agent (see tanzu-agent-deploy, §2)
cf bind-service agent-a2a-alpha my-model-service
cf bind-service agent-a2a-beta  my-model-service

# 3. Make beta a peer of alpha
cf cups beta -t a2a -p '{"uri":"https://agent-a2a-beta.<apps-domain>"}'
cf bind-service agent-a2a-alpha beta

# 4. Restage once each
cf restage agent-a2a-alpha
cf restage agent-a2a-beta

# 5. Check the worker's card
curl -s https://agent-a2a-beta.<apps-domain>/.well-known/agent-card.json | jq '{name, description, url, skills: [.skills[]?.name]}'
```

Then chat with alpha and ask it something only beta can do: it should call
`list_a2a_peers`, then `call_a2a_peer("beta", ...)`, and use the returned answer. Both
calls show in alpha's debug panel.

## Troubleshooting checklist

- **`list_a2a_peers` / `call_a2a_peer` missing**: no peers configured — no `a2a`-tagged
  binding, no peers file, or the file failed to parse (check the startup log for
  `Failed to load A2A peers file`). Restage after adding a binding.
- **"No A2A peers are configured"**: same — bind an A2A service and restage, add
  `a2a-peers.yaml`, or set `TANZU_AGENT_A2A_PEERS_FILE`.
- **Peer listed but calls fail**: the URL still has the `<apps-domain>` placeholder,
  the peer isn't running, or its agent card isn't reachable. `curl` the card.
- **401 from the peer**: SSO is bound on the worker and `/a2a` is protected — see §3.
- **Card endpoint rejected / wrong host**: the card advertises a different scheme or
  host than the URL you configured; set `TANZU_AGENT_BASE_URL` on the worker.
- **Worker answers but has none of its MCP tools**: those tools are per-user OAuth
  connections, and A2A runs have no user — give the worker statically authenticated
  bindings.
- **Duplicate work or loops between agents**: the worker's `AGENTS.md` tells it to reply
  with `call_a2a_peer`. Remove that; the answer is returned automatically.
- **Peer responds but does nothing useful**: its `AGENTS.md` doesn't cover the task, or
  the caller's message wasn't self-contained — the peer has none of the caller's context.
- **Either agent stuck in degraded mode**: no chat model bound — use the
  `tanzu-agent-deploy` skill, §2.
