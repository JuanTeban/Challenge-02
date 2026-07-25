"""
fase1_main.py
Orquesta la Fase 1 (Auditoría y Limpieza) para TechLogistics S.A.
Ejecutar: python fase1_main.py
Genera:
  - data/inventario_limpio.csv
  - data/transacciones_limpio.csv
  - data/feedback_limpio.csv
  - reporte_limpieza.md  (para la pestaña de Transparencia del dashboard
    y como insumo directo del Documento de Hallazgos)
"""

import json
import pandas as pd
from limpieza import calcular_health_score, limpiar_inventario, limpiar_transacciones, limpiar_feedback

RUTA_CRUDOS = "../data_raw"   # donde están los 3 CSV originales
RUTA_LIMPIOS = "../data"      # donde se guardan los limpios


def main():
    inv_raw = pd.read_csv(f"{RUTA_CRUDOS}/inventario_central_v2.csv")
    trx_raw = pd.read_csv(f"{RUTA_CRUDOS}/transacciones_logistica_v2.csv")
    fb_raw = pd.read_csv(f"{RUTA_CRUDOS}/feedback_clientes_v2.csv")

    # --- Health score ANTES ---
    hs_antes = {
        "inventario": calcular_health_score(inv_raw, "Inventario"),
        "transacciones": calcular_health_score(trx_raw, "Transacciones"),
        "feedback": calcular_health_score(fb_raw, "Feedback"),
    }

    # --- Limpieza ---
    inv_limpio, rep_inv = limpiar_inventario(inv_raw)
    trx_limpio, rep_trx = limpiar_transacciones(trx_raw, set(inv_limpio["SKU_ID"]))
    fb_limpio, rep_fb = limpiar_feedback(fb_raw)

    # --- Health score DESPUÉS ---
    hs_despues = {
        "inventario": calcular_health_score(inv_limpio, "Inventario"),
        "transacciones": calcular_health_score(trx_limpio, "Transacciones"),
        "feedback": calcular_health_score(fb_limpio, "Feedback"),
    }

    # --- Guardar datasets limpios ---
    inv_limpio.to_csv(f"{RUTA_LIMPIOS}/inventario_limpio.csv", index=False)
    trx_limpio.to_csv(f"{RUTA_LIMPIOS}/transacciones_limpio.csv", index=False)
    fb_limpio.to_csv(f"{RUTA_LIMPIOS}/feedback_limpio.csv", index=False)

    # --- Reporte de limpieza (Markdown, descargable desde el dashboard) ---
    with open(f"{RUTA_LIMPIOS}/reporte_limpieza.md", "w", encoding="utf-8") as f:
        f.write("# Reporte de Limpieza y Auditoría de Datos — TechLogistics S.A.\n\n")
        for nombre, reporte, hs_a, hs_d in [
            ("Inventario Central", rep_inv, hs_antes["inventario"], hs_despues["inventario"]),
            ("Transacciones Logística", rep_trx, hs_antes["transacciones"], hs_despues["transacciones"]),
            ("Feedback Clientes", rep_fb, hs_antes["feedback"], hs_despues["feedback"]),
        ]:
            f.write(f"## {nombre}\n\n")
            f.write(f"**Health Score:** {hs_a['health_score']} → {hs_d['health_score']}  \n")
            f.write(f"**Nulidad promedio:** {hs_a['pct_nulidad_promedio']}% → {hs_d['pct_nulidad_promedio']}%  \n")
            f.write(f"**Duplicados exactos:** {hs_a['duplicados_exactos']} → {hs_d['duplicados_exactos']}\n\n")
            f.write("**Decisiones aplicadas:**\n\n")
            for d in reporte["decisiones"]:
                f.write(f"- {d}\n")
            f.write("\n")

    # --- JSON crudo por si el dashboard lo necesita como dict ---
    with open(f"{RUTA_LIMPIOS}/health_scores.json", "w", encoding="utf-8") as f:
        json.dump({"antes": hs_antes, "despues": hs_despues}, f, indent=2, ensure_ascii=False)

    print("Fase 1 completada. Archivos generados en", RUTA_LIMPIOS)
    for nombre in ["inventario", "transacciones", "feedback"]:
        print(f"  {nombre}: health score {hs_antes[nombre]['health_score']} -> {hs_despues[nombre]['health_score']}")


if __name__ == "__main__":
    main()
