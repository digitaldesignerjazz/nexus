//! # nxmesh — Nexus Mesh Substrate
//!
//! Userspace, fully self-contained mesh overlay for the Nexus ecosystem.
//!
//! Built on:
//! - **Noise Protocol** for authenticated encryption (via libp2p-noise)
//! - **QUIC** as primary transport (UDP, 0-RTT, multiplexing)
//! - **libp2p** for peer discovery (mDNS + Kademlia), gossip and request-response
//!
//! Design goals:
//! - No external daemons (no Yggdrasil, no Tor, no Docker required)
//! - Pure userspace — runs with normal user privileges
//! - Strong identity (Ed25519) and end-to-end encryption by default
//! - Easy integration with Nexus agent swarms (Lyra / Xen / Elara) and QNET
//! - Future-proof for post-quantum hybrid upgrades (Kyber already in ecosystem)

pub mod identity;
pub mod node;
pub mod protocol;

pub use identity::NodeIdentity;
pub use node::{NxMeshNode, NodeConfig};
pub use protocol::{MeshMessage, MeshEvent};

/// Crate version
pub const VERSION: &str = env!("CARGO_PKG_VERSION");
