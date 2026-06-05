use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

/// Core NexusLink envelope (v0.1 aligned)
/// See interfaces/NexusLink-v0.1.md for full specification.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NexusLinkEnvelope {
    pub nexuslink_version: String,
    pub message_id: Uuid,
    pub timestamp: DateTime<Utc>,
    pub source: EntityRef,
    pub target: EntityRef,
    pub correlation_id: Option<Uuid>,
    pub trace_id: Option<String>,
    pub payload: serde_json::Value, // flexible for now; later strong typing per category
    pub metadata: MessageMetadata,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EntityRef {
    pub r#type: String, // mesh_node | agent_swarm | hardware_device | orchestrator_instance | human_interface
    pub id: String,
    pub capabilities: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageMetadata {
    pub priority: Priority,
    pub ttl_seconds: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Priority {
    High,
    Normal,
    Low,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum MessageCategory {
    Event,
    Command,
    Query,
    Response,
    Proposal,
}

impl NexusLinkEnvelope {
    pub fn new(source: EntityRef, target: EntityRef, payload: serde_json::Value) -> Self {
        Self {
            nexuslink_version: "0.1".to_string(),
            message_id: Uuid::new_v4(),
            timestamp: Utc::now(),
            source,
            target,
            correlation_id: None,
            trace_id: None,
            payload,
            metadata: MessageMetadata {
                priority: Priority::Normal,
                ttl_seconds: 300,
            },
        }
    }
}
