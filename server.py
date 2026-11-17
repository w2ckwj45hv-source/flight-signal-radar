"""Loopback-only app with a bounded background collection schedule."""
import argparse
import json
import signal
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from collector import Collector, ROOT, INTERVAL
from notify import send_events


def serve(port=8765):
    collector = Collector()
    stopping = threading.Event()
    origin = f"http://127.0.0.1:{port}"

    class Handler(SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            super().end_headers()

        def do_GET(self):
            if urlparse(self.path).path == "/api/status":
                self.reply(200, {"local": True, "interval": INTERVAL})
            elif any(part.startswith(".") for part in urlparse(self.path).path.split("/")):
                self.send_error(404)
            else:
                super().do_GET()

        def do_POST(self):
            if self.path != "/api/refresh":
                return self.reply(404, {"error": "Nicht gefunden"})
            if self.headers.get("Host") != f"127.0.0.1:{port}" or self.headers.get("Origin") != origin or self.headers.get("X-Radar-Request") != "refresh":
                return self.reply(403, {"error": "Nur aus der lokalen Radaransicht möglich"})
            try:
                self.reply(200, collector.collect())
            except (ValueError, OSError):
                self.reply(500, {"error": "Lokaler Datenstand nicht lesbar. Siehe README zur Wiederherstellung."})

        def reply(self, code, value):
            data = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, fmt, *args):
            pass

    def worker():
        while not stopping.is_set():
            try:
                state = collector.collect()
                if state["status"]["state"] == "ok":
                    send_events(state["events"])
                delay = max(1, state["status"].get("next_at", time.time()+INTERVAL) - time.time())
            except (ValueError, OSError):
                print("Lokalen Datenstand prüfen; Sammlung für 30 Minuten angehalten.", flush=True)
                delay = INTERVAL
            stopping.wait(delay)

    server = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(ROOT/"web")))
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    print(f"Flight Signal Radar: {origin} | Sammlung alle 30 Minuten | Strg+C stoppt", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stopping.set()
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    serve(parser.parse_args().port)
