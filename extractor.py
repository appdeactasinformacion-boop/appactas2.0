# ==============================================================
# EXTRACCIÓN DE INFORMACIÓN PARA EL ACTA
# Usa Claude si hay ANTHROPIC_API_KEY configurada (mejor redacción);
# si no, usa Gemini como hasta ahora.
# ==============================================================

import json
import re

import streamlit as st

from claude_utils import generar_texto_claude
from gemini_utils import generar_con_reintentos


def _construir_prompt(text_to_process, fields):
    return f"""
    Analiza el siguiente texto y extrae la información para los siguientes campos.
    Devuelve SOLO un JSON válido. Si no hay información, usa "N/A" o [] según corresponda.

    Campos esperados:
    {', '.join(fields)}

    Instrucciones especificas para campos ESPECIFICOS:
    -   {{FECHA}}: extrae la fecha de la reunión en formato DD/MM/AAAA.
    -	{{HORA_INICIO}}: extrae la hora de inicio de la reunión en formato H:mm.
    -	{{HORA_FIN}}: extrae la hora de fin de la reunión en formato H:mm.
    -	{{CIUDAD}}: extrae la ciudad donde se llevó a cabo la reunión o evento.
    -	{{SEDE}}: extrae la sede (oficina, edificio, empresa, etc.) donde se realizó la reunión.
    -   {{LUGAR_REUNION}}: extrae el lugar donde se realizo la reunion.
    -	{{OBJETIVO_DE_LA_REUNION}}: extrae el objetivo de la reunión explicado de forma clara y completa.
    - {{TEMAS_TRATADOS}}: Esta debe ser una LISTA de objetos JSON. Cada objeto representa un tema tratado en la reunión.
    - Cada objeto debe tener las claves:
        - tema: extrae el tema tratado.
        - desarrollo: extrae de manera detallada como se desarrollo el tema a tratar.
    - {{COMPROMISOS_R}}: Esta debe ser una LISTA de objetos JSON. Cada objeto representa un compromiso de la reunion.
    - Cada objeto debe tener las claves:
        - compromiso: extrae el compromiso a realizar.
        - responsable: extrae el nombre de la persona encargada de ejecutar el compromiso.
        - fechaejecucion: extrae la fecha en la cual se va a ejecutar el compromiso.
    -    {{TEMA_PROXIMA_REUNION}}: extrae el tema a tratar en la proxima reunion.
    -    {{FECHA_PROXIMA_REUNION}}: extrae la fecha en la cual se va a realizar la proxima reunion.
    - {{ASISTENTES_REUNION}}: Esta debe ser una LISTA de objetos JSON. Cada objeto representa una perona que asistio a la reunion.
    - Cada objeto debe tener las claves:
        - nombreasistentereu: extrar el nombre completo de la personas asitente a la reunion.
        - cargoasistentereunion: extrea el cargo de la persona asistente a la reunion.
    - {{TEMAS_TRATADOS_N}}: Esta debe ser una LISTA de objetos JSON. Cada objeto representa un tema tratado en la reunión.
    - Cada objeto debe tener las claves:
        - tema: extrae el tema tratado, haz que los temas relacionados los en listas en uno solo.
        - responsablet: extrae el nombre completo de la persona encargada del tema a tratar.
    - {{DESARROLLO_DE_LA_REUNION_Y_CONCLUSIONES}}: A partir de los temas extraídos en TEMAS_TRATADOS_2, redacta un texto en el que se describa detalladamente cómo se desarrolló la reunión en relación con cada tema tratado.
       - Cada tema tratado debe colocarse como subtítulo en negrilla, seguido de su respectivo desarrollo en un párrafo aparte.
       - Finalmente, incluye una conclusión general sobre los puntos abordados en la reunión, manteniendo una estructura clara y organizada, esta no debe llevar el subtitulo.
    -    {{OBJETIVO_DE_LA_REUNION_2}}: extrae el objetivo de la reunión explicado de forma clara, precisa y que no sea extensa.
    - {{COMPROMISOS_DE_REUNION}}: Esta debe ser una LISTA de objetos JSON. Cada objeto representa un compromiso de la reunion.
    - Cada objeto debe tener las claves:
        - compromiso: extrae el compromiso a realizar.
        - responsablen: extrae el nombre de la persona encargada de ejecutar el compromiso.
        - fechac: extrae la fecha de cumplimiento del compromiso.
        - fechas: extrae la fecha en la cual se va le va a hacer seguimiento al compromiso.

        Las listas deben contener objetos con las claves indicadas:
        - ASISTENTES_REUNION: nombreasistentereu, cargoasistentereunion
        - TEMAS_TRATADOS_N: tema, responsablet
        - COMPROMISOS_DE_REUNION: compromiso, resposablen, fechac, fechas
        - TEMAS_TRATADOS: tema, desarrollo
        - COMPROMISOS_R: compromiso, responsable, fechaejecucion

    TEXTO:
    ---
    {text_to_process}
    ---
    JSON:
    """


def extraer_info(cliente_gemini, cliente_claude, text_to_process, fields):
    """Extrae los campos del acta. Con Claude si está configurado; si no, con Gemini."""
    prompt = _construir_prompt(text_to_process, fields)
    try:
        if cliente_claude is not None:
            json_text = generar_texto_claude(cliente_claude, prompt)
            if json_text is None:
                return None
        else:
            response = generar_con_reintentos(cliente_gemini, prompt)
            if response is None:
                return None
            json_text = response.text
        json_text = json_text.strip()
        if json_text.startswith("```json"):
            json_text = json_text[len("```json"):].strip()
        if json_text.endswith("```"):
            json_text = json_text[:-len("```")].strip()
        match = re.search(r'\{.*\}', json_text, re.DOTALL)
        if match:
            clean_json_text = match.group(0)
            return json.loads(clean_json_text)
        else:
            st.error("⚠️ La IA no devolvió un JSON válido.")
            st.code(json_text)
            return None
    except Exception as e:
        st.error(f"Error al generar el acta: {e}")
        return None
