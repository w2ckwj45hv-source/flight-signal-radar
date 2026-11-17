"""Small free-data collector. Only the Python standard library is needed."""
import argparse
import json
import math
import os
import re
import tempfile
import threading
import time
import urllib.error
import urllib.request
from email.utils import parsedate_to_datetime
from pathlib import Path

from signals import analyze
from transport import request_json

ROOT = Path(__file__).resolve().parent
REGION = {"id": "rhein-main", "name": "Rhein-Main", "lat": 50.03, "lon": 8.57, "radius_nm": 100}
SOURCE = {"name": "adsb.lol", "url": "https://www.adsb.lol",
          "license": "ODbL 1.0", "license_url": "https://opendatacommons.org/licenses/odbl/1-0/",
          "docs": "https://www.adsb.lol/docs/open-data/api"}
INTERVAL = 1800


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def distance_nm(lat1, lon1, lat2, lon2):
    a, b = math.radians(lat1), math.radians(lat2)
    dlat, dlon = b-a, math.radians(lon2-lon1)
    h = math.sin(dlat/2)**2 + math.cos(a)*math.cos(b)*math.sin(dlon/2)**2
    return 3440.065 * 2 * math.asin(min(1, math.sqrt(h)))


def normalize(payload, region, now):
    if not isinstance(payload, dict) or not isinstance(payload.get("ac"), list):
        raise ValueError("Ungültige Antwortstruktur")
    stamp = payload.get("now")
    if not finite(stamp):
        raise ValueError("Messzeit fehlt")
    stamp /= 1000  # readsb v2 exposes epoch milliseconds.
    if now - stamp > 300 or stamp - now > 120:
        raise ValueError("Quellenzeit veraltet oder in der Zukunft")
    aircraft = {}
    positional = 0
    for a in payload["ac"]:
        if not isinstance(a, dict):
            continue
        key = a.get("hex", "")
        lat, lon, seen = a.get("lat"), a.get("lon"), a.get("seen_pos")
        if not isinstance(key, str) or not re.fullmatch(r"~?[a-fA-F0-9]{6}", key):
            continue
        if not all(finite(v) for v in (lat, lon, seen)) or not (-90 <= lat <= 90 and -180 <= lon <= 180 and 0 <= seen <= 120):
            continue
        positional += 1
        if distance_nm(region["lat"], region["lon"], lat, lon) > region["radius_nm"]:
            continue
        key = key.lower()
        item = {"id": key, "callsign": str(a.get("flight") or "").strip()[:16],
                "registration": str(a.get("r") or "")[:16], "type": str(a.get("t") or "")[:12],
                "lat": lat, "lon": lon, "observed_at": stamp - seen,
                "altitude_ft": a.get("alt_baro") if finite(a.get("alt_baro")) else None,
                "ground": a.get("alt_baro") == "ground",
                "speed_kt": a.get("gs") if finite(a.get("gs")) and a["gs"] >= 0 else None,
                "track": a.get("track") % 360 if finite(a.get("track")) else None}
        if key not in aircraft or item["observed_at"] > aircraft[key]["observed_at"]:
            aircraft[key] = item
    if payload["ac"] and not positional:
        raise ValueError("Keine verwendbaren Positionen in nichtleerer Antwort")
    return {"measured_at": stamp, "fetched_at": now, "aircraft": sorted(aircraft.values(), key=lambda a: a["id"]),
            "received": len(payload["ac"]), "valid": len(aircraft),
            "statistics_eligible": not payload["ac"] or positional / len(payload["ac"]) >= .8,
            "discarded": len(payload["ac"]) - len(aircraft)}


def fetch(region):
    url = f"https://api.adsb.lol/v2/lat/{region['lat']}/lon/{region['lon']}/dist/{region['radius_nm']}"
    return request_json(url)


def atomic_write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)


class Collector:
    def __init__(self, path=None, region=None):
        self.path = Path(path or ROOT / "web/data/state.json")
        self.region = region or REGION
        self.lock = threading.Lock()
        self.last_attempt = 0

    def load(self):
        if self.path.exists():
            # Corrupt state is never silently overwritten: restore a backup or inspect it.
            with self.path.open(encoding="utf-8") as f:
                state = json.load(f)
            if state.get("schema") != 1 or state.get("region") != self.region:
                raise ValueError("Zustand passt nicht zur Region oder Version")
            return state
        return {"schema": 1, "region": self.region, "source": SOURCE,
                "latest": None, "observations": [], "events": [], "log": [],
                "status": {"state": "empty"}, "analysis": analyze([], time.time())}

    def collect(self):
        with self.lock:
            now = time.time()
            state = self.load()
            # Persisted cooldown also survives restarting the process.
            attempted = max(self.last_attempt, state["status"].get("attempted_at", 0))
            if now - attempted < 300 or now < state["status"].get("retry_not_before", 0):
                return state
            self.last_attempt = now
            status = {"attempted_at": now, "next_at": now + INTERVAL, "interval_seconds": INTERVAL}
            try:
                snap = normalize(fetch(self.region), self.region, now)
                state["latest"] = snap
                slot = int(snap["measured_at"] // INTERVAL)
                rows = [r for r in state["observations"]
                        if r["time"] > now - 100*86400 and int(r["time"] // INTERVAL) != slot]
                if snap["statistics_eligible"]:
                    rows.append({"time": snap["measured_at"], "count": snap["valid"]})
                state["observations"] = sorted(rows, key=lambda r: r["time"])
                status.update(state="ok", message="Positionen erfolgreich geprüft", last_success=now)
                if not snap["statistics_eligible"]:
                    status["message"] = "Teilweise verwendbare Positionen; wegen Datenlücken nicht statistisch gezählt."
            except (ValueError, OSError, TimeoutError, urllib.error.URLError) as exc:
                message = "Quelle nicht erreichbar. Letzter gültiger Stand bleibt erhalten."
                if isinstance(exc, ValueError): message = "Quellenantwort nicht verwendbar. Letzter gültiger Stand bleibt erhalten."
                if isinstance(exc, urllib.error.HTTPError) and exc.code == 429:
                    message = "Abrufgrenze erreicht. Nächster Versuch frühestens in 30 Minuten."
                    header = (exc.headers or {}).get("Retry-After") or (exc.headers or {}).get("retry-after")
                    delay = 1800
                    if header:
                        try:
                            delay = max(delay, float(header))
                        except ValueError:
                            try:
                                delay = max(delay, parsedate_to_datetime(header).timestamp()-now)
                            except (ValueError, TypeError, OverflowError):
                                pass
                    status["retry_not_before"] = now + delay
                    status["next_at"] = now + delay
                status.update(state="error", message=message, last_success=state["status"].get("last_success"))
            state["status"] = status
            analysis = analyze(state["observations"], now, self.region.get("id", "rhein-main"))
            # A failed fetch cannot issue a new traffic signal from old observations.
            if status["state"] == "ok":
                known = {e["id"] for e in state["events"]}
                state["events"].extend(e for e in analysis["events"] if e["id"] not in known)
            state["events"] = [e for e in state["events"] if e["time"] > now-100*86400][-100:]
            state["analysis"] = analysis
            state["log"] = ([{"time": now, "state": status["state"], "message": status["message"]}] + state["log"])[:50]
            atomic_write(self.path, state)
            return state


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Einen kostenlosen Flugdatensatz sammeln")
    parser.add_argument("--output", type=Path, default=ROOT / "web/data/state.json")
    args = parser.parse_args()
    result = Collector(args.output).collect()
    print(json.dumps({"status": result["status"], "count": (result["latest"] or {}).get("valid")}, ensure_ascii=False))
    raise SystemExit(0 if result["status"]["state"] == "ok" else 1)
