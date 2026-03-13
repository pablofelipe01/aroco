"""CacaoQ — Interfaz de chat con Claude."""

import uuid
import streamlit as st
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_MAX_TOKENS
from engine.context_builder import build_system_prompt, build_morning_analysis_prompt
from db.models import insert_chat_message, get_chat_history, get_all_sessions


def _get_client() -> Anthropic | None:
    """Retorna cliente Anthropic o None si no hay API key."""
    if not ANTHROPIC_API_KEY:
        return None
    return Anthropic(api_key=ANTHROPIC_API_KEY)


def _ensure_session():
    """Inicializa el session state para el chat."""
    if "chat_session_id" not in st.session_state:
        # Retomar la última sesión si existe, si no crear una nueva
        sessions = get_all_sessions()
        if sessions:
            st.session_state.chat_session_id = sessions[0]["session_id"]
        else:
            st.session_state.chat_session_id = str(uuid.uuid4())[:8]
    if "messages" not in st.session_state:
        # Cargar historial existente
        history = get_chat_history(st.session_state.chat_session_id)
        st.session_state.messages = [
            {"role": m["role"], "content": m["content"]} for m in history
        ]


def render_chat():
    """Renderiza la página de chat con Claude."""
    st.header("Chat con CacaoQ")

    client = _get_client()
    if not client:
        st.error(
            "No se encontró ANTHROPIC_API_KEY. "
            "Configúrala en el archivo .env o en la página de Configuración."
        )
        return

    _ensure_session()

    # --- Botones de acción rápida ---
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Análisis Matutino", type="primary"):
            prompt = build_morning_analysis_prompt()
            st.session_state.messages.append({"role": "user", "content": prompt})
            insert_chat_message(st.session_state.chat_session_id, "user", prompt)
            st.rerun()
    with col2:
        if st.button("Nueva Conversación"):
            st.session_state.chat_session_id = str(uuid.uuid4())[:8]
            st.session_state.messages = []
            st.rerun()
    with col3:
        sessions = get_all_sessions()
        if len(sessions) > 1:
            session_ids = [s["session_id"] for s in sessions]
            options = {f"{s['session_id']} ({s['started'][:10]}, {s['messages']} msgs)": s["session_id"] for s in sessions}
            # Solo mostrar selectbox si la sesión actual está en el historial
            current_in_history = st.session_state.chat_session_id in session_ids
            if current_in_history:
                current_idx = session_ids.index(st.session_state.chat_session_id)
                selected = st.selectbox("Historial", list(options.keys()), index=current_idx, label_visibility="collapsed")
                if options[selected] != st.session_state.chat_session_id:
                    st.session_state.chat_session_id = options[selected]
                    history = get_chat_history(options[selected])
                    st.session_state.messages = [
                        {"role": m["role"], "content": m["content"]} for m in history
                    ]
                    st.rerun()
            else:
                # Sesión nueva sin mensajes: mostrar placeholder
                st.selectbox("Historial", ["Nueva conversación"], disabled=True, label_visibility="collapsed")

    st.divider()

    # --- Historial de mensajes ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # --- Input del usuario ---
    user_input = st.chat_input("Pregunta sobre tu posición de cacao...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        insert_chat_message(st.session_state.chat_session_id, "user", user_input)

        with st.chat_message("user"):
            st.markdown(user_input)

    # --- Generar respuesta si el último mensaje es del usuario ---
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        system_prompt = build_system_prompt()

        with st.chat_message("assistant"):
            with st.spinner("Analizando..."):
                try:
                    # Preparar mensajes para la API
                    api_messages = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ]

                    response = client.messages.create(
                        model=CLAUDE_MODEL,
                        max_tokens=CLAUDE_MAX_TOKENS,
                        system=system_prompt,
                        messages=api_messages,
                        stream=True,
                    )

                    # Streaming
                    full_response = ""
                    placeholder = st.empty()
                    for event in response:
                        if event.type == "content_block_delta":
                            full_response += event.delta.text
                            placeholder.markdown(full_response + "...")
                    placeholder.markdown(full_response)

                    st.session_state.messages.append({
                        "role": "assistant", "content": full_response
                    })
                    insert_chat_message(
                        st.session_state.chat_session_id, "assistant", full_response
                    )

                except Exception as e:
                    st.error(f"Error al comunicarse con Claude: {e}")
