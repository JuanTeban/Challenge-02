import numpy as np
import pandas as pd
from scipy import stats


def analizar_margen_negativo(df: pd.DataFrame) -> dict:
    con_margen = df[df["Margen_Unitario"].notna()].copy()
    excluidos = con_margen[con_margen["Outlier_Costo"].fillna(False)]
    base = con_margen[~con_margen["Outlier_Costo"].fillna(False)]

    total = len(base)
    negativos = base[base["Margen_Unitario"] < 0]
    n_negativos = len(negativos)
    pct_negativos = round(n_negativos / total * 100, 2) if total else 0.0

    por_canal = (
        base.groupby("Canal_Venta")
        .agg(
            Total_Transacciones=("Transaccion_ID", "count"),
            Transacciones_Margen_Negativo=("Margen_Unitario", lambda s: int((s < 0).sum())),
            Margen_Total_Acumulado=("Margen_Total_Transaccion", "sum"),
        )
        .reset_index()
    )
    por_canal["Pct_Margen_Negativo"] = (
        por_canal["Transacciones_Margen_Negativo"] / por_canal["Total_Transacciones"] * 100
    ).round(2)
    por_canal = por_canal.sort_values("Pct_Margen_Negativo", ascending=False)

    top_skus_perdida = (
        negativos.groupby(["SKU_ID", "Categoria"])
        .agg(
            Num_Ventas=("Transaccion_ID", "count"),
            Margen_Total_Acumulado=("Margen_Total_Transaccion", "sum"),
        )
        .reset_index()
        .sort_values("Margen_Total_Acumulado")
        .head(20)
    )

    resumen = {
        "total_transacciones_con_margen": total,
        "transacciones_margen_negativo": n_negativos,
        "pct_transacciones_margen_negativo": pct_negativos,
        "perdida_total_usd": round(negativos["Margen_Total_Transaccion"].sum(), 2),
        "transacciones_excluidas_outlier_costo": len(excluidos),
        "impacto_excluido_usd": round(excluidos["Margen_Total_Transaccion"].sum(), 2),
    }
    return {
        "resumen": resumen,
        "por_canal": por_canal,
        "top_skus_perdida": top_skus_perdida,
        "registros_excluidos": excluidos,
    }


def _correlacion_grupo(grupo: pd.DataFrame, col_x: str, col_y: str, min_muestras: int) -> pd.Series:
    if len(grupo) < min_muestras or grupo[col_x].std() == 0 or grupo[col_y].std() == 0:
        return pd.Series({"n": len(grupo), "correlacion": np.nan, "p_valor": np.nan})
    r, p = stats.pearsonr(grupo[col_x], grupo[col_y])
    return pd.Series({"n": len(grupo), "correlacion": round(r, 3), "p_valor": round(p, 4)})


def analizar_cuellos_de_botella(df: pd.DataFrame, min_muestras: int = 15) -> dict:
    base = df[df["Tiene_Feedback"] & df["Ciudad_Valida"] & ~df["Outlier_Entrega"]].copy()

    por_ciudad = (
        base.groupby("Ciudad_Destino")[["Tiempo_Entrega_Real", "Satisfaccion_NPS"]]
        .apply(lambda g: _correlacion_grupo(g, "Tiempo_Entrega_Real", "Satisfaccion_NPS", min_muestras))
        .reset_index()
        .dropna(subset=["correlacion"])
        .sort_values("correlacion")
    )
    por_bodega = (
        base.groupby("Bodega_Origen")[["Tiempo_Entrega_Real", "Satisfaccion_NPS"]]
        .apply(lambda g: _correlacion_grupo(g, "Tiempo_Entrega_Real", "Satisfaccion_NPS", min_muestras))
        .reset_index()
        .dropna(subset=["correlacion"])
        .sort_values("correlacion")
    )

    peor_ciudad = por_ciudad.iloc[0].to_dict() if not por_ciudad.empty else None
    peor_bodega = por_bodega.iloc[0].to_dict() if not por_bodega.empty else None

    return {
        "resumen": {"peor_ciudad": peor_ciudad, "peor_bodega": peor_bodega},
        "por_ciudad": por_ciudad,
        "por_bodega": por_bodega,
    }


def analizar_venta_fantasma(df: pd.DataFrame) -> dict:
    ingreso_total = df["Ingreso_Transaccion"].sum()
    ingreso_riesgo = df["Ingreso_En_Riesgo"].sum()
    pct_riesgo = round(ingreso_riesgo / ingreso_total * 100, 2) if ingreso_total else 0.0

    por_canal = df.groupby("Canal_Venta").agg(
        Ingreso_Total=("Ingreso_Transaccion", "sum"),
        Ingreso_En_Riesgo=("Ingreso_En_Riesgo", "sum"),
        Transacciones_Fantasma=("Es_SKU_Fantasma", "sum"),
    ).reset_index()
    por_canal["Pct_Riesgo"] = (por_canal["Ingreso_En_Riesgo"] / por_canal["Ingreso_Total"] * 100).round(2)

    evolucion = df.copy()
    evolucion["Mes"] = evolucion["Fecha_Venta"].dt.to_period("M").astype(str)
    evolucion_mensual = evolucion.groupby("Mes").agg(
        Ingreso_En_Riesgo=("Ingreso_En_Riesgo", "sum"),
        Ingreso_Total=("Ingreso_Transaccion", "sum"),
    ).reset_index().sort_values("Mes")

    resumen = {
        "ingreso_total_usd": round(ingreso_total, 2),
        "ingreso_en_riesgo_usd": round(ingreso_riesgo, 2),
        "pct_ingreso_en_riesgo": pct_riesgo,
        "transacciones_fantasma": int(df["Es_SKU_Fantasma"].sum()),
        "pct_transacciones_fantasma": round(df["Es_SKU_Fantasma"].mean() * 100, 2),
    }
    return {"resumen": resumen, "por_canal": por_canal, "evolucion_mensual": evolucion_mensual}


def analizar_paradoja_fidelidad(df: pd.DataFrame) -> dict:
    base = df[df["Categoria"] != "Sin Catálogo"].copy()
    resumen_categoria = base.groupby("Categoria").agg(
        Stock_Promedio=("Stock_Actual", "mean"),
        NPS_Promedio=("Satisfaccion_NPS", "mean"),
        Rating_Promedio=("Rating_Producto", "mean"),
        Margen_Pct_Mediano=("Margen_Pct", "median"),
        Tickets_Abiertos=("Ticket_Soporte_Abierto", "sum"),
        Total_Transacciones=("Transaccion_ID", "count"),
    ).reset_index()

    mediana_stock = resumen_categoria["Stock_Promedio"].median()
    mediana_nps = resumen_categoria["NPS_Promedio"].median()
    resumen_categoria["Paradoja_Fidelidad"] = (
        (resumen_categoria["Stock_Promedio"] >= mediana_stock)
        & (resumen_categoria["NPS_Promedio"] < mediana_nps)
    )

    mediana_margen = resumen_categoria["Margen_Pct_Mediano"].median()
    mediana_rating = resumen_categoria["Rating_Promedio"].median()

    def _diagnosticar(fila: pd.Series) -> str:
        if not fila["Paradoja_Fidelidad"]:
            return ""
        margen_alto = fila["Margen_Pct_Mediano"] >= mediana_margen
        rating_bajo = fila["Rating_Promedio"] < mediana_rating
        if margen_alto and rating_bajo:
            return "Sobrecosto percibido Y calidad deficiente"
        if margen_alto:
            return "Sobrecosto percibido"
        if rating_bajo:
            return "Problema de calidad de producto"
        return "Sin señal clara en margen ni calificación (investigar caso a caso)"

    resumen_categoria["Diagnostico"] = resumen_categoria.apply(_diagnosticar, axis=1)

    categorias_paradoja = resumen_categoria.loc[
        resumen_categoria["Paradoja_Fidelidad"], "Categoria"
    ].tolist()
    diagnosticos = {
        fila["Categoria"]: fila["Diagnostico"]
        for _, fila in resumen_categoria.loc[resumen_categoria["Paradoja_Fidelidad"]].iterrows()
    }

    return {
        "resumen": {"categorias_en_paradoja": categorias_paradoja, "diagnosticos": diagnosticos},
        "por_categoria": resumen_categoria.sort_values("NPS_Promedio"),
    }


def analizar_riesgo_operativo(df: pd.DataFrame) -> dict:
    base = df[df["Categoria"] != "Sin Catálogo"].copy()
    bins = [-1, 30, 90, 180, 10_000]
    etiquetas = ["<=30 días", "31-90 días", "91-180 días", ">180 días"]
    base["Rango_Antiguedad_Revision"] = pd.cut(
        base["Dias_Desde_Revision"], bins=bins, labels=etiquetas
    )

    por_bodega = base.groupby("Bodega_Origen").agg(
        Dias_Desde_Revision_Promedio=("Dias_Desde_Revision", "mean"),
        Ratio_Soporte=("Ticket_Soporte_Abierto", "mean"),
        NPS_Promedio=("Satisfaccion_NPS", "mean"),
        Total_Transacciones=("Transaccion_ID", "count"),
    ).reset_index().sort_values("Dias_Desde_Revision_Promedio", ascending=False)

    por_rango = base.groupby("Rango_Antiguedad_Revision", observed=True).agg(
        Ratio_Soporte=("Ticket_Soporte_Abierto", "mean"),
        NPS_Promedio=("Satisfaccion_NPS", "mean"),
        Total_Transacciones=("Transaccion_ID", "count"),
    ).reset_index()

    corr_base = base[["Dias_Desde_Revision", "Ticket_Soporte_Abierto"]].dropna()
    r, p = np.nan, np.nan
    if len(corr_base) > 2 and corr_base["Dias_Desde_Revision"].std() > 0:
        r, p = stats.pointbiserialr(
            corr_base["Ticket_Soporte_Abierto"].astype(int), corr_base["Dias_Desde_Revision"]
        )

    mediana_dias = por_bodega["Dias_Desde_Revision_Promedio"].median()
    mediana_ratio = por_bodega["Ratio_Soporte"].median()
    bodegas_a_ciegas = por_bodega.loc[
        (por_bodega["Dias_Desde_Revision_Promedio"] > mediana_dias)
        & (por_bodega["Ratio_Soporte"] > mediana_ratio),
        "Bodega_Origen",
    ].tolist()

    return {
        "resumen": {
            "correlacion_antiguedad_tickets": round(float(r), 3) if pd.notna(r) else None,
            "p_valor": round(float(p), 4) if pd.notna(p) else None,
            "bodegas_operando_a_ciegas": bodegas_a_ciegas,
        },
        "por_bodega": por_bodega,
        "por_rango_antiguedad": por_rango,
    }
