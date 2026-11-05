# Requisitos y estimación de carga

Sistema: consulta de stock de una cadena de farmacias (ver [PROBLEMA.md](PROBLEMA.md)).

## 1. Requisitos funcionales

| ID | Requisito | Cliente | Tipo |
|---|---|---|---|
| RF1 | Buscar productos por nombre o principio activo | Web, app | Lectura (réplica) |
| RF2 | Ver el stock de un producto en todos los locales | Web, app | Lectura (réplica) |
| RF3 | Ver el detalle de un local (dirección, comuna) | Web, app | Lectura (réplica) |
| RF4 | Listar locales de una comuna | App | Lectura (réplica) |
| RF5 | Actualizar el stock de un local por lote (varios productos) | POS | Escritura (primaria) |
| RF6 | Confirmar al POS el stock recién escrito (*read-your-writes*) | POS | Lectura (primaria) |
| RF7 | Solo el POS puede escribir: requiere API key | POS | Seguridad (gateway) |
| RF8 | Exponer `GET /health` con estado e `INSTANCE_ID` | Operación | Monitoreo |

Endpoints:
- `GET /api/v1/productos?q=`
- `GET /api/v1/stock?producto_id=`
- `GET /api/v1/locales?comuna=`
- `POST /api/v1/stock`
- `GET /health`

## 2. Requisitos no funcionales

| ID | Requisito | Objetivo medible |
|---|---|---|
| RNF1 | Latencia de lectura | p95 < 300 ms vista desde el gateway |
| RNF2 | Latencia de escritura | p95 < 800 ms |
| RNF3 | Disponibilidad de lecturas | 99,5 % mensual (≈ 3,6 h caído al mes) |
| RNF4 | Disponibilidad de escrituras | 99 % mensual; el POS reintenta en el ciclo siguiente |
| RNF5 | Atraso máximo de la réplica | ≤ 30 s |
| RNF6 | RPO | ≤ 15 min (el POS reenvía la última sincronización) |
| RNF7 | RTO | ≤ 5 min sin escrituras; las lecturas siguen desde la réplica |
| RNF8 | Límite de peticiones | 60 peticiones/min por cliente público (web/app) |
| RNF9 | Escalabilidad | Soportar 250 lecturas/s en pico agregando instancias, sin cambiar código |

## 3. Estimación de carga

### Supuestos

| # | Supuesto | Valor |
|---|---|---|
| S1 | Locales hoy / en 3 años | 120 / 300 |
| S2 | Productos en catálogo hoy / en 5 años | 5.000 / 8.000 |
| S3 | Búsquedas de clientes por día | 200.000 |
| S4 | Lecturas por búsqueda (producto + stock) | 2 |
| S5 | Horario de sincronización de los POS | 12 h al día (9:00–21:00) |
| S6 | Frecuencia de sincronización | cada 15 min por local (4 por hora) |
| S7 | Productos modificados por sincronización | 5 en promedio |
| S8 | Tráfico en la hora punta | 15 % del día |
| S9 | Factor de emergencia sanitaria | ×5 |
| S10 | Tamaño de una fila con índices | Stock ~150 B · historial ~100 B |

### Lecturas

- Por día: 200.000 × 2 = **400.000 lecturas/día**
- Promedio: 400.000 / 86.400 s ≈ **4,6 lecturas/s**
- Hora punta: 400.000 × 15 % / 3.600 s ≈ **17 lecturas/s**
- Emergencia: 17 × 5 ≈ **85 lecturas/s**
- En 3 años (×3 usuarios, 300 locales): ≈ **250 lecturas/s** en pico

### Escrituras

- Por día: 120 locales × 4/h × 12 h = **5.760 escrituras/día** (≈ 28.800 filas modificadas)
- Promedio en las 24 horas: 5.760 / 86.400 ≈ **0,07 escrituras/s**
- Promedio en el horario de los POS: 120 × 4 / 3.600 s ≈ **0,13 escrituras/s**
- Hora punta: si todos los locales sincronizan en el mismo minuto, 120 / 60 = **2 escrituras/s**
- En 3 años (300 locales): **5 escrituras/s** en el peor minuto

**Relación lecturas : escrituras ≈ 400.000 : 5.760 ≈ 70 : 1.**

### Almacenamiento a 5 años

| Tabla | Cálculo | Tamaño |
|---|---|---|
| Local | 300 × ~500 B | < 1 MB |
| Producto | 8.000 × ~1 KB | ~8 MB |
| Stock actual | 300 locales × 8.000 productos × 150 B | ~360 MB |
| Historial de cambios de stock (auditoría, para medir el RPO) | 28.800 filas/día × 365 × 5 × 100 B (con 120 locales) | ~5,3 GB |
| | Con 300 locales | ~13 GB |
| **Total** (con un margen ×1,5 por WAL y crecimiento) | | **≈ 20 GB** |

La réplica guarda una copia completa, así que en total se necesitan unos 40 GB. Es un volumen pequeño: un solo PostgreSQL lo maneja sin problemas, sin necesidad de particionar.

## 4. Conclusiones para el diseño

- Con 85–250 lecturas/s en pico, una sola instancia podría saturarse y sería un punto único de falla. Por eso usamos **balanceador + 2 o más instancias**.
- Con una relación de 70:1, la mayor parte de la carga es de lectura. Por eso las lecturas van a la **réplica**, y la primaria queda solo para las escrituras.
- Con 3 clientes y permisos distintos (solo el POS escribe), se justifica un **API gateway** con API key y límite de peticiones.
