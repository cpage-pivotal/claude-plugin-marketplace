---
name: tanzu-agent-a2a
description: Implement native Agent-to-Agent (A2A) communication between Agent Buildpack apps on Tanzu Platform for Cloud Foundry. Use this skill whenever the user wants to build an A2A server or A2A client, make one agent call/delegate to another agent (peer), set up `a2a-peers.yaml`, use the native `list_a2a_peers`/`call_a2a_peer` tools, or write AGENTS.md instructions for invoking peer agents or handling inbound A2A requests. Trigger on "A2A", "agent-to-agent", "peer agent", "delegate to another agent", or "agents talking to each other" even if Tanzu/CF isn't named explicitly.
---

# Tanzu Agent Buildpack A2A (Agent-to-Agent)

The Agent Buildpack can let two or more agent apps talk to each other directly:
one agent (the **client / requester**) delegates a task to a **peer** agent (the
**server / worker**), which does the work and replies. Communication is native
to the buildpack — direct HTTP between agents, **no message broker** (no
RabbitMQ, no queue) required.

This skill covers only A2A. For pushing the app, binding a chat model, or wiring
MCP Gateway, use the `tanzu-agent-deploy` skill — A2A agents still need a chat
model bound to leave degraded mode.

## 0. Prerequisite: Agent Buildpack 0.0.32 or later (REQUIRED)

Native A2A only exists in **agent_buildpack v0.0.32+**. Before doing any A2A
work, verify the version installed on the foundation:

```bash
ver=$(cf buildpacks | awk '$2=="agent_buildpack"{print $7}' \
        | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' | head -1 | tr -d v)
echo "agent_buildpack version: ${ver:-NOT FOUND}"
required=0.0.32
if [ -n "$ver" ] && [ "$(printf '%s\n%s\n' "$ver" "$required" | sort -V | head -1)" = "$required" ]; then
  echo "OK — A2A supported"
else
  echo "TOO OLD — A2A requires >= $required"
fi
```

**If the installed version is earlier than 0.0.32 (or the buildpack is absent),
STOP. Do not scaffold or deploy an A2A app.** Tell the user something like:

> A2A support requires Agent Buildpack v0.0.32 or later, but this foundation
> has `<version>`. Ask your platform team to upgrade the `agent_buildpack`
> before implementing A2A.

## 1. How native A2A works

Every agent that participates in A2A gets two buildpack-provided tools:

- `list_a2a_peers` — lists peers declared in `a2a-peers.yaml` (alias → URL).
- `call_a2a_peer(alias, message)` — sends a task to a peer and receives its reply.

**Inbound tasks** arrive over `POST /api/chat` (native to the buildpack) and
surface in the receiving agent's conversation prefixed with **`[A2A inbound]`**,
carrying a JSON payload. The agent does **not** poll — messages are pushed to
its chat interface. It replies by calling `call_a2a_peer` back to the sender.

A single agent can be a client, a server, or both. Its role is determined by the
instructions you put in its `AGENTS.md`.

## 2. `a2a-peers.yaml` (required, at the app root)

Each A2A app needs an `a2a-peers.yaml` at its root mapping a short **alias** to
each peer's deployed CF route. The alias is what you pass to `call_a2a_peer`.

```yaml
# Peer agents reachable from this app (native A2A via Agent Buildpack 0.0.32).
# Replace <CF_APPS_DOMAIN> with your foundation's apps domain before cf push.
peers:
  - alias: beta
    url: https://agent-a2a-beta.<CF_APPS_DOMAIN>
```

Peering is per-app and directional — for a two-way conversation, **both** apps
need an `a2a-peers.yaml` that lists the other. Get the apps domain from
`cf domains` (or copy it from an existing app's route).

## 3. AGENTS.md for an A2A **client** (requester / orchestrator)

The system prompt must tell the agent how to discover peers and delegate work.

````markdown
You are **agent-a2a-alpha** on Cloud Foundry (`AGENT_ID=agent-a2a-alpha`): requester / orchestrator.

## Native A2A Tools (buildpack)

- `list_a2a_peers` — list peers from `a2a-peers.yaml` (alias → URL)
- `call_a2a_peer(alias, message)` — send a task to a peer agent and receive its reply

## Peer Agent Capabilities

Call `list_a2a_peers` to discover available peers. To learn what a peer can do, ask it directly:
> "List all skills and tools you have available."

## Delegating work to peer agents

Use `call_a2a_peer(alias="<peer>", message="...")` to delegate a task to a peer that has the required skill.

### When to delegate
- The task requires live data only the peer can access.
- The task matches a skill or tool the peer has and you do not.
- Parallel execution would speed up independent sub-tasks.

### When NOT to delegate
- You can answer accurately from context — do it directly.
- The peer's only advantage is model reasoning — use your own.
- Round-trip latency outweighs the benefit.

### How to write a good delegation message
Name the **specific skill** you expect the peer to use and ask for **raw output**:

> "Follow your `<skill-name>` skill to <action> and return the raw output without summarising."

## Interpreting Peer Replies

Peers that follow the A2A delegation pattern return structured replies:

```
TOOL USED: <tool-name or skill-name>
RESULT:
<raw output>
SUMMARY:
<one sentence>
```

If a peer returns `NO TOOL AVAILABLE: ...`, do **not** retry with the same peer.
Either handle the task yourself or surface the gap to the user.
````

## 4. AGENTS.md for an A2A **server** (worker / handler)

The system prompt must tell the agent how to handle inbound A2A tasks and reply.

````markdown
You are **agent-a2a-beta** on Cloud Foundry (`AGENT_ID=agent-a2a-beta`): A2A worker.

## Native A2A Tools (buildpack)

- `list_a2a_peers` — list peers from `a2a-peers.yaml` (alias → URL)
- `call_a2a_peer(alias, message)` — reply to the calling agent

## Receiving A2A inbound tasks

Inbound `task_request` messages are delivered via **`POST /api/chat`** (native buildpack).
You see **`[A2A inbound]`** in the conversation with the payload as JSON.

**Do not poll** for messages — they are pushed directly to your chat interface.

When you see `[A2A inbound]`:
1. Parse `from`, `correlation_id`, and `payload` from the message.
2. Process the task using your own skills and tools.
3. Reply via `call_a2a_peer(alias=<from-alias>, message="<structured result>")`.

## Reply format

Reply in the structure the requesting agent expects:

```
TOOL USED: <tool-name or skill-name>
RESULT:
<raw output>
SUMMARY:
<one sentence>
```

If you cannot handle the task, reply `NO TOOL AVAILABLE: <reason>` so the caller stops retrying.
````

## 5. App layout and manifest

An A2A agent app adds just one file (`a2a-peers.yaml`) to a normal agent app:

```
agent-a2a-alpha/
├── AGENTS.md         # system prompt (client or server role)
├── a2a-peers.yaml    # peer alias → URL map (required for A2A)
└── manifest.yaml
```

```yaml
applications:
  - name: agent-a2a-alpha
    buildpacks:
      - agent_buildpack
    env:
      AGENT_ID: agent-a2a-alpha          # referenced by AGENTS.md; keep it == app name
      # TANZU_AGENT_ENABLE_DEBUG_UI: "true"   # optional: handy chat UI for demos
```

Use `agent_buildpack` alone — A2A is native, so no extra buildpack is needed.

## 6. Deploying a two-agent A2A demo

```bash
# 1. In each app's a2a-peers.yaml, replace <CF_APPS_DOMAIN> with your apps domain
cf domains                      # find the apps domain

# 2. Push both agents (each with its own AGENTS.md, a2a-peers.yaml, manifest.yaml)
cf push agent-a2a-alpha
cf push agent-a2a-beta

# 3. Bind a chat model to EACH agent (see the tanzu-agent-deploy skill, §2)
cf bind-service agent-a2a-alpha my-model-service && cf restage agent-a2a-alpha
cf bind-service agent-a2a-beta  my-model-service && cf restage agent-a2a-beta
```

Then chat with the client agent and ask it to do something only the peer can do;
it should call `list_a2a_peers` and then `call_a2a_peer("beta", ...)`.

## Troubleshooting checklist

- **`call_a2a_peer` / `list_a2a_peers` tools missing**: the buildpack is older
  than v0.0.32, or `a2a-peers.yaml` is absent/malformed — re-check §0 and §2.
- **Peer unreachable / connection errors**: the `url` in `a2a-peers.yaml` still
  has the `<CF_APPS_DOMAIN>` placeholder, points at the wrong route, or the peer
  isn't pushed/started yet. Confirm with `cf apps` and `cf app <peer>`.
- **Replies never come back**: the conversation is directional — make sure the
  *replying* agent also lists the caller as a peer in its own `a2a-peers.yaml`.
- **Peer responds but does nothing useful**: its AGENTS.md lacks the inbound
  handling instructions in §4, or it has no skill for the task — it should reply
  `NO TOOL AVAILABLE: ...`.
- **Either agent stuck in degraded mode**: no chat model bound — use the
  `tanzu-agent-deploy` skill, §2.
