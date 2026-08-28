# Oliver Bot

Kleiner Eminem-Fan-Bot mit Stimmungswechsel, Persistenz und Lumia-Anschluss.

## Features
- Stimmungswechsel über Schlüsselwörter (müde, wütend, gut, hyped, ...)
- Persistenz in `oliver_state.json` (Stimmung + letzte 20 Erinnerungen)
- Lumia-Event-Bus: feuert `oliver.mood_changed`
- Regex-Handler mit Wortgrenzen (`\b`)

## Start
```bash
python python/oliver_bot.py
```
