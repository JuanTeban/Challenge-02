import json
from pathlib import Path

import numpy as np
import pandas as pd


def _normalizar_valor(valor):
    if isinstance(valor, dict):
        return {clave: _normalizar_valor(v) for clave, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_normalizar_valor(v) for v in valor]
    if isinstance(valor, np.integer):
        return int(valor)
    if isinstance(valor, np.floating):
        return float(valor)
    if isinstance(valor, np.bool_):
        return bool(valor)
    if isinstance(valor, pd.Timestamp):
        return valor.isoformat()
    return valor


def guardar_json(datos: dict, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(_normalizar_valor(datos), archivo, indent=2, ensure_ascii=False)


def leer_json(ruta: Path) -> dict:
    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar_texto(contenido: str, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)


def guardar_dataframe(df: pd.DataFrame, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta, index=False, encoding="utf-8")


def leer_csv_crudo(ruta: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(ruta, encoding="utf-8")
    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"No se encontró el archivo de datos esperado en: {ruta}"
        ) from error
