from pathlib import Path

import pandas as pd

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent.parent

DIR_INPUT = RAIZ_PROYECTO / "data" / "input"
DIR_OUTPUT = RAIZ_PROYECTO / "data" / "output"
DIR_AUDITORIA = DIR_OUTPUT / "01_auditoria"
DIR_DATOS_LIMPIOS = DIR_OUTPUT / "02_datos_limpios"
DIR_REPORTES = DIR_OUTPUT / "03_reportes"

RUTA_INVENTARIO_CRUDO = DIR_INPUT / "inventario_central_v2.csv"
RUTA_TRANSACCIONES_CRUDO = DIR_INPUT / "transacciones_logistica_v2.csv"
RUTA_FEEDBACK_CRUDO = DIR_INPUT / "feedback_clientes_v2.csv"

RUTA_INVENTARIO_LIMPIO = DIR_DATOS_LIMPIOS / "inventario_limpio.csv"
RUTA_TRANSACCIONES_LIMPIO = DIR_DATOS_LIMPIOS / "transacciones_limpio.csv"
RUTA_FEEDBACK_LIMPIO = DIR_DATOS_LIMPIOS / "feedback_limpio.csv"
RUTA_DATASET_MAESTRO = DIR_DATOS_LIMPIOS / "dataset_maestro.csv"

RUTA_HEALTH_SCORES = DIR_AUDITORIA / "health_scores.json"
RUTA_REPORTE_LIMPIEZA = DIR_AUDITORIA / "reporte_limpieza.md"
RUTA_OUTLIERS_DETECTADOS = DIR_AUDITORIA / "outliers_detectados.csv"

RUTA_KPIS_RESUMEN = DIR_REPORTES / "kpis_resumen.json"
RUTA_RESPUESTAS_PREGUNTAS = DIR_REPORTES / "respuestas_5_preguntas.md"

for _directorio in (DIR_INPUT, DIR_AUDITORIA, DIR_DATOS_LIMPIOS, DIR_REPORTES):
    _directorio.mkdir(parents=True, exist_ok=True)


def fecha_corte_analisis() -> pd.Timestamp:
    """Fecha de referencia (hoy) para validar transacciones futuras y antigüedad de revisión.

    Se calcula dinámicamente (datetime.now()), tal como exige la guía de validación del
    profesor, en vez de un valor fijo que quedaría obsoleto en cada corrida futura.
    """
    return pd.Timestamp.now().normalize()
