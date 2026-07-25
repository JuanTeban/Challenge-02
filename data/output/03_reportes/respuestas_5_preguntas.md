# Respuestas a las 5 Preguntas de Alta Gerencia — Snapshot sobre el dataset completo

## 1. Fuga de Capital y Rentabilidad
- Transacciones con margen negativo: 3,188 (38.67% del total con margen calculable).
- Pérdida acumulada (excluyendo outliers de costo): $-11,292,631.90.
- Transacciones excluidas por outlier de costo: 5 (impacto aislado: $-23,768,848.93).

## 3. Análisis de la Venta Invisible
- Ingreso total: $74,087,519.58.
- Ingreso en riesgo por SKU fantasma: $12,866,162.44 (17.37% del ingreso total).
- Transacciones con SKU fantasma: 1,751 (17.51%).

## 4. Diagnóstico de Fidelidad
- Categorías con paradoja (alto stock, bajo NPS): Sin Categoría, Smartphones.
  - **Sin Categoría** → Sobrecosto percibido
  - **Smartphones** → Sin señal clara en margen ni calificación (investigar caso a caso)

## 5. Storytelling de Riesgo Operativo
- Bodegas operando a ciegas (revisión desactualizada + alta tasa de tickets): Occidente.
- Correlación antigüedad de revisión vs tickets de soporte: 0.004 (p=0.7365).

Nota: la pregunta 2 (Crisis Logística) depende de agrupaciones ciudad/bodega con su propio nivel de significancia estadística; consúltala de forma interactiva en la pestaña Operaciones del dashboard, donde se muestra el p-valor de cada zona.