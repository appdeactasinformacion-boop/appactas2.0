# ==============================================================
# CONTADOR GLOBAL DE ACTAS (JSONBin)
# ==============================================================

import requests
import streamlit as st

from config import JSONBIN_API_KEY, JSONBIN_BIN_ID

BASE_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"
HEADERS = {
    "X-Master-Key": JSONBIN_API_KEY or "",
    "Content-Type": "application/json"
}


def obtener_contador():
    try:
        response = requests.get(f"{BASE_URL}/latest", headers=HEADERS)
        response.raise_for_status()
        record = response.json().get("record", {})
        return record.get("contador_actas", 0)
    except Exception as e:
        st.warning(f"⚠️ No se pudo obtener el contador global: {e}")
        return 0


def actualizar_contador(nuevo_valor):
    try:
        response = requests.put(BASE_URL, headers=HEADERS, json={"contador_actas": nuevo_valor})
        response.raise_for_status()
    except Exception as e:
        st.error(f"⚠️ No se pudo guardar el contador en JSONBin: {e}")
