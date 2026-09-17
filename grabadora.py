# ==============================================================
# GRABADOR DE AUDIO PROPIO (componente personalizado)
# Graba en formato comprimido (webm/opus) directamente en el navegador,
# con pausar/reanudar/detener, y soporta reuniones de varias horas
# (~21 MB por hora, frente a ~700 MB/2h del grabador WAV de Streamlit).
# ==============================================================

import base64
import os

import streamlit.components.v1 as components

_RUTA_COMPONENTE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "componentes", "grabadora")

_grabadora = components.declare_component("grabadora_larga", path=_RUTA_COMPONENTE)


def grabadora_audio(key="grabadora_larga"):
    """Muestra el grabador y devuelve (bytes, duracion_seg) o (None, 0) si aún no hay grabación."""
    resultado = _grabadora(key=key, default=None)
    if not resultado or not resultado.get("b64"):
        return None, 0
    try:
        return base64.b64decode(resultado["b64"]), int(resultado.get("duracion", 0))
    except Exception:
        return None, 0
