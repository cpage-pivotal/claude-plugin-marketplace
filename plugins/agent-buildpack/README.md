# Tanzu Agent Buildpack

Build and deploy **agentic application demos** on Tanzu Platform for Cloud
Foundry. This plugin gives Claude Code the skills to stand up a custom agent —
with its own tools and behavior — in a handful of `cf` commands, using the
**Agent Buildpack** and **MCP Gateway**.

It's designed for Tanzu Solution Architects building live demos: scaffold MCP
tool servers, write the agent's `AGENTS.md`, deploy everything to Cloud Foundry,
and optionally wire up agent-to-agent (A2A) delegation.

## Skills in this plugin

Claude Code activates these automatically based on what you ask for — you don't
invoke them by name:

- **`tanzu-agent-deploy`** — pushes agents and MCP servers to Cloud Foundry,
  writes/edits `AGENTS.md` and `manifest.yaml`, binds a chat model (GenAI
  service, user-provided service, or `TANZU_AGENT_*` env vars), and wires
  everything together through an MCP Gateway.
- **`spring-ai-mcp-server`** — scaffolds a Java/Spring AI 2.0 MCP tool server
  (Streamable-HTTP, `@McpTool`-annotated tools, sample data) in its own
  subdirectory.
- **`tanzu-agent-a2a`** — sets up native agent-to-agent (A2A) communication so
  one agent app can delegate to another as a peer (`a2a-peers.yaml`, the
  `list_a2a_peers` / `call_a2a_peer` tools, and AGENTS.md patterns for invoking
  peers or handling inbound A2A requests). Requires Agent Buildpack v0.0.32+.

## Prerequisites

- **Claude Code CLI**, launched from the root of your demo project.
- **`cf` CLI**, logged into a Tanzu Platform for Cloud Foundry foundation with:
  - the Agent Buildpack available
  - the `mcp-gateway` service available in the target marketplace
  - a GenAI service instance (or credentials for an OpenAI-compatible model)
- **Java 21 + Maven**, to build and smoke-test MCP servers locally before
  deploying.

## The demo workflow

Each step is just a prompt to Claude Code — it does the work using the skills
above.

### 1. Brainstorm a demo

Describe the application domain and ask for ideas. A good demo proposal includes
**two or more MCP servers** (each exposing a handful of tools backed by
realistic sample data) and an **`AGENTS.md`** that gives the agent a persona and
behavioral guidelines that lead to interesting output.

> *"Our customer is a regional airline focused on crew scheduling and on-time
> performance. Brainstorm 2-3 demo agent ideas built on sample data — each
> should use at least two MCP servers and an AGENTS.md that makes the agent's
> responses compelling in a live demo."*

### 2. Build the chosen demo

Pick a proposal and ask Claude Code to implement it. It creates one Maven
subdirectory per MCP server (via `spring-ai-mcp-server`) plus `AGENTS.md` and
`manifest.yaml` for the agent (via `tanzu-agent-deploy`). Ask it to build and
run each MCP server locally and exercise its tools over the Streamable-HTTP
endpoint before deploying.

> *"Let's build option 2. Implement the MCP servers with sample data and write
> the AGENTS.md."*

### 3. Deploy the MCP servers and wire up the gateway

> *"Deploy the MCP servers to Cloud Foundry and wire them up to an MCP
> Gateway."*

### 4. Deploy the agent and connect everything

> *"Deploy the agent with the agent buildpack, bind it to our GenAI service, and
> connect it to the MCP servers through the gateway."*

After this step the agent should be out of degraded mode and able to call tools
on every MCP server — that's the demo.

### 5. (Optional) Add a second agent and delegate via A2A

> *"Set up A2A so this agent can delegate the scheduling lookups to a second
> agent."*

## Project layout (after a demo is built)

```
.
├── AGENTS.md                  # agent system prompt
├── manifest.yaml              # CF manifest for the agent (agent_buildpack)
├── a2a-peers.yaml             # (only if using A2A) peer alias → URL map
├── <feature>-mcp-server/      # one subdirectory per MCP server
│   ├── pom.xml
│   ├── manifest.yaml
│   └── src/main/java/...
└── <feature2>-mcp-server/
```

## Tips for good demos

- Bake realistic sample data directly into each MCP server so the demo runs
  without external dependencies or network access.
- Use `AGENTS.md` to steer the agent toward demo-friendly behavior: combining
  data from multiple tools, formatting results clearly, and proactively
  surfacing the kind of insight the user cares about.
- Keep each MCP server focused on a handful of well-named tools — it keeps the
  tool-call trace easy to narrate during a live demo.
- After any new MCP Gateway binding or model binding change, `cf restage` the
  agent — bindings are only discovered at startup.

## Installation

```bash
/plugin marketplace add cpage-pivotal/claude-plugin-marketplace
/plugin install agent-buildpack@claude-plugin-marketplace
```

## Resources

- [Agent Buildpack — Deploy an AI Agent](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/ai-services/10-4/ai/tutorials-deploy-an-ai-agent.html)
- [MCP Gateway](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/ai-services/10-4/ai/tutorials-mcp-gateway.html)
- [Spring AI MCP overview](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-overview.html)
