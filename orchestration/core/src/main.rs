use clap::Parser;
use tracing::info;

use nexus_orchestrator::{init_tracing, EventBus, WorkflowEngine, NexusLinkEnvelope, EntityRef};

#[derive(Parser, Debug)]
#[command(author, version, about = "Nexus Central Orchestration Hub — Phase 1 Core")]
struct Args {
    /// Demo workflow to run
    #[arg(short, long, default_value = "mesh_congestion_optimization")]
    workflow: String,
}

#[tokio::main]
async fn main() {
    init_tracing();
    let args = Args::parse();

    info!("Starting Nexus Orchestrator Core (Phase 1)");

    let mut bus = EventBus::new();
    let engine = WorkflowEngine::new();

    // Demo: create a sample envelope (simulating a mesh event)
    let sample_source = EntityRef {
        r#type: "mesh_node".to_string(),
        id: "ygg-hannover-01".to_string(),
        capabilities: vec!["relay".to_string(), "high_bandwidth".to_string()],
    };
    let sample_target = EntityRef {
        r#type: "orchestrator".to_string(),
        id: "main".to_string(),
        capabilities: vec![],
    };
    let demo_payload = serde_json::json!({
        "event_type": "MeshCongestionDetected",
        "severity": "medium",
        "affected_links": 12
    });
    let envelope = NexusLinkEnvelope::new(sample_source, sample_target, demo_payload);

    // Publish demo event
    bus.publish("mesh.events", envelope);

    // Execute example workflow (stub)
    engine.execute(&args.workflow, &mut bus, None).await;

    info!("Phase 1 demo completed. Ready for expansion.");
}
