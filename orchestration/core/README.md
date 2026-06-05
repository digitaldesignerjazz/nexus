# orchestration/core — Rust Core for Nexus Central Orchestration Hub (Phase 1)

**Status**: Initial skeleton (June 2026)  
**Purpose**: High-performance, safe, async foundation for the Central Orchestration Hub.  
**Phase 1 Scope**: In-memory event bus, basic workflow engine, CLI demo, NexusLink envelope types.  
**Future**: Distributed mesh integration, persistent state, self-improvement meta-layer, full NexusLink gRPC/Yggdrasil bindings.

## Quick Start (Local)

```bash
git clone https://github.com/digitaldesignerjazz/nexus.git
cd nexus/orchestration/core
cargo build --release
./target/release/nexus-orchestrator --help
```

## Current Modules
- `event_bus` — Async pub/sub with topic routing and backpressure (tokio channels + broadcast).
- `workflow_engine` — Simple state-machine / DAG executor stub (expandable to full workflow definitions).
- `nexuslink` — Shared envelope types and basic validation (aligned with interfaces/NexusLink-v0.1.md).

## Dependencies (Phase 1)
- tokio (async runtime, channels, time)
- serde + serde_json (serialization for envelopes)
- uuid (message IDs, correlation)
- tracing + tracing-subscriber (structured logging)
- clap (CLI)
- thiserror (error handling)

## Roadmap within Core
1. Event bus with persistent replay log (Phase 1+).
2. Workflow engine with declarative definitions (YAML/JSON or eDSL).
3. NexusLink transport bindings (Yggdrasil pub/sub first, then gRPC).
4. Integration with mock connectors for mesh/chain/swarm/hardware.
5. Self-improvement hooks and simulation bridge.

**License**: Apache-2.0 (preferred for core orchestration components; subject to overall Nexus licensing decision).

**Alignment**: Implements concepts from docs/orchestration-architecture.md and interfaces/NexusLink-v0.1.md.
