//! Core nxmesh node implementation using libp2p (Noise + QUIC).

use crate::identity::NodeIdentity;
use crate::protocol::{MeshEvent, MeshMessage};
use anyhow::Result;
use futures::StreamExt;
use libp2p::{
    gossipsub, identify, kad, mdns, noise, ping, quic, swarm::NetworkBehaviour,
    swarm::SwarmEvent, tcp, yamux, Multiaddr, PeerId, Swarm, SwarmBuilder,
};
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::time::Duration;
use tokio::sync::mpsc;
use tracing::{info, warn, debug};

/// Configuration for a Nexus Mesh node
#[derive(Debug, Clone)]
pub struct NodeConfig {
    /// Path to identity key file (created if missing)
    pub identity_path: String,
    /// Listen addresses (default: QUIC on random high port + TCP fallback)
    pub listen_addrs: Vec<String>,
    /// Bootstrap peers (multiaddrs)
    pub bootstrap: Vec<String>,
    /// Enable mDNS for local discovery
    pub enable_mdns: bool,
    /// Gossipsub topic for Nexus mesh
    pub mesh_topic: String,
}

impl Default for NodeConfig {
    fn default() -> Self {
        Self {
            identity_path: "nexus-identity.key".into(),
            listen_addrs: vec![
                "/ip4/0.0.0.0/udp/0/quic-v1".into(),
                "/ip4/0.0.0.0/tcp/0".into(),
            ],
            bootstrap: vec![],
            enable_mdns: true,
            mesh_topic: "nexus/mesh/v0".into(),
        }
    }
}

/// Combined network behaviour
#[derive(NetworkBehaviour)]
struct NxBehaviour {
    gossipsub: gossipsub::Behaviour,
    kademlia: kad::Behaviour<kad::store::MemoryStore>,
    mdns: mdns::tokio::Behaviour,
    identify: identify::Behaviour,
    ping: ping::Behaviour,
}

/// The main Nexus Mesh node
pub struct NxMeshNode {
    swarm: Swarm<NxBehaviour>,
    identity: NodeIdentity,
    topic: gossipsub::IdentTopic,
    event_tx: mpsc::UnboundedSender<MeshEvent>,
}

impl NxMeshNode {
    /// Create and start a new mesh node.
    /// Returns the node + a receiver for mesh events.
    pub async fn start(config: NodeConfig) -> Result<(Self, mpsc::UnboundedReceiver<MeshEvent>)> {
        let identity = NodeIdentity::load_or_generate(&config.identity_path)?;
        let peer_id = identity.peer_id();

        info!("nxmesh node starting — PeerId: {}", peer_id);
        info!("short id: {}", identity.short_id());

        // Gossipsub setup
        let message_id_fn = |message: &gossipsub::Message| {
            let mut s = DefaultHasher::new();
            message.data.hash(&mut s);
            gossipsub::MessageId::from(s.finish().to_string())
        };

        let gossipsub_config = gossipsub::ConfigBuilder::default()
            .heartbeat_interval(Duration::from_secs(10))
            .validation_mode(gossipsub::ValidationMode::Strict)
            .message_id_fn(message_id_fn)
            .build()
            .expect("valid gossipsub config");

        let mut gossipsub = gossipsub::Behaviour::new(
            gossipsub::MessageAuthenticity::Signed(identity.keypair().clone()),
            gossipsub_config,
        )?;

        let topic = gossipsub::IdentTopic::new(config.mesh_topic.clone());
        gossipsub.subscribe(&topic)?;

        // Kademlia
        let store = kad::store::MemoryStore::new(peer_id);
        let mut kademlia = kad::Behaviour::new(peer_id, store);
        kademlia.set_mode(Some(kad::Mode::Server));

        // mDNS
        let mdns = mdns::tokio::Behaviour::new(mdns::Config::default(), peer_id)?;

        let identify = identify::Behaviour::new(identify::Config::new(
            "/nexus/nxmesh/0.1.0".into(),
            identity.public_key(),
        ));

        let behaviour = NxBehaviour {
            gossipsub,
            kademlia,
            mdns,
            identify,
            ping: ping::Behaviour::new(ping::Config::new()),
        };

        let mut swarm = SwarmBuilder::with_existing_identity(identity.keypair().clone())
            .with_tokio()
            .with_tcp(
                tcp::Config::default(),
                noise::Config::new,
                yamux::Config::default,
            )?
            .with_quic()
            .with_dns()?
            .with_behaviour(|_| behaviour)?
            .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
            .build();

        // Listen
        for addr_str in &config.listen_addrs {
            let addr: Multiaddr = addr_str.parse()?;
            swarm.listen_on(addr)?;
        }

        // Bootstrap peers
        for boot in &config.bootstrap {
            let addr: Multiaddr = boot.parse()?;
            swarm.behaviour_mut().kademlia.add_address(
                &extract_peer_id(&addr).unwrap_or(PeerId::random()),
                addr.clone(),
            );
            let _ = swarm.dial(addr);
        }

        let (event_tx, event_rx) = mpsc::unbounded_channel();

        let node = Self {
            swarm,
            identity,
            topic,
            event_tx,
        };

        Ok((node, event_rx))
    }

    pub fn peer_id(&self) -> PeerId {
        self.identity.peer_id()
    }

    pub fn short_id(&self) -> String {
        self.identity.short_id()
    }

    /// Publish a MeshMessage to the mesh gossip topic
    pub fn publish(&mut self, msg: MeshMessage) -> Result<()> {
        let data = serde_json::to_vec(&msg)?;
        self.swarm
            .behaviour_mut()
            .gossipsub
            .publish(self.topic.clone(), data)?;
        Ok(())
    }

    /// Convenience: publish a simple gossip text
    pub fn gossip(&mut self, text: impl Into<String>) -> Result<()> {
        let msg = MeshMessage::Gossip {
            from: self.identity.peer_id().to_string(),
            text: text.into(),
            ts: chrono::Utc::now(),
        };
        self.publish(msg)
    }

    /// Main event loop — call this in a tokio task
    pub async fn run(mut self) {
        loop {
            match self.swarm.select_next_some().await {
                SwarmEvent::NewListenAddr { address, .. } => {
                    info!("Listening on {}", address);
                }
                SwarmEvent::Behaviour(NxBehaviourEvent::Mdns(mdns::Event::Discovered(list))) => {
                    for (peer, addr) in list {
                        debug!("mDNS discovered {} at {}", peer, addr);
                        self.swarm.behaviour_mut().kademlia.add_address(&peer, addr.clone());
                        let _ = self.event_tx.send(MeshEvent::PeerDiscovered {
                            peer_id: peer.to_string(),
                            addresses: vec![addr.to_string()],
                        });
                    }
                }
                SwarmEvent::Behaviour(NxBehaviourEvent::Gossipsub(gossipsub::Event::Message {
                    propagation_source,
                    message,
                    ..
                })) => {
                    if let Ok(msg) = serde_json::from_slice::<MeshMessage>(&message.data) {
                        let _ = self.event_tx.send(MeshEvent::MessageReceived {
                            from: propagation_source.to_string(),
                            message: msg.clone(),
                        });
                        if let MeshMessage::Gossip { text, .. } = &msg {
                            let _ = self.event_tx.send(MeshEvent::GossipReceived {
                                from: propagation_source.to_string(),
                                text: text.clone(),
                            });
                        }
                    }
                }
                SwarmEvent::ConnectionEstablished { peer_id, .. } => {
                    info!("Connected to {}", peer_id);
                    let _ = self.event_tx.send(MeshEvent::PeerConnected {
                        peer_id: peer_id.to_string(),
                    });
                }
                SwarmEvent::ConnectionClosed { peer_id, .. } => {
                    info!("Disconnected from {}", peer_id);
                    let _ = self.event_tx.send(MeshEvent::PeerDisconnected {
                        peer_id: peer_id.to_string(),
                    });
                }
                SwarmEvent::OutgoingConnectionError { peer_id, error, .. } => {
                    warn!("Outgoing connection error to {:?}: {}", peer_id, error);
                }
                _ => {}
            }
        }
    }
}

fn extract_peer_id(addr: &Multiaddr) -> Option<PeerId> {
    use libp2p::multiaddr::Protocol;
    for proto in addr.iter() {
        if let Protocol::P2p(peer) = proto {
            return Some(peer);
        }
    }
    None
}
