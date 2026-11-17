"""HTTPS with platform certificate validation, including Windows' native trust store."""
import json
import os
import subprocess
import urllib.error
import urllib.request


def request_json(url, data=None):
    if not url.startswith("https://") or any(c in url for c in "\r\n"):
        raise ValueError("HTTPS-Adresse erforderlich")
    headers = {"User-Agent": "FlightSignalRadar/1.0 (personal learning project)", "Accept": "application/json"}
    encoded = None if data is None else json.dumps(data).encode("utf-8")
    if data is not None: headers["Content-Type"] = "application/json"
    if os.name == "nt":
        # Use Schannel instead of the bundled OpenSSL trust chain. No insecure flags.
        # URL and body go through stdin so optional bot tokens never enter process arguments.
        config = ["url = " + json.dumps(url)]
        config.extend("header = " + json.dumps(k+": "+v) for k, v in headers.items())
        if encoded is not None: config.append("data = " + json.dumps(encoded.decode("utf-8")))
        curl = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "curl.exe")
        try:
            result = subprocess.run([curl, "--config", "-", "--silent", "--show-error", "--max-time", "25",
                                     "--max-filesize", "5000000", "--dump-header", "-", "--write-out", "\n%{http_code}"],
                                    input="\n".join(config).encode("utf-8"), capture_output=True, timeout=30,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
        except subprocess.TimeoutExpired:
            raise TimeoutError("HTTPS-Zeitlimit erreicht") from None
        if result.returncode:
            raise OSError("HTTPS-Anfrage fehlgeschlagen")
        raw, code = result.stdout.rsplit(b"\n", 1)
        response_headers = {}
        while raw.startswith(b"HTTP/"):
            header_block, raw = raw.split(b"\r\n\r\n", 1)
            response_headers = {}
            for line in header_block.split(b"\r\n")[1:]:
                if b":" in line:
                    key, value = line.split(b":", 1)
                    response_headers[key.decode("latin-1").lower()] = value.decode("latin-1").strip()
        status = int(code)
        if status >= 400:
            raise urllib.error.HTTPError("https://redacted.invalid", status, "HTTP-Anfrage fehlgeschlagen", response_headers, None)
    else:
        request = urllib.request.Request(url, data=encoded, headers=headers)
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read(5_000_001)
    if len(raw) > 5_000_000:
        raise ValueError("Antwort zu groß")
    return json.loads(raw)
