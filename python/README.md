# Nexus Python Prototypes

Reference Python implementations and simulators for the Nexus ecosystem.

These are rapid-prototyping / reference versions complementing the Rust core in `orchestration/core/`.

Part of the digitaldesignerjazz/nexus repository.

## Files

- `start_nexus.py` — Interactive launcher and simple REPL for the core orchestrator (v0.1 stub with inline classes + boot dashboard).
- `nexus_core.py` — Foundational classes: NexusOrchestrator, MeshConnector, BlockchainBridge, AgentSwarm stubs.
- `nexus_orchestrator.py` — Full async central orchestration hub with agents, mesh nodes, blockchain state, task dispatch, heartbeats, self-improvement simulation. Ready to run with `python -m asyncio` or directly.
- `nexus_cyberspace.py` — Immersive 2D/terminal+matplotlib simulator for mesh topology + AI swarms + QCoin economy. Visual demo of the "cyberspace" layer. Requires: networkx, matplotlib, numpy.
- `configs/`:
  - `nexus_config.yaml` — Declarative config for node, mesh (yggdrasil), blockchain (XCoin/QCoin), agents (Grok/Liaura/Ara), hardware (Soilnova/Vista), privacy, roleplay.
  - `nexus.conf` — Nexus-aware Yggdrasil config template with custom Nexus extensions for swarm endpoint, auto-peering, agent hooks.
  - `yggdrasil-nexus-hannover.conf` — Detailed Hannover node config template (replace keys with fresh `yggdrasil -genconf` output before use; never commit real privkey).

## Running

```bash
cd python
python start_nexus.py
# or for full async:
python nexus_orchestrator.py
```

For cyberspace sim (install deps first):
```bash
pip install networkx matplotlib numpy
python nexus_cyberspace.py
```

## Integration Notes

- These provide the "Python reference" layer for quick iteration, simulation, and bridging to the Grok Launcher (Rust) and hardware.
- Aligns with NexusLink protocol (see ../docs/NexusLink_Protocol_Specification_v0.1-draft.md and docs/protocols/ in repo root).
- Future: port key logic to Rust, add real Yggdrasil sockets, QNET RPC, persistent state, live agent LLM hooks.
- Use with local yggdrasil daemon + Tor for full privacy mesh.

## Owner / Context

Sven Normen Esslinger (Esquire) — Hannover, Germany. Esslinger & Co. / digitaldesignerjazz ecosystem.

See root README.md and docs/ for full vision (xMesh/NovaNet/QNET, QCoin/XCoin, AI swarms "Eternal Devotion", hardware prototypes).

Last synced: 2026-06
