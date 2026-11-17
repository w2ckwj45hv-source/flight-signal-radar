import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from notify import send_events


class NotificationTests(unittest.TestCase):
    def test_unconfigured_sends_nothing(self):
        with tempfile.TemporaryDirectory() as d, patch.dict("os.environ", {}, clear=True), patch("notify.request_json") as request:
            self.assertEqual(send_events([], Path(d)/"sent.json"), "not_configured")
            request.assert_not_called()

    def test_acknowledged_event_is_not_resent(self):
        with tempfile.TemporaryDirectory() as d, patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN":"12345:abc_DEF", "TELEGRAM_CHAT_ID":"12345"}, clear=True), patch("notify.request_json", return_value={"ok":True}) as request:
            event = {"id":"rhein-main:visible:1", "time":1, "value":30, "baseline":10,"z":3,"coverage":1,"kind":"increase"}
            path=Path(d)/"sent.json"
            self.assertEqual(send_events([event], path, now=100), "sent")
            send_events([event], path, now=200)
            self.assertEqual(request.call_count, 1)
            self.assertNotIn("abc_DEF", path.read_text())

    def test_failure_is_not_logged_as_delivered(self):
        with tempfile.TemporaryDirectory() as d, patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN":"12345:abc_DEF", "TELEGRAM_CHAT_ID":"12345"}, clear=True), patch("notify.request_json", return_value={"ok":False}):
            path=Path(d)/"sent.json"
            event={"id":"x", "time":1,"value":30,"baseline":10,"z":3,"coverage":1,"kind":"increase"}
            self.assertEqual(send_events([event],path,now=100),"failed")
            self.assertEqual(json.loads(path.read_text())["sent"],[])

    def test_old_event_is_not_sent_on_first_setup(self):
        with tempfile.TemporaryDirectory() as d, patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN":"12345:abc_DEF", "TELEGRAM_CHAT_ID":"12345"}, clear=True), patch("notify.request_json") as request:
            event={"id":"x","time":1,"value":30,"baseline":10,"z":3,"coverage":1,"kind":"increase"}
            send_events([event],Path(d)/"sent.json",now=86400)
            request.assert_not_called()


if __name__=="__main__":unittest.main()
