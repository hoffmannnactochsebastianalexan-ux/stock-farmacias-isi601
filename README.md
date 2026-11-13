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

## Componentes

| Servicio | Imagen | Función |
|---|---|---|
| `gateway` | kong:3.6 (sin BD) | Única entrada (puerto 8000). Rutas `/api/v1/*` y `/health`. API key para POST, límite de peticiones para GET |
| `balanceador` | nginx:1.27 | Round-robin entre app-1 y app-2; retira la instancia caída |
| `app-1`, `app-2` | `./app` (Python) | Sin estado. En la Fase 2 es un servicio de prueba que responde `X-Instance` |
| `db-primary` | postgres:16 | Escrituras. Crea el usuario de replicación, el slot y el esquema |
| `db-replica` | postgres:16 | Lecturas. Se copia con `pg_basebackup` y sigue a la primaria por streaming |

## Configuración

Las variables están en `.env` (no se sube a Git); `.env.example` tiene valores de ejemplo:
`POSTGRES_*`, `REPLICATION_*`, `DB_PRIMARY_URL`, `DB_REPLICA_URL` y `API_KEY_POS`.

## Estado

- [x] Fase 1 — Diseño (etiqueta `fase-1`)
- [x] Fase 2 — Arquitectura en Docker
- [ ] Fase 3 — Aplicación real y pruebas de falla
