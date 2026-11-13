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
