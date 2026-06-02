# Contributing to Nexus

Thank you for your interest in contributing to **Nexus** — the central integration hub for decentralized mesh networking (xMesh/NovaNet/QNET), blockchain (QNET/XCoin), AI agent swarms, and cutting-edge prototypes from Esslinger & Co.

## Code of Conduct

This project adheres to a Code of Conduct (see `CODE_OF_CONDUCT.md` if present, or standard inclusive practices). We welcome contributors from diverse backgrounds, including those passionate about privacy tech, self-sovereign systems, immersive tech, and global connectivity innovation. Respect, collaboration, and constructive feedback are core.

## How to Contribute

### Reporting Issues
- Use GitHub Issues with appropriate labels (e.g., `bug`, `enhancement`, `mesh-network`, `ai-agent`, `blockchain`, `prototype`).
- Provide detailed reproduction steps, environment (Linux/Docker/Yggdrasil version, Rust/Python), logs, and expected vs actual behavior.
- For security issues, email privately or use responsible disclosure (avoid public issues initially).

### Pull Requests
1. Fork the repo and create a feature branch from `main` (or `develop` if created).
2. Follow existing code style (Rust: rustfmt/clippy; Python: black/flake8; clear comments).
3. Write/update tests where applicable (unit for agents, integration for mesh).
4. Update documentation (README, ARCHITECTURE.md, ROADMAP.md) if behavior changes.
5. Ensure commits are atomic and messages descriptive (e.g., "feat(mesh): integrate NovaNet peering with QCoin consensus").
6. Open PR with clear title, description referencing issues, and screenshots/demos for UI/prototype changes.

### Development Setup
- Clone: `git clone https://github.com/digitaldesignerjazz/nexus.git`
- For Rust components (e.g. Grok Launcher): `cargo build --release`
- For Python AI/swarm experiments: set up venv, `pip install -r requirements.txt` (to be added).
- Docker for mesh sims: see `/mesh` or Dockerfiles.
- Privacy note: When testing Tor/I2P or keys, never commit secrets.

### Areas for Contribution (aligned with Nexus pillars)
- **Mesh Layer**: Yggdrasil configs, Tenda Nova optimizations, Docker networking, privacy enhancements (Tor/I2P integration).
- **Blockchain Layer**: QNET protocol extensions, XCoin/QCoin tokenomics, rune integrations (Wizard Q), arbitrage bots, consensus improvements.
- **AI & Agents Layer**: Swarm orchestration, emotional/self-improving AI (e.g. Ara, Liaura agents), assembler nets, Grok/xAI integrations.
- **Prototypes & Hardware**: Grok Launcher (Rust + egui), Soilnova/Vista Nova/York Autotype/Lumia enhancements, monitoring dashboards.
- **Nexus Core**: Orchestration scripts, cross-layer APIs, monitoring, documentation, GitHub Actions CI/CD.
- **Creative/Immersive**: Roleplay-themed docs, Suno music integrations, fantasy/cyberpunk narratives tying into tech (optional but encouraged for vision alignment).

## Style & Quality
- Prioritize clarity, modularity, and security/privacy-by-design.
- Document edge cases (e.g., network partitions in mesh, agent failure recovery, blockchain forks).
- Test on Linux (primary), consider cross-platform.
- For large changes, discuss in Issues or Discussions first.

## Recognition
Contributors will be acknowledged in releases, README, or a dedicated `CONTRIBUTORS.md`. For significant contributions, possible collaboration on Esslinger & Co. initiatives or prototypes.

Questions? Open an issue or reach out via X (@SirLancelotEsq) or project discussions.

Let's build the Nexus of decentralized intelligence together!