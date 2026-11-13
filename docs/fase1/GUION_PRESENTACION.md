# Guion para practicar la presentación de la Fase 1

Duración objetivo: **5 minutos**, unos 30–40 segundos por diapositiva. El mismo texto está en las notas del orador de `Presentacion_Fase1.pptx`.

> Consejo: no lo leas palabra por palabra. Apréndete **la idea clave** de cada diapositiva (en negrita) y explícala con tus palabras.

| # | Diapositiva | Idea clave | Lo que dices |
|---|---|---|---|
| 1 | Portada | **Qué es** | "Mi proyecto es un sistema para consultar el stock de una cadena de farmacias." |
| 2 | El problema | **70 lecturas por cada escritura** | Miles de clientes leen; solo 120 locales escriben, cada 15 min. Por eso hay réplica de lectura. Hay 3 clientes: por eso hay gateway. |
| 3 | Requisitos | **Cada requisito dice a qué base va** | Las consultas van a la réplica y las escrituras a la primaria. El POS confirma lo que escribió leyendo de la primaria. Los objetivos se pueden medir: 300 ms, 30 s, RPO 15 min, RTO 5 min. |
| 4 | Estimación | **17 → 85 → 250 lecturas/s** | Parto de 200.000 búsquedas al día. Una sola instancia no aguanta el crecimiento: por eso hay balanceador. ~20 GB a 5 años. |
| 5 | Diagrama lógico | **Dos caminos: lectura y escritura** | Recorre con el dedo: lectura → réplica (429 si excede el límite); escritura → API key (401 si falta) → primaria → WAL → réplica. |
| 6 | Diagrama físico | **Puntos únicos de falla en rojo** | Solo el gateway está expuesto. SPOF: gateway, balanceador, primaria y el host. Las instancias no lo son, porque hay dos. |
| 7 | Componentes | **Cada pieza tiene un costo** | Gateway: seguridad (+ms). Balanceador: reparte (+1 ms). Instancias: escalar (×2 recursos). Réplica: carga de lectura (atraso ≤ 30 s). |
| 8 | Riesgos | **Primaria, atraso, saturación** | Promover la réplica en ≤ 5 min; si el atraso pasa de 30 s, leer de la primaria; rate limit y más instancias. |
| 9 | Próximos pasos | **Fechas** | 12: BD + balanceador. 13: Fase 2 en Docker. 20: app real y pruebas de falla. "¿Preguntas?" |

## Preguntas probables (practica responderlas en voz alta)

**¿Por qué no usar el gateway también como balanceador?**
El enunciado exige separarlos para demostrar qué hace cada uno. Además, el gateway decide *quién puede entrar y a dónde va* (seguridad y rutas), y el balanceador decide *qué instancia atiende* (reparto y salud).

**¿Qué pasa si se cae la réplica?**
Las lecturas fallan o, mejor, la app las redirige a la primaria. Funciona porque la primaria tiene poca carga de escritura (2 escrituras/s como máximo).

**¿Qué pasa si se cae una instancia?**
NGINX la marca como caída (`max_fails`) y envía todo a la otra. El cliente no lo nota.

**¿Por qué la replicación es asíncrona y no síncrona?**
Con la síncrona, cada escritura espera a la réplica: más latencia, y si la réplica cae, se bloquean las escrituras. Con la asíncrona se pueden perder unos segundos de datos, pero el POS los reenvía, así que el RPO es aceptable.

**¿Qué ve un cliente si consulta justo después de que el POS escribió?**
Puede ver el dato anterior durante unos segundos (el atraso de la réplica, ≤ 30 s). Es aceptable porque el stock se confirma en el mesón.

**¿Qué es RPO y RTO?**
- RPO: cuántos datos puedo perder (15 min, un ciclo del POS).
- RTO: cuánto tiempo puedo estar sin escribir (5 min).

**¿De dónde sale el 70 : 1?**
- 400.000 lecturas al día: 200.000 búsquedas × 2.
- 5.760 escrituras al día: 120 locales × 4 por hora × 12 h.
- 400.000 / 5.760 ≈ 70.

**¿Por qué la app debe ser sin estado?**
Para que cualquier instancia pueda atender cualquier petición. Si guardara datos en memoria, cada instancia vería cosas distintas y el balanceador no podría repartir.
