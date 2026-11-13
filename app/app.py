"""Servicio de prueba (Fase 2).

Solo responde quién atendió la petición (INSTANCE_ID) en el cuerpo y en la
cabecera X-Instance. En la Fase 3 se reemplaza por la aplicación real.
No guarda nada en memoria ni en disco (sin estado).
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

INSTANCE_ID = os.environ.get("INSTANCE_ID", "desconocida")


class Handler(BaseHTTPRequestHandler):
    def _responder(self, status=200):
        body = {"instance": INSTANCE_ID, "method": self.command, "path": self.path}
        if self.path == "/health":
            body = {"status": "ok", "instance": INSTANCE_ID}
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Instance", INSTANCE_ID)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._responder()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        self._responder(201)

    def log_message(self, fmt, *args):
        print(f"[{INSTANCE_ID}] {self.command} {self.path}", flush=True)


if __name__ == "__main__":
    print(f"{INSTANCE_ID} escuchando en :8080", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
