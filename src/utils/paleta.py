CATEGORICO = [
    "#2a78d6",
    "#eb6834",
    "#1baf7a",
    "#eda100",
    "#e87ba4",
    "#008300",
    "#4a3aa7",
    "#e34948",
]

GRIS_NEUTRAL = "#898781"

ESTADO = {
    "bueno": "#0ca30c",
    "advertencia": "#fab219",
    "grave": "#ec835a",
    "critico": "#d03b3b",
}

DIVERGENTE = {"positivo": "#2a78d6", "negativo": "#e34948", "neutro": "#f0efec"}

SECUENCIAL_AZUL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

TINTA = {"primaria": "#0b0b0b", "secundaria": "#52514e", "tenue": "#898781"}

SUPERFICIE = {"grafico": "#fcfcfb", "pagina": "#f9f9f7"}

GRID = "#e1e0d9"

CANAL_COLORES = {
    "Físico": CATEGORICO[0],
    "WhatsApp": CATEGORICO[1],
    "Online": CATEGORICO[2],
    "App": CATEGORICO[3],
}

CIUDAD_COLORES = {
    "Bogotá": CATEGORICO[0],
    "Medellín": CATEGORICO[1],
    "Cali": CATEGORICO[2],
    "Barranquilla": CATEGORICO[3],
    "Bucaramanga": CATEGORICO[4],
    "Sin Ciudad (Venta Web)": GRIS_NEUTRAL,
}

BODEGA_COLORES = {
    "Norte": CATEGORICO[0],
    "Sur": CATEGORICO[1],
    "Occidente": CATEGORICO[2],
    "ZONA_FRANCA": CATEGORICO[3],
    "BOD-EXT-99": CATEGORICO[4],
    "Sin Catálogo": GRIS_NEUTRAL,
}

CATEGORIA_COLORES = {
    "Smartphones": CATEGORICO[0],
    "Laptops": CATEGORICO[1],
    "Accesorios": CATEGORICO[2],
    "Monitores": CATEGORICO[3],
    "Tablets": CATEGORICO[4],
    "Sin Categoría": GRIS_NEUTRAL,
    "Sin Catálogo": TINTA["secundaria"],
}


def plantilla_plotly() -> dict:
    return {
        "layout": {
            "paper_bgcolor": SUPERFICIE["grafico"],
            "plot_bgcolor": SUPERFICIE["grafico"],
            "font": {"color": TINTA["primaria"], "family": "system-ui, -apple-system, 'Segoe UI', sans-serif"},
            "colorway": CATEGORICO,
            "xaxis": {"gridcolor": GRID, "linecolor": GRID, "zerolinecolor": GRID},
            "yaxis": {"gridcolor": GRID, "linecolor": GRID, "zerolinecolor": GRID},
            "legend": {"font": {"color": TINTA["secundaria"]}},
            "margin": {"t": 56, "l": 8, "r": 8, "b": 8},
            "title": {"font": {"size": 16, "color": TINTA["primaria"]}},
        },
        "data": {
            "bar": [{"marker": {"cornerradius": 4}}],
            "scatter": [
                {
                    "line": {"width": 2},
                    "marker": {"size": 11, "line": {"width": 2, "color": SUPERFICIE["grafico"]}},
                }
            ],
        },
    }
