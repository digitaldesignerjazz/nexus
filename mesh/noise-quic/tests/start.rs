//! Smoke test: a node starts, persists its identity and keeps the same PeerId.

use nxmesh::{MeshMessage, NodeConfig, NxMeshNode};

#[tokio::test]
async fn node_starts_and_identity_persists() {
    let dir = std::env::temp_dir().join(format!("nxmesh-test-{}", rand::random::<u32>()));
    let key = dir.join("id.key").to_string_lossy().to_string();
    let cfg = NodeConfig {
        identity_path: key.clone(),
        listen_addrs: vec!["/ip4/127.0.0.1/tcp/0".into()],
        enable_mdns: false,
        ..Default::default()
    };
    let (a, _rx) = NxMeshNode::start(cfg.clone()).await.expect("start");
    let first = a.peer_id();
    drop(a);
    let (b, _rx) = NxMeshNode::start(cfg).await.expect("restart");
    assert_eq!(first, b.peer_id());
    let _ = std::fs::remove_dir_all(dir);
}

#[test]
fn heartbeat_is_tagged_json() {
    let m = MeshMessage::AgentHeartbeat {
        agent: "onyx-node".into(),
        node_id: "n1".into(),
        status: "alive".into(),
        ts: chrono::Utc::now(),
        extra: None,
    };
    let v = serde_json::to_value(&m).unwrap();
    assert_eq!(v["type"], "AgentHeartbeat");
    assert_eq!(v["payload"]["node_id"], "n1");
}
