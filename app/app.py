"""API de consulta de stock de farmacias (Fase 3).

Contrato:
- Variables de entorno: DB_PRIMARY_URL, DB_REPLICA_URL, INSTANCE_ID
- GET /health -> 200 {"status", "instance"}
- Escrituras (POST) van a la PRIMARIA  -> cabecera X-DB: primary
- Lecturas (GET) van a la RÉPLICA      -> cabecera X-DB: replica
- Todas las respuestas llevan X-Instance
- Sin estado: no guarda nada en memoria ni en disco; abre una conexión por petición.
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import psycopg
from psycopg.rows import dict_row

INSTANCE_ID = os.environ.get("INSTANCE_ID", "desconocida")
DB_PRIMARY_URL = os.environ["DB_PRIMARY_URL"]
DB_REPLICA_URL = os.environ["DB_REPLICA_URL"]


def conectar(url):
    return psycopg.connect(url, row_factory=dict_row, connect_timeout=3)


def leer(sql, params=()):
    """Lee de la réplica. Si la réplica no responde, lee de la primaria (fallback)."""
    try:
        with conectar(DB_REPLICA_URL) as conn:
            return conn.execute(sql, params).fetchall(), "replica"
    except psycopg.OperationalError:
        with conectar(DB_PRIMARY_URL) as conn:
            return conn.execute(sql, params).fetchall(), "primary"


class Handler(BaseHTTPRequestHandler):
    def responder(self, status, body, db=None):
        data = json.dumps(body, ensure_ascii=False, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Instance", INSTANCE_ID)
        if db:
            self.send_header("X-DB", db)
        self.end_headers()
        self.wfile.write(data)

    # ---------- Lecturas ----------
    def do_GET(self):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if url.path == "/health":
                return self.responder(200, {"status": "ok", "instance": INSTANCE_ID})

            if url.path == "/api/v1/productos":
                texto = f"%{q.get('q', '')}%"
                filas, db = leer(
                    "SELECT id, nombre, principio_activo, presentacion FROM producto "
                    "WHERE nombre ILIKE %s OR principio_activo ILIKE %s ORDER BY id",
                    (texto, texto))
                return self.responder(200, filas, db)

            if url.path == "/api/v1/stock":
                if "producto_id" not in q:
                    return self.responder(400, {"error": "falta producto_id"})
                filas, db = leer(
                    "SELECT l.id AS local_id, l.nombre AS local, l.comuna, s.cantidad, s.actualizado_en "
                    "FROM stock s JOIN local l ON l.id = s.local_id "
                    "WHERE s.producto_id = %s ORDER BY s.cantidad DESC",
                    (int(q["producto_id"]),))
                return self.responder(200, filas, db)

            if url.path == "/api/v1/locales":
                filas, db = leer(
                    "SELECT id, nombre, comuna, direccion FROM local "
                    "WHERE %s = '' OR comuna ILIKE %s ORDER BY id",
                    (q.get("comuna", ""), q.get("comuna", "")))
                return self.responder(200, filas, db)

            return self.responder(404, {"error": "ruta no encontrada"})
        except ValueError:
            return self.responder(400, {"error": "parámetro inválido"})
        except psycopg.Error as e:
            return self.responder(503, {"error": "base de datos no disponible", "detalle": str(e).strip()})

    # ---------- Escrituras ----------
    def do_POST(self):
        url = urlparse(self.path)
        if url.path != "/api/v1/stock":
            return self.responder(404, {"error": "ruta no encontrada"})
        try:
            largo = int(self.headers.get("Content-Length", 0))
            datos = json.loads(self.rfile.read(largo) or b"{}")
            local_id = int(datos["local_id"])
            items = datos["items"]
            if not items:
                raise ValueError
            pares = [(int(i["producto_id"]), int(i["cantidad"])) for i in items]
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            return self.responder(400, {
                "error": "formato esperado: {\"local_id\": 1, \"items\": [{\"producto_id\": 1, \"cantidad\": 5}]}"})

        try:
            with conectar(DB_PRIMARY_URL) as conn:  # una transacción
                for producto_id, cantidad in pares:
                    conn.execute(
                        "INSERT INTO stock (local_id, producto_id, cantidad, actualizado_en) "
                        "VALUES (%s, %s, %s, now()) "
                        "ON CONFLICT (local_id, producto_id) "
                        "DO UPDATE SET cantidad = EXCLUDED.cantidad, actualizado_en = now()",
                        (local_id, producto_id, cantidad))
                    conn.execute(
                        "INSERT INTO historial_stock (local_id, producto_id, cantidad) VALUES (%s, %s, %s)",
                        (local_id, producto_id, cantidad))
                # Lectura de lo recién escrito: se confirma desde la PRIMARIA
                filas = conn.execute(
                    "SELECT producto_id, cantidad, actualizado_en FROM stock "
                    "WHERE local_id = %s AND producto_id = ANY(%s) ORDER BY producto_id",
                    (local_id, [p for p, _ in pares])).fetchall()
            return self.responder(201, {"local_id": local_id, "actualizado": filas}, "primary")
        except psycopg.errors.ForeignKeyViolation:
            return self.responder(400, {"error": "local o producto no existe"})
        except psycopg.errors.CheckViolation:
            return self.responder(400, {"error": "la cantidad no puede ser negativa"})
        except psycopg.Error as e:
            return self.responder(503, {"error": "base primaria no disponible", "detalle": str(e).strip()})

    def log_message(self, fmt, *args):
        print(f"[{INSTANCE_ID}] {self.command} {self.path}", flush=True)


if __name__ == "__main__":
    print(f"{INSTANCE_ID} escuchando en :8080", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
