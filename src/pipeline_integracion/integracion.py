import pandas as pd
import numpy as np


def _moda_segura(serie: pd.Series, valor_por_defecto: str) -> str:
    modas = serie.dropna().mode()
    return modas.iloc[0] if not modas.empty else valor_por_defecto


def agregar_feedback_por_transaccion(fb_limpio: pd.DataFrame) -> pd.DataFrame:
    def resumir_comentarios(serie: pd.Series) -> str:
        comentarios = [c for c in serie.dropna().unique() if c != "Sin comentario"]
        return "; ".join(comentarios) if comentarios else "Sin comentario"

    agregado = fb_limpio.groupby("Transaccion_ID").agg(
        Rating_Producto=("Rating_Producto", "mean"),
        Rating_Logistica=("Rating_Logistica", "mean"),
        Satisfaccion_NPS=("Satisfaccion_NPS", "mean"),
        Ticket_Soporte_Abierto=("Ticket_Soporte_Abierto", "any"),
        Recomienda_Marca=("Recomienda_Marca", lambda s: _moda_segura(s, "Sin Respuesta")),
        Comentario_Texto=("Comentario_Texto", resumir_comentarios),
        Feedback_Count=("Feedback_ID", "count"),
    ).reset_index()
    return agregado


def construir_dataset_maestro(
    inv_limpio: pd.DataFrame, trx_limpio: pd.DataFrame, fb_limpio: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:
    reporte = {"decisiones": []}

    n_transacciones = len(trx_limpio)
    df = trx_limpio.merge(inv_limpio, on="SKU_ID", how="left", suffixes=("", "_inventario"))

    df["Categoria"] = df["Categoria"].fillna("Sin Catálogo")
    df["Bodega_Origen"] = df["Bodega_Origen"].fillna("Sin Catálogo")
    for columna_flag in ("Bodega_Externa", "Stock_Imputado", "Outlier_Costo"):
        df[columna_flag] = df[columna_flag].astype("boolean")
    reporte["decisiones"].append(
        f"Dilema del SKU Fantasma: {int(df['Es_SKU_Fantasma'].sum())} de {n_transacciones} "
        "transacciones ({:.1f}%) referencian un SKU_ID ausente del maestro de inventario. Se "
        "tratan como ventas reales de productos no catalogados (el ingreso se conserva y se "
        "reporta), NO como errores a descartar, porque el dinero fue efectivamente cobrado. "
        "Se excluyen únicamente del cálculo de margen (no existe Costo_Unitario_USD de "
        "referencia) y de los análisis de stock/bodega, quedando Categoria/Bodega_Origen "
        "marcados como 'Sin Catálogo' para trazabilidad.".format(df["Es_SKU_Fantasma"].mean() * 100)
    )

    feedback_agregado = agregar_feedback_por_transaccion(fb_limpio)
    n_trx_con_multiples_feedback = int((fb_limpio.groupby("Transaccion_ID").size() > 1).sum())
    df = df.merge(feedback_agregado, on="Transaccion_ID", how="left")
    reporte["decisiones"].append(
        f"Feedback_Clientes: {n_trx_con_multiples_feedback} transacciones tenían más de un "
        "registro de feedback asociado. Se agregaron (promedio de ratings/NPS, moda de "
        "Recomienda_Marca, OR lógico de Ticket_Soporte_Abierto) ANTES del cruce para que cada "
        "fila de dataset_maestro represente una única transacción y no se dupliquen ingresos "
        "ni cantidades al unir (evita fan-out del merge)."
    )
    df["Tiene_Feedback"] = df["Feedback_Count"].notna() & (df["Feedback_Count"] > 0)
    df["Feedback_Count"] = df["Feedback_Count"].fillna(0).astype(int)
    df["Ticket_Soporte_Abierto"] = df["Ticket_Soporte_Abierto"].fillna(False).astype(bool)

    df["Ingreso_Transaccion"] = df["Precio_Venta_Final"] * df["Cantidad_Vendida"]
    df["Margen_Unitario"] = df["Precio_Venta_Final"] - df["Costo_Unitario_USD"]
    df["Margen_Pct"] = df["Margen_Unitario"] / df["Precio_Venta_Final"]
    df["Margen_Total_Transaccion"] = df["Margen_Unitario"] * df["Cantidad_Vendida"]
    reporte["decisiones"].append(
        "Variable derivada Margen_Unitario/Margen_Pct/Margen_Total_Transaccion: "
        "Precio_Venta_Final - Costo_Unitario_USD. NaN para ventas fantasma (sin costo de "
        "referencia); se excluyen explícitamente de los KPIs de rentabilidad global."
    )

    df["Brecha_Entrega"] = df["Tiempo_Entrega_Real"] - df["Lead_Time_Dias"]
    reporte["decisiones"].append(
        "Variable derivada Brecha_Entrega = Tiempo_Entrega_Real - Lead_Time_Dias del inventario. "
        "Supuesto documentado: el modelo de datos no registra un tiempo de entrega 'prometido' "
        "por transacción, por lo que se usa el Lead_Time_Dias del proveedor (inventario) como "
        "único proxy disponible de la expectativa de entrega."
    )

    df["Ingreso_En_Riesgo"] = np.where(df["Es_SKU_Fantasma"], df["Ingreso_Transaccion"], 0.0)
    reporte["decisiones"].append(
        "Variable derivada Ingreso_En_Riesgo: ingreso de transacciones con SKU fantasma, "
        "aislado para cuantificar el impacto financiero de la falta de control de inventario "
        "(pregunta de negocio #3)."
    )

    return df, reporte


def calcular_ratio_soporte_por_categoria(df_maestro: pd.DataFrame) -> pd.DataFrame:
    resumen = df_maestro.groupby("Categoria").agg(
        Total_Transacciones=("Transaccion_ID", "count"),
        Tickets_Abiertos=("Ticket_Soporte_Abierto", "sum"),
    ).reset_index()
    resumen["Ratio_Soporte_Categoria"] = (
        resumen["Tickets_Abiertos"] / resumen["Total_Transacciones"]
    ).round(4)
    return resumen.sort_values("Ratio_Soporte_Categoria", ascending=False)
