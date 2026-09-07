"""Fixtures partagées : le chargeur de doubles et une route locale scriptée."""

import importlib.util
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

DOUBLES_DIR = Path(__file__).resolve().parents[2] / "tests" / "doubles"


@pytest.fixture
def double():
    "Charge un double par nom : `tests/` n'est pas un paquet importable, on passe par le chemin."

    def load(name):
        spec = importlib.util.spec_from_file_location(f"doubles_{name}", DOUBLES_DIR / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        return module

    return load


def completion(content, finish_reason="stop", **message):
    "Corps de réponse au format de la route, tel qu'Ollama le rend sur `/v1/chat/completions`."

    return {
        "choices": [{"message": {"content": content, **message}, "finish_reason": finish_reason}],
        "usage": {"prompt_tokens": 11, "completion_tokens": 7},
    }


class _Handler(BaseHTTPRequestHandler):
    "Route locale scriptée : elle enregistre ce qu'elle reçoit et ce qu'elle a réellement accompli."

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        received = json.loads(self.rfile.read(length))
        self.server.requests.append(received)

        status, body, delay = self.server.scenario(received)
        if delay:
            time.sleep(delay)

        # l'effet est accompli avant l'écriture : un client qui abandonne ne l'annule pas
        self.server.effects.append(received)
        raw = json.dumps(body).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        except OSError:
            pass

    def do_GET(self):
        raw = json.dumps({"data": self.server.models}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


@pytest.fixture
def route(monkeypatch):
    "Démarre une vraie route locale sur un port libre et y branche `bridge`."

    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    server.requests = []
    server.effects = []
    server.scenario = lambda received: (200, completion("{}"), 0)
    server.models = [{"id": "pithos/ling-3.0-tiny:8b-16k", "meta": {"n_ctx_train": 16384}}]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("PITHOS_OLLAMA_URL", f"http://127.0.0.1:{server.server_port}")

    yield server

    server.shutdown()
    server.server_close()
