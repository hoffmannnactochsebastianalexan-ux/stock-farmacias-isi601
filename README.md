# Stock Farmacias — ISI601 Proyecto individual

API de consulta de stock de una cadena de farmacias con API Gateway, balanceador de carga,
2 instancias de la aplicación y PostgreSQL 16 con réplica por streaming.

```
Clientes ──► Kong (gateway, :8000) ──► NGINX (balanceador) ──► app-1 / app-2
                                                                  │      │
                                              escrituras ──► db-primary ─(WAL)─► db-replica ◄── lecturas
```

- Problemática: [docs/fase1/PROBLEMA.md](docs/fase1/PROBLEMA.md)
- Diseño (Fase 1): [docs/fase1/DISENO.md](docs/fase1/DISENO.md)
- Evidencias (Fase 2): [docs/fase2/EVIDENCIAS.md](docs/fase2/EVIDENCIAS.md)
- Bitácora: [BITACORA.md](BITACORA.md)

## Requisitos

- Docker Desktop (con Docker Compose v2) encendido
- Git

## Cómo levantar el sistema (desde cero)

1. Clonar el repositorio y entrar a la carpeta:
   ```bash
   git clone https://github.com/hoffmannnactochsebastianalexan-ux/stock-farmacias-isi601.git
   cd stock-farmacias-isi601
   ```
2. Crear el archivo `.env` a partir del ejemplo (en Windows PowerShell: `copy .env.example .env`):
   ```bash
   cp .env.example .env
   ```
3. Levantar todo:
   ```bash
   docker compose up -d --build
   ```
4. Comprobar que funciona (en PowerShell usa `curl.exe`):
   ```bash
   docker compose ps
   curl -i http://localhost:8000/api/v1/stock
   ```

Para apagar: `docker compose down`. Para borrar también los datos: `docker compose down -v`.

## Cómo probar la aplicación

En Windows PowerShell usa `curl.exe`. Todas las respuestas traen `X-Instance` (qué instancia respondió) y `X-DB` (qué base atendió).

| Acción | Comando | Base |
|---|---|---|
| Salud | `curl.exe -i http://localhost:8000/health` | — |
| Buscar productos | `curl.exe -i "http://localhost:8000/api/v1/productos?q=ibu"` | réplica |
| Stock de un producto por local | `curl.exe -i "http://localhost:8000/api/v1/stock?producto_id=1"` | réplica |
| Locales de una comuna | `curl.exe -i "http://localhost:8000/api/v1/locales?comuna=Santiago"` | réplica |
| Actualizar stock (POS) | `curl.exe -i -X POST http://localhost:8000/api/v1/stock -H "apikey: cambiar_esto" -H "Content-Type: application/json" -d "@ejemplos/stock.json"` | primaria |

Formato del POST: `{"local_id": 2, "items": [{"producto_id": 1, "cantidad": 12}]}`.

### Lectura de lo recién escrito

- El **POST** responde con el stock recién guardado leído desde la **primaria** (`X-DB: primary`), así el POS confirma su propia escritura sin esperar a la réplica (*read-your-writes*).
- Los **GET** leen de la **réplica** (`X-DB: replica`). Justo después de un POST pueden mostrar el valor anterior durante el atraso de la réplica (normalmente menos de 1 s; el objetivo es ≤ 30 s). Cada fila trae `actualizado_en` para saber qué tan reciente es.
- Si la réplica no responde, la aplicación lee de la primaria y lo indica con `X-DB: primary`.

## Componentes

| Servicio | Imagen | Función |
|---|---|---|
| `gateway` | kong:3.6 (sin BD) | Única entrada (puerto 8000). Rutas `/api/v1/*` y `/health`. API key para POST, límite de peticiones para GET |
| `balanceador` | nginx:1.27 | Round-robin entre app-1 y app-2; retira la instancia caída |
| `app-1`, `app-2` | `./app` (Python + psycopg) | Aplicación real, sin estado. POST → primaria, GET → réplica; cabeceras `X-Instance` y `X-DB` |
| `db-primary` | postgres:16 | Escrituras. Crea el usuario de replicación, el slot y el esquema |
| `db-replica` | postgres:16 | Lecturas. Se copia con `pg_basebackup` y sigue a la primaria por streaming |

## Configuración

Las variables están en `.env` (no se sube a Git); `.env.example` tiene valores de ejemplo:
`POSTGRES_*`, `REPLICATION_*`, `DB_PRIMARY_URL`, `DB_REPLICA_URL` y `API_KEY_POS`.

## Estado

- [x] Fase 1 — Diseño (etiqueta `fase-1`)
- [x] Fase 2 — Arquitectura en Docker
- [ ] Fase 3 — Aplicación real y pruebas de falla
