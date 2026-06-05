use tokio::sync::broadcast;
use tracing::{info, warn};
use std::collections::HashMap;

use crate::nexuslink::{NexusLinkEnvelope, MessageCategory};

/// Simple in-memory async EventBus for Phase 1.
/// Topics are strings; later can be hierarchical or NexusLink-aware.
/// Supports multiple subscribers per topic with backpressure via broadcast.
pub struct EventBus {
    senders: HashMap<String, broadcast::Sender<NexusLinkEnvelope>>,
}

impl EventBus {
    pub fn new() -> Self {
        Self {
            senders: HashMap::new(),
        }
    }

    /// Subscribe to a topic. Returns a receiver.
    pub fn subscribe(&mut self, topic: &str) -> broadcast::Receiver<NexusLinkEnvelope> {
        let sender = self.senders
            .entry(topic.to_string())
            .or_insert_with(|| {
                let (tx, _) = broadcast::channel(1024); // capacity
                tx
            });
        sender.subscribe()
    }

    /// Publish an envelope to a topic.
    pub fn publish(&self, topic: &str, envelope: NexusLinkEnvelope) {
        if let Some(sender) = self.senders.get(topic) {
            if let Err(e) = sender.send(envelope) {
                warn!("Failed to publish to topic {}: {}", topic, e);
            } else {
                info!("Published message to topic: {}", topic);
            }
        } else {
            warn!("No subscribers for topic: {} (message dropped)", topic);
        }
    }
}

// Example usage in tests or main:
// let mut bus = EventBus::new();
// let mut rx = bus.subscribe("mesh.events");
// bus.publish("mesh.events", some_envelope);
