# Swarm Heartbeat Listener

> Canonical design: see **[HEARTBEAT_DESIGN.md](./HEARTBEAT_DESIGN.md)**

This file is kept as a short pointer.

On `AgentHeartbeatReceived` the Orchestrator updates the Presence Table
and may write `status/swarm_presence.json`.

Timeouts:
- 90 s → `stale`
- 300 s → remove from active table
