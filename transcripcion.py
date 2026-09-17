# ==============================================================
# TRANSCRIPCIÓN DE AUDIO CON GEMINI
# ==============================================================

import os
import shutil
import subprocess
import tempfile
import time

import streamlit as st
from google.genai import types

from gemini_utils import generar_con_reintentos

PROMPT_TRANSCRIPCION = """
Transcribe fielmente y de forma completa el audio de esta reunión, en español.
Instrucciones:
- Devuelve SOLO el texto de la transcripción, sin comentarios ni encabezados adicionales.
- Transcribe ÚNICAMENTE lo que realmente se dice en el audio: NO inventes palabras,
  NO completes frases a medias, NO agregues contenido que no esté en el audio.
- Si una palabra o fragmento no se entiende con claridad, escribe [inaudible] en su
  lugar. Es preferible marcar [inaudible] a adivinar lo que se dijo.
- Los nombres propios, cifras, fechas y siglas transcríbelos exactamente como se
  pronuncian; si no estás seguro de un nombre, escríbelo seguido de (?).
- Si es posible identificar a los hablantes, indícalos como "Hablante 1:", "Hablante 2:", etc.
- No resumas ni omitas partes: transcribe todo lo que se dice.
- Corrige solo la puntuación para que el texto sea legible.
"""

# Duración de cada segmento en segundos. Transcribir por partes evita dos
# problemas con audios largos: el límite de tokens de salida del modelo
# (que corta la respuesta) y la tendencia de Gemini a resumir u omitir
# tramos cuando el audio pasa de ~30 min.
SEGUNDOS_POR_SEGMENTO = 600  # 10 minutos

# Configuración de generación: temperatura baja para máxima fidelidad y
# tope de salida alto para que no se corte un segmento largo
CONFIG_TRANSCRIPCION = types.GenerateContentConfig(temperature=0.1, max_output_tokens=65535)


def _dividir_audio(audio_bytes, extension, carpeta):
    """Convierte el audio a MP3 mono 16 kHz y lo divide en segmentos de 10 min.

    Devuelve la lista de rutas de los segmentos (ordenada). Si ffmpeg no está
    disponible o falla, devuelve una lista con el archivo original completo.
    Todo se hace en disco para no agotar la RAM con grabaciones de horas.
    """
    entrada = os.path.join(carpeta, "original" + extension)
    with open(entrada, "wb") as f:
        f.write(audio_bytes)
    try:
        patron_salida = os.path.join(carpeta, "parte_%03d.mp3")
        resultado = subprocess.run(
            [
                "ffmpeg", "-y", "-i", entrada,
                "-ac", "1", "-ar", "16000", "-b:a", "64k",
                "-f", "segment", "-segment_time", str(SEGUNDOS_POR_SEGMENTO),
                "-reset_timestamps", "1",
                patron_salida,
            ],
            capture_output=True,
            timeout=1800,
        )
        partes = sorted(
            os.path.join(carpeta, n) for n in os.listdir(carpeta) if n.startswith("parte_")
        )
        if resultado.returncode == 0 and partes:
            return partes
    except Exception:
        pass
    # Sin ffmpeg no se puede trocear: se transcribe el archivo completo de una vez
    return [entrada]


def _subir_con_reintentos(cliente, ruta, intentos=3):
    """Sube el archivo a Gemini reintentando ante fallos transitorios (SSL, red)."""
    for intento in range(intentos):
        try:
            return cliente.files.upload(file=ruta)
        except Exception:
            if intento == intentos - 1:
                raise
            time.sleep(3 * (intento + 1))  # 3s, 6s


def _transcribir_segmento(cliente, ruta, indice, total):
    """Sube un segmento a Gemini y devuelve su transcripción, o None si falla."""
    audio_file = _subir_con_reintentos(cliente, ruta)
    while audio_file.state.name == "PROCESSING":
        time.sleep(2)
        audio_file = cliente.files.get(name=audio_file.name)
    if audio_file.state.name != "ACTIVE":
        return None

    prompt = PROMPT_TRANSCRIPCION
    if total > 1:
        prompt += (
            f"\nNota: este audio es la parte {indice} de {total} de una misma reunión "
            "(fue dividida en segmentos). Transcribe TODO este segmento completo, "
            "desde el primer segundo hasta el último."
        )
    try:
        respuesta = generar_con_reintentos(cliente, [prompt, audio_file], config=CONFIG_TRANSCRIPCION)
    finally:
        try:
            cliente.files.delete(name=audio_file.name)
        except Exception:
            pass
    if respuesta is None or not getattr(respuesta, "text", None):
        return None

    # Avisar si Gemini cortó la respuesta por el límite de tokens de salida
    candidatos = getattr(respuesta, "candidates", None) or []
    if candidatos and "MAX_TOKENS" in str(getattr(candidatos[0], "finish_reason", "")):
        st.warning(
            f"⚠️ La parte {indice}/{total} pudo quedar incompleta "
            "(se alcanzó el límite de la respuesta). Revisa el final de ese tramo."
        )
    return respuesta.text.strip()


def transcribir_audio(cliente, audio_bytes, extension=".wav"):
    """Transcribe el audio con Gemini y devuelve el texto completo, o None si falla.

    El audio se divide en segmentos de 10 minutos y se transcribe parte por
    parte: así no se pierde texto en grabaciones largas.
    """
    carpeta = tempfile.mkdtemp(prefix="transcripcion_")
    try:
        with st.status("🎧 Transcribiendo audio...", expanded=True) as status:
            inicio = time.time()

            # --- Etapa 1: preparar y dividir el audio ---
            status.update(label="1/2 · 📦 Preparando y dividiendo el audio...")
            mb_original = len(audio_bytes) / (1024 * 1024)
            partes = _dividir_audio(audio_bytes, extension, carpeta)
            total = len(partes)
            if total > 1:
                st.write(f"📦 Audio de {mb_original:.1f} MB dividido en {total} partes de ~10 min")
            else:
                st.write(f"📦 Audio preparado ({mb_original:.1f} MB)")

            # --- Etapa 2: transcribir cada parte ---
            textos = []
            for i, ruta in enumerate(partes, start=1):
                status.update(label=f"2/2 · ✍️ Transcribiendo parte {i} de {total}...")
                texto = _transcribir_segmento(cliente, ruta, i, total)
                if texto is None:
                    status.update(label=f"❌ Falló la transcripción de la parte {i} de {total}", state="error")
                    st.error(f"⚠️ No se pudo transcribir la parte {i} de {total}. Intenta de nuevo.")
                    return None
                textos.append(texto)
                st.write(f"✅ Parte {i}/{total} transcrita")

            minutos, segundos = divmod(int(time.time() - inicio), 60)
            status.update(
                label=f"✅ Transcripción completada en {minutos} min {segundos} s",
                state="complete",
                expanded=False,
            )
            return "\n\n".join(textos)
    except Exception as e:
        st.error(f"Error al transcribir el audio: {e}")
        return None
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
