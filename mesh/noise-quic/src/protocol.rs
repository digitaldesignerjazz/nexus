//! High-level mesh protocol messages and events for Nexus.

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

/// Messages that travel across the Nexus mesh
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", content = "payload")]
pub enum MeshMessage {
    /// Simple text / status broadcast
    Gossip {
        from: String,
        text: String,
        ts: DateTime<Utc>,
    },

    /// Agent swarm heartbeat / presence
    AgentHeartbeat {
        agent: String,          // "lyra" | "xen" | "elara" | custom
        node_id: String,
        status: String,
        ts: DateTime<Utc>,
    },

    /// Request / response for future QNET / rune / oracle data
    DataRequest {
        id: String,
        topic: String,
        query: serde_json::Value,
    },

    DataResponse {
        id: String,
        data: serde_json::Value,
    },

    /// Peer introduction (used during bootstrap)
    PeerIntro {
        peer_id: String,
        addrs: Vec<String>,
    },
}

/// Events emitted by the mesh node to the application / swarm layer
#[derive(Debug, Clone)]
pub enum MeshEvent {
    PeerDiscovered {
        peer_id: String,
        addresses: Vec<String>,
    },
    PeerConnected {
        peer_id: String,
    },
    PeerDisconnected {
        peer_id: String,
    },
    MessageReceived {
        from: String,
        message: MeshMessage,
    },
    GossipReceived {
        from: String,
        text: String,
    },
}
