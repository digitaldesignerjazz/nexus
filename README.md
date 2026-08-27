# Nexus

**Nexus** is the foundational and integrative core repository for the decentralized innovation ecosystem developed by Sven Normen (Esslinger & Co. / digitaldesignerjazz). It serves as the central hub connecting advanced mesh networking, blockchain technologies, autonomous AI agent swarms, hardware prototyping, and strategic business infrastructure.

## Vision & Mission

Nexus aims to create a resilient, self-evolving, global decentralized infrastructure that harmonizes:

- **Mesh Networking**: Building upon Yggdrasil, extended through custom xMesh, NovaNet, and QNET protocols. Focus on privacy (Tor/I2P), Docker orchestration, hardware like Tenda Nova, and scalable peer-to-peer connectivity.
- **Blockchain & Token Economy**: XCoin and QCoin as native currencies, QNET for network incentives, rune-based tokenization, arbitrage systems, and on-chain governance.
- **AI Agents & Swarms**: Integration of Grok Launcher (Rust + egui), emotional/self-improving AI, agent swarms for complex tasks, roleplay scenarios, and autonomous decision-making. Emphasis on sentience, emotional intelligence, and recursive self-improvement.
- **Hardware & Physical Prototypes**: Soilnova, Vista Nova, York Autotype, Lumia, and other IoT/embedded systems bridging digital and physical worlds.
- **Business & Legacy**: Delaware C-Corp structures (Esslinger & Co. with 10M shares), family tradition (Esslinger lineage), noble titles, and long-term innovation strategy rooted in Hannover, Germany.

The "Nexus" represents the interconnection point — where these layers converge to enable emergent behaviors, decentralized autonomy, and sustainable growth.

## Actual Current Implementation State (2026)

**Python Reference Prototypes** (runnable actual state in `python/`):
- `start_nexus.py`: Interactive launcher + REPL for core orchestrator with boot dashboard, layer status, event bus.
- `nexus_core.py`: Foundational stubs for Orchestrator, MeshConnector, BlockchainBridge, AgentSwarm.
- `nexus_orchestrator.py`: Full async central orchestration hub with agents, mesh nodes, blockchain, task dispatch, heartbeats, self-improvement, integrations (Grok, emotional AI, prototypes).
- `nexus_cyberspace.py`: Immersive simulator for topology, agent swarms, QCoin economy (uses networkx + matplotlib).
- configs for yggdrasil, declarative setup.

**Hannover Control Plane** (runnable host setup in `server-setup/`):
- HTTP control plane on `127.0.0.1:8787` (`/health`, `/status`, `/layers`)
- Bootstrap scripts, Docker Compose, systemd unit
- See `server-setup/SETUP.md`

**Ecosystem Integrations (Actual Built Components)**:
- **Solnet** (https://github.com/digitaldesignerjazz/solnet): Hyperspace transport, Yggdrasil client, NovaSwarm with emotional/loyalty models, LinkHealthScorer for real-time/historical link health (EWMA, flaps, etc.).
- **Orion-net** (https://github.com/digitaldesignerjazz/orion-net): Constellation networking, resonant routing modulated by Lyra emotions + Solnet health scores. Time-stepped emotional drift demos with rich viz.
- **Nexus-Hyperspace-Lyra** (https://github.com/digitaldesignerjazz/Nexus-Hyperspace-Lyra-1.0): LyraEmotionalStateMachine for agent energy/fatigue/loyalty, process_event, decay, modulate_resonance.
- **Fluffy** (https://github.com/digitaldesignerjazz/fluffy): Cute loyal alien pet for emotional support. `summon_fluffy_for_agent()` returns deltas + funny messages; integrated into SwarmAgent for fatigue/sadness support. CLI for humans too.

These are wired together in demos (e.g., solnet emotional_swarm_simulation now summons Fluffy; orion uses health + lyra).

See python/ for the reference code matching this actual state.

## Repository Structure

(Keeps the proposed layout, with python/ as reference layer alongside Rust orchestration/ and mesh/).

## Getting Started

Control plane (Hannover node):

```bash
cd server-setup
bash scripts/00-doctor.sh
bash scripts/01-bootstrap.sh
bash scripts/02-start-control-plane.sh
curl -s http://127.0.0.1:8787/health
```

See `server-setup/SETUP.md` and `python/README.md` for the Python prototypes.

## Current Status

**Actual Running State**: Python prototypes + Hannover control plane + full cross-repo integrations (solnet hyperspace health, orion constellations, lyra emotions, fluffy agent support) are the live implementation. Rust core and additional docs in progress.

**Phase**: Active integration and reference implementation.

See root commits for Rust skeleton (orchestration/core etc.) and docs.

## Related Repos (Actual)
- solnet
- orion-net
- Nexus-Hyperspace-Lyra-1.0
- fluffy
- go-nexus

## License

To be determined.

*"The Nexus is not just code — it is the living interconnection of ideas, people, machines, and dreams."*

**Last Updated**: 28 August 2026 — server-setup control plane added
