# ==============================================================
# ESTILOS Y ELEMENTOS VISUALES (CSS, encabezado, advertencia, pie)
# ==============================================================

import base64
import os

import streamlit as st

CSS = """
    <style>
        .app-header {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: center;
            text-align: center;
            gap: 12px;
            margin-bottom: 25px;
            background-color: #ffffff;
            padding: 15px 20px;
            border-radius: 15px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }
        .app-header img {
            height: 80px;
            max-width: 100%;
            width: auto;
            object-fit: contain;
            border-radius: 10px;
        }
        .app-header h1 {
            /* se adapta al ancho de la pantalla: min 1.3em, max 2.2em */
            font-size: clamp(1.3em, 5vw, 2.2em);
            font-weight: 700;
            color: #1E3A8A;
            margin: 0;
        }
        /* En celulares: logo arriba y título debajo, más compactos */
        @media (max-width: 640px) {
            .app-header {
                flex-direction: column;
                gap: 8px;
                padding: 12px 14px;
            }
            .app-header img {
                height: 54px;
            }
        }
        .section-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #1E40AF;
            margin-top: 25px;
        }
        .footer {
            text-align: center;
            color: #6B7280;
            font-size: 0.9em;
            margin-top: 50px;
            padding-top: 10px;
            border-top: 1px solid #E5E7EB;
        }
        .stButton button {
            background-color: #2563EB;
            color: white;
            border-radius: 8px;
            font-weight: bold;
            padding: 8px 20px;
            transition: all 0.3s ease;
        }
        .stButton button:hover {
            background-color: #1E40AF;
            transform: scale(1.02);
        }
    </style>
"""


def aplicar_css():
    st.markdown(CSS, unsafe_allow_html=True)


def mostrar_encabezado(logo_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo", "logo.png")):
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode("utf-8")
        st.markdown(
            f"""
            <div class="app-header">
                <img src="data:image/png;base64,{logo_base64}" alt="Logo">
                <h1>Generador de Actas</h1>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.title("📝 Generador de Actas")


def mostrar_advertencia():
    st.markdown("""
    <div style="
        background-color: #fff0f0;
        border: 2px solid #ff9999;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        color: #660000;
        font-size: 16px;
        margin-top: 25px;
    ">
    🚨 <b>Advertencia:</b> Esta herramienta es susceptible de mejoras. Si identifica alguna inconsistencia en el diligenciamiento del acta, por favor notifíquelo al área responsable de su diseño.
    Se recomienda validar cuidadosamente toda la información generada antes de su uso, distribución o almacenamiento.<br>
    </div>
    """, unsafe_allow_html=True)


def mostrar_footer():
    st.markdown(
        "<div class='footer'>© 2025 Generador de Actas • Streamlit + Gemini + JSONBin</div>",
        unsafe_allow_html=True
    )
