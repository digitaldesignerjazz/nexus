//! Node identity management for nxmesh.
//!
//! Each Nexus node has a long-term Ed25519 keypair that is used both
//! for libp2p PeerId and for Noise handshake authentication.

use anyhow::{Context, Result};
use libp2p::identity::{Keypair, PublicKey};
use libp2p::PeerId;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

/// Persistent node identity
#[derive(Clone)]
pub struct NodeIdentity {
    keypair: Keypair,
    peer_id: PeerId,
}

impl NodeIdentity {
    /// Generate a fresh random identity
    pub fn generate() -> Self {
        let keypair = Keypair::generate_ed25519();
        let peer_id = PeerId::from(keypair.public());
        Self { keypair, peer_id }
    }

    /// Load identity from a file (or generate + save if missing)
    pub fn load_or_generate(path: impl AsRef<Path>) -> Result<Self> {
        let path = path.as_ref();
        if path.exists() {
            let data = fs::read(path).context("failed to read identity file")?;
            let keypair = Keypair::from_protobuf_encoding(&data)
                .context("invalid identity key encoding")?;
            let peer_id = PeerId::from(keypair.public());
            Ok(Self { keypair, peer_id })
        } else {
            let id = Self::generate();
            if let Some(parent) = path.parent() {
                fs::create_dir_all(parent).ok();
            }
            let encoded = id.keypair.to_protobuf_encoding()
                .context("failed to encode keypair")?;
            fs::write(path, encoded).context("failed to write identity file")?;
            tracing::info!("Generated new node identity → {}", id.peer_id);
            Ok(id)
        }
    }

    pub fn peer_id(&self) -> PeerId {
        self.peer_id
    }

    pub fn keypair(&self) -> &Keypair {
        &self.keypair
    }

    pub fn public_key(&self) -> PublicKey {
        self.keypair.public()
    }

    /// Short hex representation of PeerId (for logs)
    pub fn short_id(&self) -> String {
        let s = self.peer_id.to_string();
        if s.len() > 12 {
            format!("{}…{}", &s[..6], &s[s.len()-4..])
        } else {
            s
        }
    }
}

/// Serializable public view of a peer (for gossip / discovery)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PeerInfo {
    pub peer_id: String,
    pub multiaddrs: Vec<String>,
    pub agent_version: String,
    pub last_seen: i64,
}
