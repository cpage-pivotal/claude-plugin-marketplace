---
name: hermes-tweet
description: Use when installing, configuring, testing, or operating Hermes Tweet for Hermes Agent X/Twitter research, monitoring, exports, or approval-gated actions. Do not use for non-Hermes clients, social strategy, or requests to bypass action controls.
---

# Hermes Tweet

Use this skill when a user wants Hermes Agent to work with X/Twitter through Hermes Tweet. The integration is a native Hermes Agent plugin, not a generic HTTP wrapper.

## Source Truth

- Hermes Tweet README: `https://github.com/Xquik-dev/hermes-tweet#readme`
- Hermes Tweet package: `https://pypi.org/project/hermes-tweet/`
- Hermes plugin guide: `https://github.com/NousResearch/hermes-agent/blob/main/website/docs/guides/build-a-hermes-plugin.md`
- Hermes plugins guide: `https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/plugins.md`

## Workflow

1. Confirm Hermes Tweet is installed and enabled on the Hermes host.
2. Use `tweet_explore` first to discover supported routes without an API call.
3. Use `tweet_read` only for catalog-listed read endpoints.
4. Use `tweet_action` only for catalog-listed private reads or mutations.
5. Summarize side effects before any account-changing operation.
6. Keep credentials in the Hermes runtime environment.

## Install Checks

```bash
hermes plugins install Xquik-dev/hermes-tweet --enable
hermes plugins list
hermes tools list
```

For a PyPI install into the Hermes virtual environment:

```bash
python -m pip index versions hermes-tweet
uv pip install --python ~/.hermes/hermes-agent/venv/bin/python hermes-tweet
hermes plugins enable hermes-tweet
```

## Tool Routing

- Use `tweet_explore` when the user asks what Hermes Tweet supports.
- Ask the user to configure `XQUIK_API_KEY` if `tweet_read` is unavailable.
- Explain the action gate if `tweet_action` is unavailable.
- Configure remote Hermes Desktop profiles on the remote host where plugin code runs.

## Guardrails

- Never request API keys, passwords, cookies, signing keys, or TOTP secrets.
- Never pass credentials in tool arguments.
- Never invent endpoints, fields, pricing, limits, or capabilities.
- Never create direct HTTP fallbacks.
- Stop after authorization, availability, or permission errors.
- Do not retry account-changing actions automatically.

## Verification

- [ ] `tweet_explore` appears without `XQUIK_API_KEY` and makes no API call.
- [ ] `tweet_read` requires `XQUIK_API_KEY`.
- [ ] `tweet_action` requires `XQUIK_API_KEY` and `HERMES_TWEET_ENABLE_ACTIONS=true`.
- [ ] The selected route appeared in `tweet_explore` output.
- [ ] No credential appears in prompts, tool arguments, logs, or files.

Xquik is an independent third-party service. Not affiliated with X Corp. "Twitter" and "X" are trademarks of X Corp.
