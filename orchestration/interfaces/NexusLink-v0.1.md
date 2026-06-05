# NexusLink v0.1 — Core Interface Specification for the Nexus Central Orchestration Hub

**Status**: Draft (June 2026)  
**Version**: 0.1  
**Owner**: Sven Normen / Esslinger & Co.  
**Related**: [orchestration-architecture.md](../docs/orchestration-architecture.md)  
**License**: To be aligned with Nexus core (MIT/Apache-2.0 preference)

---

## 1. Purpose & Scope

NexusLink defines the **standardized, versioned, transport-agnostic interfaces** that allow the Central Orchestration Hub to communicate with:

- Mesh networking layer (xMesh/NovaNet/Yggdrasil nodes & events)
- Blockchain layer (QNET/XCoin/QCoin oracles, smart contracts, incentive events)
- AI Agent Swarms (Lyra, emotional models, task dispatch & results)
- Hardware / IoT prototypes (Soilnova, Vista Nova, sensors, actuators, digital twins)
- Human interfaces (Grok Launcher, dashboards, immersive narrative systems)
- Other orchestrator instances (hierarchical/federated setups)

**Goals**:
- Loose coupling & evolvability (semantic versioning, backward-compatible extensions)
- Privacy-preserving by default (encryption, selective disclosure, ZK-friendly where applicable)
- Mesh-native friendliness (works over Yggdrasil overlays, intermittent links)
- Polyglot support (Rust core, Python agents, future WASM)
- Auditability & replayability (event sourcing friendly)

**Non-goals (v0.1)**: Full cryptographic proof systems, complex multi-party workflows, on-chain governance encoding (deferred to later versions or QNET integration).

---

## 2. Core Concepts

### 2.1 Message Categories

| Category   | Direction                  | Purpose                                      | Examples                                      |
|------------|----------------------------|----------------------------------------------|-----------------------------------------------|
| Event      | Many → Hub (or Hub → Many) | Asynchronous notifications of state changes | `MeshNodeJoined`, `BlockMined`, `AgentTaskCompleted`, `HardwareTelemetry` |
| Command    | Hub → Target             | Imperative actions / workflow steps         | `AdjustRoutes`, `SpawnAgentSwarm`, `ExecuteHardwareCommand`, `ClaimReward` |
| Query      | Hub → Target             | Request current state or capabilities       | `GetMeshTopology`, `GetAgentStatus`, `GetHardwareSensors` |
| Response   | Target → Hub             | Answers to Queries or Command acknowledgments | `TopologySnapshot`, `TaskResult`, `SensorReadings` |
| Proposal   | Hub/AI → Hub (meta)     | Self-improvement suggestions                | `CodePatchProposal`, `TopologyOptimization`, `ParameterTuning` |

### 2.2 Envelope Structure (JSON Schema draft)

All NexusLink messages share a common envelope for routing, versioning, security, and tracing:

```json
{
  "nexuslink_version": "0.1",
  "message_id": "uuid-v7-or-ulid",
  "timestamp": "2026-06-05T15:00:00Z",
  "source": {
    "type": "mesh_node | agent_swarm | hardware_device | orchestrator_instance | human_interface",
    "id": "node-42 | swarm-lyra-001 | soilnova-v2-03 | orchestrator-hannover-01 | grok-launcher-sven",
    "capabilities": ["relay", "high_bandwidth", "emotional_inference", "soil_sensor_v2"]
  },
  "target": {
    "type": "orchestrator | mesh | chain | swarm | hardware | broadcast",
    "id": "orchestrator-main | broadcast"
  },
  "correlation_id": "optional-uuid-for-request-response",
  "trace_id": "for-distributed-tracing",
  "security": {
    "encryption": "end-to-end | hop-by-hop | none",
    "signature": "optional-ed25519-or-schnorr-signature",
    "capability_proof": "optional-zk-or-capability-token"
  },
  "payload": { /* category-specific schema */ },
  "metadata": {
    "priority": "high | normal | low",
    "ttl_seconds": 300,
    "retry_policy": {...}
  }
}
```

### 2.3 Payload Schemas (Examples)

**Event: MeshNodeJoined**
```json
{
  "event_type": "MeshNodeJoined",
  "node_id": "ygg-abc123",
  "public_key": "ed25519:...",
  "coordinates": {"lat": 52.37, "lon": 9.73},  // optional, privacy-sensitive
  "announced_capabilities": ["relay", "storage"],
  "bandwidth_mbps": 120,
  "joined_at": "2026-06-05T14:55:00Z"
}
```

**Command: SpawnAgentSwarm**
```json
{
  "command_type": "SpawnAgentSwarm",
  "swarm_type": "optimization | monitoring | creative | emotional_support",
  "task_description": "Optimize mesh routes under current congestion",
  "constraints": {
    "max_agents": 8,
    "deadline": "2026-06-05T16:00:00Z",
    "qcoin_budget": 250
  },
  "initial_context": { /* shared knowledge graph snapshot or CID */ }
}
```

**Query: GetMeshTopology**
```json
{
  "query_type": "GetMeshTopology",
  "scope": "local | regional | global",
  "filters": {"min_reliability": 0.95, "include_hardware": false}
}
```

**Response** and **Proposal** schemas follow similar patterns (full details in future revision or generated .proto / OpenAPI).

---

## 3. Transport Bindings (v0.1)

NexusLink is transport-agnostic. Recommended bindings for early implementation:

1. **Yggdrasil Native Pub/Sub** (preferred for mesh-native)
   - Topic naming: `nexuslink.v0_1.<category>.<subtype>`
   - Payload: JSON or CBOR (compact)
   - Encryption: Yggdrasil built-in + optional application-layer

2. **gRPC + Protocol Buffers** (high-performance, polyglot)
   - `.proto` definitions to be generated from this spec
   - Unary + streaming RPCs for Commands/Queries
   - Server streaming for Events

3. **QUIC / HTTP/3** (fallback or cross-cloud)
4. **JSON over WebSocket** (for Grok Launcher / human interfaces)

**Future**: libp2p, NATS, or custom gossip over mesh for fully decentralized operation.

---

## 4. Versioning, Compatibility & Evolution

- Semantic Versioning: MAJOR.MINOR.PATCH
- Backward compatibility within minor versions
- New fields must be optional with sensible defaults
- Deprecation via `deprecated: true` + sunset timeline in metadata
- Major changes trigger new `nexuslink_version` and coordinated rollout via self-improvement proposals + governance

---

## 5. Security, Privacy & Trust Model (v0.1)

- **Identity**: Mesh node keys + optional DID or noble title assertions
- **Auth**: Capability-based (least privilege). Capability tokens or ZK proofs for sensitive Commands
- **Confidentiality**: End-to-end encryption for inter-orchestrator or human-sensitive flows
- **Integrity**: Signatures on critical messages; hash-chaining for event logs
- **Replay Protection**: Timestamps + nonces + bounded TTL
- **Audit**: All Commands/Events logged with correlation; privacy-preserving aggregates published on-chain where appropriate

**Edge Cases Handled**:
- Intermittent connectivity → local queuing + replay on reconnect
- Partial trust → reputation-weighted routing + sandboxed execution for untrusted sources
- Conflicting commands → priority + multi-source consensus (future)

---

## 6. Example End-to-End Flow (Mesh Congestion → Optimization Swarm)

1. Mesh layer emits `MeshCongestionDetected` Event via NexusLink.
2. Orchestrator receives Event, correlates with recent topology & QCoin economics.
3. Orchestrator issues `SpawnAgentSwarm` Command to AI layer (with task + budget).
4. Swarm completes task → emits `AgentTaskCompleted` with optimization plan.
5. Orchestrator validates plan (simulation + reputation) → issues `AdjustRoutes` Command to mesh.
6. Mesh applies changes → emits confirmation Events.
7. Orchestrator triggers `ClaimReward` on-chain via blockchain connector (incentive alignment).
8. Self-improvement meta-layer logs outcome and may propose parameter tuning.

All steps use NexusLink envelopes with full tracing.

---

## 7. Implementation Notes & Code Generation

- **Rust**: Use `prost` or `tonic` for gRPC; `serde` + `uuid` for JSON/CBOR envelopes. Shared types in `orchestration/interfaces/src/lib.rs`.
- **Python**: `pydantic` models + `grpcio` or `aiohttp`. Fast iteration for agent experimentation.
- **Schema Evolution**: Consider adopting Buf or similar for proto management.
- **Testing**: Property-based testing on envelopes; chaos testing for partition/replay scenarios.

**Next for v0.2+**:
- Formal .proto + OpenAPI specs (auto-generated from this Markdown or dedicated IDL)
- Workflow definition language (declarative DAGs)
- On-chain anchoring of critical interface versions
- Full ZK integration hooks

---

## 8. Open Questions & Feedback Areas

- Preferred primary transport for v0.1 MVP (Yggdrasil pub/sub vs gRPC)?
- Should capability proofs be mandatory for Commands that affect economics?
- How to represent "noble title" or role-based assertions in identity fields (thematic extension)?
- Bilingual documentation priority (EN primary + DE summary)?

---

*This specification is living. It will be refined through implementation feedback, self-improvement proposals from the orchestration hub itself, and community input.*

**Last Updated**: June 2026  
**Author**: Grok (assisting Sven Normen)
