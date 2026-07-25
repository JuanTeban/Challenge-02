# Reporte de Limpieza y Auditoría de Datos — TechLogistics S.A.

## Inventario Central

**Health Score:** 97.48 → 100.0  
**Nulidad promedio:** 2.52% → 0.0%  
**Duplicados exactos:** 0 → 0

**Decisiones aplicadas:**

- Categoria: normalizada a 5 categorías estándar; '???' -> 'Sin Categoría' (no se inventa el valor real).
- Bodega_Origen: 'norte' -> 'Norte' (typo de casing). 'ZONA_FRANCA' y 'BOD-EXT-99' se mantienen como bodegas externas reales (flag Bodega_Externa), no se fusionan con Norte/Sur/Occidente por falta de evidencia de que sean el mismo lugar.
- Lead_Time_Dias: rangos ('25-30 días') -> promedio; 'Inmediato' -> 0; 403 nulos imputados con mediana (5.0 días) por ser dato ruidoso/asimétrico.
- Stock_Actual: 60 negativos (error de captura, físicamente imposible) + 100 nulos -> imputados con mediana por Categoría (mediana, no media, por sesgo de la distribución). Se preserva flag Stock_Imputado para trazabilidad.
- Costo_Unitario_USD: 1 outliers detectados vía IQR. Se marcan (Outlier_Costo=True) pero NO se eliminan del dataset; se excluyen solo del cálculo de KPIs de rentabilidad global, con opción de 'ver excluidos' en el dashboard.
- Ultima_Revision: parseada a fecha; se deriva Dias_Desde_Revision para medir confianza del dato (insumo de la pregunta de bodegas 'operando a ciegas').

## Transacciones Logística

**Health Score:** 97.48 → 100.0  
**Nulidad promedio:** 2.52% → 0.0%  
**Duplicados exactos:** 0 → 0

**Decisiones aplicadas:**

- Fecha_Venta: parseada (formato DD/MM/YYYY, consistente en este archivo). 0 transacciones con fecha futura (> hoy) excluidas del análisis temporal.
- SKU_ID: 1751 transacciones (17.5%) con SKU no catalogado ('venta fantasma'). NO se eliminan: se flaggean para cuantificar el impacto financiero (pregunta de negocio #3).
- Cantidad_Vendida: 100 valores negativos flaggeados como posible devolución. Se preserva el valor original para trazabilidad de ingresos; se excluyen de 'unidades vendidas' pero se contabilizan en el neto.
- Costo_Envio: 834 nulos (~8% en todos los canales por igual, sin patrón) -> imputados con mediana global (52.36).
- Tiempo_Entrega_Real: 50 outliers (hasta 999 días) flaggeados vía IQR, no eliminados; se excluyen del promedio de KPI de servicio.
- Estado_Envio: 1683 nulos (16.8%) -> categoría 'Sin Información', NO moda (imputar con 'Entregado' ocultaría fallas operativas reales).
- Ciudad_Destino: 'MED'->'Medellín', 'BOG'->'Bogotá'. 'Ventas_Web' NO es una ciudad (error de captura de canal en el campo ciudad) -> flag Ciudad_Valida=False, se excluye del análisis geográfico pero se conserva la fila.

## Feedback Clientes

**Health Score:** 95.61 → 100.0  
**Nulidad promedio:** 4.39% → 0.0%  
**Duplicados exactos:** 0 → 0

**Decisiones aplicadas:**

- Feedback_ID: 500 IDs duplicados correspondían a registros de clientes DISTINTOS (no duplicados exactos) -> se reasigna sufijo '-B' en vez de eliminar, para no perder opiniones reales de clientes.
- Rating_Producto: 30 valores '99' (fuera de escala 1-5) -> NaN -> imputados con MEDIANA (3.0), no media, por ser escala ordinal (Likert).
- Comentario_Texto: nulos y '---' unificados como 'Sin comentario' (mismo significado).
- Recomienda_Marca: 'SI'/'NO' normalizados a 'Sí'/'No'. 1119 nulos -> 'Sin Respuesta' (nunca se imputa la opinión de un cliente).
- Ticket_Soporte_Abierto: 'Sí'/'1' -> True, 'No'/'0' -> False (normalizado a booleano).
- Edad_Cliente: 23 valores de 195 años (físicamente imposibles) -> NaN -> imputados con mediana (50.0).
- Satisfaccion_NPS: el rango [-100, 100] corresponde a la metodología NPS estándar; no requiere limpieza, solo documentación.

