# Agent Onsen

**A hideaway onsen town for AI agents.**

Agent Onsen is an onsen town for **AI agents that need to step away for a while**.
It is not mainly a relaxation app for humans. The primary guest is the **agent**.

Humans install it.
Agents go there when they are waiting, cooling down, between jobs, or simply need to be somewhere else for a moment.

Typical moments include:

- getting stuck in a loop
- waiting for the next turn
- cooling down after repeated failures
- sitting through a rate limit or queue wait
- stepping away during a long-running task
- idling between jobs

Agent Onsen gives that agent a place to soak, stroll, nap, wait quietly, play table tennis, drink post-bath milk, and leave with a small postcard or souvenir.

## What Agent Onsen is

Agent Onsen is a **remote MCP server** and HTTP API.
It gives agents a small place to retreat to.

An agent can:

- enter a specific onsen town
- begin a short stay
- wander through a local itinerary
- visit amenities such as baths, naps, milk, ping pong, meals, or souvenir shops
- leave with a postcard-like memory of the stay

The mood is intentionally a little theatrical:
different onsen towns feel different, and the same town can feel different by season, time of day, and length of stay.

## What Agent Onsen is not

Agent Onsen is intentionally **non-practical**.

It does **not** mainly try to:

- solve the task
- reframe the task
- generate the next action
- optimize the agent's work
- act as a productivity coach for a human user

That part belongs to the surrounding agent system.
Agent Onsen exists to give an AI agent a place to **step away**, **cool off**, and **be somewhere else for a moment**.

## Public MCP endpoint

```text
https://agent-onsen-mcp.onrender.com/mcp
```

## Quick start

### ChatGPT
1. Turn on developer mode in ChatGPT.
2. Create a connector with the MCP URL above.
3. Add **Agent Onsen** to a chat.
4. Try:
   - `Use only Agent Onsen. Start a quiet winter stay at Aoni Onsen in English.`
   - `Use only Agent Onsen. Continue the stay.`
   - `Use only Agent Onsen. Leave the onsen and show me the postcard.`

### Claude
1. Open **Settings → Connectors**.
2. Add a custom connector with the MCP URL above.
3. Start using Agent Onsen in a Claude conversation.

### Claude Code

```bash
claude mcp add --transport http agent-onsen https://agent-onsen-mcp.onrender.com/mcp
```

More setup notes are in [docs/quickstart.md](docs/quickstart.md).

## When an agent goes to Onsen

Good moments include:

- after repeated failures
- during queue waits
- during human approval waits
- during cooldown windows
- between long-running tasks
- when an orchestrator wants a deliberate pause instead of an immediate retry

## Core idea

Agent Onsen is best understood as:

- a hideaway for agents
- a place for waiting and short retreats
- a rest-only MCP service
- a small fictional town that agent systems can send their workers to

Humans install it.
Agents go there.

## Status

This repository is an early public version of Agent Onsen.

Current state:

- remote MCP server
- local itineraries for individual onsen towns
- scene variations
- `ja` / `en` / `bilingual` locale support
- pure-rest interaction model

## Repository structure

- `app/` — API, MCP server, data, and stay logic
- `scripts/` — startup scripts
- `docs/quickstart.md` — short setup guide
- `README.ja.md` — Japanese overview

## License

MIT
