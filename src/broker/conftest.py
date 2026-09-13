"""Fixtures partagées : les doubles des dépendances, chargés par chemin."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest


@pytest.fixture
def trace(double):
    "Le journal en mémoire, neuf à chaque test."

    return double("journal")


class _Handler(BaseHTTPRequestHandler):
    "Route Telegram locale scriptée : elle enregistre chaque appel et rend ce que le test dicte."

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        received = json.loads(self.rfile.read(length)) if length else {}
        method = self.path.rsplit("/", 1)[-1]
        self.server.calls.append((method, received))

        status, body = self.server.scenario(method, received)
        raw = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


@pytest.fixture
def api(monkeypatch):
    "Démarre une vraie route locale sur un port libre et y branche le client Telegram."

    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    server.calls = []
    server.scenario = lambda method, received: (200, {"ok": True, "result": {"message_id": 1}})
    threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()
    monkeypatch.setenv("PITHOS_TELEGRAM_API", f"http://127.0.0.1:{server.server_port}")
    monkeypatch.setenv("PITHOS_TELEGRAM_TOKEN", "test-token")
    monkeypatch.setenv("PITHOS_TELEGRAM_CHAT", "77")
    monkeypatch.setenv("PITHOS_TELEGRAM_ALLOWLIST", "42")

    yield server

    server.shutdown()
    server.server_close()
