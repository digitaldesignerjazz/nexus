# Swarm Heartbeat Listener (Design)

When any node receives an `AgentHeartbeat` on topic `nexus/mesh/v0`,
nxmesh emits:

```rust
MeshEvent::AgentHeartbeatReceived {
    agent: String,      // "lyra" | "xen" | "elara" | "york-autotype" | ...
    node_id: String,
    status: String,
    from: String,       // PeerId of the sender
}
```

## Intended Handling in the Orchestrator

```
on AgentHeartbeatReceived:
  - update local presence table
  - if agent ∈ {lyra, xen, elara}:
      mark swarm member as seen
  - if agent == "york-autotype":
      mark prototype as online
  - optional: notify the corresponding agent persona
  - optional: write to status/swarm_presence.json
```

## Presence Table (example)

```json
{
  "updated": "2026-08-23T21:00:00Z",
  "members": {
    "lyra":            { "node_id": "...", "status": "alive", "last_seen": "..." },
    "xen":             { "node_id": "...", "status": "alive", "last_seen": "..." },
    "elara":           { "node_id": "...", "status": "alive", "last_seen": "..." },
    "york-autotype":   { "node_id": "...", "status": "alive", "last_seen": "..." }
  }
}
```

This table becomes the single source of truth for “who is online in the swarm”.
