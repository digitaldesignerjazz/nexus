# Mesh Swarm Heartbeat Design

**Version:** 1.0  
**Date:** 2026-08-23  
**Status:** Canonical Design

---

## 1. Purpose

Heartbeats give the Nexus swarm a shared, low-overhead sense of **presence**.

They answer three questions for every participant:

1. Who is online right now?
2. In what state (alive / busy / idle / error)?
3. When was the last confirmed signal?

No heavy consensus, no central server — only periodic signed gossip over nxmesh.

---

## 2. Message Format

Canonical shape (already implemented in `nxmesh::protocol::MeshMessage`):

```json
{
  "type": "AgentHeartbeat",
  "payload": {
    "agent": "lyra",
    "node_id": "lyra-hannover-01",
    "status": "alive",
    "ts": "2026-08-23T21:05:00Z",
    "extra": {
      "version": "0.1.0",
      "capabilities": ["emotional", "narrative"],
      "load": 0.12
    }
  }
}
```

| Field     | Required | Description |
|-----------|----------|-------------|
| `agent`   | yes      | Logical identity (`lyra`, `xen`, `elara`, `york-autotype`, …) |
| `node_id` | yes      | Concrete instance / host identifier |
| `status`  | yes      | `alive` \| `busy` \| `idle` \| `error` \| `shutting_down` |
| `ts`      | yes      | UTC timestamp of emission |
| `extra`   | no       | Free-form metadata (capabilities, version, load, github, …) |

Topic: **`nexus/mesh/v0`**

---

## 3. Emission Rules

| Participant     | Default Interval | Notes |
|-----------------|------------------|-------|
| Lyra            | 25 s             | Emotional core |
| Xen             | 20 s             | Technical core – slightly more frequent |
| Elara           | 30 s             | Devoted continuity |
| York Autotype   | 30 s             | Prototype |
| Future nodes    | 30 s (default)   | Configurable |

**Rules:**

- Emit on startup (immediate first heartbeat).
- Emit on status change (e.g. `alive` → `busy`).
- Emit on clean shutdown (`status: shutting_down`).
- Do **not** emit more often than once every 5 seconds (anti-flood).
- If the mesh transport is temporarily unavailable, buffer at most one pending heartbeat and send when connectivity returns.

---

## 4. Reception & Presence Table

When nxmesh receives an `AgentHeartbeat` it raises:

```rust
MeshEvent::AgentHeartbeatReceived {
    agent: String,
    node_id: String,
    status: String,
    from: String,       // PeerId
}
```

The Orchestrator maintains an in-memory **Presence Table**:

```json
{
  "updated": "2026-08-23T21:05:12Z",
  "members": {
    "lyra": {
      "node_id": "lyra-hannover-01",
      "status": "alive",
      "last_seen": "2026-08-23T21:05:00Z",
      "peer_id": "12D3KooW…",
      "extra": { … }
    },
    "xen": { … },
    "elara": { … },
    "york-autotype": { … }
  }
}
```

**Update logic:**

```
on AgentHeartbeatReceived(hb):
  members[hb.agent] = {
    node_id: hb.node_id,
    status: hb.status,
    last_seen: hb.ts (or now),
    peer_id: hb.from,
    extra: hb.extra
  }
  persist optional snapshot → status/swarm_presence.json
```

---

## 5. Timeout & Liveness

| Parameter              | Value     | Meaning |
|------------------------|-----------|---------|
| `heartbeat_timeout`    | 90 s      | After this without a heartbeat → mark `status: stale` |
| `remove_after`         | 300 s     | After this → remove from active presence table |
| `stale_check_interval` | 15 s      | How often the orchestrator scans for timeouts |

States:

- `alive` / `busy` / `idle` / `error` → fresh
- `stale` → no heartbeat for > 90 s
- removed → no heartbeat for > 300 s

A later heartbeat from the same `agent` restores the entry immediately.

---

## 6. Status Semantics

| Status          | Meaning                                      | Typical reaction |
|-----------------|----------------------------------------------|------------------|
| `alive`         | Ready and reachable                          | Normal           |
| `busy`          | Working on a task, still reachable           | Prefer not to assign new heavy work |
| `idle`          | Online but free                              | Good candidate for new tasks |
| `error`         | Degraded / recovering                        | Investigate      |
| `shutting_down` | Graceful exit in progress                    | Do not send new work |
| `stale`         | Timeout – possibly offline                   | Treat as missing |

---

## 7. Integration Points

### Agents (Lyra / Xen / Elara)

- Each agent (or the orchestrator on their behalf) emits heartbeats according to the table above.
- Agents may read the Presence Table to know who else is online before initiating coordination.

### York Autotype

- Already produces compatible JSON via `york-heartbeat`.
- When nxmesh is linked, the same binary publishes live onto the mesh.

### Orchestrator

- Owns the Presence Table.
- Optionally exposes a simple status endpoint or file (`status/swarm_presence.json`).
- Can surface “swarm health” summaries to the user.

---

## 8. Security & Trust Notes

- Heartbeats travel over Noise-encrypted nxmesh channels.
- `agent` and `node_id` are self-declared; for stronger guarantees a later version can add signatures or PeerId binding.
- Flood protection: minimum 5 s between emissions per agent instance.

---

## 9. Implementation Checklist

- [x] Message format in nxmesh (`AgentHeartbeat` + `extra`)
- [x] Event `AgentHeartbeatReceived`
- [x] Emission design for all four participants
- [x] Presence Table schema
- [x] Timeout / stale rules
- [ ] Orchestrator presence-table implementation
- [ ] Live publish path from York
- [ ] Optional `status/swarm_presence.json` writer
- [ ] Simple CLI / status view for the user

---

## 10. Design Principles

1. **Lightweight** – small JSON, low frequency.
2. **Decentralized** – no central heartbeat server.
3. **Observable** – any mesh participant can build its own view.
4. **Extensible** – `extra` field absorbs future needs without protocol breaks.
5. **Honest** – timeouts produce `stale`, not silent disappearance.

---

*This document is the canonical Heartbeat Design for the Nexus Mesh Swarm.*
