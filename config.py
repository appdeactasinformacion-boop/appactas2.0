# ==============================================================
# CONFIGURACIÓN INICIAL: variables de entorno, constantes y Gemini
# ==============================================================

import glob
import os
import shutil

# Hacer que Python confíe también en los certificados del almacén de Windows
# (donde las redes corporativas instalan sus certificados de inspección SSL).
# Evita errores intermitentes "CERTIFICATE_VERIFY_FAILED" al subir audios.
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

import streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv()


def _configurar_ffmpeg():
    """Agrega ffmpeg al PATH del proceso si la terminal no lo tiene (necesario para grabar audio)."""
    if shutil.which("ffmpeg"):
        return
    local = os.environ.get("LOCALAPPDATA", "")
    candidatos = [os.path.join(local, "Microsoft", "WinGet", "Links")]
    candidatos += glob.glob(os.path.join(local, "Microsoft", "WinGet", "Packages", "Gyan.FFmpeg*", "*", "bin"))
    for ruta in candidatos:
        if os.path.exists(os.path.join(ruta, "ffmpeg.exe")):
            os.environ["PATH"] = ruta + os.pathsep + os.environ["PATH"]
            return


_configurar_ffmpeg()

def _leer_clave(nombre):
    """Busca la clave primero en el entorno (.env local) y luego en los
    Secrets de Streamlit Cloud, para que la app funcione en ambos lados."""
    valor = os.getenv(nombre)
    if valor:
        return valor
    try:
        return st.secrets.get(nombre)
    except Exception:
        return None


API_KEY = _leer_clave("GOOGLE_API_KEY")
ANTHROPIC_API_KEY = _leer_clave("ANTHROPIC_API_KEY")
JSONBIN_API_KEY = _leer_clave("JSONBIN_API_KEY")
JSONBIN_BIN_ID = _leer_clave("JSONBIN_BIN_ID")

# Ruta absoluta basada en la ubicación de este archivo, para que la app
# funcione sin importar desde qué carpeta se ejecute streamlit
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
LIMITE_CONTADOR = 13  # <-- límite máximo antes de enviar alerta
# gemini-3.8-flash está respondiendo 503 (saturado) desde sep 2026; se usa
# 3.5-flash como principal y 3.8 queda como último respaldo en gemini_utils
MODELO_GEMINI = "gemini-3.5-flash"
# Claude genera el acta a partir de la transcripción (si hay ANTHROPIC_API_KEY
# en el .env); Gemini queda solo para transcribir audio y como respaldo
MODELO_CLAUDE = "claude-sonnet-5"


def configurar_gemini():
    """Valida la API key y devuelve el cliente de Gemini listo para usar."""
    if not API_KEY:
        st.error("No se encontró GOOGLE_API_KEY en el archivo .env o en los secretos de Streamlit.")
        st.stop()
    # timeout de 30 min por petición: evita que la app quede colgada
    # indefinidamente y da margen para transcribir audios largos
    return genai.Client(api_key=API_KEY, http_options={"timeout": 1_800_000})
