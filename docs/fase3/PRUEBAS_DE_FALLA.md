# Pruebas de falla — Fase 3

Tres experimentos sobre el sistema corriendo en Docker Compose (18 nov 2026).
Para cada uno: **qué hice, qué pasó, cuánto duró y qué aprendí**.

> En Windows PowerShell usa `curl.exe`. Los comandos `docker compose` se ejecutan desde la carpeta del proyecto.
> Al terminar los experimentos se restaura todo con `docker compose down -v` y `docker compose up -d`.

## Resumen

| # | Falla | ¿El sistema siguió respondiendo? | Medición |
|---|---|---|---|
| 1 | Apagar una instancia (app-1) | **Sí**, 60 de 60 peticiones OK | 0 peticiones fallidas; app-1 vuelve a recibir tráfico 4 s después de encenderla |
| 2 | Cortar la réplica | **Sí**, pero con datos atrasados | La réplica mostró 10 unidades cuando la primaria tenía 99; atraso de 2.384 bytes de WAL. Con la réplica apagada, la app leyó de la primaria (`X-DB: primary`) |
| 3 | Matar la primaria y promover la réplica | Las lecturas sí; las escrituras no durante el cambio | **RPO = 0** (9 de 9 escrituras confirmadas sobrevivieron) · **RTO = 11,1 s** |

---

## Experimento 1: apagar una instancia de la aplicación

### Qué hice
Envié 60 peticiones seguidas a `GET /health` por el gateway (una cada 0,2 s). En la petición 15 apagué app-1:

```bash
docker compose stop app-1
```

### Qué pasó

```
200:app-1, 200:app-2, 200:app-1, 200:app-2 … (alternando 25 peticiones)
35 × 200:app-2
ok=60 fail=0
```

- **Ninguna petición falló.** Mientras app-1 terminaba de apagarse, NGINX siguió alternando; cuando dejó de responder, NGINX reintentó en app-2 (`proxy_next_upstream`) y la sacó de la rotación (`max_fails=1 fail_timeout=10s`).
- Al volver a encenderla (`docker compose start app-1`), **app-1 volvió a recibir tráfico a los 4 s**.

### Cuánto duró
- Interrupción para el cliente: **0 s**, porque ninguna petición falló.
- Recuperación de la instancia: **4 s**.

### Qué aprendí
- Como la aplicación es **sin estado**, cualquier instancia puede atender cualquier petición. Por eso perder una no afecta al cliente.
- El balanceador necesita *health checks* o reintentos. Sin `proxy_next_upstream`, la petición que llega justo cuando cae la instancia devolvería un error 502.

---

## Experimento 2: cortar la comunicación con la réplica

### 2a. Réplica atrasada (lecturas desactualizadas)

**Qué hice:** detuve la aplicación del WAL en la réplica, que simula que la réplica dejó de recibir cambios. Después el POS escribió 99 unidades y un cliente consultó 5 segundos más tarde.

```bash
docker compose exec db-replica psql -U app -d farmacias -c "SELECT pg_wal_replay_pause();"
curl.exe -i -X POST http://localhost:8000/api/v1/stock -H "apikey: cambiar_esto" -H "Content-Type: application/json" -d "{\"local_id\":1,\"items\":[{\"producto_id\":2,\"cantidad\":99}]}"
curl.exe -i "http://localhost:8000/api/v1/stock?producto_id=2"
```

**Qué pasó:**

| | Resultado |
|---|---|
| POST del POS | `201`, **`X-DB: primary`**, cantidad **99** (el POS ve su propia escritura) |
| GET del cliente | `200`, **`X-DB: replica`**, cantidad **10**: **dato desactualizado** |
| Primaria / réplica | 99 / 10 |
| Atraso medido | 2.384 bytes de WAL sin aplicar (`pg_stat_replication`) |

Al reanudar (`SELECT pg_wal_replay_resume();`), la réplica **se puso al día en ~2 s** y el GET mostró 99.

### 2b. Réplica caída

**Qué hice:** `docker compose stop db-replica` y una lectura.

**Qué pasó:** la lectura **no falló**. Respondió `200` con **`X-DB: primary`** porque la aplicación detectó que la réplica no respondía y leyó de la primaria (*fallback*). Esa respuesta tardó **7,9 s**, por el tiempo de espera de la conexión a la réplica caída. Al encender la réplica, las lecturas volvieron a `X-DB: replica`.

### Cómo lo maneja mi aplicación
1. **El POS nunca ve datos viejos:** el POST responde lo recién escrito, leído desde la primaria (*read-your-writes*).
2. **Los clientes pueden ver datos atrasados,** pero cada fila trae `actualizado_en` para saber qué tan reciente es.
3. **Si la réplica cae, se lee de la primaria,** y la cabecera `X-DB` lo deja visible.

### Qué aprendí
- La réplica asíncrona entrega **consistencia eventual**: mientras está atrasada, un cliente puede ver stock que ya no existe. En mi problema es aceptable hasta 30 s.
- El *fallback* funciona, pero es lento (7,9 s). **Mejora:** bajar `connect_timeout` y recordar por unos segundos que la réplica está caída, para no esperar en cada petición.
- Se debería **monitorear el atraso** (`pg_stat_replication`) y leer de la primaria si supera 30 s.

---

## Experimento 3: matar la primaria y promover la réplica

### Qué hice
1. Un "POS" enviaba un POST cada 0,5 s con una cantidad distinta (1001, 1002, …).
2. Maté la primaria de golpe, sin apagado ordenado:
   ```bash
   docker kill proyectofarmacias-db-primary-1
   ```
3. Promoví la réplica a primaria:
   ```bash
   docker compose exec db-replica psql -U app -d farmacias -c "SELECT pg_promote();"
   ```
4. Apunté las aplicaciones a la nueva primaria: en `.env` cambié `DB_PRIMARY_URL` de `@db-primary:5432` a `@db-replica:5432` y recreé las instancias:
   ```bash
   docker compose up -d --no-deps app-1 app-2
   ```

### Qué pasó (registro real de escrituras)

| Hora relativa | Cantidad | Código | Momento |
|---|---|---|---|
| −6,0 s … −0,3 s | 1001–1009 | **201** | Primaria funcionando |
| **0,0 s** | — | — | **`docker kill` de la primaria** |
| +0,4 s | 1010 | 503 | Primaria caída: la app responde "base primaria no disponible" |
| +1,1 s | 1011 | 503 | |
| +3,9 s | — | — | `pg_promote()` en la réplica |
| +5,0 s | — | — | Las apps se recrean apuntando a la nueva primaria |
| +5,7 s / +9,5 s | 1012, 1013 | 502 | Instancias reiniciándose |
| **+11,1 s** | 1014 | **201** | **Primera escritura exitosa en la nueva primaria** |
| +11,8 s … | 1015–1019 | 201 | Normal |

Comprobaciones en la nueva primaria:
- `pg_is_in_recovery()` = `f`: ya no es réplica, acepta escrituras.
- De las **9 escrituras confirmadas** (201) antes de la caída, **las 9 están** en `historial_stock`.
- Las lecturas siguieron funcionando durante todo el experimento, porque la réplica nunca se cayó.

### Cuánto duró: RPO y RTO

| Métrica | Objetivo (Fase 1) | Medido |
|---|---|---|
| **RPO** (datos perdidos) | ≤ 15 min | **0 escrituras confirmadas perdidas** |
| **RTO** (tiempo sin poder escribir) | ≤ 5 min | **11,1 s** |

Las escrituras 1010–1013 no se perdieron: fueron **rechazadas** (503/502), y el POS lo sabe y las reenvía en el siguiente ciclo. Lo que importa para el RPO es que nada que recibió un 201 desapareció.

### Qué aprendí
- **El RPO fue 0 por suerte, no por diseño:** la replicación es asíncrona, y con más carga podrían perderse las últimas transacciones que no alcanzaron a llegar a la réplica. Para garantizar RPO = 0 haría falta replicación **síncrona**, a cambio de más latencia en cada escritura.
- **El RTO de 11 s fue con los pasos automatizados en un script.** Hecho a mano por una persona tomaría 1–3 minutos; sigue dentro del objetivo de 5 min. Para bajarlo habría que automatizar el *failover* (por ejemplo, con Patroni).
- **Problema encontrado:** al recrear las instancias cambian sus IP y NGINX seguía usando las antiguas, lo que producía errores 502. Lo corregí agregando `resolver 127.0.0.11` y `resolve` en el `upstream` de NGINX, para que vuelva a resolver los nombres cada 5 s.
- **Riesgo de *split-brain*:** si la primaria antigua vuelve a encenderse, habría dos primarias. Hay que mantenerla apagada y reconstruirla como réplica de la nueva.

### Cómo volver al estado normal

```bash
docker compose down -v      # borra contenedores y datos de prueba
```
Devolver `DB_PRIMARY_URL` a `@db-primary:5432` en `.env` y luego:
```bash
docker compose up -d
```
