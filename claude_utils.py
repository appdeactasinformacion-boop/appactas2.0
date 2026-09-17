

import anthropic
import streamlit as st

from config import ANTHROPIC_API_KEY, MODELO_CLAUDE


def configurar_claude():
    """Devuelve el cliente de Claude, o None si no hay API key configurada."""
    if not ANTHROPIC_API_KEY:
        return None
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def generar_texto_claude(cliente, prompt):
    """Envía el prompt a Claude y devuelve el texto de la respuesta, o None si falla.

    El SDK reintenta automáticamente los errores transitorios (429/5xx).
    """
    try:
        respuesta = cliente.messages.create(
            model=MODELO_CLAUDE,
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(bloque.text for bloque in respuesta.content if bloque.type == "text")
    except anthropic.AuthenticationError:
        st.error("❌ La ANTHROPIC_API_KEY del archivo .env no es válida.")
    except anthropic.RateLimitError:
        st.error("❌ El servicio de Claude está recibiendo muchas peticiones. Espera un minuto e intenta de nuevo.")
    except anthropic.APIStatusError as e:
        if e.status_code >= 500:
            st.error("❌ El servicio de Claude está saturado en este momento. Intenta de nuevo en unos minutos.")
        else:
            st.error(f"❌ Error del servicio de Claude: {e.message}")
    except anthropic.APIConnectionError:
        st.error("❌ No se pudo conectar con el servicio de Claude. Revisa la conexión a internet.")
    return None
