# Informe de Hallazgos
## Taller de Consultoría de Datos
### TechLogistics S.A.S.

---

## Objetivo

A partir de la integración de las bases de inventario, ventas y satisfacción del cliente se construyó un conjunto de datos maestro que permitió responder cinco preguntas estratégicas de negocio relacionadas con rentabilidad, logística, control del inventario y fidelización.

---

# Resumen Ejecutivo

El análisis permitió identificar cinco hallazgos principales:

- El 38.7% de las transacciones presentan margen negativo.
- El 17.4% de los ingresos proviene de productos que no existen en el inventario maestro.
- No se encontró evidencia de que mayores tiempos de entrega expliquen la baja satisfacción del cliente.
- Se identificaron categorías con alto inventario pero baja satisfacción.
- Existen bodegas con revisiones muy antiguas que podrían representar un riesgo operativo.

---

# 1. ¿Dónde se está perdiendo dinero?

**Figura 1. Dashboard de Rentabilidad**

*(Insertar captura de la sección 1 del dashboard)*

### Hallazgo

El problema más importante encontrado fue la rentabilidad.

- 38.7% de las ventas tienen margen negativo.
- La pérdida acumulada supera los **11.3 millones de USD**.
- El comportamiento es similar en todos los canales de venta.

Esto indica que el problema no parece estar asociado a un único canal, sino a una política de costos o precios que afecta gran parte de la operación.

### Recomendación

Priorizar una revisión de costos para los productos con mayores pérdidas acumuladas antes de modificar la estrategia comercial.

---

# 2. ¿Los tiempos de entrega afectan la satisfacción?

**Figura 2. Correlaciones por ciudad y bodega**

*(Insertar captura de la sección 2)*

### Hallazgo

Las correlaciones encontradas fueron muy cercanas a cero.

Esto sugiere que, para este conjunto de datos, los tiempos de entrega no explican la satisfacción del cliente de manera significativa.

Probablemente existen otros factores con mayor impacto, como la calidad del producto, el precio o el servicio recibido.

### Recomendación

Ampliar el análisis incorporando variables relacionadas con experiencia del cliente y calidad del producto.

---

# 3. ¿Qué impacto tienen los SKU fantasma?

**Figura 3. Ingreso en riesgo**

*(Insertar captura de la sección 3)*

### Hallazgo

Se encontró que:

- El 17.4% del ingreso corresponde a ventas cuyos SKU no existen en el inventario maestro.
- Estas ventas representan aproximadamente **12.9 millones de USD**.

Aunque las ventas son reales, la ausencia del SKU impide calcular correctamente el margen y dificulta el control del inventario.

### Recomendación

Fortalecer el proceso de sincronización entre inventario y ventas para evitar la generación de nuevos SKU no catalogados.

---

# 4. ¿Existen problemas de fidelización?

**Figura 4. Stock vs NPS**

*(Insertar captura de la sección 4)*

### Hallazgo

Se identificaron dos categorías que llaman la atención:

- Smartphones
- Sin Categoría

Ambas presentan inventario disponible, pero niveles bajos de satisfacción.

Esto indica que disponer de stock no garantiza una buena experiencia del cliente.

### Recomendación

Realizar un análisis específico sobre estas categorías para identificar posibles problemas de calidad, precio o percepción del producto.

---

# 5. ¿Qué riesgos operativos existen?

**Figura 5. Antigüedad de revisión y tickets**

*(Insertar captura de la sección 5)*

### Hallazgo

La bodega **Occidente** presenta la mayor combinación entre:

- revisiones desactualizadas;
- alta tasa de tickets de soporte.

Aunque no se encontró una correlación estadísticamente significativa, este comportamiento representa una señal de alerta para la operación.

### Recomendación

Programar auditorías periódicas sobre las bodegas con revisiones más antiguas y realizar seguimiento a sus indicadores de soporte.

---

# Conclusiones

A partir del proceso de integración y limpieza de datos fue posible construir un dataset confiable para responder las preguntas de negocio planteadas.

El principal riesgo identificado corresponde a la rentabilidad, ya que cerca del 39% de las transacciones generan pérdidas. Adicionalmente, la existencia de ventas asociadas a SKU no catalogados limita la capacidad de medir correctamente los márgenes y controlar el inventario.

Finalmente, el análisis evidencia que no todos los problemas del negocio están relacionados con la logística. Variables como la gestión del catálogo, la calidad del producto y la estrategia de costos parecen tener un impacto mayor sobre los indicadores analizados.

---

# Trabajo futuro

Como continuación de este proyecto sería recomendable:

- incorporar costos históricos de adquisición;
- incluir información sobre devoluciones;
- analizar campañas comerciales;
- desarrollar modelos predictivos para detectar pérdidas antes de que ocurran;
- implementar monitoreo continuo mediante el dashboard desarrollado.
