import pandas as pd
import plotly.express as px
import plotly.io as pio
import streamlit as st

from src.pipeline_analisis.analisis import (
    analizar_cuellos_de_botella,
    analizar_margen_negativo,
    analizar_paradoja_fidelidad,
    analizar_riesgo_operativo,
    analizar_venta_fantasma,
)
from src.pipeline_ia.ia_groq import MODELOS_LLAMA3, ErrorIAGroq, generar_recomendacion
from src.pipeline_integracion.integracion import construir_dataset_maestro
from src.pipeline_limpieza.limpieza import (
    calcular_health_score,
    limpiar_feedback,
    limpiar_inventario,
    limpiar_transacciones,
    obtener_registros_excluidos,
)
from src.utils import config, io_utils, paleta

st.set_page_config(
    page_title="TechLogistics S.A.S. — Consultoría de Datos",
    page_icon="📦",
    layout="wide",
)

pio.templates["techlogistics"] = paleta.plantilla_plotly()
px.defaults.template = "techlogistics"

CSS_PERSONALIZADO = """
<style>
[data-testid="stMetricLabel"] {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    opacity: 0.72;
}
[data-testid="stMetricValue"] {
    font-weight: 600;
    font-size: 1.55rem;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: unset !important;
    overflow-wrap: break-word;
    line-height: 1.2;
}
[data-testid="stMetricLabel"] {
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: unset !important;
    overflow-wrap: break-word;
    line-height: 1.25;
}
div[data-testid="stVerticalBlock"] {
    border-radius: 14px;
}
div[data-testid="stTabs"] [role="tablist"] {
    gap: 6px;
}
div[data-testid="stTab"] {
    padding: 10px 20px !important;
    font-weight: 500;
}
h1 { letter-spacing: -0.01em; }
.bloque-titulo {
    border-left: 4px solid #2a78d6;
    padding: 2px 0 2px 14px;
    margin: 0.4rem 0 0.2rem 0;
}
.bloque-titulo h3 { margin: 0; padding: 0; }
</style>
"""
st.markdown(CSS_PERSONALIZADO, unsafe_allow_html=True)


def encabezado_seccion(texto: str) -> None:
    st.markdown(f'<div class="bloque-titulo"><h3>{texto}</h3></div>', unsafe_allow_html=True)


def construir_reporte_markdown(rep_inv, rep_trx, rep_fb, rep_integracion, hs_antes, hs_despues) -> str:
    lineas = ["# Reporte de Limpieza y Auditoría de Datos — TechLogistics S.A.S.", ""]
    secciones = [
        ("Inventario Central", rep_inv, hs_antes["inventario"], hs_despues["inventario"]),
        ("Transacciones Logística", rep_trx, hs_antes["transacciones"], hs_despues["transacciones"]),
        ("Feedback Clientes", rep_fb, hs_antes["feedback"], hs_despues["feedback"]),
    ]
    for nombre, reporte, hs_a, hs_d in secciones:
        lineas.append(f"## {nombre}")
        lineas.append("")
        lineas.append(f"**Health Score:** {hs_a['health_score']} → {hs_d['health_score']}  ")
        lineas.append(f"**Nulidad promedio:** {hs_a['pct_nulidad_promedio']}% → {hs_d['pct_nulidad_promedio']}%  ")
        lineas.append(f"**Duplicados exactos:** {hs_a['duplicados_exactos']} → {hs_d['duplicados_exactos']}")
        lineas.append("")
        lineas.append("**Decisiones aplicadas:**")
        lineas.append("")
        for decision in reporte["decisiones"]:
            lineas.append(f"- {decision}")
        lineas.append("")
    lineas.append("## Integración (Sola Fuente de Verdad)")
    lineas.append("")
    for decision in rep_integracion["decisiones"]:
        lineas.append(f"- {decision}")
    return "\n".join(lineas)


def construir_reporte_preguntas_markdown(kpis: dict) -> str:
    m = kpis["margen_negativo"]
    f = kpis["venta_fantasma"]
    fid = kpis["paradoja_fidelidad"]
    r = kpis["riesgo_operativo"]
    lineas = [
        "# Respuestas a las 5 Preguntas de Alta Gerencia — Snapshot sobre el dataset completo",
        "",
        "## 1. Fuga de Capital y Rentabilidad",
        f"- Transacciones con margen negativo: {m['transacciones_margen_negativo']:,} "
        f"({m['pct_transacciones_margen_negativo']}% del total con margen calculable).",
        f"- Pérdida acumulada (excluyendo outliers de costo): ${m['perdida_total_usd']:,.2f}.",
        f"- Transacciones excluidas por outlier de costo: {m['transacciones_excluidas_outlier_costo']} "
        f"(impacto aislado: ${m['impacto_excluido_usd']:,.2f}).",
        "",
        "## 3. Análisis de la Venta Invisible",
        f"- Ingreso total: ${f['ingreso_total_usd']:,.2f}.",
        f"- Ingreso en riesgo por SKU fantasma: ${f['ingreso_en_riesgo_usd']:,.2f} "
        f"({f['pct_ingreso_en_riesgo']}% del ingreso total).",
        f"- Transacciones con SKU fantasma: {f['transacciones_fantasma']:,} "
        f"({f['pct_transacciones_fantasma']}%).",
        "",
        "## 4. Diagnóstico de Fidelidad",
        f"- Categorías con paradoja (alto stock, bajo NPS): "
        f"{', '.join(fid['categorias_en_paradoja']) or 'Ninguna'}.",
    ] + [
        f"  - **{cat}** → {fid['diagnosticos'].get(cat, '')}" for cat in fid["categorias_en_paradoja"]
    ] + [
        "",
        "## 5. Storytelling de Riesgo Operativo",
        f"- Bodegas operando a ciegas (revisión desactualizada + alta tasa de tickets): "
        f"{', '.join(r['bodegas_operando_a_ciegas']) or 'Ninguna'}.",
        f"- Correlación antigüedad de revisión vs tickets de soporte: "
        f"{r['correlacion_antiguedad_tickets']} (p={r['p_valor']}).",
        "",
        "Nota: la pregunta 2 (Crisis Logística) depende de agrupaciones ciudad/bodega con su "
        "propio nivel de significancia estadística; consúltala de forma interactiva en la "
        "pestaña Operaciones del dashboard, donde se muestra el p-valor de cada zona.",
    ]
    return "\n".join(lineas)


@st.cache_data(show_spinner="Ejecutando auditoría, limpieza e integración de datos...")
def ejecutar_pipeline():
    inv_raw = io_utils.leer_csv_crudo(config.RUTA_INVENTARIO_CRUDO)
    trx_raw = io_utils.leer_csv_crudo(config.RUTA_TRANSACCIONES_CRUDO)
    fb_raw = io_utils.leer_csv_crudo(config.RUTA_FEEDBACK_CRUDO)

    hs_antes = {
        "inventario": calcular_health_score(inv_raw, "Inventario"),
        "transacciones": calcular_health_score(trx_raw, "Transacciones"),
        "feedback": calcular_health_score(fb_raw, "Feedback"),
    }

    inv_limpio, rep_inv = limpiar_inventario(inv_raw)
    trx_limpio, rep_trx = limpiar_transacciones(trx_raw, set(inv_limpio["SKU_ID"]))
    fb_limpio, rep_fb = limpiar_feedback(fb_raw)

    hs_despues = {
        "inventario": calcular_health_score(inv_limpio, "Inventario"),
        "transacciones": calcular_health_score(trx_limpio, "Transacciones"),
        "feedback": calcular_health_score(fb_limpio, "Feedback"),
    }

    df_maestro, rep_integracion = construir_dataset_maestro(inv_limpio, trx_limpio, fb_limpio)
    registros_excluidos = obtener_registros_excluidos(inv_limpio, trx_limpio)
    reporte_md = construir_reporte_markdown(rep_inv, rep_trx, rep_fb, rep_integracion, hs_antes, hs_despues)

    kpis_snapshot = {
        "margen_negativo": analizar_margen_negativo(df_maestro)["resumen"],
        "venta_fantasma": analizar_venta_fantasma(df_maestro)["resumen"],
        "paradoja_fidelidad": analizar_paradoja_fidelidad(df_maestro)["resumen"],
        "riesgo_operativo": analizar_riesgo_operativo(df_maestro)["resumen"],
    }
    reporte_preguntas_md = construir_reporte_preguntas_markdown(kpis_snapshot)

    io_utils.guardar_dataframe(inv_limpio, config.RUTA_INVENTARIO_LIMPIO)
    io_utils.guardar_dataframe(trx_limpio, config.RUTA_TRANSACCIONES_LIMPIO)
    io_utils.guardar_dataframe(fb_limpio, config.RUTA_FEEDBACK_LIMPIO)
    io_utils.guardar_dataframe(df_maestro, config.RUTA_DATASET_MAESTRO)
    io_utils.guardar_json({"antes": hs_antes, "despues": hs_despues}, config.RUTA_HEALTH_SCORES)
    io_utils.guardar_texto(reporte_md, config.RUTA_REPORTE_LIMPIEZA)
    io_utils.guardar_json(kpis_snapshot, config.RUTA_KPIS_RESUMEN)
    io_utils.guardar_texto(reporte_preguntas_md, config.RUTA_RESPUESTAS_PREGUNTAS)

    return {
        "df_maestro": df_maestro,
        "hs_antes": hs_antes,
        "hs_despues": hs_despues,
        "reporte_inventario": rep_inv,
        "reporte_transacciones": rep_trx,
        "reporte_feedback": rep_fb,
        "reporte_integracion": rep_integracion,
        "registros_excluidos": registros_excluidos,
        "reporte_md": reporte_md,
        "reporte_preguntas_md": reporte_preguntas_md,
        "inv_limpio": inv_limpio,
        "trx_limpio": trx_limpio,
        "fb_limpio": fb_limpio,
    }


def formatear_moneda(valor: float) -> str:
    signo = "-" if valor < 0 else ""
    abs_valor = abs(valor)
    if abs_valor >= 1_000_000:
        return f"{signo}${abs_valor / 1_000_000:,.1f}M"
    if abs_valor >= 1_000:
        return f"{signo}${abs_valor / 1_000:,.0f}K"
    return f"{signo}${abs_valor:,.0f}"


def formatear_pct(valor: float) -> str:
    return f"{valor:.1f}%"


def render_bloque_descargas(datos: dict, df_maestro: pd.DataFrame, key_prefix: str) -> None:
    st.caption("Reportes de auditoría")
    c1, c2 = st.columns(2)
    c1.download_button(
        "📄 Reporte de Limpieza (.md)", datos["reporte_md"], file_name="reporte_limpieza.md",
        use_container_width=True, key=f"{key_prefix}_reporte_md",
    )
    c2.download_button(
        "📈 Respuestas a las 5 Preguntas (.md)", datos["reporte_preguntas_md"],
        file_name="respuestas_5_preguntas.md", use_container_width=True, key=f"{key_prefix}_respuestas_md",
    )
    st.caption("Datasets limpios (CSV)")
    d1, d2 = st.columns(2)
    d1.download_button(
        "🗄️ Dataset Maestro", df_maestro.to_csv(index=False), file_name="dataset_maestro.csv",
        use_container_width=True, key=f"{key_prefix}_maestro",
    )
    d1.download_button(
        "📊 Inventario Limpio", datos["inv_limpio"].to_csv(index=False), file_name="inventario_limpio.csv",
        use_container_width=True, key=f"{key_prefix}_inv",
    )
    d2.download_button(
        "📊 Transacciones Limpias", datos["trx_limpio"].to_csv(index=False), file_name="transacciones_limpio.csv",
        use_container_width=True, key=f"{key_prefix}_trx",
    )
    d2.download_button(
        "📊 Feedback Limpio", datos["fb_limpio"].to_csv(index=False), file_name="feedback_limpio.csv",
        use_container_width=True, key=f"{key_prefix}_fb",
    )


datos = ejecutar_pipeline()
df_maestro = datos["df_maestro"]

st.sidebar.title("📦 TechLogistics S.A.S.")
st.sidebar.caption("Sistema de Soporte a la Decisión — Consultoría Senior")
st.sidebar.divider()
st.sidebar.subheader("Filtros de Análisis")

fecha_min = df_maestro["Fecha_Venta"].min().date()
fecha_max = df_maestro["Fecha_Venta"].max().date()
rango_fechas = st.sidebar.date_input(
    "Rango de fechas de venta",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max,
)

categorias_disponibles = sorted(df_maestro["Categoria"].unique())
categorias_sel = st.sidebar.multiselect("Categoría", categorias_disponibles, default=categorias_disponibles)

bodegas_disponibles = sorted(df_maestro["Bodega_Origen"].unique())
bodegas_sel = st.sidebar.multiselect("Bodega de Origen", bodegas_disponibles, default=bodegas_disponibles)

ciudades_disponibles = sorted(df_maestro["Ciudad_Destino"].unique())
ciudades_sel = st.sidebar.multiselect("Ciudad Destino", ciudades_disponibles, default=ciudades_disponibles)

canales_disponibles = sorted(df_maestro["Canal_Venta"].unique())
canales_sel = st.sidebar.multiselect("Canal de Venta", canales_disponibles, default=canales_disponibles)

st.sidebar.divider()
if st.sidebar.button("🔄 Refrescar Análisis", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.caption(
    "Salud de datos post-limpieza — "
    f"Inventario {datos['hs_despues']['inventario']['health_score']:.0f} · "
    f"Transacciones {datos['hs_despues']['transacciones']['health_score']:.0f} · "
    f"Feedback {datos['hs_despues']['feedback']['health_score']:.0f} "
    "(detalle antes/después en la pestaña Auditoría)"
)

if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
    fecha_inicio, fecha_fin = rango_fechas
else:
    fecha_inicio, fecha_fin = fecha_min, fecha_max

mascara = (
    df_maestro["Fecha_Venta"].dt.date.between(fecha_inicio, fecha_fin)
    & df_maestro["Categoria"].isin(categorias_sel)
    & df_maestro["Bodega_Origen"].isin(bodegas_sel)
    & df_maestro["Ciudad_Destino"].isin(ciudades_sel)
    & df_maestro["Canal_Venta"].isin(canales_sel)
)
df_filtrado = df_maestro[mascara].copy()

col_titulo, col_descargas = st.columns([5, 1], vertical_alignment="bottom")
with col_titulo:
    st.title("Dashboard de Recuperación Rentable — TechLogistics S.A.S.")
    st.caption(
        "Curaduría de datos, integración multi-fuente e inteligencia artificial para diagnosticar "
        "la erosión de margen y la fuga de lealtad de clientes."
    )
with col_descargas:
    with st.popover("📥 Descargas", use_container_width=True):
        render_bloque_descargas(datos, df_maestro, "header")

if df_filtrado.empty:
    st.warning("No hay transacciones para la combinación de filtros seleccionada. Ajusta los filtros en la barra lateral.")
    st.stop()

try:
    resultado_margen = analizar_margen_negativo(df_filtrado)
    resultado_logistica = analizar_cuellos_de_botella(df_filtrado)
    resultado_fantasma = analizar_venta_fantasma(df_filtrado)
    resultado_fidelidad = analizar_paradoja_fidelidad(df_filtrado)
    resultado_riesgo = analizar_riesgo_operativo(df_filtrado)
except Exception as error:
    st.error(f"No fue posible calcular los indicadores para este filtro: {error}")
    st.stop()

resumen_m = resultado_margen["resumen"]
resumen_l = resultado_logistica["resumen"]
resumen_f = resultado_fantasma["resumen"]
resumen_fid = resultado_fidelidad["resumen"]
resumen_r = resultado_riesgo["resumen"]

with st.container(border=True):
    st.markdown("##### 📌 Resumen Ejecutivo — Las 5 Preguntas de un Vistazo")
    e1, e2, e3, e4, e5 = st.columns(5)
    icono_margen = "🔴" if resumen_m["pct_transacciones_margen_negativo"] > 30 else "🟡"
    e1.metric(
        f"{icono_margen} Margen Negativo",
        formatear_pct(resumen_m["pct_transacciones_margen_negativo"]),
        help="Q1 · Fuga de Capital: % de transacciones vendidas por debajo del costo.",
    )
    icono_riesgo = (
        "🔴" if resumen_f["pct_ingreso_en_riesgo"] > 15
        else "🟡" if resumen_f["pct_ingreso_en_riesgo"] > 5
        else "🟢"
    )
    e2.metric(
        f"{icono_riesgo} Ingreso en Riesgo",
        formatear_pct(resumen_f["pct_ingreso_en_riesgo"]),
        help="Q3 · Venta Invisible: % del ingreso ligado a SKUs sin catálogo oficial.",
    )
    zona_sig = bool(resumen_l["peor_ciudad"]) and resumen_l["peor_ciudad"]["p_valor"] < 0.05
    peor_zona = resumen_l["peor_ciudad"]["Ciudad_Destino"] if resumen_l["peor_ciudad"] else "N/D"
    e3.metric(
        "🚚 Zona Crítica" if zona_sig else "🚚 Zona Más Débil",
        peor_zona,
        help=(
            "Q2 · Crisis Logística: ciudad con la correlación más negativa entre tiempo de entrega y NPS."
            if zona_sig else
            "Q2 · Crisis Logística: ciudad con la correlación más negativa entre tiempo de entrega y NPS, "
            "pero NO estadísticamente significativa (p > 0.05) con los filtros actuales — no se recomienda "
            "actuar solo con esta señal."
        ),
    )
    e4.metric(
        "👥 Categorías en Paradoja",
        len(resumen_fid["categorias_en_paradoja"]),
        help="Q4 · Diagnóstico de Fidelidad: categorías con alto stock y bajo NPS simultáneamente.",
    )
    e5.metric(
        "🏭 Bodegas a Ciegas",
        len(resumen_r["bodegas_operando_a_ciegas"]),
        help="Q5 · Riesgo Operativo: bodegas con revisión de stock desactualizada y alta tasa de tickets.",
    )

tab_auditoria, tab_operaciones, tab_cliente, tab_ia = st.tabs(
    ["🔍 Auditoría", "🚚 Operaciones", "👥 Cliente", "🤖 Insights de IA"]
)

with tab_auditoria:
    encabezado_seccion("📥 Exportables")
    with st.container(border=True):
        render_bloque_descargas(datos, df_maestro, "auditoria")

    st.divider()
    encabezado_seccion("Módulo de Transparencia — Antes vs Después")
    columnas_hs = st.columns(3)
    etiquetas_dataset = [("inventario", "Inventario Central"), ("transacciones", "Transacciones Logística"), ("feedback", "Feedback Clientes")]
    for columna, (clave, etiqueta) in zip(columnas_hs, etiquetas_dataset):
        hs_a = datos["hs_antes"][clave]["health_score"]
        hs_d = datos["hs_despues"][clave]["health_score"]
        columna.metric(etiqueta, f"{hs_d:.1f}", delta=f"{hs_d - hs_a:+.1f} vs. crudo")

    st.divider()
    encabezado_seccion("Detalle de Nulidad, Duplicados y Decisiones de Limpieza")
    for clave, etiqueta, reporte in [
        ("inventario", "Inventario Central", datos["reporte_inventario"]),
        ("transacciones", "Transacciones Logística", datos["reporte_transacciones"]),
        ("feedback", "Feedback Clientes", datos["reporte_feedback"]),
    ]:
        with st.expander(f"{etiqueta} — decisiones de limpieza"):
            hs_a, hs_d = datos["hs_antes"][clave], datos["hs_despues"][clave]
            col_a, col_b = st.columns(2)
            col_a.write("**Nulidad por columna antes (%)**")
            col_a.dataframe(pd.Series(hs_a["nulidad_por_columna_%"], name="% Nulos"))
            col_b.write("**Nulidad por columna después (%)**")
            col_b.dataframe(pd.Series(hs_d["nulidad_por_columna_%"], name="% Nulos"))
            st.write(f"**Duplicados exactos:** {hs_a['duplicados_exactos']} -> {hs_d['duplicados_exactos']}")
            st.write("**Decisiones aplicadas:**")
            for decision in reporte["decisiones"]:
                st.markdown(f"- {decision}")

    with st.expander("Integración — dilema del SKU fantasma y variables derivadas"):
        for decision in datos["reporte_integracion"]["decisiones"]:
            st.markdown(f"- {decision}")

    st.divider()
    encabezado_seccion("Registros Excluidos de los KPIs Globales")
    excl = datos["registros_excluidos"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Outliers de Costo (IQR)", len(excl["costos_inventario_outliers"]))
    col2.metric("Outliers de Tiempo de Entrega (IQR)", len(excl["tiempos_entrega_outliers"]))
    col3.metric("Ventas con SKU Fantasma", len(excl["ventas_fantasma"]))
    with st.expander("Ver registros excluidos"):
        st.write("**Costos atípicos de inventario**")
        st.dataframe(excl["costos_inventario_outliers"])
        st.write("**Tiempos de entrega atípicos**")
        st.dataframe(excl["tiempos_entrega_outliers"])
        st.write("**Ventas con SKU no catalogado**")
        st.dataframe(excl["ventas_fantasma"])

with tab_operaciones:
    encabezado_seccion("1. Fuga de Capital y Rentabilidad")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Transacciones con margen negativo", f"{resumen_m['transacciones_margen_negativo']:,}")
    c2.metric("% del total con margen calculable", formatear_pct(resumen_m["pct_transacciones_margen_negativo"]))
    c3.metric("Pérdida acumulada (USD)", formatear_moneda(resumen_m["perdida_total_usd"]))
    c4.metric(
        "Excluidas por outlier de costo",
        resumen_m["transacciones_excluidas_outlier_costo"],
        help="Transacciones con Costo_Unitario_USD atípico (IQR); se excluyen del KPI global para no distorsionarlo.",
    )
    fig_canal = px.bar(
        resultado_margen["por_canal"],
        x="Canal_Venta",
        y="Pct_Margen_Negativo",
        color="Canal_Venta",
        color_discrete_map=paleta.CANAL_COLORES,
        text="Pct_Margen_Negativo",
        labels={"Pct_Margen_Negativo": "% Transacciones con Margen Negativo", "Canal_Venta": "Canal de Venta"},
        title="Porcentaje de Ventas con Margen Negativo por Canal",
    )
    fig_canal.update_traces(texttemplate="%{text:.1f}%", textposition="outside", showlegend=False)
    fig_canal.update_layout(bargap=0.35)
    st.plotly_chart(fig_canal, use_container_width=True)
    pct_online = resultado_margen["por_canal"].set_index("Canal_Venta")["Pct_Margen_Negativo"].get("Online", 0)
    pct_promedio_otros = resultado_margen["por_canal"][resultado_margen["por_canal"]["Canal_Venta"] != "Online"]["Pct_Margen_Negativo"].mean()
    if pct_online > pct_promedio_otros + 3:
        st.warning(f"El canal Online concentra más margen negativo ({pct_online:.1f}%) que el resto ({pct_promedio_otros:.1f}%): indicio de falla de precios, no solo volumen.")
    else:
        st.info("El margen negativo se distribuye de forma similar entre canales: parece un fenómeno de volumen/costo generalizado, no una falla de precios exclusiva de un canal.")
    with st.expander("Top 20 SKUs con mayor pérdida acumulada"):
        st.dataframe(resultado_margen["top_skus_perdida"], use_container_width=True)
    with st.expander("Ver registros excluidos por outlier de costo"):
        st.dataframe(resultado_margen["registros_excluidos"], use_container_width=True)

    st.divider()
    encabezado_seccion("2. Crisis Logística y Cuellos de Botella")
    col_ciudad, col_bodega = st.columns(2)
    with col_ciudad:
        fig_ciudad = px.bar(
            resultado_logistica["por_ciudad"],
            x="Ciudad_Destino",
            y="correlacion",
            color="correlacion",
            color_continuous_scale=[paleta.DIVERGENTE["negativo"], paleta.DIVERGENTE["neutro"], paleta.DIVERGENTE["positivo"]],
            color_continuous_midpoint=0,
            labels={"correlacion": "Correlación Tiempo Entrega vs NPS"},
            title="Correlación Tiempo de Entrega vs NPS por Ciudad",
        )
        fig_ciudad.update_layout(bargap=0.35, coloraxis_showscale=False)
        st.plotly_chart(fig_ciudad, use_container_width=True)
    with col_bodega:
        fig_bodega = px.bar(
            resultado_logistica["por_bodega"],
            x="Bodega_Origen",
            y="correlacion",
            color="correlacion",
            color_continuous_scale=[paleta.DIVERGENTE["negativo"], paleta.DIVERGENTE["neutro"], paleta.DIVERGENTE["positivo"]],
            color_continuous_midpoint=0,
            labels={"correlacion": "Correlación Tiempo Entrega vs NPS"},
            title="Correlación Tiempo de Entrega vs NPS por Bodega",
        )
        fig_bodega.update_layout(bargap=0.35, coloraxis_showscale=False)
        st.plotly_chart(fig_bodega, use_container_width=True)
    if resumen_l["peor_ciudad"] and resumen_l["peor_bodega"]:
        p_ciudad = resumen_l["peor_ciudad"]["p_valor"]
        p_bodega = resumen_l["peor_bodega"]["p_valor"]
        sig_ciudad = "estadísticamente significativa" if p_ciudad < 0.05 else "no estadísticamente significativa (p > 0.05)"
        sig_bodega = "estadísticamente significativa" if p_bodega < 0.05 else "no estadísticamente significativa (p > 0.05)"
        st.info(
            f"Zona con la correlación más negativa: **{resumen_l['peor_ciudad']['Ciudad_Destino']}** "
            f"(r={resumen_l['peor_ciudad']['correlacion']}, {sig_ciudad}) y bodega "
            f"**{resumen_l['peor_bodega']['Bodega_Origen']}** (r={resumen_l['peor_bodega']['correlacion']}, {sig_bodega}). "
            "Con los filtros actuales, ninguna zona muestra una relación fuerte y significativa entre tiempo de "
            "entrega y satisfacción: la insatisfacción probablemente responde a otros factores (producto, precio)."
            if (p_ciudad >= 0.05 and p_bodega >= 0.05)
            else "Prioriza esta zona para renegociar el operador logístico."
        )

    st.divider()
    encabezado_seccion("3. Análisis de la Venta Invisible")
    c1, c2, c3 = st.columns(3)
    c1.metric("Ingreso Total (USD)", formatear_moneda(resumen_f["ingreso_total_usd"]))
    c2.metric("Ingreso en Riesgo (USD)", formatear_moneda(resumen_f["ingreso_en_riesgo_usd"]))
    c3.metric("% de Ingreso en Riesgo", formatear_pct(resumen_f["pct_ingreso_en_riesgo"]))
    col_canal_fant, col_evol = st.columns(2)
    with col_canal_fant:
        fig_fantasma_canal = px.bar(
            resultado_fantasma["por_canal"],
            x="Canal_Venta",
            y="Pct_Riesgo",
            color="Canal_Venta",
            color_discrete_map=paleta.CANAL_COLORES,
            text="Pct_Riesgo",
            title="% de Ingreso en Riesgo por Canal",
        )
        fig_fantasma_canal.update_traces(texttemplate="%{text:.1f}%", textposition="outside", showlegend=False)
        fig_fantasma_canal.update_layout(bargap=0.35)
        st.plotly_chart(fig_fantasma_canal, use_container_width=True)
    with col_evol:
        fig_evolucion = px.line(
            resultado_fantasma["evolucion_mensual"],
            x="Mes",
            y="Ingreso_En_Riesgo",
            markers=True,
            title="Evolución Mensual del Ingreso en Riesgo",
        )
        fig_evolucion.update_traces(line_color=paleta.ESTADO["critico"])
        st.plotly_chart(fig_evolucion, use_container_width=True)

with tab_cliente:
    encabezado_seccion("4. Diagnóstico de Fidelidad")
    tabla_fid = resultado_fidelidad["por_categoria"].copy()
    tabla_fid["Estado"] = tabla_fid["Paradoja_Fidelidad"].map({True: "Paradoja detectada", False: "Normal"})
    mediana_stock_fid = tabla_fid["Stock_Promedio"].median()
    mediana_nps_fid = tabla_fid["NPS_Promedio"].median()
    fig_fid = px.scatter(
        tabla_fid,
        x="Stock_Promedio",
        y="NPS_Promedio",
        size="Total_Transacciones",
        color="Estado",
        color_discrete_map={"Paradoja detectada": paleta.ESTADO["critico"], "Normal": paleta.GRIS_NEUTRAL},
        text="Categoria",
        labels={"Stock_Promedio": "Stock Promedio Disponible", "NPS_Promedio": "NPS Promedio"},
        title="Disponibilidad de Stock vs Satisfacción del Cliente por Categoría",
    )
    fig_fid.update_traces(textposition="top center")
    fig_fid.add_vline(
        x=mediana_stock_fid, line_dash="dash", line_color=paleta.TINTA["tenue"], line_width=1,
        annotation_text="Stock mediano", annotation_position="top",
        annotation_font_color=paleta.TINTA["secundaria"], annotation_font_size=11,
    )
    fig_fid.add_hline(
        y=mediana_nps_fid, line_dash="dash", line_color=paleta.TINTA["tenue"], line_width=1,
        annotation_text="NPS mediano", annotation_position="right",
        annotation_font_color=paleta.TINTA["secundaria"], annotation_font_size=11,
    )
    st.plotly_chart(fig_fid, use_container_width=True)
    if resumen_fid["categorias_en_paradoja"]:
        diagnosticos = resumen_fid["diagnosticos"]
        lineas_diag = "\n".join(
            f"- **{cat}** → {diagnosticos.get(cat, '')}" for cat in resumen_fid["categorias_en_paradoja"]
        )
        st.warning(
            "Categorías con alto stock y bajo NPS (paradoja de fidelidad), con diagnóstico calculado "
            "cruzando margen (¿cobra de más?) contra calificación de producto (¿el producto falla?) "
            "de cada categoría contra la mediana del resto:\n\n"
            f"{lineas_diag}\n\n"
            "Cuadrante inferior derecho del gráfico (alto stock, NPS bajo) es la señal de alerta."
        )
    st.dataframe(
        tabla_fid[["Categoria", "Stock_Promedio", "NPS_Promedio", "Rating_Promedio", "Margen_Pct_Mediano", "Estado", "Diagnostico"]],
        use_container_width=True,
    )
    st.caption(
        "Diagnóstico: 'Sobrecosto percibido' si el margen mediano de la categoría es igual o mayor a la "
        "mediana de todas las categorías (el cliente paga relativamente más); 'Problema de calidad de "
        "producto' si su calificación promedio (Rating_Producto) queda por debajo de esa mediana. Ambas "
        "señales pueden coexistir."
    )

    st.divider()
    encabezado_seccion("5. Storytelling de Riesgo Operativo")
    col_r1 = st.columns(1)[0]
    with col_r1:
        datos = resultado_riesgo["por_bodega"].copy()

        fig = px.scatter(
            datos,
            x="Dias_Desde_Revision_Promedio",
            y="Ratio_Soporte",
            color="Nivel_Antiguedad",
            text="Bodega_Origen",
            size="Total_Transacciones",
            hover_data={
                "Dias_Desde_Revision_Promedio": ":.0f",
                "Ratio_Soporte": ":.2%",
                "NPS_Promedio": ":.2f",
                "Total_Transacciones": True,
            },
        )

        fig.update_traces(textposition="top center")

        # Línea vertical (mediana)
        fig.add_vline(
            x=resultado_riesgo["mediana_antiguedad"],
            line_dash="dash",
            line_color="gray",
        )

        # Línea horizontal (mediana)
        fig.add_hline(
            y=datos["Ratio_Soporte"].median(),
            line_dash="dash",
            line_color="gray",
        )

        fig.update_layout(
            title="Antigüedad de revisión vs tasa de tickets por bodega",
            xaxis_title="Días desde la última revisión",
            yaxis_title="Tasa de tickets de soporte",
        )

        st.plotly_chart(fig, use_container_width=True)

    if resumen_r["bodegas_operando_a_ciegas"]:
        st.warning(
            f"Bodegas 'operando a ciegas' (revisión desactualizada + alta tasa de tickets): "
            f"{', '.join(resumen_r['bodegas_operando_a_ciegas'])}."
        )
    if resumen_r["correlacion_antiguedad_tickets"] is not None:
        st.caption(
            f"Correlación punto-biserial antigüedad de revisión vs tickets de soporte: "
            f"{resumen_r['correlacion_antiguedad_tickets']} (p={resumen_r['p_valor']})."
        )
    st.dataframe(resultado_riesgo["por_rango_antiguedad"], use_container_width=True)

with tab_ia:
    encabezado_seccion("Recomendación Estratégica con IA (Groq · Llama-3)")
    st.info(
        "Esta app no incluye un API Key propio: ingresa el tuyo de Groq (console.groq.com) para "
        "esta sesión. Nunca se guarda ni se envía a ningún lado distinto de la API de Groq."
    )
    col_key, col_modelo = st.columns([2, 1])
    api_key = col_key.text_input("API Key de Groq", type="password", key="groq_api_key")
    modelo_sel = col_modelo.selectbox("Modelo Llama-3", MODELOS_LLAMA3 + ["Personalizado..."])
    if modelo_sel == "Personalizado...":
        modelo_sel = col_modelo.text_input("ID de modelo personalizado", value="llama-3.3-70b-versatile")

    resumen_estadistico = {
        "Periodo analizado": f"{fecha_inicio} a {fecha_fin}",
        "Transacciones en el filtro actual": len(df_filtrado),
        "Categorías incluidas": ", ".join(categorias_sel),
        "Ciudades incluidas": ", ".join(ciudades_sel),
        "% transacciones con margen negativo": resumen_m["pct_transacciones_margen_negativo"],
        "Pérdida acumulada por margen negativo (USD)": resumen_m["perdida_total_usd"],
        "% de ingreso en riesgo por SKU fantasma": resumen_f["pct_ingreso_en_riesgo"],
        "Ingreso en riesgo (USD)": resumen_f["ingreso_en_riesgo_usd"],
        "Categorías con paradoja de fidelidad": ", ".join(resumen_fid["categorias_en_paradoja"]) or "Ninguna",
        "Bodegas operando a ciegas": ", ".join(resumen_r["bodegas_operando_a_ciegas"]) or "Ninguna",
    }

    if st.button("✨ Generar Recomendación Estratégica", type="primary"):
        with st.spinner("Consultando a Llama-3 en Groq..."):
            try:
                recomendacion = generar_recomendacion(api_key, modelo_sel, resumen_estadistico)
                st.success("Análisis generado con base exclusiva en los filtros aplicados.")
                st.markdown(recomendacion)
            except ErrorIAGroq as error:
                st.error(str(error))

    with st.expander("Ver resumen estadístico enviado al modelo"):
        st.json(resumen_estadistico)
