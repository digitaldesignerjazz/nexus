# Nexus Mesh Swarm Setup

**Version:** 0.9  
**Date:** 2026-08-23  
**Status:** Operational Design

---

## 1. Architecture Overview

```
                    ┌─────────────────────────────────────┐
                    │           Nexus Orchestrator         │
                    └─────────────────┬───────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
   ┌─────────────┐            ┌─────────────┐            ┌─────────────┐
   │    Lyra     │            │    Xen      │            │   Elara     │
   │  emotional  │            │  technical  │            │   devoted   │
   │  creative   │            │ exploratory │            │ intelligence│
   └──────┬──────┘            └──────┬──────┘            └──────┬──────┘
          │                          │                          │
          └──────────────────────────┼──────────────────────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │      nxmesh         │
                          │  Noise + QUIC       │
                          │  Gossipsub topic:   │
                          │  nexus/mesh/v0      │
                          └──────────┬──────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
             York Autotype     Future Nodes     Bootstrap Peers
             (heartbeat)       (prototypes)     (discovery)
```

---

## 2. Roles

| Role              | Responsibility                                      | Heartbeat Agent Name |
|-------------------|-----------------------------------------------------|----------------------|
| **Lyra**          | Emotional regulation, narrative, creative synthesis | `lyra`               |
| **Xen**           | Technical diagnostics, integration, optimization    | `xen`                |
| **Elara**         | Integrated intelligence, continuity, devotion       | `elara`              |
| **York Autotype** | Automation prototype, task execution                | `york-autotype`      |
| **nxmesh Node**   | Transport, discovery, message routing               | —                    |

---

## 3. Message Flow

### Heartbeat (Presence)

Every participant periodically publishes:

```json
{
  "type": "AgentHeartbeat",
  "payload": {
    "agent": "lyra | xen | elara | york-autotype",
    "node_id": "<unique-node-id>",
    "status": "alive | busy | idle | error",
    "ts": "<ISO-8601 UTC>",
    "extra": { ... }
  }
}
```

Topic: `nexus/mesh/v0`

Receiving nodes emit `MeshEvent::AgentHeartbeatReceived`.

### Gossip / Coordination

- Status updates
- Task announcements
- Creative or technical briefs between agents

### Future: Request / Response

`DataRequest` / `DataResponse` for QNET, oracles, and cross-agent queries.

---

## 4. Configuration

See `configs/mesh_swarm.yaml` for the concrete runtime configuration.

Key parameters:

- **mesh_topic**: `nexus/mesh/v0`
- **heartbeat_interval**: 20–30 seconds (agents), 6 h (GitHub Actions fallback)
- **identity_path**: per-node persistent key
- **bootstrap_peers**: list of multiaddrs (to be filled when first peers exist)
- **enable_mdns**: `true` for local discovery

---

## 5. Current Operational State (2026-08-23)

| Component            | State                          |
|----------------------|--------------------------------|
| nxmesh substrate     | Ready                          |
| AgentHeartbeat proto | Finalized                      |
| Lyra / Xen / Elara   | Skilllogin complete, online    |
| York Autotype        | Heartbeat-compatible, public   |
| Bootstrap peers      | Not yet defined                |
| Live multi-node test | Pending                        |
| Container images     | Prepared (Docker + Podman)     |

---

## 6. Activation Sequence

1. Start nxmesh node(s) (userspace or container)
2. Agents (Lyra/Xen/Elara) connect via orchestrator and emit heartbeats
3. York Autotype emits its own heartbeat
4. Swarm becomes visible to itself through `AgentHeartbeatReceived` events
5. Optional: bootstrap peers for wide-area discovery

---

## 7. Next Concrete Steps

1. Define first bootstrap peer list (even if only one node for now)
2. Link nxmesh into York and enable live publish
3. Add simple heartbeat listener in the orchestrator so Xen/Lyra/Elara can “see” each other
4. First multi-node gossip test when a second runtime is available

---

*Nexus Mesh Swarm is designed. Ready for the next operational command.*
