"""Optional Telegram delivery; secrets remain in the process environment."""
import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from collector import ROOT, atomic_write
from transport import request_json


def send_events(events, ledger=None, now=None, test=False):
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN", ""), os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat:
        return "not_configured"
    if not re.fullmatch(r"\d+:[A-Za-z0-9_-]+", token) or not re.fullmatch(r"-?\d+", chat):
        return "invalid_config"
    now = time.time() if now is None else now
    ledger = Path(ledger or ROOT / ".local/sent.json")
    record = json.loads(ledger.read_text(encoding="utf-8")) if ledger.exists() else {"sent": [], "last_attempt": 0}
    if now-record["last_attempt"] < 60:
        return "cooldown"
    pending = [e for e in events if e["id"] not in record["sent"] and 0 <= now-e["time"] <= 7200]
    if not pending and not test:
        return "nothing_new"
    if test:
        message = "TEST · Flight Signal Radar\nDie Verbindung steht. Dies ist keine gemessene Auffälligkeit."
        event = None
    else:
        event = sorted(pending, key=lambda e:e["time"])[-1]
        stamp = datetime.fromtimestamp(event["time"], timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
        message = (f"Flight Signal Radar · Rhein-Main\n{stamp}\n"
                   f"Stundenmedian: {event['value']} sichtbare Flugzeuge\nVergleich: {event['baseline']:.1f}; z={event['z']:.2f}\n"
                   f"Abdeckung: {event['coverage']:.0%}\nPrüfhinweis zur Sichtbarkeit im Empfangsnetz. Kein Börsensignal.\n"
                   "Quelle: adsb.lol · ODbL 1.0")
        public_url = os.environ.get("RADAR_PUBLIC_URL", "")
        if public_url.startswith("https://") and not any(c in public_url for c in "\r\n"):
            message += "\n" + public_url
    # Save the attempt before contacting Telegram, bounding retries after ambiguous responses.
    record["last_attempt"] = now
    atomic_write(ledger, record)
    try:
        response = request_json(f"https://api.telegram.org/bot{token}/sendMessage",
                                {"chat_id": chat, "text": message, "disable_web_page_preview": True})
        if response.get("ok") is not True:
            return "failed"
    except (ValueError, OSError, TimeoutError):
        return "failed"
    if event:
        record["sent"] = (record["sent"] + [event["id"]])[-1000:]
    atomic_write(ledger, record)
    return "sent"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Eine ausdrücklich markierte Testnachricht senden")
    parser.add_argument("--ledger", type=Path, default=ROOT / ".local/sent.json")
    args = parser.parse_args()
    state_path = ROOT / "web/data/state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"events": []}
    result = send_events(state["events"], ledger=args.ledger, test=args.test)
    print(result)
    raise SystemExit(0 if result in ("sent", "nothing_new", "cooldown", "not_configured") else 1)
