# Glosario para estudiar

Cada concepto tiene: **qué es** y **cómo aparece en mi proyecto**. Los marcados con ⭐ son los más probables en las preguntas.

## 1. Arquitectura

| Concepto | Qué es | En mi proyecto |
|---|---|---|
| ⭐ **API** | Conjunto de "puertas" (URL) por las que un programa pide o envía datos a otro | `GET /api/v1/stock`, `POST /api/v1/stock` |
| **Endpoint** | Una de esas puertas: una URL más un método | `GET /health` |
| **GET / POST** | GET pide datos (lectura); POST envía datos para guardar (escritura) | Los clientes hacen GET; el POS hace POST |
| **Código HTTP** | Número que indica cómo terminó la petición | 200 OK, 201 creado, 401 sin permiso, 429 demasiadas peticiones |
| **Cabecera (header)** | Dato extra que viaja con la petición o la respuesta | `X-Instance`, `X-DB`, `apikey` |
| ⭐ **API Gateway** | Única puerta de entrada al sistema; decide quién entra y a dónde va | Kong: rutas `/api/v1`, API key y límite de peticiones |
| ⭐ **API key** | Clave que identifica a un cliente autorizado | Solo el POS la tiene y puede escribir; sin ella → 401 |
| ⭐ **Rate limiting** | Límite de peticiones por cliente en un tiempo | 10 por minuto (demo); al pasarse → 429 |
| ⭐ **Balanceador de carga** | Reparte las peticiones entre varias copias de la app | NGINX entre app-1 y app-2 |
| **Round-robin** | Reparto por turnos: una a cada uno | app-1, app-2, app-1, app-2… |
| **Health check** | Comprobar si un servicio está vivo | `GET /health`; NGINX saca a la instancia que no responde |
| **Instancia** | Una copia de la aplicación corriendo | app-1 y app-2 |
| ⭐ **Sin estado (stateless)** | La app no guarda datos en su memoria ni en su disco; todo está en la BD | Cualquier instancia puede atender cualquier petición |
| **Escalar horizontalmente** | Crecer agregando más instancias | Pasar de 2 a 5 instancias si sube la carga |
| **Escalar verticalmente** | Crecer con una máquina más potente | Más CPU o RAM a un solo servidor |

## 2. Base de datos

| Concepto | Qué es | En mi proyecto |
|---|---|---|
| **PostgreSQL** | Motor de base de datos relacional | Versión 16 |
| ⭐ **Primaria** | La base donde se escribe; es la fuente de verdad | `db-primary`: recibe los POST |
| ⭐ **Réplica de lectura** | Copia automática de la primaria, solo para leer | `db-replica`: atiende las consultas |
| **WAL (Write-Ahead Log)** | Registro de cada cambio que hace la primaria | Se envía a la réplica |
| ⭐ **Replicación por streaming** | La primaria envía el WAL a la réplica de forma continua | Probado: inserto en la primaria y aparece en la réplica |
| **Asíncrona vs síncrona** | Asíncrona: la primaria no espera a la réplica. Síncrona: espera la confirmación de la réplica | Uso asíncrona: más rápida, pero se pueden perder unos segundos |
| **Replication lag (atraso)** | Cuánto va atrasada la réplica | Objetivo ≤ 30 s |
| **Hot standby** | Réplica que acepta lecturas mientras replica | La mía rechaza INSERT: "read-only transaction" |
| **pg_basebackup** | Copia inicial completa de la primaria para crear la réplica | Se ejecuta la primera vez que arranca la réplica |
| **Slot de replicación** | Hace que la primaria guarde el WAL hasta que la réplica lo reciba | `replica_slot` |
| ⭐ **Promover la réplica** | Convertir la réplica en la nueva primaria cuando la primaria cae | `pg_promote()`; se prueba en la Fase 3 |
| **Failover** | Cambiar a un componente de respaldo cuando el principal falla | Promover la réplica |

## 3. Confiabilidad

| Concepto | Qué es | En mi proyecto |
|---|---|---|
| ⭐ **RPO** (Recovery Point Objective) | Cuántos **datos** puedo perder como máximo | ≤ 15 min (un ciclo del POS) |
| ⭐ **RTO** (Recovery Time Objective) | Cuánto **tiempo** puede estar caído el sistema | ≤ 5 min sin escribir |
| ⭐ **SPOF** (punto único de falla) | Componente que, si falla, hace caer todo | Gateway, balanceador, primaria y el host |
| **Disponibilidad** | Porcentaje del tiempo en que el sistema funciona | 99,5 % para lecturas |
| ⭐ **Consistencia eventual** | Los datos se igualan "eventualmente", tras un pequeño atraso | La réplica puede mostrar el dato de hace unos segundos |
| **Read-your-writes** | Quien escribe ve de inmediato lo que escribió | El POS confirma leyendo de la primaria |
| **Latencia** | Cuánto tarda en llegar la respuesta | Objetivo p95 < 300 ms |
| **p95** | El 95 % de las peticiones tarda menos que ese valor | 95 de cada 100 lecturas en menos de 300 ms |

## 4. Estimación de carga

| Concepto | Qué es | En mi proyecto |
|---|---|---|
| ⭐ **Relación lecturas : escrituras** | Cuántas lecturas hay por cada escritura | 70 : 1 |
| **Peticiones por segundo (RPS)** | Carga del sistema | 4,6 en promedio, 17 en hora punta, 85 en emergencia |
| **Hora punta** | Momento de más tráfico | 15 % del día en 1 hora |
| **Supuesto** | Dato asumido para poder calcular | 200.000 búsquedas al día, 120 locales… |

## 5. Docker y herramientas

| Concepto | Qué es | En mi proyecto |
|---|---|---|
| **Docker** | Corre programas en "contenedores" aislados | Cada pieza es un contenedor |
| **Imagen** | Plantilla con la que se crea un contenedor | `postgres:16`, `nginx:1.27`, `kong:3.6` |
| **Contenedor** | Una imagen en ejecución | `proyectofarmacias-app-1-1` |
| ⭐ **Docker Compose** | Define y levanta varios contenedores con un solo archivo | `docker-compose.yml` + `docker compose up -d` |
| **Volumen** | Disco que guarda datos aunque el contenedor se borre | `primary-data`, `replica-data` |
| **Puerto expuesto** | Puerto accesible desde fuera de Docker | Solo el 8000 (el gateway) |
| **Variable de entorno** | Configuración que se pasa al programa desde fuera | `INSTANCE_ID`, `DB_PRIMARY_URL`, `DB_REPLICA_URL` |
| **.env** | Archivo con contraseñas; no se sube a Git | Se sube solo `.env.example` |
| **Kong** | Software de API Gateway | Modo sin base de datos (archivo `kong.yml`) |
| **NGINX** | Servidor web usado como balanceador | `upstream` con app-1 y app-2 |
| **Git / commit / push / tag** | Control de versiones / guardar un cambio / subirlo a GitHub / marcar una versión | Etiquetas `fase-1`, `fase-2` |
