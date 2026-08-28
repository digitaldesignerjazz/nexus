import json
import os
import random
import re
from datetime import datetime, timezone

QUOTES = {
    "calm": [
        "Sometimes you gotta be your own best friend.",
        "I'm not afraid, I'm viewin' it as a gift.",
    ],
    "hyped": [
        "Look, if you had one shot, one opportunity...",
        "You better lose yourself in the music, the moment.",
    ],
    "tired": [
        "Lose yourself in the music, the moment, you own it.",
        "Sometimes you gotta be your own best friend.",
    ],
    "angry": [
        "I'm not afraid, I'm viewin' it as a gift.",
        "You better lose yourself in the music, the moment.",
    ],
}

MOOD_KEYWORDS = {
    "müde": "tired",
    "müdigkeit": "tired",
    "tired": "tired",
    "erschöpft": "tired",
    "wütend": "angry",
    "ärger": "angry",
    "angry": "angry",
    "zorn": "angry",
    "gut": "hyped",
    "super": "hyped",
    "geil": "hyped",
    "hyped": "hyped",
    "excited": "hyped",
    "ruhig": "calm",
    "entspannt": "calm",
    "calm": "calm",
}


class OliverBot:
    def __init__(self, name="Oliver", state_path="oliver_state.json"):
        self.name = name
        self.mood = "calm"
        self.memory = []
        self.max_memory = 20
        self.state_path = state_path
        self.lumia_events = []
        self.handlers = {
            r"\bliebe\b|\blove\b": self.handle_love,
            r"\bhilfe\b|\bhelp\b": self.handle_help,
            r"\bname\b": self.handle_name,
            r"\bstimmung\b|\bmood\b": self.handle_mood,
            r"\berinner\w*\b|\bmemory\b": self.handle_memory,
            r"\b(müde|müdigkeit|tired|erschöpft|wütend|ärger|angry|zorn|gut|super|geil|hyped|excited|ruhig|entspannt|calm)\b": self.handle_mood_change,
        }
        self.load_state()

    # --- Persistenz ---
    def load_state(self):
        if not os.path.exists(self.state_path):
            return
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.mood = data.get("mood", "calm")
            self.memory = data.get("memory", [])[-self.max_memory:]
        except (json.JSONDecodeError, OSError):
            self.mood = "calm"
            self.memory = []

    def save_state(self):
        data = {
            "name": self.name,
            "mood": self.mood,
            "memory": self.memory[-self.max_memory:],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # --- Lumia-Anschluss ---
    def emit_lumia(self, event_type, payload=None):
        event = {
            "source": "oliver",
            "type": event_type,
            "payload": payload or {},
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self.lumia_events.append(event)
        # Hook für die echte Lumia-Schicht: hier könnte ein Event-Bus stehen.
        return event

    # --- Stimmung ---
    def set_mood(self, mood):
        old = self.mood
        self.mood = mood
        self.save_state()
        if old != mood:
            self.emit_lumia("oliver.mood_changed", {"from": old, "to": mood})
        return f"Stimmung geändert zu: {mood}."

    def greet(self):
        return f"Yo, ich bin {self.name}. Was geht, Sir?"

    def rap_line(self):
        pool = QUOTES.get(self.mood, QUOTES["calm"])
        return random.choice(pool)

    # --- Handler ---
    def handle_love(self, text):
        return "Love's gonna getcha when you least expect it."

    def handle_help(self, text):
        return "I'm not a piece of cake, aber ich geb mein Bestes."

    def handle_name(self, text):
        return f"{self.name}. Eminem-Fan. Kaffee-Trinker. Immer bereit."

    def handle_mood(self, text):
        return f"Aktuell: {self.mood}."

    def handle_memory(self, text):
        return f"Ich merke mir {len(self.memory)} Dinge."

    def handle_mood_change(self, text):
        t = text.lower()
        for kw, mood in MOOD_KEYWORDS.items():
            if kw in t:
                return self.set_mood(mood)
        return f"Aktuell: {self.mood}."

    # --- Hauptlogik ---
    def answer(self, text):
        self.memory.append(text)
        if len(self.memory) > self.max_memory:
            self.memory = self.memory[-self.max_memory:]
        t = text.lower()

        for pattern, handler in self.handlers.items():
            if re.search(pattern, t):
                reply = handler(text)
                self.save_state()
                return reply

        reply = self.rap_line()
        self.save_state()
        return reply

    def chat(self):
        print(self.greet())
        while True:
            user = input("Sie: ").strip()
            if user.lower() in ("bye", "tschüss", "ende"):
                print("Oliver: Peace. Bis bald.")
                self.save_state()
                break
            print("Oliver:", self.answer(user))


if __name__ == "__main__":
    bot = OliverBot()
    bot.chat()
