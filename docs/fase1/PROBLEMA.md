# Problemática: Consulta de stock de una cadena de farmacias

## Quién la usa y qué problema resuelve

Una cadena de farmacias con **120 locales** en Chile necesita que sus clientes puedan saber,
antes de salir de casa, **en qué local hay stock de un medicamento**. Hoy el cliente llama o
recorre varios locales, y muchas veces el medicamento no está.

El sistema expone una API que responde: *"¿qué locales tienen el producto X y cuántas unidades?"*.

## Tipos de cliente (justifica el API Gateway)

| Cliente | Qué hace | Necesidad en el gateway |
|---|---|---|
| **Web pública** | Clientes buscan medicamentos y ven stock por local | Límite de peticiones (evitar scraping) |
| **App móvil** | Lo mismo, más "locales cerca de mí" | Límite de peticiones por cliente |
| **Sistema POS de los locales** (sistema externo) | Actualiza el stock al vender o recibir mercadería (escrituras) | API key obligatoria: solo los locales pueden escribir |

Tres clientes distintos con permisos distintos → un único punto de entrada que enrute
(`/api/v1/stock`, `/api/v1/productos`) y aplique API key / rate limit es justificado.

## Entidades (alcance pequeño)

1. **Local** (id, nombre, comuna, dirección)
2. **Producto** (id, nombre, principio activo, presentación)
3. **Stock** (local_id, producto_id, cantidad, actualizado_en)

Endpoints previstos: `GET /productos?q=`, `GET /stock?producto_id=`, `POST /stock` (actualización desde POS), `GET /health`.

## Por qué hay muchas más lecturas que escrituras (justifica la réplica)

Supuestos:
- 200.000 consultas diarias de clientes (web + app) → cada búsqueda genera ~2 lecturas (buscar producto + ver stock) = **400.000 lecturas/día**.
- Los POS no envían cada venta individual: sincronizan el stock por lotes cada 15 minutos
  por local. 120 locales × 4 por hora × 12 horas = **5.760 escrituras/día** (cada una con varios productos, ~5 filas → ~29.000 filas/día).

Relación lecturas : escrituras ≈ 400.000 : 5.760 ≈ **70 : 1** (muy por sobre 10:1).
Muchas personas consultan lo mismo; solo los locales escriben. Por eso las lecturas pueden ir a una réplica y la primaria queda libre para escrituras.

## Escala objetivo (justifica el balanceador y varias instancias)

- Promedio: 400.000 lecturas / 86.400 s ≈ **4,6 lecturas/s**.
- Hora punta (lunes 9–10 h y campañas de invierno, ~15% del tráfico diario en 1 hora): 60.000 / 3.600 ≈ **17 lecturas/s**, con picos ×5 en emergencias sanitarias (ej. brote de influenza) ≈ **85 lecturas/s**.
- Escala objetivo a 3 años: expansión a **300 locales** y ×3 usuarios → ~**250 lecturas/s** en pico.

Una sola instancia también sería un punto único de falla: con 2+ instancias detrás de un balanceador, si una cae, el servicio sigue.

## Dato cuya pérdida o atraso importa (RPO, RTO y consistencia)

El dato crítico es la **cantidad de stock**.

- **Atraso aceptable en lecturas:** hasta **30 segundos** de retraso de la réplica. Si un cliente ve "3 unidades" y en realidad quedan 2, no es grave: el stock igual se confirma en el mesón.
  Mostrar "hay stock" cuando hace horas que no hay sí es grave (el cliente viaja en vano).
- **RPO objetivo: ≤ 15 minutos.** Si se pierde la última sincronización, el POS la reenvía en el siguiente ciclo de 15 min.
- **RTO objetivo: ≤ 5 minutos** sin escrituras. Las lecturas siguen funcionando desde la réplica mientras se promueve.
- **Consistencia:** eventual para clientes (leen réplica); el POS que acaba de escribir puede leer desde la primaria para confirmar su propia escritura (*read-your-writes*).

## Verificación de los 5 criterios

| Criterio | ¿Cumple? | Cifra |
|---|---|---|
| Lecturas ≥ 10× escrituras | ✅ | ~70:1 |
| Más de un tipo de cliente | ✅ | Web, app móvil, POS de locales |
| Puede crecer, escala estimada | ✅ | 17 lect/s punta hoy → ~250 lect/s en 3 años |
| Dato cuya pérdida/atraso importa | ✅ | Stock: atraso ≤ 30 s, RPO ≤ 15 min, RTO ≤ 5 min |
| Alcance pequeño | ✅ | 3 entidades, 4 endpoints |
