"""Conservative comparisons of completed UTC hours, never incomplete live windows."""
import statistics
from datetime import datetime, timezone


def analyze(observations, now, region_id="rhein-main"):
    cutoff = int(now // 3600) * 3600
    buckets = {}
    for row in sorted(observations, key=lambda x: x["time"]):
        t = row["time"]
        if t >= cutoff or t < now - 100 * 86400:
            continue
        hour = int(t // 3600) * 3600
        # One value per expected half-hour slot; refresh clicks never add coverage.
        buckets.setdefault(hour, {})[int(t // 1800)] = row["count"]
    hourly = [{"time": h, "value": statistics.median(slots.values()),
               "coverage": len(slots) / 2, "samples": len(slots), "expected": 2}
              for h, slots in sorted(buckets.items())]
    result = {"state": "learning", "baseline_count": 0, "required": 8,
              "hourly": hourly, "events": [], "current": None}
    current = next((h for h in hourly if h["time"] == cutoff - 3600), None)
    if current is None:
        result["state"] = "coverage"
        return result
    result["current"] = current
    dt = datetime.fromtimestamp(current["time"], timezone.utc)
    previous = [h for h in hourly if h["time"] < current["time"] and h["coverage"] >= .8
                and datetime.fromtimestamp(h["time"], timezone.utc).weekday() == dt.weekday()
                and datetime.fromtimestamp(h["time"], timezone.utc).hour == dt.hour][-8:]
    result["baseline_count"] = len(previous)
    if current["coverage"] < .8:
        result["state"] = "coverage"
        return result
    if len(previous) < 8:
        return result
    mean = statistics.mean(h["value"] for h in previous)
    deviation = statistics.pstdev(h["value"] for h in previous)
    result.update(baseline_mean=mean, baseline_std=deviation)
    if deviation == 0:
        result["state"] = "no_variance"
        return result
    z = (current["value"] - mean) / deviation
    result.update(state="normal", z=z)
    if abs(z) > 2 and abs(current["value"] - mean) >= 5:
        result["state"] = "signal"
        result["events"] = [{"id": f"{region_id}:visible:{current['time']}",
                              "time": current["time"], "value": current["value"],
                              "baseline": mean, "z": round(z, 3), "coverage": current["coverage"],
                              "kind": "increase" if z > 0 else "decrease"}]
    return result
