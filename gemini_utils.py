# ==============================================================
# LLAMADAS A GEMINI CON REINTENTOS Y MODELOS DE RESPALDO
# Si el modelo principal responde 503 (saturado), se reintenta con
# espera creciente y, si persiste, se pasa al siguiente modelo.
# ==============================================================

import time

import streamlit as st
from google.genai import errors

from config import MODELO_GEMINI

MODELOS = [
    MODELO_GEMINI,        # principal
    "gemini-2.5-flash",   # respaldo 1
    "gemini-3.8-flash",   # respaldo 2 (saturado desde sep 2026, por eso va de último)
]
INTENTOS_POR_MODELO = 3
ERRORES_TRANSITORIOS = (429, 500, 502, 503)


def generar_con_reintentos(cliente, contents, config=None):
    """Genera contenido probando cada modelo con reintentos. Devuelve la respuesta o None."""
    for modelo in MODELOS:
        for intento in range(INTENTOS_POR_MODELO):
            try:
                return cliente.models.generate_content(model=modelo, contents=contents, config=config)
            except errors.APIError as e:
                if e.code not in ERRORES_TRANSITORIOS:
                    raise
                # Reintento silencioso: el usuario solo ve el indicador de carga
                if intento < INTENTOS_POR_MODELO - 1:
                    time.sleep(2 ** (intento + 1))  # 2s, 4s
    st.error("❌ El servicio está saturado en este momento. Espera unos minutos e intenta de nuevo.")
    return None
