# Bitácora

## Mié 4 nov
- **Qué hice hoy:** creé el repositorio con la estructura recomendada y elegí la problemática (consulta de stock de una cadena de farmacias) en `docs/fase1/PROBLEMA.md`.
- **Dónde me trabé:** estimar cuántas escrituras hacen los POS; decidí que sincronizan por lotes cada 15 min.
- **Qué haré la próxima clase:** requisitos funcionales/no funcionales y estimación de carga completa (incluido almacenamiento a 5 años).
- **Uso de IA:** le pedí a Claude armar la estructura del repo y un borrador de PROBLEMA.md; yo revisé y ajusté los supuestos y cifras.

## Jue 5 nov
- **Qué hice hoy:** escribí los requisitos funcionales y no funcionales y la estimación de carga en `docs/fase1/REQUISITOS.md`.
- **Dónde me trabé:** calcular el almacenamiento a 5 años; decidí guardar un historial de cambios de stock para auditoría.
- **Qué haré la próxima clase:** borrador de los diagramas lógico y físico (PNG y draw.io).
- **Uso de IA:** le pedí a Claude un borrador de requisitos y cálculos; revisé los supuestos y verifiqué las cuentas.

## Vie 6 nov
- **Qué hice hoy:** borrador de los diagramas lógico (flujo de lectura, escritura y modelo de datos) y físico (gateway, balanceador, 2 instancias, primaria y réplica, con los SPOF marcados), en PNG y draw.io, en `docs/fase1/`.
- **Dónde me trabé:** decidir qué componentes son puntos únicos de falla; marqué el gateway, el balanceador y la primaria.
- **Qué haré la próxima clase:** escribir DISENO.md (justificación de cada componente y 3 riesgos) y la presentación .pptx para la entrega de la Fase 1.
- **Uso de IA:** le pedí a Claude generar los diagramas; revisé que cada flecha corresponda al flujo real y que los SPOF estén bien marcados.

## Mié 11 nov — Entrega Fase 1 (sin clases: avancé en casa)
- **Qué hice hoy:** completé `docs/fase1/DISENO.md` (problemática, requisitos, estimación, diagramas, justificación de cada componente y 3 riesgos) y la presentación `Presentacion_Fase1.pptx`, con un guion para practicar.
- **Dónde me trabé:** explicar el costo de cada componente; separé latencia, complejidad y dinero.
- **Qué haré la próxima clase:** levantar la primaria y la réplica con Docker Compose y comprobar la replicación; balanceador con 2 instancias de prueba.
- **Uso de IA:** le pedí a Claude un borrador del documento, la presentación y el guion; ensayé la presentación y ajusté lo que no sabía explicar.

## Jue 12 nov (estaba de viaje; avancé en la noche)
- **Qué hice hoy:** levanté con Docker Compose la primaria y la réplica (streaming con `pg_basebackup` y slot) y comprobé que la réplica sigue a la primaria; NGINX alterna entre 2 instancias de prueba.
- **Dónde me trabé:** Docker Desktop no arrancaba por un archivo `engine.sock` bloqueado; lo resolví renombrando la carpeta `docker-secrets-engine`.
- **Qué haré la próxima clase:** agregar el gateway con API key y límite de peticiones, documentar EVIDENCIAS.md y etiquetar `fase-2`.

## Vie 13 nov — Entrega Fase 2
- **Qué hice hoy:** Kong como gateway (rutas `/api/v1`, API key para POST y límite de peticiones para GET) y `docs/fase2/EVIDENCIAS.md` con las 4 pruebas; README con los pasos para levantar el sistema.
- **Dónde me trabé:** el límite de peticiones se comparte entre pruebas en el mismo minuto; hay que esperar un minuto para repetirla.
- **Qué haré la próxima clase:** reemplazar el servicio de prueba por la aplicación real (POST a la primaria con X-DB: primary).
- **Uso de IA:** Claude armó el docker-compose y las configuraciones; yo ejecuté las pruebas en Kiro y revisé que entiendo qué hace cada servicio.

## Mié 18 nov
- **Qué hice hoy:** reemplacé el servicio de prueba por la aplicación real en Python. El `POST /api/v1/stock` escribe en la base primaria y responde `X-DB: primary`; las consultas de stock, productos y locales leen de la réplica y responden `X-DB: replica`. Las dos funciones del gateway siguen activas (API key y límite de peticiones). Además adelanté las tres pruebas de falla y las documenté en `docs/fase3/PRUEBAS_DE_FALLA.md`: al apagar una instancia no falló ninguna petición; al cortar la réplica se vieron lecturas desactualizadas; y al matar la primaria y promover la réplica medí RPO = 0 y RTO = 11,1 s.
- **Dónde me trabé:** Docker Desktop volvió a fallar al iniciar por un archivo `engine.sock` bloqueado, y lo resolví renombrando la carpeta `docker-secrets-engine`. En la tercera prueba, después de recrear las instancias, NGINX seguía usando sus direcciones IP antiguas y respondía 502; lo corregí configurando NGINX para que vuelva a resolver los nombres cada 5 segundos.
- **Qué haré la próxima clase:** completar el README final con las decisiones de diseño y las limitaciones, y practicar la demostración en vivo para la presentación.
- **Uso de IA:** le pedí a Claude el código de la aplicación y scripts para medir las fallas. Yo probé cada endpoint por el gateway, revisé las cabeceras X-Instance y X-DB, y verifiqué que los resultados y las conclusiones de cada prueba tuvieran sentido.

## Jue 19 nov
- **Qué hice hoy:** completé el README final con las decisiones de diseño (cada una con su justificación y su costo) y las limitaciones del sistema. Hice la prueba de "clon limpio": cloné el repositorio desde GitHub en una carpeta nueva, copié `.env.example` a `.env` y levanté todo con `docker compose up -d --build`; los 6 servicios quedaron arriba, la réplica en streaming, el GET respondió `X-DB: replica` y el POST `X-DB: primary`.
- **Dónde me trabé:** Docker Desktop volvió a fallar al iniciar por el archivo `engine.sock`; ya sé resolverlo renombrando la carpeta `docker-secrets-engine`. Lo dejo anotado para el día de la presentación.
- **Práctica de la presentación:** ensayé la demostración completa en Kiro: una escritura (`201`, `X-DB: primary`) y una lectura (`200`, `X-DB: replica`), explicando cada cabecera. También practiqué las dos fallas en vivo: apagué app-1 y el sistema siguió respondiendo con app-2; y maté la primaria, mostré que las lecturas seguían funcionando y las escrituras daban 503, promoví la réplica con `pg_promote()`, cambié `DB_PRIMARY_URL` en `.env`, recreé las instancias y las escrituras volvieron. Al final restauré el sistema con `docker compose down -v` y `docker compose up -d`.
- **Qué haré la próxima clase:** etiquetar `fase-3` para la entrega y repasar las preguntas sobre mis decisiones de diseño.
- **Uso de IA:** le pedí a Claude redactar las decisiones y limitaciones a partir de lo que medimos en las pruebas de falla; las revisé para poder explicarlas con mis palabras.
