# ==============================================================
# ALERTA POR CORREO (actualmente desactivada en app.py)
# ==============================================================

import os
import smtplib
from email.mime.text import MIMEText

import streamlit as st


def enviar_alerta_correo(mensaje):
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    destino = os.getenv("DESTINO_ALERTA")

    if not all([user, password, destino]):
        st.warning("⚠️ No se configuró correctamente el envío de correo (revisa .env o secretos).")
        return

    msg = MIMEText(mensaje)
    msg["Subject"] = "⚠️ Alerta: Límite de ACTAS alcanzado"
    msg["From"] = user
    msg["To"] = destino

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(user, password)
            server.send_message(msg)
        st.info("📨 Se envió una alerta por correo.")
    except Exception as e:
        st.error(f"Error al enviar correo: {e}")
