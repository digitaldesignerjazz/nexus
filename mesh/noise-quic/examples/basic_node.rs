//! Minimal nxmesh node example.
//!
//! Run with:
//!   cargo run --example basic_node
//!
//! Two nodes on the same LAN will discover each other via mDNS
//! and can exchange gossip messages.

use anyhow::Result;
use nxmesh::{NodeConfig, NxMeshNode, MeshEvent};
use tracing_subscriber::EnvFilter;

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env().add_directive("nxmesh=info".parse()?))
        .init();

    let config = NodeConfig {
        identity_path: "data/node-identity.key".into(),
        enable_mdns: true,
        ..Default::default()
    };

    let (mut node, mut events) = NxMeshNode::start(config).await?;
    println!("nxmesh node online — {}", node.short_id());

    // Spawn the event loop
    let node_handle = tokio::spawn(async move {
        node.run().await;
    });

    // Simple event printer + periodic gossip
    let mut interval = tokio::time::interval(std::time::Duration::from_secs(15));

    loop {
        tokio::select! {
            Some(ev) = events.recv() => {
                match ev {
                    MeshEvent::PeerDiscovered { peer_id, addresses } => {
                        println!("Discovered peer {} at {:?}", &peer_id[..12.min(peer_id.len())], addresses);
                    }
                    MeshEvent::PeerConnected { peer_id } => {
                        println!("Connected → {}", &peer_id[..12.min(peer_id.len())]);
                    }
                    MeshEvent::GossipReceived { from, text } => {
                        println!("Gossip from {}: {}", &from[..12.min(from.len())], text);
                    }
                    MeshEvent::MessageReceived { from, message } => {
                        println!("Message from {}: {:?}", &from[..12.min(from.len())], message);
                    }
                    _ => {}
                }
            }
            _ = interval.tick() => {
                // In a real integration the swarm agents would publish here
                // For demo we just keep the node alive
            }
        }
    }
}
