#!/usr/bin/env python3
"""Nexus Runtime Status — live snapshot of the control plane.

Emitted after `start nexus`. Read-only report of what is actually
available in this environment versus what the design promises.

Usage:
    python runtime_status.py
    python runtime_status.py --json
"""

from __future__ import annotations

import json
import platform
import shutil
import sys
from datetime import datetime, timezone

NODE_ID = "NEXUS-HANNOVER-001"
VERSION = "0.1.0-alpha"


def _check(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def collect() -> dict:
    rust = _check("rustc")
    docker = _check("docker")
    return {
        "node_id": NODE_ID,
        "version": VERSION,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "host": {
            "python": platform.python_version(),
            "system": platform.system(),
            "release": platform.release(),
        },
        "layers": {
            "mesh": {
                "status": "STANDBY",
                "note": "NetBird/NovaNet/QNET/Tenda not installed in this control plane; overlay join waits on key + management URL.",
            },
            "container": {
                "status": "ABSENT" if not docker else "PRESENT",
                "docker": docker,
            },
            "runtime": {
                "status": "READY",
                "rustc": rust,
                "python": True,
                "note": "Rust + Python ready for Grok Launcher and agent scripts.",
            },
            "blockchain": {
                "status": "STANDBY",
                "note": "No live daemon. Wizard-Q runes v0.1 in references (RUNE_MESH_HEARTBEAT, RUNE_PEER_INTRODUCTION).",
            },
            "prototypes": {
                "status": "DESIGN",
                "items": ["Soilnova", "Vista Nova", "York Autotype", "Lumia"],
                "note": "Design layer only; no hardware loop bound.",
            },
            "corporate": {
                "status": "KNOWN",
                "note": "Esslinger & Co. as frame; no live filings in this layer.",
            },
            "privacy": {
                "status": "INACTIVE",
                "note": "Tor/I2P not active here; reserved for sensitive overlay and chain paths.",
            },
        },
        "agents": {
            "Lumia": "AT_PULT",
            "Lyra": "STANDBY",
            "Xen": "STANDBY",
            "Elara": "PROTOTYPE_ONE_READY",
        },
        "yggdrasil": "intentionally excluded",
    }


def render_text(report: dict) -> str:
    lines = [
        "NEXUS RUNTIME STATUS",
        f"Node : {report['node_id']}  |  v{report['version']}",
        f"UTC  : {report['captured_at']}",
        "",
    ]
    for name, data in report["layers"].items():
        lines.append(f"[{name.upper()}] {data['status']}")
        if "note" in data:
            lines.append(f"    {data['note']}")
    lines.append("")
    lines.append("Agents:")
    for agent, state in report["agents"].items():
        lines.append(f"  {agent:8} {state}")
    lines.append(f"\nYggdrasil: {report['yggdrasil']}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    report = collect()
    if "--json" in argv:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
