# Challenge 02 — El Desafío de los Datos Erróneos e Interconectados

Integrantes:
Juan Esteban Garcia - 
Manuela Castaño - 1011510403
Juan Felipe Restrepo - 

Sistema de Soporte a la Decisión (DSS) para **TechLogistics S.A.S.**, un retailer tecnológico
ficticio que sospecha que la erosión de su margen y la caída en la lealtad de sus clientes
viene de la desconexión entre sus tres sistemas: Inventario, Logística y Feedback de Clientes.

Este repositorio contiene la curaduría de datos, la integración multi-fuente y un dashboard
interactivo en Streamlit (con un módulo de recomendación estratégica vía IA) que responde a
cinco preguntas de alta gerencia con evidencia estadística y visual.

## El problema en cifras

- **inventario_central_v2.csv** (2.500 SKUs): costos entre $0.05 y $850.000, stock negativo,
  lead times mezclados entre rangos de texto y números.
- **transacciones_logistica_v2.csv** (10.000 ventas): ~17.5% de las ventas referencian un
  SKU que no existe en el inventario oficial ("venta fantasma"); tiempos de entrega de hasta
  999 días.
- **feedback_clientes_v2.csv** (4.500 registros): duplicados intencionales, edades de hasta
  195 años y una escala NPS que va de -100 a 100.

## Arquitectura

```
Challenge-02/
├── data/
│   ├── input/                 CSV crudos originales (no se modifican)
│   └── output/
│       ├── 01_auditoria/      health_scores.json, reporte_limpieza.md
│       ├── 02_datos_limpios/  CSV curados + dataset_maestro.csv (Sola Fuente de Verdad)
│       └── 03_reportes/       KPIs y reportes exportables
├── documentacion/
│   ├── ejercicio/             Enunciado, diccionario de datos y guía de validación (PDF)
│   └── solucion/              Documento de Hallazgos para la junta directiva (PDF)
├── src/
│   ├── utils/                 Rutas centralizadas (config.py), I/O de artefactos, paleta de color
│   ├── pipeline_limpieza/     Auditoría y limpieza por dataset (Fase 1)
│   ├── pipeline_integracion/  Merge, dilema del SKU fantasma, feature engineering (Fase 2)
│   ├── pipeline_analisis/     Las 5 preguntas de alta gerencia
│   └── pipeline_ia/           Cliente Groq/Llama-3 aislado (sin secretos en el código)
├── app.py                     Dashboard Streamlit
└── requirements.txt
```

Cada función de limpieza retorna `(dataframe_limpio, reporte_de_decisiones)`; el dashboard
usa ese reporte para su Módulo de Transparencia y para el `reporte_limpieza.md` descargable.

## Instalación

El repositorio ya incluye un entorno virtual (`.venv`). Actívalo e instala las dependencias:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

Si prefieres crear el entorno desde cero:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

```bash
streamlit run app.py
```

La primera carga ejecuta el pipeline completo (auditoría → limpieza → integración) y guarda
todos los artefactos en `data/output/`. El botón **🔄 Refrescar Análisis** en la barra lateral
limpia la caché y vuelve a correrlo desde los CSV crudos.

## Módulo de Inteligencia Artificial (Groq · Llama-3)

Por tratarse de una app pública, **no se incluye ningún API Key en el repositorio**. En la
pestaña **🤖 Insights de IA** cada usuario ingresa su propio API Key de Groq
([console.groq.com](https://console.groq.com)) y selecciona el modelo Llama-3 a usar. El key
solo vive en la sesión del navegador (`st.session_state`) y nunca se persiste a disco ni se
registra en logs.

## Las 5 preguntas de alta gerencia

1. **Fuga de Capital y Rentabilidad** — pestaña Operaciones.
2. **Crisis Logística y Cuellos de Botella** — pestaña Operaciones.
3. **Análisis de la Venta Invisible** — pestaña Operaciones.
4. **Diagnóstico de Fidelidad** — pestaña Cliente.
5. **Storytelling de Riesgo Operativo** — pestaña Cliente.

Cada respuesta se recalcula en vivo según los filtros de fecha, categoría, bodega, ciudad y
canal aplicados en la barra lateral.

## Hallazgo destacado de auditoría

El KPI global de margen quedaba distorsionado en más de $23M por un único SKU con un costo
unitario atípico de $850.000 (el outlier deliberado del ejercicio). Ese registro se excluye
del cálculo de rentabilidad global —tal como exige la guía de validación— pero queda visible
en la sección **"Ver registros excluidos"** de la pestaña Auditoría para no perder trazabilidad.

## Stack técnico

Python 3.13 · pandas · numpy · scipy (pruebas de correlación) · Plotly · Streamlit · Groq SDK.




## LINK STREAMLIT

https://challenge-02.streamlit.app/
