# nxmesh — Nexus Mesh Substrate (Noise + QUIC / libp2p)

**Userspace, zero-daemon mesh overlay for the Nexus ecosystem.**

This crate replaces the previous hard dependency on Yggdrasil (and Tor for privacy routing) with a pure Rust, fully self-contained solution based on:

- **Noise Protocol Framework** → authenticated, encrypted handshakes
- **QUIC** (UDP) as primary transport → fast, multiplexed, 0-RTT capable
- **libp2p** → peer discovery (mDNS + Kademlia DHT), Gossipsub, Identify, Ping
- TCP + Yamux as fallback transport

### Why this change?

Many environments (restricted containers, no-root, corporate policies, mobile, certain cloud sandboxes) cannot install or run Yggdrasil or Tor.  
nxmesh runs with normal user privileges, needs no external services, and still provides:

- Strong node identity (Ed25519)
- End-to-end encrypted channels
- Automatic local discovery
- Global discovery via Kademlia + bootstrap peers
- Gossip and request/response primitives ready for agent swarms (Lyra / Xen / Elara) and QNET data

### Quick start

```bash
cd mesh/noise-quic
cargo run --example basic_node
```

Two instances on the same LAN will discover each other via mDNS and can exchange messages.

### Integration points

| Nexus Layer          | How nxmesh connects                          |
|----------------------|----------------------------------------------|
| Agent Swarm (Lyra/Xen/Elara) | Publish `AgentHeartbeat` + custom gossip    |
| QNET / XCoin / Runes | `DataRequest` / `DataResponse` messages      |
| Grok Launcher        | Status & control plane over mesh             |
| Prototypes           | Sensor / actuator oracles via gossip topics  |
| Privacy              | Noise already encrypts; can add multi-hop later |

### Status (2026-08-23)

- [x] Core identity + Noise + QUIC + Gossipsub skeleton
- [x] mDNS local discovery
- [x] Kademlia ready
- [ ] Bootstrap peer list + persistent peer store
- [ ] Request-Response protocol for QNET
- [ ] Hybrid post-quantum (Kyber) Noise upgrade path
- [ ] Integration tests with Lyra / Xen heartbeat
- [ ] Documentation for multi-node Hannover / global deployment

### License

MIT OR Apache-2.0  
Part of the Nexus / Esslinger & Co. ecosystem.
