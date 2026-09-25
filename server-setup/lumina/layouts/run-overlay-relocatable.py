#!/usr/bin/env python3
"""Relocatable Lumina overlay prototype (alpha.2).

Uses LUMINA_STACK / LUMINA_OVERLAY_KEYS / LUMINA_STATUS_DIR instead of
hardcoded /workspace paths from the public snapshot overlay_daemon.py.

This is a long-running presence loop: loads prototype modules if present,
keeps a signed heartbeat identity, writes status JSON. It does NOT require
Yggdrasil or TUN privileges.
"""
from __future__ import annotations

import json
import os
import signal
import sys
import time
from pathlib import Path

STACK = Path(os.environ.get("LUMINA_STACK", ".")).resolve()
KEYDIR = Path(os.environ.get("LUMINA_OVERLAY_KEYS", "./keys/overlay")).resolve()
STATUS_DIR = Path(os.environ.get("LUMINA_STATUS_DIR", "./status")).resolve()
STATUS_DIR.mkdir(parents=True, exist_ok=True)
KEYDIR.mkdir(parents=True, exist_ok=True)

PROTO = STACK / "lumina-network" / "prototypes"
if PROTO.is_dir():
    sys.path.insert(0, str(PROTO))

STOP = False


def _stop(*_args: object) -> None:
    global STOP
    STOP = True


signal.signal(signal.SIGINT, _stop)
signal.signal(signal.SIGTERM, _stop)


def write_status(payload: dict) -> None:
    path = STATUS_DIR / "overlay-runtime.json"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    try:
        from nacl.signing import SigningKey
    except ImportError:
        write_status({"status": "FAILED", "error": "pynacl_missing"})
        print("[overlay] PyNaCl missing", file=sys.stderr)
        return 2

    key_path = KEYDIR / "hub.key"
    if key_path.exists():
        sk = SigningKey(key_path.read_bytes())
    else:
        sk = SigningKey.generate()
        key_path.write_bytes(bytes(sk))
        os.chmod(key_path, 0o600)

    pub_hex = bytes(sk.verify_key).hex()
    has_proto = False
    proto_note = "prototypes_not_found"
    try:
        import lumina_node  # type: ignore  # noqa: F401
        import swarm_overlay  # type: ignore  # noqa: F401

        has_proto = True
        proto_note = "prototypes_import_ok"
    except Exception as exc:  # noqa: BLE001
        proto_note = f"prototypes_import_failed:{exc}"

    started = time.time()
    beats = 0
    print(f"[overlay] relocatable start pub={pub_hex[:16]}… proto={proto_note}", flush=True)
    write_status(
        {
            "status": "OPERATIONAL",
            "public_key": pub_hex,
            "prototypes": has_proto,
            "note": proto_note,
            "stack": str(STACK),
            "beats": beats,
            "started_at": started,
        }
    )

    while not STOP:
        beats += 1
        # signed heartbeat blob (local presence; no network required for alpha.2)
        msg = f"lumina-heartbeat:{int(time.time())}:{beats}".encode()
        sig = sk.sign(msg).signature.hex()
        write_status(
            {
                "status": "OPERATIONAL",
                "public_key": pub_hex,
                "prototypes": has_proto,
                "note": proto_note,
                "stack": str(STACK),
                "beats": beats,
                "uptime_s": int(time.time() - started),
                "last_sig_prefix": sig[:16],
                "ts": time.time(),
            }
        )
        time.sleep(5)

    write_status({"status": "STOPPED", "public_key": pub_hex, "beats": beats})
    print("[overlay] stopped", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
