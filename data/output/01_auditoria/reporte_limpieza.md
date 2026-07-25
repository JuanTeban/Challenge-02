# Reporte de Limpieza y Auditoría de Datos — TechLogistics S.A.S.

## Inventario Central

**Health Score:** 97.48 → 100.0  
**Nulidad promedio:** 2.52% → 0.0%  
**Duplicados exactos:** 0 → 0

**Decisiones aplicadas:**

- Categoria: normalizada a 5 categorías estándar; '???' -> 'Sin Categoría' (no se inventa el valor real).
- Bodega_Origen: 'norte' -> 'Norte' (typo de casing). 'ZONA_FRANCA' y 'BOD-EXT-99' se mantienen como bodegas externas reales (flag Bodega_Externa), no se fusionan con Norte/Sur/Occidente por falta de evidencia de que sean el mismo lugar.
- Lead_Time_Dias: rangos ('25-30 días') -> promedio; 'Inmediato' -> 0; 403 nulos imputados con mediana (5.0 días) por ser dato ruidoso/asimétrico.
- Stock_Actual: 60 negativos (error de captura, físicamente imposible) + 100 nulos -> imputados con mediana por Categoria (mediana, no media, por sesgo de la distribución). Se preserva flag Stock_Imputado para trazabilidad.
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
- Ciudad_Destino: 'MED'->'Medellín', 'BOG'->'Bogotá' (abreviaturas de captura). 'Ventas_Web' NO es una ciudad real, sino un error de captura del canal en el campo ciudad -> renombrada a la etiqueta explícita 'Sin Ciudad (Venta Web)' (en vez de dejar el valor crudo, que aparecería como una ciudad falsa en el filtro de la barra lateral) y flag Ciudad_Valida=False; se excluye del análisis geográfico pero se conserva la fila y su ingreso en los KPIs financieros.
- Canal_Venta: valores ('Físico', 'WhatsApp', 'Online', 'App') ya consistentes; validado, no requiere normalización.

## Feedback Clientes

**Health Score:** 95.61 → 100.0  
**Nulidad promedio:** 4.39% → 0.0%  
**Duplicados exactos:** 0 → 0

**Decisiones aplicadas:**

- Feedback_ID: 500 IDs duplicados correspondían a registros de clientes DISTINTOS (no duplicados exactos) -> se reasigna sufijo '-B' en vez de eliminar, para no perder opiniones reales de clientes.
- Rating_Producto: 30 valores '99' (fuera de escala 1-5) -> NaN -> imputados con MEDIANA (3.0), no media, por ser escala ordinal (Likert).
- Rating_Logistica: sin valores fuera de rango (1-5) ni nulos detectados; no requiere limpieza.
- Comentario_Texto: nulos y '---' unificados como 'Sin comentario' (mismo significado).
- Recomienda_Marca: 'SI'/'NO' normalizados a 'Sí'/'No'; 'Maybe' (inglés suelto en un campo por lo demás en español) -> 'Tal vez'. 1119 nulos -> 'Sin Respuesta' (nunca se imputa la opinión de un cliente).
- Ticket_Soporte_Abierto: 'Sí'/'1' -> True, 'No'/'0' -> False (normalizado a booleano).
- Edad_Cliente: 23 valores de 195 años (físicamente imposibles) -> NaN -> imputados con mediana (50.0).
- Satisfaccion_NPS: el rango [-100, 100] corresponde a la metodología NPS estándar; no requiere limpieza, solo documentación.

## Integración (Sola Fuente de Verdad)

- Dilema del SKU Fantasma: 1751 de 10000 transacciones (17.5%) referencian un SKU_ID ausente del maestro de inventario. Se tratan como ventas reales de productos no catalogados (el ingreso se conserva y se reporta), NO como errores a descartar, porque el dinero fue efectivamente cobrado. Se excluyen únicamente del cálculo de margen (no existe Costo_Unitario_USD de referencia) y de los análisis de stock/bodega, quedando Categoria/Bodega_Origen marcados como 'Sin Catálogo' para trazabilidad.
- Feedback_Clientes: 767 transacciones tenían más de un registro de feedback asociado. Se agregaron (promedio de ratings/NPS, moda de Recomienda_Marca, OR lógico de Ticket_Soporte_Abierto) ANTES del cruce para que cada fila de dataset_maestro represente una única transacción y no se dupliquen ingresos ni cantidades al unir (evita fan-out del merge).
- Variable derivada Margen_Unitario/Margen_Pct/Margen_Total_Transaccion: Precio_Venta_Final - Costo_Unitario_USD. NaN para ventas fantasma (sin costo de referencia); se excluyen explícitamente de los KPIs de rentabilidad global.
- Variable derivada Brecha_Entrega = Tiempo_Entrega_Real - Lead_Time_Dias del inventario. Supuesto documentado: el modelo de datos no registra un tiempo de entrega 'prometido' por transacción, por lo que se usa el Lead_Time_Dias del proveedor (inventario) como único proxy disponible de la expectativa de entrega.
- Variable derivada Ingreso_En_Riesgo: ingreso de transacciones con SKU fantasma, aislado para cuantificar el impacto financiero de la falta de control de inventario (pregunta de negocio #3).