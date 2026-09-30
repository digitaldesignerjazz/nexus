#!/usr/bin/env python3
"""Nexus Control Plane — lightweight HTTP orchestrator for the Hannover node."""
from __future__ import annotations

import json
import subprocess
import os
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

try:
    import vip_payment_messages as _vip_msg
except Exception:  # pragma: no cover
    _vip_msg = None  # type: ignore

try:
    import qmainnet_marketplace as _mkt
except Exception:  # pragma: no cover
    _mkt = None  # type: ignore

try:
    import qmainnet_forum as _forum
except Exception:  # pragma: no cover
    _forum = None  # type: ignore

from urllib.parse import urlparse
import urllib.request
import urllib.error

STARTED = time.time()
NODE_NAME = os.environ.get("NEXUS_NODE_NAME", "hannover-primary")
BIND = os.environ.get("NEXUS_BIND", "127.0.0.1")
PORT = int(os.environ.get("NEXUS_PORT", "8787"))
OWNER = os.environ.get("NEXUS_OWNER", "Sir Sven Normen Eßlinger")
SITE = os.environ.get("NEXUS_SITE", "Hannover")
ENV = os.environ.get("NEXUS_ENV", "development")
HERE = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("NEXUS_DATA_DIR", HERE / "data")).resolve()
LOG_DIR = Path(os.environ.get("NEXUS_LOG_DIR", HERE / "logs")).resolve()
SWARM_SIZE = int(os.environ.get("NEXUS_SWARM_SIZE", "5"))
MESH_PEERS = int(os.environ.get("NEXUS_MESH_PEERS", "12"))

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "nexus-control.log"
STATE_FILE = DATA_DIR / "state.json"
LOCK = threading.Lock()

STATE: dict[str, Any] = {
    "node": NODE_NAME,
    "owner": OWNER,
    "site": SITE,
    "env": ENV,
    "status": "INITIALIZING",
    "started_at": datetime.now(timezone.utc).isoformat(),
    "layers": {
        "control": {"status": "INITIALIZING"},
        "mesh": {"status": "STANDBY", "peers": 0},
        "blockchain": {"status": "STANDBY", "height": 0},
        "swarm": {"status": "STANDBY", "agents": 0},
        "prototypes": {"status": "STANDBY"},
    },
    "events": [],
    "metrics": {"events": 0, "requests": 0},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(level: str, message: str) -> None:
    line = f"{utc_now()} [{level}] {message}"
    print(line, flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def persist() -> None:
    payload = dict(STATE)
    payload["events"] = STATE["events"][-50:]
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(STATE_FILE)
    except OSError as exc:
        log("WARN", f"state persist skipped: {exc}")


def emit(event_type: str, payload: dict[str, Any] | None = None) -> None:
    event = {"ts": utc_now(), "type": event_type, "payload": payload or {}}
    STATE["events"].append(event)
    STATE["events"] = STATE["events"][-200:]
    STATE["metrics"]["events"] += 1
    log("EVENT", f"{event_type} {payload or {}}")
    if event_type in {"NEXUS_ONLINE", "MESH_EXPAND", "SWARM_EXPAND", "NEXUS_STOP"}:
        persist()


PROTOTYPES_DIR = Path(os.environ.get("PROTOTYPES_DIR", "/workspace/lumina-state/prototypes"))


def prototype_real_status(name: str) -> dict[str, Any] | None:
    """Real start time/pid from the prototype's own status file, if its process is alive."""
    slug = name.lower().replace(" ", "-")
    try:
        cur = json.loads((PROTOTYPES_DIR / f"{slug}.status.json").read_text(encoding="utf-8"))
        pid = int(cur.get("pid") or 0)
        if pid <= 0 or not Path(f"/proc/{pid}").exists() or not cur.get("started_at"):
            return None
        out = {"started_at": cur["started_at"], "pid": pid, "source": f"{slug}.status.json"}
        if cur.get("controlled_by"):
            out["controlled_by"] = cur["controlled_by"]
        return out
    except Exception:
        return None


def boot() -> None:
    log("INFO", f"Boot {NODE_NAME} · {SITE} · {OWNER}")
    sequence = [
        ("control", "OPERATIONAL", {}),
        ("mesh", "STANDBY", {"peers": 0, "note": "Yggdrasil host-side"}),
        ("blockchain", "STANDBY", {"height": 0, "note": "QCoin/XCoin; active production=qmainnet", "active_network": "qmainnet"}),
        ("swarm", "STANDBY", {"agents": 0}),
        ("prototypes", "STANDBY", {"note": "Soilnova / Vista Nova / Lumia"}),
    ]
    for layer, status, extra in sequence:
        STATE["layers"][layer]["status"] = status
        STATE["layers"][layer].update(extra)
        emit("LAYER_READY", {"layer": layer, "status": status})
    STATE["status"] = "OPERATIONAL"
    emit("NEXUS_ONLINE", {"bind": f"{BIND}:{PORT}"})


def snapshot() -> dict[str, Any]:
    return {
        **STATE,
        "uptime_s": int(time.time() - STARTED),
        "listen": f"{BIND}:{PORT}",
        "events": STATE["events"][-20:],
    }



def cyberspace_pkg_root() -> Path | None:
    """Locate server-setup/lumina next to this control plane, if present."""
    env = os.environ.get("LUMINA_SETUP_ROOT", "").strip()
    if env:
        p = Path(env).expanduser().resolve()
        if (p / "scripts" / "03-start-cyberspace.sh").is_file():
            return p
    candidate = HERE / "lumina"
    if (candidate / "scripts" / "03-start-cyberspace.sh").is_file():
        return candidate.resolve()
    return None


def cyberspace_status_payload() -> dict[str, Any]:
    root = cyberspace_pkg_root()
    if root is None:
        return {"available": False, "reason": "lumina_package_missing"}
    status_dir = root / "runtime" / "status"
    files: dict[str, str] = {}
    if status_dir.is_dir():
        for p in sorted(status_dir.glob("*.status")):
            try:
                files[p.name] = p.read_text(encoding="utf-8")[:2000]
            except OSError:
                files[p.name] = "<unreadable>"
    orch_alive = False
    try:
        orch_alive = (
            subprocess.run(
                ["pgrep", "-f", "nexus_orchestrator.py"],
                check=False,
                capture_output=True,
            ).returncode
            == 0
        )
    except OSError:
        orch_alive = False
    return {
        "available": True,
        "package": str(root),
        "version": (root / "VERSION").read_text(encoding="utf-8").strip()
        if (root / "VERSION").is_file()
        else None,
        "orchestrator_alive": orch_alive,
        "status_files": files,
        "note": "Control plane does not own the process tree; scripts under lumina/ do.",
    }


def cyberspace_start() -> dict[str, Any]:
    """Thin hook: spawn scripts/03-start-cyberspace.sh in background if present."""
    root = cyberspace_pkg_root()
    if root is None:
        return {"ok": False, "error": "lumina_package_missing", "hint": "Install server-setup/lumina"}
    script = root / "scripts" / "03-start-cyberspace.sh"
    log_dir = root / "runtime" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "control-plane-start.log"
    try:
        with log_file.open("a", encoding="utf-8") as fh:
            fh.write(f"\n--- control-plane trigger {utc_now()} ---\n")
            proc = subprocess.Popen(  # noqa: S603
                ["bash", str(script)],
                cwd=str(root),
                stdout=fh,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        emit("CYBERSPACE_START", {"pid": proc.pid, "script": str(script)})
        STATE["layers"].setdefault("prototypes", {})
        STATE["layers"]["prototypes"].update(
            {"status": "STARTING", "cyberspace_pid": proc.pid}
        )
        return {
            "ok": True,
            "pid": proc.pid,
            "script": str(script),
            "log": str(log_file),
            "note": "Spawned start script; poll GET /cyberspace/status",
        }
    except OSError as exc:
        return {"ok": False, "error": str(exc)}



def ygg_peer_snapshot() -> dict[str, Any]:
    """Live Yggdrasil peer list via yggdrasilctl -json getPeers."""
    try:
        raw = subprocess.check_output(
            ["yggdrasilctl", "-json", "getPeers"],
            text=True,
            timeout=5,
        )
        data = json.loads(raw)
        peers = data.get("peers", []) if isinstance(data, dict) else []
        up = [p for p in peers if p.get("up")]
        return {
            "peers": len(peers),
            "peers_up": len(up),
            "peer_list": [
                {
                    "remote": p.get("remote"),
                    "address": p.get("address"),
                    "inbound": p.get("inbound"),
                    "uptime_s": round(float(p.get("uptime") or 0), 1),
                    "latency_ms": round((p.get("latency") or 0) / 1e6, 2),
                }
                for p in up
            ],
        }
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, ValueError) as exc:
        return {"peers": 0, "peers_up": 0, "peer_list": [], "error": str(exc)}


# Named QNet-style local ledgers (Hannover control plane)
# Canonical production network: qmainnet (local XCoin). Solana Mainnet is NOT active.
NETWORK_DEFS: dict[str, dict[str, Any]] = {
    "legacy": {
        "file": "qcoin_xcoin_chain.json",
        "chain_id": "qcoin-xcoin-hannover-local",
        "genesis_hash": "0xgenesis_qcoin_xcoin_hannover",
        "label": "Hannover legacy local (NON-PRODUCTION archive)",
        "role": "archive",
    },
    "qmainnet": {
        "file": "networks/qmainnet_chain.json",
        "chain_id": "qcoin-xcoin-qmainnet",
        "genesis_hash": "0xgenesis_qmainnet",
        "label": "QNet mainnet (local XCoin) — ACTIVE PRODUCTION",
        "role": "production",
    },
    "qdevnet": {
        "file": "networks/qdevnet_chain.json",
        "chain_id": "qcoin-xcoin-qdevnet",
        "genesis_hash": "0xgenesis_qdevnet",
        "label": "QNet devnet (local XCoin)",
        "role": "dev",
    },
    "qtestnet": {
        "file": "networks/qtestnet_chain.json",
        "chain_id": "qcoin-xcoin-qtestnet",
        "genesis_hash": "0xgenesis_qtestnet",
        "label": "QNet testnet (local XCoin)",
        "role": "test",
    },
}
INCINERATOR_IDS = {"1nc1nerator", "burn", "1nc1nerator11111111111111111111111111111111"}

# Sole active production default — not Solana, not legacy.
DEFAULT_NETWORK = "qmainnet"
ACTIVE_PRODUCTION_NETWORK = "qmainnet"

# Perpetual XCoin tokenomics (no hard cap, no end date). Spec: docs/xcoin-tokenomics.md
# Emission asymptotes to a positive floor; burns track usage; governance can retune.
TOKENOMICS_BY_NETWORK: dict[str, dict[str, Any]] = {
    "qmainnet": {
        "asset": "XCoin",
        "model": "perpetual_emission_usage_burn",
        "hard_cap": None,
        "end_date": None,
        "indefinite": True,
        "initial_supply": 1000.0,
        "genesis_allocation": {
            "hannover-primary": {
                "amount": 1000.0,
                "role": "treasury_seed",
                "note": "Genesis seed — treasury / operator bootstrap (ledger account)"
            }
        },
        "reserve_allocation_pct": {
            "treasury": 45.0,
            "node_operators": 35.0,
            "swarm_rewards": 20.0,
            "governance_community": 0.0,
        },
        "emission": {
            "unit": "XCoin_per_day",
            "initial_rate": 5.0,
            "floor_rate": 1.0,
            "half_life_days": 365,
            "note": "FINAL LOCKED — initial 5 XCoin/day, floor 1 (hard safety anchor, never zero), half-life 365d; rate(t)=floor+(initial-floor)*0.5^(t/half_life)",
            "split_pct": {
                "treasury": 45.0,
                "node_operators": 35.0,
                "swarm_rewards": 20.0,
                "governance_community": 0.0,
            }
        },
        "burn": {
            "activation_base_xcoin": 1.0,
            "activation_min_xcoin": 0.1,
            "activation_dynamic": "price = max(1.0 - floor(burn_pct_of_circulating/10)*0.1, 0.1)",
            "transfer_fee_burn_bps": 15,
            "activation_burn_bps": 15,
            "note": "FINAL LOCKED — activation/usage burn 15 bps (0.15%); activation base 1.0 XCoin / min 0.1; staking disabled; indefinite runtime."
        },
        "staking": {
            "enabled": False,
            "rewards": None,
            "apy": None,
            "note": "Staking rewards fully removed — no APY, no staking emissions, no pool rewards."
        },
        "governance": {
            "type": "7_member_multisig_council",
            "members": 7,
            "threshold": "simple_majority_4_of_7",
            "tie_break": "chair_casting_vote",
            "voting_rule": "Each member 1 equal vote; Sven has casting vote on ties",
            "seats": [
                {
                    "seat": 0,
                    "name": "Sven Normen Eßlinger",
                    "role": "chair",
                    "vote": "full",
                    "casting_vote": True,
                    "weight": 1,
                    "pubkey": "4JkK7b9rNaVQnrYXHfuRUEmWnSgoJ2poXuv4ztF2NGz4",
                    "derivation": "m/44'/501'/0'/0'",
                    "account": 0
                },
                {
                    "seat": 1,
                    "name": "Diana",
                    "role": "council",
                    "vote": "equal",
                    "casting_vote": False,
                    "weight": 1,
                    "pubkey": "4zXAN4fiXJEL8TxY2oTZS8r5hLMtydL1XpbuatDeuLut",
                    "derivation": "m/44'/501'/1'/0'",
                    "account": 1
                },
                {
                    "seat": 2,
                    "name": "Silvia",
                    "role": "council",
                    "vote": "equal",
                    "casting_vote": False,
                    "weight": 1,
                    "pubkey": "GeUAkDYxnyQWbPgyzTwg7fEMr8kxGAFDsLc86aVsuKon",
                    "derivation": "m/44'/501'/2'/0'",
                    "account": 2
                },
                {
                    "seat": 3,
                    "name": "Jana",
                    "role": "council",
                    "vote": "equal",
                    "casting_vote": False,
                    "weight": 1,
                    "pubkey": "EL5UdqzGWGKfhe83iNgprGeU9QG83KEFo1mNTh6TuGJM",
                    "derivation": "m/44'/501'/3'/0'",
                    "account": 3
                },
                {
                    "seat": 4,
                    "name": "Melanie",
                    "role": "council",
                    "vote": "equal",
                    "casting_vote": False,
                    "weight": 1,
                    "pubkey": "9hh9dH5E69NaYrPeT4NmvWcP5wtQpfd7Uhg3HSnf6bd3",
                    "derivation": "m/44'/501'/4'/0'",
                    "account": 4
                },
                {
                    "seat": 5,
                    "name": "Sandra",
                    "role": "council",
                    "vote": "equal",
                    "casting_vote": False,
                    "weight": 1,
                    "pubkey": "3br98DW2Bhpx5yBr52EV1Ywy12WsRRSE7TRfbRWwbfSv",
                    "derivation": "m/44'/501'/5'/0'",
                    "account": 5
                },
                {
                    "seat": 6,
                    "name": "Nina",
                    "role": "council",
                    "vote": "equal",
                    "casting_vote": False,
                    "weight": 1,
                    "pubkey": "9F3HXGt1z5hS5ZU9GRanvsS4mNRQeMy2todRirUuvyUT",
                    "derivation": "m/44'/501'/6'/0'",
                    "account": 6
                }
            ],
            "governance_ops_pubkey": "AkzCGMufpEwwxRRgnhKL6rTJgAnpGnABcgVSJq5CtB41",
            "migration_wallets": {
                "treasury": {
                    "pubkey": "88NM2KQTuAf4tnRa9vDqhhU8CaXvFovPUfSw8q7j81S2",
                    "derivation": "m/44'/501'/10'/0'"
                },
                "burn": {
                    "pubkey": "1nc1nerator",
                    "derivation": None
                },
                "governance": {
                    "pubkey": "AkzCGMufpEwwxRRgnhKL6rTJgAnpGnABcgVSJq5CtB41",
                    "derivation": "m/44'/501'/13'/0'"
                },
                "distribution": {
                    "pubkey": "AeGqAGNxp1yBpfuVy7nY9Lc2qfHY6yanyeNt6nTSPC1q",
                    "derivation": "m/44'/501'/11'/0'"
                },
                "reserves": {
                    "pubkey": "FXpm8G7xkcJuDfwagz1VBavKK272WnhpPbWF5z6YErvR",
                    "derivation": "m/44'/501'/12'/0'"
                }
            },
            "parameter_bounds": {
                "emission_floor_rate_min": 0.1,
                "emission_floor_rate_max": 50.0,
                "transfer_fee_burn_bps_min": 1,
                "transfer_fee_burn_bps_max": 100
            },
            "note": "Council may adjust emission/burn within bounds indefinitely. Staking rewards permanently disabled."
        },
        "wallets": {
            "treasury": "88NM2KQTuAf4tnRa9vDqhhU8CaXvFovPUfSw8q7j81S2",
            "burn": "1nc1nerator",
            "governance": "AkzCGMufpEwwxRRgnhKL6rTJgAnpGnABcgVSJq5CtB41",
            "distribution": "AeGqAGNxp1yBpfuVy7nY9Lc2qfHY6yanyeNt6nTSPC1q",
            "reserves": "FXpm8G7xkcJuDfwagz1VBavKK272WnhpPbWF5z6YErvR",
            "founder_activation": "4JkK7b9rNaVQnrYXHfuRUEmWnSgoJ2poXuv4ztF2NGz4"
        },
        "version": "1.2.0-infinite-runtime",
        "spec": "docs/xcoin-tokenomics.md"
    },
    "qdevnet": {
        "asset": "XCoin",
        "model": "perpetual_emission_usage_burn",
        "hard_cap": None,
        "end_date": None,
        "indefinite": True,
        "initial_supply": 1000.0,
        "genesis_allocation": {
            "hannover-primary": {
                "amount": 1000.0,
                "role": "treasury_seed",
                "note": "Genesis seed — treasury / operator bootstrap (ledger account)"
            }
        },
        "reserve_allocation_pct": {
            "treasury": 45.0,
            "node_operators": 35.0,
            "swarm_rewards": 20.0,
            "governance_community": 0.0,
        },
        "emission": {
            "unit": "XCoin_per_day",
            "initial_rate": 100.0,
            "floor_rate": 10.0,
            "half_life_days": 30,
            "note": "qdevnet perpetual floor (accelerated vs qmainnet)",
            "split_pct": {
                "treasury": 45.0,
                "node_operators": 35.0,
                "swarm_rewards": 20.0,
                "governance_community": 0.0,
            }
        },
        "burn": {
            "activation_base_xcoin": 0.1,
            "activation_min_xcoin": 0.01,
            "transfer_fee_burn_bps": 15,
            "note": "transfer fee burn bps identical to qmainnet final locked model (15)"
        },
        "staking": {
            "enabled": False,
            "rewards": None,
            "apy": None,
            "note": "Staking rewards fully removed — no APY, no staking emissions, no pool rewards."
        },
        "governance": {
            "type": "7_member_multisig_council",
            "members": 7,
            "threshold": "simple_majority_4_of_7",
            "tie_break": "chair_casting_vote",
            "voting_rule": "Each member 1 equal vote; Sven has casting vote on ties",
            "seats": [
                {
                    "seat": 0,
                    "name": "Sven Normen Eßlinger",
                    "role": "chair",
                    "vote": "full",
                    "casting_vote": True,
                    "weight": 1,
                    "pubkey": "4JkK7b9rNaVQnrYXHfuRUEmWnSgoJ2poXuv4ztF2NGz4",
                    "derivation": "m/44'/501'/0'/0'",
                    "account": 0
                },
                {
                    "seat": 1,
                    "name": "Diana",
                    "role": "council",
                    "vote": "equal",
                    "casting_vote": False,
                    "weight": 1,
                    "pubkey": "4zXAN4fiXJEL8TxY2oTZS8r5hLMtydL1XpbuatDeuLut",
                    "derivation": "m/44'/501'/1'/0'",
                    "account": 1
                },
                {
                    "seat": 2,
                    "name": "Silvia",
                    "role": "council",
                    "vote": "equal",
                    "casting_vote": False,
                    "weight": 1,
                    "pubkey": "GeUAkDYxnyQWbPgyzTwg7fEMr8kxGAFDsLc86aVsuKon",
                    "derivation": "m/44'/501'/2'/0'",
                    "account": 2
                },
                {
                    "seat": 3,
                    "name": "Jana",
                    "role": "council",
                    "vote": "equal",
                    "casting_vote": False,
                    "weight": 1,
                    "pubkey": "EL5UdqzGWGKfhe83iNgprGeU9QG83KEFo1mNTh6TuGJM",
                    "derivation": "m/44'/501'/3'/0'",
                    "account": 3
                },
                {
                    "seat": 4,
                    "name": "Melanie",
                    "role": "council",
                    "vote": "equal",
                    "casting_vote": False,
                    "weight": 1,
                    "pubkey": "9hh9dH5E69NaYrPeT4NmvWcP5wtQpfd7Uhg3HSnf6bd3",
                    "derivation": "m/44'/501'/4'/0'",
                    "account": 4
                },
                {
                    "seat": 5,
                    "name": "Sandra",
                    "role": "council",
                    "vote": "equal",
                    "casting_vote": False,
                    "weight": 1,
                    "pubkey": "3br98DW2Bhpx5yBr52EV1Ywy12WsRRSE7TRfbRWwbfSv",
                    "derivation": "m/44'/501'/5'/0'",
                    "account": 5
                },
                {
                    "seat": 6,
                    "name": "Nina",
                    "role": "council",
                    "vote": "equal",
                    "casting_vote": False,
                    "weight": 1,
                    "pubkey": "9F3HXGt1z5hS5ZU9GRanvsS4mNRQeMy2todRirUuvyUT",
                    "derivation": "m/44'/501'/6'/0'",
                    "account": 6
                }
            ],
            "governance_ops_pubkey": "AkzCGMufpEwwxRRgnhKL6rTJgAnpGnABcgVSJq5CtB41",
            "migration_wallets": {
                "treasury": {
                    "pubkey": "88NM2KQTuAf4tnRa9vDqhhU8CaXvFovPUfSw8q7j81S2",
                    "derivation": "m/44'/501'/10'/0'"
                },
                "burn": {
                    "pubkey": "1nc1nerator",
                    "derivation": None
                },
                "governance": {
                    "pubkey": "AkzCGMufpEwwxRRgnhKL6rTJgAnpGnABcgVSJq5CtB41",
                    "derivation": "m/44'/501'/13'/0'"
                },
                "distribution": {
                    "pubkey": "AeGqAGNxp1yBpfuVy7nY9Lc2qfHY6yanyeNt6nTSPC1q",
                    "derivation": "m/44'/501'/11'/0'"
                },
                "reserves": {
                    "pubkey": "FXpm8G7xkcJuDfwagz1VBavKK272WnhpPbWF5z6YErvR",
                    "derivation": "m/44'/501'/12'/0'"
                }
            },
            "parameter_bounds": {
                "emission_floor_rate_min": 0.1,
                "emission_floor_rate_max": 50.0,
                "transfer_fee_burn_bps_min": 1,
                "transfer_fee_burn_bps_max": 100
            },
            "note": "Same council roster mirrored on qdevnet; production authority is qmainnet"
        },
        "wallets": {
            "treasury": "88NM2KQTuAf4tnRa9vDqhhU8CaXvFovPUfSw8q7j81S2",
            "burn": "1nc1nerator",
            "governance": "AkzCGMufpEwwxRRgnhKL6rTJgAnpGnABcgVSJq5CtB41",
            "distribution": "AeGqAGNxp1yBpfuVy7nY9Lc2qfHY6yanyeNt6nTSPC1q",
            "reserves": "FXpm8G7xkcJuDfwagz1VBavKK272WnhpPbWF5z6YErvR",
            "founder_activation": "4JkK7b9rNaVQnrYXHfuRUEmWnSgoJ2poXuv4ztF2NGz4"
        },
        "version": "1.1.0-perpetual-qdevnet-no-staking",
        "spec": "docs/xcoin-tokenomics.md"
    },
    "qtestnet": {
        "asset": "XCoin",
        "model": "perpetual_emission_usage_burn",
        "hard_cap": None,
        "end_date": None,
        "indefinite": True,
        "initial_supply": 1000.0,
        "genesis_allocation": {
            "hannover-primary": {
                "amount": 1000.0,
                "role": "treasury_seed",
                "note": "Genesis seed — treasury / operator bootstrap (ledger account)"
            }
        },
        "reserve_allocation_pct": {
            "treasury": 45.0,
            "node_operators": 35.0,
            "swarm_rewards": 20.0,
            "governance_community": 0.0,
        },
        "emission": {
            "unit": "XCoin_per_day",
            "initial_rate": 50.0,
            "floor_rate": 5.0,
            "half_life_days": 90,
            "note": "qtestnet perpetual floor (accelerated vs qmainnet)",
            "split_pct": {
                "treasury": 45.0,
                "node_operators": 35.0,
                "swarm_rewards": 20.0,
                "governance_community": 0.0,
            }
        },
        "burn": {
            "activation_base_xcoin": 0.5,
            "activation_min_xcoin": 0.05,
            "transfer_fee_burn_bps": 15,
            "note": "transfer fee burn bps identical to qmainnet final locked model (15)"
        },
        "staking": {
            "enabled": False,
            "rewards": None,
            "apy": None,
            "note": "Staking rewards fully removed — no APY, no staking emissions, no pool rewards."
        },
        "governance": {
            "type": "7_member_multisig_council",
            "members": 7,
            "threshold": "simple_majority_4_of_7",
            "tie_break": "chair_casting_vote",
            "voting_rule": "Each member 1 equal vote; Sven has casting vote on ties",
            "seats": [
                {
                    "seat": 0,
                    "name": "Sven Normen Eßlinger",
                    "role": "chair",
                    "vote": "full",
                    "casting_vote": True,
                    "weight": 1,
                    "pubkey": "4JkK7b9rNaVQnrYXHfuRUEmWnSgoJ2poXuv4ztF2NGz4",
                    "derivation": "m/44'/501'/0'/0'",
                    "account": 0
                },
                {
                    "seat": 1,
                    "name": "Diana",
                    "role": "council",
                    "vote": "equal",
                    "casting_vote": False,
                    "weight": 1,
                    "pubkey": "4zXAN4fiXJEL8TxY2oTZS8r5hLMtydL1XpbuatDeuLut",
                    "derivation": "m/44'/501'/1'/0'",
                    "account": 1
                },
                {
                    "seat": 2,
                    "name": "Silvia",
                    "role": "council",
                    "vote": "equal",
                    "casting_vote": False,
                    "weight": 1,
                    "pubkey": "GeUAkDYxnyQWbPgyzTwg7fEMr8kxGAFDsLc86aVsuKon",
                    "derivation": "m/44'/501'/2'/0'",
                    "account": 2
                },
                {
                    "seat": 3,
                    "name": "Jana",
                    "role": "council",
                    "vote": "equal",
                    "casting_vote": False,
                    "weight": 1,
                    "pubkey": "EL5UdqzGWGKfhe83iNgprGeU9QG83KEFo1mNTh6TuGJM",
                    "derivation": "m/44'/501'/3'/0'",
                    "account": 3
                },
                {
                    "seat": 4,
                    "name": "Melanie",
                    "role": "council",
                    "vote": "equal",
                    "casting_vote": False,
                    "weight": 1,
                    "pubkey": "9hh9dH5E69NaYrPeT4NmvWcP5wtQpfd7Uhg3HSnf6bd3",
                    "derivation": "m/44'/501'/4'/0'",
                    "account": 4
                },
                {
                    "seat": 5,
                    "name": "Sandra",
                    "role": "council",
                    "vote": "equal",
                    "casting_vote": False,
                    "weight": 1,
                    "pubkey": "3br98DW2Bhpx5yBr52EV1Ywy12WsRRSE7TRfbRWwbfSv",
                    "derivation": "m/44'/501'/5'/0'",
                    "account": 5
                },
                {
                    "seat": 6,
                    "name": "Nina",
                    "role": "council",
                    "vote": "equal",
                    "casting_vote": False,
                    "weight": 1,
                    "pubkey": "9F3HXGt1z5hS5ZU9GRanvsS4mNRQeMy2todRirUuvyUT",
                    "derivation": "m/44'/501'/6'/0'",
                    "account": 6
                }
            ],
            "governance_ops_pubkey": "AkzCGMufpEwwxRRgnhKL6rTJgAnpGnABcgVSJq5CtB41",
            "migration_wallets": {
                "treasury": {
                    "pubkey": "88NM2KQTuAf4tnRa9vDqhhU8CaXvFovPUfSw8q7j81S2",
                    "derivation": "m/44'/501'/10'/0'"
                },
                "burn": {
                    "pubkey": "1nc1nerator",
                    "derivation": None
                },
                "governance": {
                    "pubkey": "AkzCGMufpEwwxRRgnhKL6rTJgAnpGnABcgVSJq5CtB41",
                    "derivation": "m/44'/501'/13'/0'"
                },
                "distribution": {
                    "pubkey": "AeGqAGNxp1yBpfuVy7nY9Lc2qfHY6yanyeNt6nTSPC1q",
                    "derivation": "m/44'/501'/11'/0'"
                },
                "reserves": {
                    "pubkey": "FXpm8G7xkcJuDfwagz1VBavKK272WnhpPbWF5z6YErvR",
                    "derivation": "m/44'/501'/12'/0'"
                }
            },
            "parameter_bounds": {
                "emission_floor_rate_min": 0.1,
                "emission_floor_rate_max": 50.0,
                "transfer_fee_burn_bps_min": 1,
                "transfer_fee_burn_bps_max": 100
            },
            "note": "Same council roster mirrored on qtestnet; production authority is qmainnet"
        },
        "wallets": {
            "treasury": "88NM2KQTuAf4tnRa9vDqhhU8CaXvFovPUfSw8q7j81S2",
            "burn": "1nc1nerator",
            "governance": "AkzCGMufpEwwxRRgnhKL6rTJgAnpGnABcgVSJq5CtB41",
            "distribution": "AeGqAGNxp1yBpfuVy7nY9Lc2qfHY6yanyeNt6nTSPC1q",
            "reserves": "FXpm8G7xkcJuDfwagz1VBavKK272WnhpPbWF5z6YErvR",
            "founder_activation": "4JkK7b9rNaVQnrYXHfuRUEmWnSgoJ2poXuv4ztF2NGz4"
        },
        "version": "1.1.0-perpetual-qtestnet-no-staking",
        "spec": "docs/xcoin-tokenomics.md"
    },
    "legacy": {
        "asset": "XCoin",
        "model": "archive_historical",
        "hard_cap": None,
        "end_date": None,
        "indefinite": True,
        "initial_supply": 1000.0,
        "staking": {
            "enabled": False,
            "note": "removed"
        },
        "burn": {
            "transfer_fee_burn_bps": 15,
            "activation_base_xcoin": 1.0
        },
        "note": "HISTORICAL — not production; qmainnet is sole active network",
        "version": "archive",
        "spec": "docs/xcoin-tokenomics.md"
    }
}


def tokenomics_for(network: str) -> dict[str, Any]:
    return dict(TOKENOMICS_BY_NETWORK.get(network) or TOKENOMICS_BY_NETWORK["qmainnet"])


def circulating_supply(chain: dict[str, Any], asset: str = "XCoin") -> float:
    total = 0.0
    for bals in (chain.get("balances") or {}).values():
        if isinstance(bals, dict):
            total += float(bals.get(asset, 0) or 0)
    return round(total, 6)


def enrich_tokenomics(chain: dict[str, Any], net: str) -> dict[str, Any]:
    """Merge static tokenomics with live supply/burn figures from the ledger."""
    base = tokenomics_for(net)
    asset = str(base.get("asset") or "XCoin")
    burned = float((chain.get("burned_supply") or {}).get(asset, 0) or 0)
    circ = circulating_supply(chain, asset)
    issued = round(circ + burned, 6)
    live = {
        **base,
        "live": {
            "circulating_supply": circ,
            "burned_supply": burned,
            "issued_supply": issued,
            "hard_cap": None,
            "network": net,
            "chain_id": chain.get("chain_id"),
        },
    }
    return live


def ensure_tokenomics(chain: dict[str, Any], net: str) -> dict[str, Any]:
    """Persist tokenomics + governance onto chain JSON (parameters + live counters)."""
    tok = enrich_tokenomics(chain, net)
    params = {k: v for k, v in tok.items() if k != "live"}
    live = tok.get("live") or {}
    chain["tokenomics"] = {
        **params,
        "circulating_supply": live.get("circulating_supply"),
        "burned_supply_asset": live.get("burned_supply"),
        "issued_supply": live.get("issued_supply"),
        "applied_at": utc_now(),
    }
    gov = params.get("governance")
    if isinstance(gov, dict):
        chain["governance"] = gov
    wallets = params.get("wallets")
    if isinstance(wallets, dict):
        chain["system_wallets"] = wallets
    return chain



def normalize_network(name: str | None) -> str:
    n = (name or DEFAULT_NETWORK).strip().lower()
    aliases = {
        "mainnet": "qmainnet",
        "devnet": "qdevnet",
        "testnet": "qtestnet",
        "qnet-mainnet": "qmainnet",
        "qnet-devnet": "qdevnet",
        "qnet-testnet": "qtestnet",
        "production": "qmainnet",
        "active": "qmainnet",
        "hannover": "legacy",
        "local": "legacy",
        "default": "qmainnet",
        # Explicit Solana aliases rejected — operators must use qmainnet
        "solana": "qmainnet",
        "solana-mainnet": "qmainnet",
        "mainnet-beta": "qmainnet",
    }
    n = aliases.get(n, n)
    if n not in NETWORK_DEFS:
        raise KeyError(n)
    return n


def chain_path(network: str | None = None) -> Path:
    net = normalize_network(network)
    return DATA_DIR / NETWORK_DEFS[net]["file"]


def load_chain(network: str | None = None) -> dict[str, Any]:
    path = chain_path(network)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_chain(chain: dict[str, Any], network: str | None = None) -> None:
    path = chain_path(network)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(chain, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _refresh_network_layer(net: str, chain: dict[str, Any]) -> None:
    nets = STATE["layers"].setdefault("blockchain", {}).setdefault("networks", {})
    tok = chain.get("tokenomics") or {}
    nets[net] = {
        "status": chain.get("status", "STANDBY"),
        "height": chain.get("height", 0),
        "tip_hash": chain.get("tip_hash"),
        "chain_id": chain.get("chain_id"),
        "path": str(chain_path(net)),
        "tx_possible": chain.get("status") == "OPERATIONAL",
        "label": NETWORK_DEFS[net]["label"],
        "role": NETWORK_DEFS[net].get("role"),
        "burned_supply": chain.get("burned_supply", {}),
        "circulating_supply": tok.get("circulating_supply"),
        "tokenomics_version": tok.get("version"),
        "active_production": net == ACTIVE_PRODUCTION_NETWORK,
    }
    # Canonical top-level blockchain summary prefers qmainnet (sole active production)
    if net == ACTIVE_PRODUCTION_NETWORK or (
        net == "legacy"
        and STATE["layers"]["blockchain"].get("chain_id") not in {
            NETWORK_DEFS["qmainnet"]["chain_id"],
            None,
        }
        and STATE["layers"]["blockchain"].get("status") != "OPERATIONAL"
    ):
        if net == ACTIVE_PRODUCTION_NETWORK or STATE["layers"]["blockchain"].get("status") != "OPERATIONAL":
            STATE["layers"]["blockchain"].update(
                {
                    "status": chain.get("status", "STANDBY") if net == ACTIVE_PRODUCTION_NETWORK else STATE["layers"]["blockchain"].get("status", "STANDBY"),
                    "height": chain.get("height", 0) if net == ACTIVE_PRODUCTION_NETWORK else STATE["layers"]["blockchain"].get("height", 0),
                    "tip_hash": chain.get("tip_hash") if net == ACTIVE_PRODUCTION_NETWORK else STATE["layers"]["blockchain"].get("tip_hash"),
                    "chain_id": chain.get("chain_id") if net == ACTIVE_PRODUCTION_NETWORK else STATE["layers"]["blockchain"].get("chain_id"),
                    "tx_possible": (chain.get("status") == "OPERATIONAL") if net == ACTIVE_PRODUCTION_NETWORK else STATE["layers"]["blockchain"].get("tx_possible"),
                    "active_network": ACTIVE_PRODUCTION_NETWORK,
                    "note": "QCoin/XCoin multi-network; sole active production = qmainnet (not Solana)",
                }
            )
    if net == ACTIVE_PRODUCTION_NETWORK:
        STATE["layers"]["blockchain"].update(
            {
                "status": chain.get("status", "STANDBY"),
                "height": chain.get("height", 0),
                "tip_hash": chain.get("tip_hash"),
                "chain_id": chain.get("chain_id"),
                "tx_possible": chain.get("status") == "OPERATIONAL",
                "active_network": ACTIVE_PRODUCTION_NETWORK,
                "note": "QCoin/XCoin multi-network; sole active production = qmainnet (not Solana)",
            }
        )


def blockchain_start(network: str | None = None) -> dict[str, Any]:
    """Initialize ledger (genesis if missing) and mark OPERATIONAL."""
    try:
        net = normalize_network(network)
    except KeyError:
        return {"ok": False, "error": "unknown_network", "network": network}
    meta = NETWORK_DEFS[net]
    chain = load_chain(net)
    now = utc_now()
    if not chain or not chain.get("blocks"):
        genesis = {
            "height": 0,
            "hash": meta["genesis_hash"],
            "ts": now,
            "txs": [
                {
                    "id": "tx-genesis",
                    "type": "GENESIS",
                    "from": "network",
                    "to": "hannover-primary",
                    "amount": 0,
                    "asset": "XCoin",
                    "note": f"{meta['label']} genesis",
                    "network": net,
                }
            ],
        }
        chain = {
            "chain_id": meta["chain_id"],
            "network": net,
            "status": "OPERATIONAL",
            "created_at": now,
            "height": 0,
            "tip_hash": genesis["hash"],
            "blocks": [genesis],
            "balances": {"hannover-primary": {"XCoin": 1000.0, "QCoin": 1000.0}},
            "tx_index": {"tx-genesis": 0},
            "burned_supply": {"XCoin": 0.0, "QCoin": 0.0},
        }
        ensure_tokenomics(chain, net)
        save_chain(chain, net)
        note = "genesis_created"
    else:
        chain["status"] = "OPERATIONAL"
        chain["activated_at"] = now
        chain.setdefault("network", net)
        chain.setdefault("burned_supply", {"XCoin": 0.0, "QCoin": 0.0})
        ensure_tokenomics(chain, net)
        save_chain(chain, net)
        note = "existing_chain_activated"
    _refresh_network_layer(net, chain)
    STATE["layers"]["blockchain"]["note"] = "QCoin/XCoin multi-network local ledger"
    STATE["layers"]["blockchain"]["peers"] = len(STATE.get("blockchain_peers", []))
    emit("BLOCKCHAIN_START", {"height": chain.get("height", 0), "note": note, "network": net})
    return {
        "ok": True,
        "note": note,
        "network": net,
        "path": str(chain_path(net)),
        **STATE["layers"]["blockchain"]["networks"][net],
        "balances": chain.get("balances", {}),
    }


def blockchain_networks_status() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name in NETWORK_DEFS:
        chain = load_chain(name)
        if chain:
            _refresh_network_layer(name, chain)
            out[name] = {
                "status": chain.get("status", "STANDBY"),
                "height": chain.get("height", 0),
                "tip_hash": chain.get("tip_hash"),
                "chain_id": chain.get("chain_id"),
                "path": str(chain_path(name)),
                "balances_accounts": len(chain.get("balances") or {}),
                "burned_supply": chain.get("burned_supply", {}),
                "circulating_supply": (chain.get("tokenomics") or {}).get("circulating_supply"),
                "label": NETWORK_DEFS[name]["label"],
                "role": NETWORK_DEFS[name].get("role"),
                "active_production": name == ACTIVE_PRODUCTION_NETWORK,
                "tokenomics_version": (chain.get("tokenomics") or {}).get("version"),
            }
        else:
            out[name] = {
                "status": "UNINITIALIZED",
                "path": str(chain_path(name)),
                "chain_id": NETWORK_DEFS[name]["chain_id"],
                "label": NETWORK_DEFS[name]["label"],
            }
    return {"ok": True, "active_network": ACTIVE_PRODUCTION_NETWORK, "default_network": DEFAULT_NETWORK, "networks": out, "legacy_peers": STATE.get("blockchain_peers", [])}


def blockchain_tx(body: dict[str, Any], network: str | None = None) -> dict[str, Any]:
    try:
        net = normalize_network(body.get("network") if network is None else network)
    except KeyError:
        return {"ok": False, "error": "unknown_network", "network": network or body.get("network")}
    # body network wins only when path/param not given
    if network is None and body.get("network"):
        try:
            net = normalize_network(str(body.get("network")))
        except KeyError:
            return {"ok": False, "error": "unknown_network", "network": body.get("network")}
    chain = load_chain(net)
    if not chain or not chain.get("blocks"):
        return {"ok": False, "error": "chain_not_initialized", "network": net}
    if chain.get("status") != "OPERATIONAL":
        return {"ok": False, "error": "chain_not_operational", "network": net}
    now = utc_now()
    tx_type = str(body.get("type") or body.get("tx_type") or "TRANSFER").upper()
    sender = str(body.get("from", "hannover-primary"))
    recipient = str(body.get("to", "swarm"))
    asset = str(body.get("asset", "XCoin"))
    amount = float(body.get("amount", 1))
    if amount <= 0:
        return {"ok": False, "error": "invalid_amount"}
    balances = chain.setdefault("balances", {})
    balances.setdefault(sender, {"XCoin": 0.0, "QCoin": 0.0})
    if balances[sender].get(asset, 0) < amount:
        return {"ok": False, "error": "insufficient_balance", "balances": balances[sender], "network": net}

    is_burn = tx_type == "BURN" or recipient.lower() in INCINERATOR_IDS
    if is_burn:
        tx_type = "BURN"
        recipient = "1nc1nerator"
        balances[sender][asset] = round(balances[sender].get(asset, 0) - amount, 6)
        # do NOT credit incinerator — supply reduction
        burned = chain.setdefault("burned_supply", {"XCoin": 0.0, "QCoin": 0.0})
        burned[asset] = round(float(burned.get(asset, 0)) + amount, 6)
    else:
        balances.setdefault(recipient, {"XCoin": 0.0, "QCoin": 0.0})
        balances[sender][asset] = round(balances[sender].get(asset, 0) - amount, 6)
        balances[recipient][asset] = round(balances[recipient].get(asset, 0) + amount, 6)

    height = int(chain.get("height", 0)) + 1
    tx_id = f"tx-{height}-{int(time.time())}"
    block = {
        "height": height,
        "hash": f"0xblock_{height}_{tx_id}",
        "prev": chain.get("tip_hash"),
        "ts": now,
        "network": net,
        "txs": [
            {
                "id": tx_id,
                "type": tx_type,
                "from": sender,
                "to": recipient,
                "amount": amount,
                "asset": asset,
                "network": net,
                **({"burned": True} if is_burn else {}),
                **({"memo": str(body.get("memo") or body.get("message")).strip()} if (body.get("memo") or body.get("message")) else {}),
                **({"vip": True} if body.get("vip") else {}),
            }
        ],
    }
    chain["blocks"].append(block)
    chain["height"] = height
    chain["tip_hash"] = block["hash"]
    chain.setdefault("tx_index", {})[tx_id] = height
    save_chain(chain, net)
    _refresh_network_layer(net, chain)
    emit("BLOCKCHAIN_TX", {"tx_id": tx_id, "height": height, "type": tx_type, "network": net})
    vip_notice = None
    try:
        if _vip_msg is not None and not is_burn:
            tx0 = block["txs"][0]
            memo = tx0.get("memo")
            force = bool(body.get("vip")) or str(recipient).startswith("vip:") or str(recipient).startswith("github:")
            if force or _vip_msg.is_vip_payout(tx0):
                if not memo:
                    _vn0 = body.get("vip_number")
                    try:
                        _vn0i = int(_vn0) if _vn0 is not None else _vip_msg.resolve_vip_number(recipient)
                    except (TypeError, ValueError):
                        _vn0i = _vip_msg.resolve_vip_number(recipient)
                    memo = _vip_msg.build_thanks(amount, asset, tx_id, net, lang=str(body.get("lang") or "en"), vip_number=_vn0i)
                    tx0["memo"] = memo
                    # persist memo onto saved chain
                    chain["blocks"][-1]["txs"][0]["memo"] = memo
                    save_chain(chain, net)
                _vn = body.get("vip_number")
                try:
                    _vn_int = int(_vn) if _vn is not None else None
                except (TypeError, ValueError):
                    _vn_int = None
                vip_notice = _vip_msg.notify_vip_payment(
                    to=recipient,
                    amount=amount,
                    asset=asset,
                    tx_id=tx_id,
                    height=height,
                    network=net,
                    memo=memo,
                    lang=str(body.get("lang") or "") or None,
                    vip_number=_vn_int,
                )
    except Exception as _vip_exc:  # never fail the payout on notify errors
        log("WARN", f"vip_payment_notify_failed: {_vip_exc}")
    out = {
        "ok": True,
        "tx_id": tx_id,
        "height": height,
        "type": tx_type,
        "network": net,
        "chain_id": chain.get("chain_id"),
        "block": block,
        "balances": balances,
        "burned_supply": chain.get("burned_supply"),
    }
    if vip_notice is not None:
        out["vip_message"] = vip_notice
    return out



def blockchain_export(network: str | None = None) -> dict[str, Any]:
    try:
        net = normalize_network(network)
    except KeyError:
        net = DEFAULT_NETWORK
    chain = load_chain(net)
    return {
        "ok": True,
        "node": NODE_NAME,
        "listen": f"{BIND}:{PORT}",
        "network": net,
        "chain": chain,
        "layer": STATE["layers"].get("blockchain", {}),
        "peers": STATE.get("blockchain_peers", []) if net == "legacy" else [],
    }


def _http_json(method: str, url: str, body: dict[str, Any] | None = None, timeout: float = 5.0) -> dict[str, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def blockchain_apply_remote(remote_chain: dict[str, Any], peer_url: str) -> dict[str, Any]:
    """Adopt remote chain if compatible and at least as long; otherwise keep local and push.
    Peer sync remains on the legacy Hannover ledger (archive); qmainnet is sole production.
    """
    local = load_chain("legacy")
    if not remote_chain or not remote_chain.get("blocks"):
        return {"ok": False, "error": "remote_empty"}
    if local and local.get("chain_id") and remote_chain.get("chain_id") != local.get("chain_id"):
        return {
            "ok": False,
            "error": "chain_id_mismatch",
            "local": local.get("chain_id"),
            "remote": remote_chain.get("chain_id"),
        }
    local_h = int(local.get("height", -1)) if local else -1
    remote_h = int(remote_chain.get("height", -1))
    action = "noop"
    if remote_h > local_h or (not local or not local.get("blocks")):
        # fork check on common prefix
        if local and local.get("blocks"):
            for i, lb in enumerate(local.get("blocks") or []):
                if i >= len(remote_chain.get("blocks") or []):
                    break
                rb = remote_chain["blocks"][i]
                if lb.get("hash") != rb.get("hash"):
                    return {
                        "ok": False,
                        "error": "fork_detected",
                        "height": i,
                        "local_hash": lb.get("hash"),
                        "remote_hash": rb.get("hash"),
                    }
        save_chain(remote_chain, "legacy")
        local = remote_chain
        action = "pulled"
    elif local_h > remote_h:
        action = "push_needed"
    else:
        # equal height — require same tip
        if local.get("tip_hash") != remote_chain.get("tip_hash"):
            return {
                "ok": False,
                "error": "fork_detected",
                "height": local_h,
                "local_hash": local.get("tip_hash"),
                "remote_hash": remote_chain.get("tip_hash"),
            }
        action = "already_synced"
    STATE["layers"]["blockchain"].update(
        {
            "status": "OPERATIONAL",
            "height": local.get("height", 0),
            "tip_hash": local.get("tip_hash"),
            "chain_id": local.get("chain_id"),
            "note": "QCoin/XCoin multi-node local ledger",
            "tx_possible": True,
            "peers": len(STATE.get("blockchain_peers", [])),
        }
    )
    return {
        "ok": True,
        "action": action,
        "height": local.get("height"),
        "tip_hash": local.get("tip_hash"),
        "peer": peer_url,
    }


def blockchain_peer_connect(body: dict[str, Any]) -> dict[str, Any]:
    peer_url = str(body.get("url") or body.get("peer") or "").rstrip("/")
    if not peer_url:
        return {"ok": False, "error": "missing_peer_url"}
    try:
        remote = _http_json("GET", f"{peer_url}/blockchain/export")
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": "peer_unreachable", "detail": str(exc), "peer": peer_url}
    remote_chain = remote.get("chain") if isinstance(remote, dict) else None
    if not isinstance(remote_chain, dict):
        return {"ok": False, "error": "peer_bad_export", "peer": peer_url}
    local = load_chain()
    remote_empty = not remote_chain.get("blocks")
    if remote_empty and local and local.get("blocks"):
        try:
            _http_json(
                "POST",
                f"{peer_url}/blockchain/import",
                {"chain": local, "from": NODE_NAME, "listen": f"http://{BIND}:{PORT}"},
            )
            result = {
                "ok": True,
                "action": "seeded_peer",
                "height": local.get("height"),
                "tip_hash": local.get("tip_hash"),
                "peer": peer_url,
            }
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": "push_failed", "detail": str(exc), "peer": peer_url}
    else:
        result = blockchain_apply_remote(remote_chain, peer_url)
        if not result.get("ok"):
            return result
        # push if we are ahead
        if result.get("action") == "push_needed":
            try:
                _http_json(
                    "POST",
                    f"{peer_url}/blockchain/import",
                    {"chain": load_chain(), "from": NODE_NAME, "listen": f"http://{BIND}:{PORT}"},
                )
                result["action"] = "pushed"
            except Exception as exc:  # noqa: BLE001
                return {"ok": False, "error": "push_failed", "detail": str(exc), "peer": peer_url}
    peers = STATE.setdefault("blockchain_peers", [])
    entry = {
        "url": peer_url,
        "node": remote.get("node"),
        "status": "established",
        "connected_at": utc_now(),
        "height": result.get("height"),
        "tip_hash": result.get("tip_hash"),
    }
    peers[:] = [p for p in peers if p.get("url") != peer_url] + [entry]
    STATE["layers"]["blockchain"]["peers"] = len(peers)
    STATE["layers"]["blockchain"]["peer_list"] = peers
    emit("BLOCKCHAIN_PEER_CONNECT", {"peer": peer_url, "action": result.get("action"), "height": result.get("height")})
    return {"ok": True, "connection": "established", **result, "peers": peers}


def blockchain_import(body: dict[str, Any]) -> dict[str, Any]:
    remote_chain = body.get("chain") if isinstance(body, dict) else None
    peer_url = str(body.get("listen") or body.get("from") or "remote")
    if not isinstance(remote_chain, dict):
        return {"ok": False, "error": "missing_chain"}
    result = blockchain_apply_remote(remote_chain, peer_url)
    if result.get("ok") and body.get("listen"):
        peers = STATE.setdefault("blockchain_peers", [])
        url = str(body.get("listen")).rstrip("/")
        entry = {
            "url": url,
            "node": body.get("from"),
            "status": "established",
            "connected_at": utc_now(),
            "height": result.get("height"),
            "tip_hash": result.get("tip_hash"),
        }
        peers[:] = [p for p in peers if p.get("url") != url] + [entry]
        STATE["layers"]["blockchain"]["peers"] = len(peers)
        STATE["layers"]["blockchain"]["peer_list"] = peers
    return result



class Handler(BaseHTTPRequestHandler):
    server_version = "NexusControl/0.1"

    def _json(self, code: int, body: Any) -> None:
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, fmt: str, *args: Any) -> None:
        log("HTTP", fmt % args)

    def do_GET(self) -> None:  # noqa: N802
        with LOCK:
            STATE["metrics"]["requests"] += 1
            path = urlparse(self.path).path
            if path in ("/", "/health"):
                self._json(200, {"status": "ok", "node": NODE_NAME, "plane": STATE["status"]})
            elif path == "/status":
                self._json(200, snapshot())
            elif path == "/layers":
                self._json(200, STATE["layers"])
            elif path == "/blockchain/status":
                chain = load_chain("legacy")
                self._json(200, {"layer": STATE["layers"].get("blockchain", {}), "chain": {
                    "chain_id": chain.get("chain_id"),
                    "height": chain.get("height"),
                    "tip_hash": chain.get("tip_hash"),
                    "status": chain.get("status"),
                    "balances": chain.get("balances"),
                    "blocks": len(chain.get("blocks") or []),
                    "peers": STATE.get("blockchain_peers", []),
                    "tx_possible": True,
                    "networks": (STATE["layers"].get("blockchain") or {}).get("networks", {}),
                }})
            elif path == "/blockchain/networks":
                self._json(200, blockchain_networks_status())
            elif path.startswith("/blockchain/network/") and path.endswith("/status"):
                net = path[len("/blockchain/network/"):-len("/status")]
                try:
                    net = normalize_network(net)
                except KeyError:
                    self._json(404, {"error": "unknown_network", "network": net})
                else:
                    chain = load_chain(net)
                    self._json(200, {
                        "ok": True,
                        "network": net,
                        "layer": ((STATE["layers"].get("blockchain") or {}).get("networks") or {}).get(net, {}),
                        "chain": {
                            "chain_id": chain.get("chain_id"),
                            "height": chain.get("height"),
                            "tip_hash": chain.get("tip_hash"),
                            "status": chain.get("status"),
                            "balances": chain.get("balances"),
                            "blocks": len(chain.get("blocks") or []),
                            "burned_supply": chain.get("burned_supply"),
                            "circulating_supply": (chain.get("tokenomics") or {}).get("circulating_supply"),
                            "tokenomics": chain.get("tokenomics"),
                            "governance": chain.get("governance"),
                            "system_wallets": chain.get("system_wallets"),
                            "tx_possible": chain.get("status") == "OPERATIONAL",
                            "path": str(chain_path(net)),
                        },
                    })
            elif path.startswith("/blockchain/network/") and path.endswith("/export"):
                net = path[len("/blockchain/network/"):-len("/export")]
                try:
                    net = normalize_network(net)
                except KeyError:
                    self._json(404, {"error": "unknown_network", "network": net})
                else:
                    self._json(200, blockchain_export(net))
            elif path == "/blockchain/export":
                self._json(200, blockchain_export("legacy"))
            elif path == "/blockchain/peers":
                self._json(200, {"ok": True, "peers": STATE.get("blockchain_peers", []), "layer": STATE["layers"].get("blockchain", {})})
            elif path.startswith("/blockchain/network/") and path.endswith("/tokenomics"):
                net = path[len("/blockchain/network/"):-len("/tokenomics")]
                try:
                    net = normalize_network(net)
                except KeyError:
                    self._json(404, {"error": "unknown_network", "network": net})
                else:
                    chain = load_chain(net)
                    if chain and not chain.get("tokenomics"):
                        ensure_tokenomics(chain, net)
                        save_chain(chain, net)
                    self._json(200, {
                        "ok": True,
                        "network": net,
                        "active_production": net == ACTIVE_PRODUCTION_NETWORK,
                        "tokenomics": (chain or {}).get("tokenomics") or enrich_tokenomics(chain or {}, net),
                        "governance": (chain or {}).get("governance"),
                        "system_wallets": (chain or {}).get("system_wallets"),
                    })
            elif path.startswith("/blockchain/network/") and path.endswith("/governance"):
                net = path[len("/blockchain/network/"):-len("/governance")]
                try:
                    net = normalize_network(net)
                except KeyError:
                    self._json(404, {"error": "unknown_network", "network": net})
                else:
                    chain = load_chain(net)
                    if chain and not chain.get("governance"):
                        ensure_tokenomics(chain, net)
                        save_chain(chain, net)
                    self._json(200, {
                        "ok": True,
                        "network": net,
                        "governance": (chain or {}).get("governance") or (tokenomics_for(net).get("governance")),
                        "system_wallets": (chain or {}).get("system_wallets"),
                    })
            elif path == "/forum/status":
                self._json(200, _forum.status() if _forum else {"ok": False, "error": "forum_unavailable"})
            elif path == "/forum/boards":
                self._json(200, _forum.boards() if _forum else {"ok": False, "error": "forum_unavailable"})
            elif path == "/forum/threads":
                from urllib.parse import parse_qs
                qs = parse_qs(urlparse(self.path).query)
                board = (qs.get("board") or [None])[0]
                self._json(200, _forum.list_threads(board) if _forum else {"ok": False, "error": "forum_unavailable"})
            elif path.startswith("/forum/thread/"):
                tid = path[len("/forum/thread/"):]
                self._json(200, _forum.thread_detail(tid) if _forum else {"ok": False, "error": "forum_unavailable"})
            elif path == "/marketplace/status":
                self._json(200, _mkt.status() if _mkt else {"ok": False, "error": "marketplace_unavailable"})
            elif path == "/marketplace/categories":
                self._json(200, _mkt.categories() if _mkt else {"ok": False, "error": "marketplace_unavailable"})
            elif path == "/marketplace/listings":
                self._json(200, _mkt.list_listings(active_only=True) if _mkt else {"ok": False, "error": "marketplace_unavailable"})
            elif path == "/blockchain/active":
                self._json(200, {
                    "ok": True,
                    "active_network": ACTIVE_PRODUCTION_NETWORK,
                    "default_network": DEFAULT_NETWORK,
                    "endpoint": f"http://127.0.0.1:{PORT}/blockchain/network/{ACTIVE_PRODUCTION_NETWORK}/status",
                    "note": "Sole active production network is qmainnet (local XCoin). Solana Mainnet is not used.",
                })
            else:
                self._json(404, {"error": "not_found", "path": path})

    def do_POST(self) -> None:  # noqa: N802
        with LOCK:
            STATE["metrics"]["requests"] += 1
            path = urlparse(self.path).path
            if path == "/mesh/start":
                snap = ygg_peer_snapshot()
                peers_up = int(snap.get("peers_up") or MESH_PEERS)
                STATE["layers"]["mesh"].update(
                    {
                        "status": "OPERATIONAL",
                        "peers": peers_up,
                        "peers_total": snap.get("peers"),
                        "peer_list": snap.get("peer_list", []),
                        "note": "Yggdrasil host-side live",
                        "substrate": "yggdrasil",
                    }
                )
                emit("MESH_EXPAND", {"peers": peers_up})
                self._json(200, STATE["layers"]["mesh"])
            elif path == "/swarm/spawn":
                STATE["layers"]["swarm"].update({"status": "OPERATIONAL", "agents": SWARM_SIZE})
                emit("SWARM_EXPAND", {"agents": SWARM_SIZE})
                self._json(200, STATE["layers"]["swarm"])
            elif path == "/prototypes/start":
                now = utc_now()
                items = {
                    "Soilnova": {"status": "running", "started_at": now, "role": "soil-sensing"},
                    "Vista Nova": {"status": "running", "started_at": now, "role": "vision"},
                    "Lumia": {"status": "running", "started_at": now, "role": "light-layer"},
                }
                for _name, _item in items.items():
                    _real = prototype_real_status(_name)
                    if _real:
                        _item.update(_real)
                STATE["layers"]["prototypes"].update(
                    {
                        "status": "OPERATIONAL",
                        "note": "Soilnova / Vista Nova / Lumia",
                        "items": items,
                        "activated_at": now,
                    }
                )
                emit("PROTOTYPES_START", {"items": list(items.keys())})
                self._json(200, STATE["layers"]["prototypes"])
            elif path == "/cyberspace/start":
                result = cyberspace_start()
                self._json(200 if result.get("ok") else 503, result)
            elif path == "/blockchain/start":
                length = int(self.headers.get("Content-Length") or 0)
                raw_body = self.rfile.read(length) if length else b"{}"
                try:
                    body = json.loads(raw_body.decode("utf-8") or "{}") if raw_body else {}
                except json.JSONDecodeError:
                    body = {}
                net = (body or {}).get("network") if isinstance(body, dict) else None
                result = blockchain_start(net)
                self._json(200 if result.get("ok") else 503, result)
            elif path.startswith("/blockchain/network/") and path.endswith("/start"):
                net = path[len("/blockchain/network/"):-len("/start")]
                result = blockchain_start(net)
                self._json(200 if result.get("ok") else (404 if result.get("error") == "unknown_network" else 503), result)
            elif path == "/blockchain/tx":
                length = int(self.headers.get("Content-Length") or 0)
                raw_body = self.rfile.read(length) if length else b"{}"
                try:
                    body = json.loads(raw_body.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    body = {}
                result = blockchain_tx(body if isinstance(body, dict) else {}, network=(body or {}).get("network") if isinstance(body, dict) else None)
                self._json(200 if result.get("ok") else 400, result)
            elif path.startswith("/blockchain/network/") and path.endswith("/tx"):
                net = path[len("/blockchain/network/"):-len("/tx")]
                length = int(self.headers.get("Content-Length") or 0)
                raw_body = self.rfile.read(length) if length else b"{}"
                try:
                    body = json.loads(raw_body.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    body = {}
                if not isinstance(body, dict):
                    body = {}
                result = blockchain_tx(body, network=net)
                self._json(200 if result.get("ok") else 400, result)
            elif path == "/blockchain/peer/connect":
                length = int(self.headers.get("Content-Length") or 0)
                raw_body = self.rfile.read(length) if length else b"{}"
                try:
                    body = json.loads(raw_body.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    body = {}
                result = blockchain_peer_connect(body if isinstance(body, dict) else {})
                self._json(200 if result.get("ok") else 400, result)
            elif path == "/blockchain/import":
                length = int(self.headers.get("Content-Length") or 0)
                raw_body = self.rfile.read(length) if length else b"{}"
                try:
                    body = json.loads(raw_body.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    body = {}
                result = blockchain_import(body if isinstance(body, dict) else {})
                self._json(200 if result.get("ok") else 400, result)
            elif path == "/forum/register":
                length = int(self.headers.get("Content-Length") or 0)
                raw_body = self.rfile.read(length) if length else b"{}"
                try:
                    body = json.loads(raw_body.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    body = {}
                result = _forum.register(body if isinstance(body, dict) else {}) if _forum else {"ok": False, "error": "forum_unavailable"}
                self._json(200 if result.get("ok") else 400, result)
            elif path == "/forum/thread":
                length = int(self.headers.get("Content-Length") or 0)
                raw_body = self.rfile.read(length) if length else b"{}"
                try:
                    body = json.loads(raw_body.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    body = {}
                result = _forum.create_thread(body if isinstance(body, dict) else {}) if _forum else {"ok": False, "error": "forum_unavailable"}
                self._json(200 if result.get("ok") else 400, result)
            elif path == "/forum/reply":
                length = int(self.headers.get("Content-Length") or 0)
                raw_body = self.rfile.read(length) if length else b"{}"
                try:
                    body = json.loads(raw_body.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    body = {}
                result = _forum.reply(body if isinstance(body, dict) else {}) if _forum else {"ok": False, "error": "forum_unavailable"}
                self._json(200 if result.get("ok") else 400, result)
            elif path == "/forum/vote":
                length = int(self.headers.get("Content-Length") or 0)
                raw_body = self.rfile.read(length) if length else b"{}"
                try:
                    body = json.loads(raw_body.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    body = {}
                result = _forum.vote(body if isinstance(body, dict) else {}) if _forum else {"ok": False, "error": "forum_unavailable"}
                self._json(200 if result.get("ok") else 400, result)
            elif path == "/forum/governance/moderate":
                length = int(self.headers.get("Content-Length") or 0)
                raw_body = self.rfile.read(length) if length else b"{}"
                try:
                    body = json.loads(raw_body.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    body = {}
                result = _forum.governance_moderate(body if isinstance(body, dict) else {}) if _forum else {"ok": False, "error": "forum_unavailable"}
                self._json(200 if result.get("ok") else 400, result)
            elif path == "/marketplace/list":
                length = int(self.headers.get("Content-Length") or 0)
                raw_body = self.rfile.read(length) if length else b"{}"
                try:
                    body = json.loads(raw_body.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    body = {}
                result = _mkt.create_listing(body if isinstance(body, dict) else {}) if _mkt else {"ok": False, "error": "marketplace_unavailable"}
                self._json(200 if result.get("ok") else 400, result)
            elif path == "/marketplace/order":
                length = int(self.headers.get("Content-Length") or 0)
                raw_body = self.rfile.read(length) if length else b"{}"
                try:
                    body = json.loads(raw_body.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    body = {}
                result = _mkt.place_order(body if isinstance(body, dict) else {}, blockchain_tx) if _mkt else {"ok": False, "error": "marketplace_unavailable"}
                self._json(200 if result.get("ok") else 400, result)
            elif path == "/marketplace/confirm":
                length = int(self.headers.get("Content-Length") or 0)
                raw_body = self.rfile.read(length) if length else b"{}"
                try:
                    body = json.loads(raw_body.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    body = {}
                result = _mkt.confirm_delivery(body if isinstance(body, dict) else {}, blockchain_tx) if _mkt else {"ok": False, "error": "marketplace_unavailable"}
                self._json(200 if result.get("ok") else 400, result)
            elif path == "/marketplace/governance/review":
                length = int(self.headers.get("Content-Length") or 0)
                raw_body = self.rfile.read(length) if length else b"{}"
                try:
                    body = json.loads(raw_body.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    body = {}
                result = _mkt.governance_review(body if isinstance(body, dict) else {}) if _mkt else {"ok": False, "error": "marketplace_unavailable"}
                self._json(200 if result.get("ok") else 400, result)
            elif path == "/stop":
                STATE["status"] = "STOPPING"
                emit("NEXUS_STOP", {})
                self._json(200, {"status": "stopping"})
                threading.Thread(target=lambda: (time.sleep(0.3), os._exit(0)), daemon=True).start()
            else:
                self._json(404, {"error": "not_found", "path": path})


def main() -> None:
    boot()
    httpd = ThreadingHTTPServer((BIND, PORT), Handler)
    log("INFO", f"Control Plane listening on http://{BIND}:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        emit("NEXUS_STOP", {"reason": "keyboard"})
        httpd.server_close()


if __name__ == "__main__":
    main()
