import copy
import json
import tempfile
import unittest
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from collector import Collector, normalize
from signals import analyze

NOW = datetime(2026, 11, 17, 12, 10, tzinfo=timezone.utc).timestamp()
REGION = {"name": "Rhein-Main", "lat": 50.03, "lon": 8.57, "radius_nm": 100}


def payload(ac=None, stamp=NOW):
    return {"now": stamp * 1000, "ac": ac if ac is not None else [
        {"hex": "abc123", "lat": 50, "lon": 8.5, "seen_pos": 2,
         "flight": "TEST1 ", "alt_baro": 10000, "gs": 300, "track": 90}]}


def history(values, end=NOW):
    # Prior weeks plus last completed hour; two distinct slots per hour.
    hour = int(end // 3600) * 3600 - 3600
    return [{"time": hour - weeks * 7 * 86400 + slot * 1800 + 10, "count": count}
            for weeks, count in enumerate(values) for slot in range(2)]


class ValidationTests(unittest.TestCase):
    def test_units_and_unique_aircraft(self):
        p = payload(); p["ac"] *= 2
        snap = normalize(p, REGION, NOW)
        self.assertEqual(len(snap["aircraft"]), 1)
        self.assertEqual(snap["aircraft"][0]["callsign"], "TEST1")
        self.assertEqual(snap["aircraft"][0]["altitude_ft"], 10000)

    def test_empty_is_valid(self):
        self.assertEqual(normalize(payload([]), REGION, NOW)["aircraft"], [])

    def test_missing_list_and_old_or_future_source_rejected(self):
        for p in ({"now": NOW * 1000}, payload(stamp=NOW-601), payload(stamp=NOW+301)):
            with self.subTest(p=p), self.assertRaises(ValueError): normalize(p, REGION, NOW)

    def test_stale_invalid_and_outside_positions_ignored(self):
        aircraft = payload()["ac"][0]
        rows = [aircraft, {**aircraft, "hex": "bbb123", "seen_pos": 400},
                {**aircraft, "hex": "ccc123", "lat": 95},
                {**aircraft, "hex": "ddd123", "lat": 0},
                {**aircraft, "hex": "eee123", "lon": float("nan")}]
        self.assertEqual(len(normalize(payload(rows), REGION, NOW)["aircraft"]), 1)

    def test_all_bad_positions_are_quality_error_not_zero_traffic(self):
        with self.assertRaises(ValueError): normalize(payload([{"hex": "abc123"}]), REGION, NOW)


class SignalTests(unittest.TestCase):
    def test_warmup(self):
        self.assertEqual(analyze(history([20, 10]), NOW)["state"], "learning")

    def test_outlier_uses_only_previous_matching_hours(self):
        result = analyze(history([30, 9, 10, 11, 10, 9, 11, 10, 10]), NOW)
        self.assertEqual(result["state"], "signal")
        self.assertEqual(len(result["events"]), 1)
        self.assertEqual(result["baseline_count"], 8)
        self.assertEqual(result["events"][0]["value"], 30)

    def test_zero_variance_is_not_signal(self):
        self.assertEqual(analyze(history([30] + [10]*8), NOW)["state"], "no_variance")

    def test_tiny_difference_is_not_signal(self):
        self.assertEqual(analyze(history([13] + [9,10]*4), NOW)["events"], [])

    def test_repeated_slot_does_not_fill_gap(self):
        rows = history([30, 9, 10, 11, 10, 9, 11, 10, 10])
        rows = [r for r in rows if r["time"] != rows[1]["time"]]
        rows.append(copy.deepcopy(rows[0]))
        self.assertEqual(analyze(rows, NOW)["state"], "coverage")

    def test_current_hour_and_future_cannot_create_baseline(self):
        rows = [{"time": NOW+i, "count": 100} for i in range(10)]
        self.assertEqual(analyze(rows, NOW)["events"], [])

    def test_signal_id_is_stable(self):
        rows = history([30,9,10,11,10,9,11,10,10])
        self.assertEqual(analyze(rows, NOW)["events"], analyze(rows, NOW+30)["events"])


class StorageTests(unittest.TestCase):
    def test_degraded_partial_snapshot_does_not_count_as_traffic_measurement(self):
        with tempfile.TemporaryDirectory() as d:
            c = Collector(Path(d)/"state.json", REGION)
            degraded = payload(payload()["ac"] + [{"hex":"abc124"}]*99)
            with patch("collector.fetch", return_value=degraded), patch("collector.time.time", return_value=NOW):
                s = c.collect()
            self.assertEqual(s["latest"]["valid"], 1)
            self.assertEqual(s["observations"], [])
            self.assertFalse(s["latest"]["statistics_eligible"])

    def test_429_retry_after_is_persisted_across_restart(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"state.json"
            failure=urllib.error.HTTPError("https://example.com",429,"limit",{"Retry-After":"7200"},None)
            with patch("collector.fetch", side_effect=failure) as f, patch("collector.time.time", return_value=NOW):
                Collector(path,REGION).collect()
                self.assertEqual(f.call_count,1)
            with patch("collector.fetch",return_value=payload(stamp=NOW+1900)) as f, patch("collector.time.time",return_value=NOW+1900):
                Collector(path,REGION).collect()
                f.assert_not_called()

    def test_failure_preserves_last_good_snapshot_and_records_safe_error(self):
        with tempfile.TemporaryDirectory() as d:
            c = Collector(Path(d)/"state.json", REGION)
            with patch("collector.fetch", return_value=payload()), patch("collector.time.time", return_value=NOW):
                c.collect()
            original = json.loads(c.path.read_text())["latest"]
            with patch("collector.fetch", side_effect=ValueError("secret-token")), patch("collector.time.time", return_value=NOW+1900):
                c.collect()
            state = json.loads(c.path.read_text())
            self.assertEqual(state["latest"], original)
            self.assertEqual(state["status"]["state"], "error")
            self.assertNotIn("secret-token", c.path.read_text())

    def test_fast_repeat_does_not_fetch_twice(self):
        with tempfile.TemporaryDirectory() as d:
            c = Collector(Path(d)/"state.json", REGION)
            with patch("collector.fetch", return_value=payload()) as f, patch("collector.time.time", return_value=NOW):
                c.collect(); c.collect()
                self.assertEqual(f.call_count, 1)


if __name__ == "__main__": unittest.main()
