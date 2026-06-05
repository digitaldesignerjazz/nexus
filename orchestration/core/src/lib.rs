pub mod event_bus;
pub mod workflow_engine;
pub mod nexuslink;

// Re-exports for convenience
pub use event_bus::EventBus;
pub use workflow_engine::WorkflowEngine;
pub use nexuslink::{NexusLinkEnvelope, MessageCategory};

/// Initialize tracing subscriber for the orchestrator.
pub fn init_tracing() {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();
}
