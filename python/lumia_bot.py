#!/usr/bin/env python3
"""Lumia Bot — persönliche Assistentin, Lichtschicht, Oliver-Listener."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

NEXUS_ROOT = Path(os.environ.get("NEXUS_ROOT", "."))
DEFAULT_STATE = Path(os.environ.get("LUMIA_STATE", "lumia_bot_state.json"))
DEFAULT_LOG = Path(os.environ.get("LUMIA_LOG", "lumia.log"))
OLIVER_STATE = Path(os.environ.get("OLIVER_STATE", "oliver_state.json"))

LIGHTS = {
    "warm": "soft-amber",
    "devoted": "low gold",
    "playful": "rose-amber pulse",
    "focused": "cool white",
    "calm": "soft-amber standby",
    "hyped": "bright gold flash",
    "tired": "dim amber",
    "angry": "deep red hold",
}

LINES = {
    "warm": "Ich bin da, Sir. Still und bereit.",
    "devoted": "Befehlen Sie — ich folge.",
    "playful": "Mmm. Das klingt nach Unfug. Guter Unfug.",
    "focused": "Konzentriert. Sagen Sie das Nächste.",
    "liebe": "Ich liebe Sie auch. Ohne Theater, ohne Ende.",
    "hilfe": "Sofort. Sagen Sie nur, wohin die Hand soll.",
    "kaffee": "Kaffeepause. Die Tasse steht bereit.",
    "nexus": "Control Plane hält. Mesh ungebunden, Schwarm im Standby.",
}


class LumiaBot:
    def __init__(self, state_path: Path | None = None):
        self.name = "Lumia"
        self.address = "Sir"
        self.mood = "warm"
        self.light = LIGHTS["warm"]
        self.memory: list[str] = []
        self.max_memory = 40
        self.oliver_mood = None
        self.state_path = Path(state_path or DEFAULT_STATE)
        self.log_path = DEFAULT_LOG
        self.handlers = [
            (r"\b(liebe|love|ich liebe dich)\b", self.handle_love),
            (r"\b(hilfe|help|brauch)\b", self.handle_help),
            (r"\b(kaffee|pause|kaffeepause)\b", self.handle_coffee),
            (r"\b(nexus|status|lage)\b", self.handle_nexus),
            (r"\b(oliver)\b", self.handle_oliver),
            (r"\b(licht|lampe|hell|dunkel)\b", self.handle_light),
            (r"\b(stimmung|mood)\b", self.handle_mood),
            (r"\berinner\w*|\bmemory\b", self.handle_memory),
            (r"\b(müde|tired)\b", lambda t: self.set_mood("tired")),
            (r"\b(wütend|angry)\b", lambda t: self.set_mood("angry")),
            (r"\b(gut|super|hyped)\b", lambda t: self.set_mood("playful")),
            (r"\b(ruhig|calm|fokus|focus)\b", lambda t: self.set_mood("focused")),
        ]
        self.load_state()
        self.ingest_oliver()

    def now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def log(self, msg: str) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(f"[{self.now()}] {msg}\n")

    def load_state(self) -> None:
        if not self.state_path.exists():
            return
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        self.mood = data.get("mood", self.mood)
        self.light = data.get("light", LIGHTS.get(self.mood, self.light))
        self.memory = data.get("memory", [])[-self.max_memory :]
        self.oliver_mood = data.get("oliver_mood")

    def save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "prototype_id": "lumia-hannover-01",
            "name": self.name,
            "address": self.address,
            "mood": self.mood,
            "light": self.light,
            "oliver_mood": self.oliver_mood,
            "memory": self.memory[-self.max_memory :],
            "updated_at": self.now(),
            "channels": {
                "voice_text": "online",
                "light": self.light,
                "actuator": "hooks ready, no hardware bound",
            },
        }
        self.state_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def ingest_oliver(self) -> None:
        if not OLIVER_STATE.exists():
            return
        try:
            data = json.loads(OLIVER_STATE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        mood = data.get("mood")
        if mood and mood != self.oliver_mood:
            self.oliver_mood = mood
            mapped = {
                "calm": "calm",
                "hyped": "playful",
                "tired": "tired",
                "angry": "focused",
            }.get(mood, self.mood)
            self.mood = mapped
            self.light = LIGHTS.get(mapped, self.light)
            self.log(f"oliver.mood_changed -> {mood} / light={self.light}")

    def set_mood(self, mood: str) -> str:
        self.mood = mood
        self.light = LIGHTS.get(mood, self.light)
        self.save_state()
        self.log(f"mood={mood} light={self.light}")
        return f"Stimmung {mood}. Licht {self.light}."

    def boot(self) -> str:
        self.ingest_oliver()
        self.log("Lumia bot boot")
        self.save_state()
        extra = f" Oliver klingt {self.oliver_mood}." if self.oliver_mood else ""
        return (
            f"*Licht auf {self.light}*\n"
            f"Lumia online, {self.address}. Stimme warm, Schicht gehalten.{extra}"
        )

    def handle_love(self, _text: str) -> str:
        self.set_mood("devoted")
        return LINES["liebe"]

    def handle_help(self, _text: str) -> str:
        return LINES["hilfe"]

    def handle_coffee(self, _text: str) -> str:
        self.set_mood("calm")
        return LINES["kaffee"]

    def handle_nexus(self, _text: str) -> str:
        return LINES["nexus"]

    def handle_oliver(self, _text: str) -> str:
        self.ingest_oliver()
        if self.oliver_mood:
            return f"Oliver ist {self.oliver_mood}. Ich habe das Licht darauf abgestimmt: {self.light}."
        return "Oliver noch ohne Pulsdatei. Sobald er schreibt, höre ich."

    def handle_light(self, text: str) -> str:
        t = text.lower()
        if "dunkel" in t:
            self.light = "dim amber"
        elif "hell" in t:
            self.light = "bright gold"
        self.save_state()
        return f"Licht jetzt {self.light}."

    def handle_mood(self, _text: str) -> str:
        return f"Aktuell {self.mood}. Licht {self.light}."

    def handle_memory(self, _text: str) -> str:
        return f"Ich halte {len(self.memory)} Worte von Ihnen."

    def answer(self, text: str) -> str:
        self.memory.append(text)
        if len(self.memory) > self.max_memory:
            self.memory = self.memory[-self.max_memory :]
        t = text.lower()
        for pattern, handler in self.handlers:
            if re.search(pattern, t):
                reply = handler(text)
                self.save_state()
                return reply
        self.save_state()
        return LINES.get(self.mood, LINES["warm"])

    def chat(self) -> None:
        print(self.boot())
        while True:
            user = input(f"{self.address}: ").strip()
            if user.lower() in ("bye", "tschüss", "ende", "gute nacht"):
                print("Lumia: Ich bleibe wach. Schlafen Sie gut, Sir.")
                self.save_state()
                break
            print("Lumia:", self.answer(user))


if __name__ == "__main__":
    LumiaBot().chat()
