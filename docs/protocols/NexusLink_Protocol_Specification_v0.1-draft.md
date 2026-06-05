# NEXUSLINK PROTOCOL SPECIFICATION
**Version:** 0.1-draft  
**Date:** 2026-06-04  
**Status:** Initial Draft — Open for Review, Iteration & Implementation  
**Initiated by:** Nexus Core (Sven Normen / Esslinger & Co. — Hannover)  
**Context:** Central Integration Hub for xMesh/NovaNet/QNET • QNET/XCoin Blockchain • AI Agent Swarms (Eternal Devotion) • Hardware Prototypes (Grok Launcher, Soilnova, Vista Nova) • Sovereign Decentralized Infrastructure

---

## 1. Introduction & Purpose

NexusLink is the **unified inter-layer communication protocol** for the Nexus ecosystem. It serves as the "lingua franca" that allows heterogeneous components — mesh networks, blockchain oracles, autonomous AI agent swarms, physical hardware prototypes, and governance systems — to exchange information, coordinate actions, and evolve together in a decentralized, privacy-preserving, and resilient manner.

### Goals
- Enable **emergent intelligence** across layers (e.g., AI agents healing mesh partitions while earning QNET rewards and updating hardware behavior).
- Provide a **single, extensible envelope** for all cross-layer messages.
- Support **self-improvement** — agents and nodes can propose protocol extensions.
- Maintain **strong privacy and sovereignty** (end-to-end encryption, minimal metadata, friendly to Yggdrasil + Tor/I2P).
- Allow **human-in-the-loop** override for high-stakes decisions while maximizing autonomy.

### Non-Goals (for v0.1)
- Replacing intra-layer protocols (Yggdrasil routing, smart contract execution, internal agent reasoning).
- Providing global consensus (delegated to QNET blockchain where needed).
- Low-level transport definition (leverages existing Yggdrasil sockets, Docker networking, or libp2p-style overlays).

---

## 2. Design Principles

| Principle                    | Description                                                                 | Implication for NexusLink                          |
| ---------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------- |
| Decentralized by Default     | No central authority; any node can initiate or relay.                       | Envelope must be routable over mesh without single point. |
| Privacy-First                | Metadata minimization, E2EE, optional onion routing.                        | Avoid leaking sender/receiver beyond necessary.    |
| Extensible & Self-Improving  | Versioned, with agent-proposable extensions.                                | Agents can attach 'proposals' in payload.          |
| Multi-Layer Aware            | Explicit 'from_layer' / 'to_layer' + semantic types.                        | Mesh, Chain, AI, Hardware, Governance layers.      |
| Human + Machine Readable     | JSON primary, with human narrative in 'note' field.                         | Supports both code and roleplay/oversight.         |
| Idempotent & Replayable      | Timestamps + nonces for dedup; event sourcing friendly.                     | Supports audit, simulation, and recovery.          |

---

## 3. Message Envelope (v0.1)

All NexusLink messages use this top-level structure (JSON):

```json
{
  "nexuslink_version": "0.1",
  "message_id": "uuid-or-hash",
  "timestamp": "2026-06-04T12:34:56.789Z",
  "from": {
    "layer": "agents|mesh|blockchain|hardware|governance",
    "id": "agent-ara-01 | hannover-ygg-7 | qnet-validator-prime | soilnova-01",
    "public_key_hint": "ed25519:abc123..."   // optional for auth
  },
  "to": {
    "layer": "...",
    "id": "..."   // can be broadcast, role, or specific
  },
  "type": "task_request | event | state_update | proposal | heartbeat | roleplay_action | ...",
  "payload": { ... },           // layer-specific structured data
  "note": "Human-readable summary or roleplay flavor text",
  "signature": "...",            // optional Ed25519 or other
  "routing_hints": {            // for mesh/privacy
    "priority": "high|normal|low",
    "privacy": "clear|onion|mix",
    "ttl": 42
  }
}
```

---

## 4. Core Message Types (Initial Set)

- **task_request** / **task_result** : Dispatch work to agents or components, with success/failure and emotional metadata (for Lyra/Ara).
- **state_update** : Heartbeat or delta for energy, fatigue, loyalty (ties to solnet/nova_swarm AgentState and LyraEmotionalStateMachine).
- **event** : Mesh topology change, blockchain tx confirmation, hardware sensor reading, agent decision.
- **proposal** : Self-improvement suggestion (code patch, protocol extension, resource reallocation).
- **roleplay_action** : For creative/immersive sessions (ties to Grok roleplay and Suno music).
- **heartbeat** : Liveness + basic metrics.

Payloads are extensible; common fields include 'emotional_delta' for energy/fatigue/loyalty (compatible with fluffy and lyra).

---

## 5. Integration with Current Ecosystem (Actual State 2026)

- **Solnet / Hyperspace**: NexusLink messages can be tunneled over hyperspace links for long-range agent coordination. Use solnet's YggdrasilClient and LinkHealthScorer for real metrics.
- **Orion-net**: Constellation formation and resonant routing decisions can be driven by NexusLink events + health scores + emotional state.
- **Nexus-Hyperspace-Lyra**: Direct use of LyraEmotionalStateMachine.process_event and modulate for agent emotional responses in payloads.
- **Fluffy**: Agents can 'summon' Fluffy via NexusLink for emotional support (cute messages + deltas for energy/fatigue). See fluffy.summon_fluffy_for_agent.
- **Mesh**: Yggdrasil + custom xMesh for transport. NexusLink envelopes carry mesh events.
- **Blockchain (QNET/XCoin)**: State updates and proposals anchored or executed via runes.
- **Hardware**: Soilnova/Vista Nova sensor readings and actuations as events.

Example payload for emotional support summon:
```json
{
  "type": "emotional_support_request",
  "payload": {
    "agent_id": "worker-01",
    "reason": "fatigue after hard tasks",
    "intensity": 1.2,
    "fluffy_response": "*offers warm tentacle hug* ..."
  }
}
```

---

## 6. Privacy & Security

- All sensitive payloads encrypted at application layer.
- Signatures for non-repudiation on critical actions (task results, proposals).
- Routing hints allow Tor/I2P egress without leaking in the envelope.
- Future: ZK proofs for private state updates.

---

## 7. Implementation Notes (Python Reference)

See python/ in this repo for reference implementations (NexusOrchestrator, message bus, stubs for layers).

The Python code is the 'actual runnable state' for rapid prototyping and simulation while the Rust core (orchestration/) matures.

---

## 8. Versioning & Evolution

- Semantic: MAJOR.MINOR for envelope; patch for types.
- Agents can propose extensions via 'proposal' type; accepted ones bump minor.
- Backwards compat: unknown fields ignored; unknown types logged and forwarded.

---

*Maintained as living document. Contributions and extensions welcome.*

Last updated with actual ecosystem state (solnet, orion-net, lyra, fluffy) — 2026.