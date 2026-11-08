#!/usr/bin/env python3
"""Puente local Groq para DeepSeek Harness.

dsh acepta cualquier endpoint OpenAI-compatible, pero necesita una clave
que Marco no tiene a la mano (la guardada en la bóveda no se puede leer
de vuelta) y él no tiene computadora para ponerla. Este puente corre en
la máquina de Pecas: dsh apunta a http://127.0.0.1:8080/v1 sin clave, y
el puente reenvía a Groq usando el mecanismo del conector. La clave real
nunca sale de la bóveda ni pasa por este archivo.

Endpoints: GET /v1/models, POST /v1/chat/completions (con y sin stream).

Uso:
    python3 proxy.py [--port PUERTO]
"""
import argparse
import json
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from dynamic_credentials import add_surrogate_to_request

GROQ_BASE = "https://api.groq.com/openai/v1"
HOSTS = ["api.groq.com"]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise RuntimeError("redirect refused, verify the endpoint")


def groq_request(path, method="GET", payload=None, stream=False):
    """Llama a Groq con el mecanismo del conector. Devuelve la respuesta
    abierta (para stream) o el JSON (sin stream)."""
    url = f"{GROQ_BASE}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")
    request.add_header("Accept", "application/json")
    if data is not None:
        request.add_header("Content-Type", "application/json")
    add_surrogate_to_request(request, "custom.groq", allowed_hosts=HOSTS)
    return urllib.request.build_opener(NoRedirect()).open(
        request, timeout=300 if stream else 60
    )


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send_json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/v1/models", "/models"):
            try:
                with groq_request("/models") as resp:
                    self._send_json(200, json.load(resp))
            except urllib.error.HTTPError as exc:
                self._send_json(exc.code, json.loads(exc.read() or b"{}"))
            except Exception as exc:
                self._send_json(502, {"error": str(exc)})
        else:
            self._send_json(404, {"error": "no existe"})

    def do_POST(self):
        if self.path not in ("/v1/chat/completions", "/chat/completions"):
            self._send_json(404, {"error": "no existe"})
            return
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        try:
            resp = groq_request("/chat/completions", method="POST", payload=payload, stream=bool(payload.get("stream")))
        except urllib.error.HTTPError as exc:
            self._send_json(exc.code, json.loads(exc.read() or b"{}"))
            return
        except Exception as exc:
            self._send_json(502, {"error": str(exc)})
            return
        if payload.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            try:
                for line in resp:
                    self.wfile.write(line)
                    self.wfile.flush()
            finally:
                resp.close()
        else:
            with resp:
                self._send_json(200, json.load(resp))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Puente Groq en http://127.0.0.1:{args.port}/v1", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
