import subprocess
import unittest
from unittest.mock import patch

from transport import request_json


class TransportTests(unittest.TestCase):
    def test_windows_subprocess_timeout_becomes_handled_network_timeout(self):
        with patch("transport.os.name", "nt"), patch("transport.subprocess.CREATE_NO_WINDOW", 0, create=True), patch("transport.subprocess.run", side_effect=subprocess.TimeoutExpired("curl", 30)):
            with self.assertRaises(TimeoutError):
                request_json("https://example.com")

    def test_secret_url_and_payload_are_not_command_arguments(self):
        result = subprocess.CompletedProcess([], 0, b'{"ok":true}\n200', b'')
        with patch("transport.os.name", "nt"), patch("transport.subprocess.CREATE_NO_WINDOW", 0, create=True), patch("transport.subprocess.run", return_value=result) as run:
            self.assertTrue(request_json("https://example.com/private-token", {"chat_id": "private-chat"})["ok"])
            args, kwargs = run.call_args
            self.assertNotIn("private-token", str(args))
            self.assertNotIn("private-chat", str(args))
            self.assertIn(b"private-token", kwargs["input"])


if __name__ == "__main__":unittest.main()
