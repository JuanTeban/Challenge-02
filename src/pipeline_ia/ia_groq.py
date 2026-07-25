from groq import Groq
from groq import APIConnectionError, APIStatusError, AuthenticationError, RateLimitError

MODELOS_LLAMA3 = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "llama3-8b-8192",
]


class ErrorIAGroq(Exception):
    pass


def construir_prompt(resumen_estadistico: dict) -> str:
    lineas = [
        "Eres un consultor senior de datos presentando hallazgos a la junta directiva de "
        "TechLogistics S.A.S., un retailer tecnológico. A continuación tienes el resumen "
        "estadístico de los datos YA FILTRADOS por el usuario en el dashboard (respeta "
        "exactamente ese alcance, no asumas datos fuera de este resumen):",
        "",
    ]
    for clave, valor in resumen_estadistico.items():
        lineas.append(f"- {clave}: {valor}")
    lineas.extend([
        "",
        "Redacta exactamente TRES párrafos en español, dirigidos a la junta directiva, sin "
        "títulos ni viñetas: (1) diagnóstico del hallazgo más crítico en las cifras anteriores, "
        "(2) causa raíz probable e impacto financiero, (3) una recomendación táctica concreta y "
        "priorizable. Sé específico con las cifras dadas, no inventes datos adicionales.",
    ])
    return "\n".join(lineas)


def generar_recomendacion(api_key: str, modelo: str, resumen_estadistico: dict) -> str:
    if not api_key or not api_key.strip():
        raise ErrorIAGroq("Debes ingresar un API Key de Groq válido antes de generar el análisis.")

    prompt = construir_prompt(resumen_estadistico)

    try:
        cliente = Groq(api_key=api_key.strip())
        respuesta = cliente.chat.completions.create(
            model=modelo,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=700,
        )
        return respuesta.choices[0].message.content
    except AuthenticationError as error:
        raise ErrorIAGroq("El API Key de Groq no es válido o fue rechazado.") from error
    except RateLimitError as error:
        raise ErrorIAGroq("Límite de solicitudes de Groq alcanzado. Intenta de nuevo en unos segundos.") from error
    except APIConnectionError as error:
        raise ErrorIAGroq("No fue posible conectar con la API de Groq. Verifica tu conexión.") from error
    except APIStatusError as error:
        raise ErrorIAGroq(f"Groq respondió con un error ({error.status_code}). Verifica el modelo seleccionado.") from error
