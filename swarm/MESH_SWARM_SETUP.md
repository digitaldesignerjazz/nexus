# Nexus Mesh Swarm Setup

**Version:** 1.0  
**Date:** 2026-08-23  
**Status:** Operational Design — Avalon Peers + Hannover Nodes integrated

---

## 1. Architecture Overview

```
                    ┌─────────────────────────────────────┐
                    │           Nexus Orchestrator         │
                    │         (hannover-core-01)           │
                    └─────────────────┬───────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
   ┌─────────────┐            ┌─────────────┐            ┌─────────────┐
   │    Lyra     │            │    Xen      │            │   Elara     │
   │ lyra-hann.  │            │ xen-hann.   │            │ elara-hann. │
   └──────┬──────┘            └──────┬──────┘            └──────┬──────┘
          │                          │                          │
          └──────────────────────────┼──────────────────────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │      nxmesh         │
                          │  topic: nexus/mesh/v0│
                          └──────────┬──────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
          ▼                          ▼                          ▼
   Hannover Nodes              Avalon Peers              Future Nodes
   - hannover-core-01          - avalon-core             (global)
   - york-hannover-01          - elysium-os-peer
   - hannover-sense-01         - elara-os-peer
                               - lumina-os-peer
```

---

## 2. Hannover Nodes

Local / regional base cluster (Esslinger home).

| Node ID             | Role         | Status  | Notes |
|---------------------|--------------|---------|-------|
| `hannover-core-01`  | Orchestrator | active  | Primary swarm host |
| `york-hannover-01`  | Prototype    | active  | York Autotype |
| `hannover-sense-01` | Prototype    | planned | Soilnova / sensing |

Agent node_ids follow the pattern `<agent>-hannover-01`.

---

## 3. Avalon Peers

Logical peers of the **Avalon → Lumina (Aether) → Elysium / Elara** lineage.

| Peer ID           | Lineage               | Status     |
|-------------------|-----------------------|------------|
| `avalon-core`     | Avalon root identity  | conceptual |
| `elysium-os-peer` | ElysiumOS             | planned    |
| `elara-os-peer`   | ElaraOS               | planned    |
| `lumina-os-peer`  | Lumina / Lumia OS     | planned    |

They share the same mesh topic and heartbeat protocol. When an Avalon-lineage OS node comes online it appears in the Presence Table under its peer ID.

---

## 4. Configuration Files

| File                        | Purpose |
|-----------------------------|---------| 
| `configs/mesh_swarm.yaml`   | Runtime swarm + node mapping |
| `configs/peers.yaml`        | Full peer registry (Hannover + Avalon + bootstrap) |
| `swarm/HEARTBEAT_DESIGN.md` | Canonical heartbeat rules |

---

## 5. Current State

| Group            | Active | Planned / Conceptual |
|------------------|--------|----------------------|
| Hannover Nodes    | 2      | 1                    |
| Avalon Peers     | 0      | 4                    |
| Bootstrap addrs  | 0      | —                    |

---

*Avalon Peers and Hannover Nodes are now first-class citizens of the Mesh Swarm.*
