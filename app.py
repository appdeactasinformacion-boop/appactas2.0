# ==============================================================
# GENERADOR DE ACTAS - INTERFAZ PRINCIPAL
# Punto de entrada: streamlit run app.py
# ==============================================================

import os
import time

import streamlit as st

import estilos
from config import TEMPLATES_DIR, configurar_gemini
from contador import actualizar_contador, obtener_contador
from documentos import create_word_document, get_fields_from_template
from claude_utils import configurar_claude
from extractor import extraer_info
from grabadora import grabadora_audio
from transcripcion import transcribir_audio
# from correo import enviar_alerta_correo   # <- descomentar para activar alertas
# from config import LIMITE_CONTADOR

st.set_page_config(page_title="Generador de Actas", page_icon="📝", layout="wide")

cliente = configurar_gemini()          # transcribe el audio (y respaldo del acta)
cliente_claude = configurar_claude()   # genera el acta; None si no hay API key

estilos.aplicar_css()
estilos.mostrar_encabezado()

contador_actual = obtener_contador()
st.info(f"🧮 Contador global de actas: **{contador_actual}**")

# if contador_actual >= LIMITE_CONTADOR:
#     st.warning(f"⚠️ Se alcanzó el límite de {LIMITE_CONTADOR} actas. Es momento de reiniciar el contador.")
#     enviar_alerta_correo(f"Se ha alcanzado el límite de {contador_actual} actas. Debes reiniciar el API en la app de actas.")

if "transcripcion_area" not in st.session_state:
    st.session_state["transcripcion_area"] = ""
if "clear_text" not in st.session_state:
    st.session_state["clear_text"] = False

if not os.path.exists(TEMPLATES_DIR):
    st.error(f"No se encontró el directorio de plantillas: {TEMPLATES_DIR}")
    st.stop()

template_files = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".docx")]
if not template_files:
    st.error("No hay plantillas disponibles en la carpeta 'templates'.")
    st.stop()

template_docx = st.selectbox("📂 Selecciona una plantilla", template_files)
template_path = os.path.join(TEMPLATES_DIR, template_docx)
template_fields = get_fields_from_template(template_path)

# ==============================================================
# PASO 1: AUDIO DE LA REUNIÓN (subir archivo o grabar)
# ==============================================================

st.markdown("<p class='section-title'>1️⃣ 🎙️ Audio de la reunión <i>(opcional: si ya tienes la transcripción, pásala directo al paso 2)</i></p>", unsafe_allow_html=True)

audio_bytes = None
audio_extension = ".wav"

tab_subir, tab_grabar = st.tabs(["📁 Subir archivo", "🎤 Grabar audio"])

with tab_subir:
    archivo_audio = st.file_uploader(
        "Arrastra o busca el archivo de audio",
        type=["mp3", "wav", "m4a", "ogg", "aac", "flac", "opus", "webm"]
    )
    if archivo_audio is not None:
        audio_bytes = archivo_audio.getvalue()
        audio_extension = os.path.splitext(archivo_audio.name)[1].lower() or ".wav"
        st.audio(audio_bytes)

with tab_grabar:
    st.caption(
        "⚠️ La grabación vive en esta pestaña del navegador: **no recargues la página, no cierres la pestaña "
        "y evita que el equipo se suspenda** mientras grabas, o se perderá. "
        "Graba en formato comprimido, así que soporta reuniones de varias horas."
    )
    grabacion_bytes, duracion_seg = grabadora_audio()
    if grabacion_bytes is not None:
        print(f"[GRABADORA] Audio recibido del navegador: {len(grabacion_bytes) / 1048576:.1f} MB, {duracion_seg} s", flush=True)
        st.audio(grabacion_bytes, format="audio/webm")
        if audio_bytes is None:
            audio_bytes = grabacion_bytes
            audio_extension = ".webm"
        else:
            st.info("ℹ️ Hay un archivo subido y una grabación: se usará el archivo subido. Quítalo si prefieres usar la grabación.")

if audio_bytes is not None:
    if st.button("🎧 Transcribir audio"):
        texto_transcrito = transcribir_audio(cliente, audio_bytes, audio_extension)
        if texto_transcrito:
            st.session_state["transcripcion_area"] = texto_transcrito
            st.success("✅ Audio transcrito correctamente. El texto se colocó en el paso 2 — revísalo y edítalo si es necesario.")

# ==============================================================
# PASO 2: TRANSCRIPCIÓN
# ==============================================================

st.markdown("<p class='section-title'>2️⃣ 🗒️ Transcripción de la reunión</p>", unsafe_allow_html=True)

transcripcion = st.text_area("Pega la transcripción o revisa la generada desde el audio", height=300, key="transcripcion_area")

col1, col2 = st.columns(2)
with col1:
    elaborada_por = st.text_input("👤 Acta elaborada por")
with col2:
    cargo = st.text_input("💼 Cargo")

col_gen, col_clear = st.columns([3, 1])
with col_gen:
    generar = st.button("📝 Generar Acta")
with col_clear:
    if st.button("🧹 Limpiar texto"):
        st.session_state["clear_text"] = True
        st.rerun()

if generar:
    if not transcripcion.strip():
        st.warning("⚠️ Debes ingresar la transcripción antes de generar.")
        st.stop()

    motor_acta = "Claude" if cliente_claude is not None else "Gemini"
    st.info(f"Generando el acta con {motor_acta}... Esto puede tardar unos segundos ⏳")
    progress_bar = st.progress(0)

    extracted_data = extraer_info(cliente, cliente_claude, transcripcion, template_fields)
    for i in range(1, 101):
        time.sleep(0.01)
        progress_bar.progress(i)

    if extracted_data:
        st.success("✅ Datos extraídos correctamente. Generando documento Word...")
        output_path = create_word_document(template_path, extracted_data, elaborada_por, cargo)

        if output_path:
            nuevo_valor = contador_actual + 1
            actualizar_contador(nuevo_valor)
            st.success(f"🎉 Acta número {nuevo_valor} generada correctamente.")

            # if nuevo_valor >= LIMITE_CONTADOR:
            #     enviar_alerta_correo(f"Se ha alcanzado el límite de {nuevo_valor} actas. Debes reiniciar el API en la app.")

            with open(output_path, "rb") as f:
                st.download_button(
                    "📥 Descargar Acta Generada",
                    data=f.read(),
                    file_name=f"acta_{nuevo_valor}.docx"
                )
    else:
        st.error("No se pudo extraer información del texto.")

estilos.mostrar_advertencia()
estilos.mostrar_footer()
