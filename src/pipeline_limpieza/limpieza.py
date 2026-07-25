import pandas as pd
import numpy as np

from src.utils.config import fecha_corte_analisis


def calcular_health_score(df: pd.DataFrame, nombre: str) -> dict:
    n_filas = len(df)
    nulidad_col = (df.isnull().mean() * 100).round(2).to_dict()
    pct_nulidad_promedio = float(np.mean(list(nulidad_col.values()))) if nulidad_col else 0.0
    duplicados = int(df.duplicated().sum())
    pct_duplicados = round((duplicados / n_filas * 100), 2) if n_filas else 0.0

    health_score = round(max(0, 100 - pct_nulidad_promedio - pct_duplicados), 2)

    return {
        "dataset": nombre,
        "n_filas": n_filas,
        "nulidad_por_columna_%": nulidad_col,
        "pct_nulidad_promedio": round(pct_nulidad_promedio, 2),
        "duplicados_exactos": duplicados,
        "pct_duplicados": pct_duplicados,
        "health_score": health_score,
    }


def detectar_outliers_iqr(serie: pd.Series) -> pd.Series:
    q1, q3 = serie.quantile(0.25), serie.quantile(0.75)
    iqr = q3 - q1
    lim_inf, lim_sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return (serie < lim_inf) | (serie > lim_sup)


def limpiar_inventario(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = df.copy()
    reporte = {"decisiones": []}

    mapa_categoria = {
        "smart-phone": "Smartphones", "Smartphones": "Smartphones",
        "LAPTOP": "Laptops", "Laptops": "Laptops",
        "Accesorios": "Accesorios", "Monitores": "Monitores",
        "Tablets": "Tablets", "???": "Sin Categoría",
    }
    df["Categoria"] = df["Categoria"].map(mapa_categoria).fillna("Sin Categoría")
    reporte["decisiones"].append(
        "Categoria: normalizada a 5 categorías estándar; '???' -> 'Sin Categoría' (no se inventa el valor real)."
    )

    df["Bodega_Origen"] = df["Bodega_Origen"].replace({"norte": "Norte"})
    df["Bodega_Externa"] = df["Bodega_Origen"].isin(["ZONA_FRANCA", "BOD-EXT-99"])
    reporte["decisiones"].append(
        "Bodega_Origen: 'norte' -> 'Norte' (typo de casing). "
        "'ZONA_FRANCA' y 'BOD-EXT-99' se mantienen como bodegas externas reales (flag Bodega_Externa), "
        "no se fusionan con Norte/Sur/Occidente por falta de evidencia de que sean el mismo lugar."
    )

    def parse_lead_time(x):
        if pd.isna(x):
            return np.nan
        x = str(x).strip()
        if x == "Inmediato":
            return 0.0
        if "-" in x:
            a, b = x.replace(" días", "").split("-")
            return (float(a) + float(b)) / 2
        try:
            return float(x)
        except ValueError:
            return np.nan

    n_nulos_lt = df["Lead_Time_Dias"].isna().sum()
    df["Lead_Time_Dias"] = df["Lead_Time_Dias"].apply(parse_lead_time)
    mediana_lt = df["Lead_Time_Dias"].median()
    df["Lead_Time_Dias"] = df["Lead_Time_Dias"].fillna(mediana_lt)
    reporte["decisiones"].append(
        f"Lead_Time_Dias: rangos ('25-30 días') -> promedio; 'Inmediato' -> 0; "
        f"{n_nulos_lt} nulos imputados con mediana ({mediana_lt:.1f} días) por ser dato ruidoso/asimétrico."
    )

    n_negativos = (df["Stock_Actual"] < 0).sum()
    n_nulos_stock = df["Stock_Actual"].isna().sum()
    df.loc[df["Stock_Actual"] < 0, "Stock_Actual"] = np.nan
    df["Stock_Imputado"] = df["Stock_Actual"].isna()
    df["Stock_Actual"] = df.groupby("Categoria")["Stock_Actual"].transform(
        lambda s: s.fillna(s.median())
    )
    reporte["decisiones"].append(
        f"Stock_Actual: {n_negativos} negativos (error de captura, físicamente imposible) + "
        f"{n_nulos_stock} nulos -> imputados con mediana por Categoria (mediana, no media, "
        f"por sesgo de la distribución). Se preserva flag Stock_Imputado para trazabilidad."
    )

    df["Outlier_Costo"] = detectar_outliers_iqr(df["Costo_Unitario_USD"])
    reporte["decisiones"].append(
        f"Costo_Unitario_USD: {int(df['Outlier_Costo'].sum())} outliers detectados vía IQR. "
        "Se marcan (Outlier_Costo=True) pero NO se eliminan del dataset; se excluyen "
        "solo del cálculo de KPIs de rentabilidad global, con opción de 'ver excluidos' en el dashboard."
    )

    df["Ultima_Revision"] = pd.to_datetime(df["Ultima_Revision"], errors="coerce")
    df["Dias_Desde_Revision"] = (fecha_corte_analisis() - df["Ultima_Revision"]).dt.days
    reporte["decisiones"].append(
        "Ultima_Revision: parseada a fecha; se deriva Dias_Desde_Revision para medir "
        "confianza del dato (insumo de la pregunta de bodegas 'operando a ciegas')."
    )

    return df, reporte


def limpiar_transacciones(df: pd.DataFrame, skus_validos: set) -> tuple[pd.DataFrame, dict]:
    df = df.copy()
    reporte = {"decisiones": []}

    df["Fecha_Venta"] = pd.to_datetime(df["Fecha_Venta"], format="%d/%m/%Y", errors="coerce")
    hoy = fecha_corte_analisis()
    n_futuras = (df["Fecha_Venta"] > hoy).sum()
    df = df[df["Fecha_Venta"] <= hoy].copy()
    reporte["decisiones"].append(
        f"Fecha_Venta: parseada (formato DD/MM/YYYY, consistente en este archivo). "
        f"{n_futuras} transacciones con fecha futura (> hoy) excluidas del análisis temporal."
    )

    df["Es_SKU_Fantasma"] = ~df["SKU_ID"].isin(skus_validos)
    reporte["decisiones"].append(
        f"SKU_ID: {int(df['Es_SKU_Fantasma'].sum())} transacciones ({df['Es_SKU_Fantasma'].mean()*100:.1f}%) "
        "con SKU no catalogado ('venta fantasma'). NO se eliminan: se flaggean para "
        "cuantificar el impacto financiero (pregunta de negocio #3)."
    )

    df["Posible_Devolucion"] = df["Cantidad_Vendida"] < 0
    reporte["decisiones"].append(
        f"Cantidad_Vendida: {int(df['Posible_Devolucion'].sum())} valores negativos flaggeados como "
        "posible devolución. Se preserva el valor original para trazabilidad de ingresos; "
        "se excluyen de 'unidades vendidas' pero se contabilizan en el neto."
    )

    n_nulos_envio = df["Costo_Envio"].isna().sum()
    mediana_envio = df["Costo_Envio"].median()
    df["Costo_Envio"] = df["Costo_Envio"].fillna(mediana_envio)
    reporte["decisiones"].append(
        f"Costo_Envio: {n_nulos_envio} nulos (~8% en todos los canales por igual, sin patrón) "
        f"-> imputados con mediana global ({mediana_envio:.2f})."
    )

    df["Outlier_Entrega"] = detectar_outliers_iqr(df["Tiempo_Entrega_Real"])
    reporte["decisiones"].append(
        f"Tiempo_Entrega_Real: {int(df['Outlier_Entrega'].sum())} outliers (hasta 999 días) flaggeados "
        "vía IQR, no eliminados; se excluyen del promedio de KPI de servicio."
    )

    n_nulos_estado = df["Estado_Envio"].isna().sum()
    df["Estado_Envio"] = df["Estado_Envio"].fillna("Sin Información")
    reporte["decisiones"].append(
        f"Estado_Envio: {n_nulos_estado} nulos ({n_nulos_estado/len(df)*100:.1f}%) -> categoría "
        "'Sin Información', NO moda (imputar con 'Entregado' ocultaría fallas operativas reales)."
    )

    mapa_ciudad = {"MED": "Medellín", "BOG": "Bogotá", "Ventas_Web": "Sin Ciudad (Venta Web)"}
    df["Ciudad_Destino"] = df["Ciudad_Destino"].replace(mapa_ciudad)
    df["Ciudad_Valida"] = df["Ciudad_Destino"] != "Sin Ciudad (Venta Web)"
    reporte["decisiones"].append(
        "Ciudad_Destino: 'MED'->'Medellín', 'BOG'->'Bogotá' (abreviaturas de captura). "
        "'Ventas_Web' NO es una ciudad real, sino un error de captura del canal en el campo "
        "ciudad -> renombrada a la etiqueta explícita 'Sin Ciudad (Venta Web)' (en vez de dejar "
        "el valor crudo, que aparecería como una ciudad falsa en el filtro de la barra lateral) "
        "y flag Ciudad_Valida=False; se excluye del análisis geográfico pero se conserva la fila "
        "y su ingreso en los KPIs financieros."
    )

    reporte["decisiones"].append(
        "Canal_Venta: valores ('Físico', 'WhatsApp', 'Online', 'App') ya consistentes; "
        "validado, no requiere normalización."
    )

    return df, reporte


def limpiar_feedback(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = df.copy()
    reporte = {"decisiones": []}

    dup_mask = df["Feedback_ID"].duplicated(keep="first")
    n_dup = int(dup_mask.sum())
    df.loc[dup_mask, "Feedback_ID"] = df.loc[dup_mask, "Feedback_ID"] + "-B"
    df["ID_Reasignado"] = dup_mask
    reporte["decisiones"].append(
        f"Feedback_ID: {n_dup} IDs duplicados correspondían a registros de clientes DISTINTOS "
        "(no duplicados exactos) -> se reasigna sufijo '-B' en vez de eliminar, "
        "para no perder opiniones reales de clientes."
    )

    n_invalido = (df["Rating_Producto"] == 99).sum()
    df.loc[df["Rating_Producto"] == 99, "Rating_Producto"] = np.nan
    mediana_rating = df["Rating_Producto"].median()
    df["Rating_Producto"] = df["Rating_Producto"].fillna(mediana_rating)
    reporte["decisiones"].append(
        f"Rating_Producto: {n_invalido} valores '99' (fuera de escala 1-5) -> NaN -> "
        f"imputados con MEDIANA ({mediana_rating}), no media, por ser escala ordinal (Likert)."
    )

    reporte["decisiones"].append(
        "Rating_Logistica: sin valores fuera de rango (1-5) ni nulos detectados; no requiere limpieza."
    )

    df["Comentario_Texto"] = df["Comentario_Texto"].replace("---", np.nan).fillna("Sin comentario")
    reporte["decisiones"].append(
        "Comentario_Texto: nulos y '---' unificados como 'Sin comentario' (mismo significado)."
    )

    df["Recomienda_Marca"] = df["Recomienda_Marca"].replace(
        {"SI": "Sí", "NO": "No", "Maybe": "Tal vez"}
    )
    n_sin_resp = df["Recomienda_Marca"].isna().sum()
    df["Recomienda_Marca"] = df["Recomienda_Marca"].fillna("Sin Respuesta")
    reporte["decisiones"].append(
        f"Recomienda_Marca: 'SI'/'NO' normalizados a 'Sí'/'No'; 'Maybe' (inglés suelto en un "
        f"campo por lo demás en español) -> 'Tal vez'. {n_sin_resp} nulos -> "
        "'Sin Respuesta' (nunca se imputa la opinión de un cliente)."
    )

    df["Ticket_Soporte_Abierto"] = df["Ticket_Soporte_Abierto"].map(
        {"Sí": True, "1": True, "No": False, "0": False}
    ).astype(bool)
    reporte["decisiones"].append(
        "Ticket_Soporte_Abierto: 'Sí'/'1' -> True, 'No'/'0' -> False (normalizado a booleano)."
    )

    n_edad_invalida = (df["Edad_Cliente"] > 100).sum()
    df.loc[df["Edad_Cliente"] > 100, "Edad_Cliente"] = np.nan
    mediana_edad = df["Edad_Cliente"].median()
    df["Edad_Cliente"] = df["Edad_Cliente"].fillna(mediana_edad)
    reporte["decisiones"].append(
        f"Edad_Cliente: {n_edad_invalida} valores de 195 años (físicamente imposibles) -> NaN -> "
        f"imputados con mediana ({mediana_edad})."
    )

    reporte["decisiones"].append(
        "Satisfaccion_NPS: el rango [-100, 100] corresponde a la metodología NPS estándar; "
        "no requiere limpieza, solo documentación."
    )

    return df, reporte


def obtener_registros_excluidos(inv_limpio: pd.DataFrame, trx_limpio: pd.DataFrame) -> dict:
    return {
        "costos_inventario_outliers": inv_limpio[inv_limpio["Outlier_Costo"]].copy(),
        "tiempos_entrega_outliers": trx_limpio[trx_limpio["Outlier_Entrega"]].copy(),
        "ventas_fantasma": trx_limpio[trx_limpio["Es_SKU_Fantasma"]].copy(),
    }
