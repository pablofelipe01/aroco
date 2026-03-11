"""CacaoQ — App principal Streamlit."""

import sys
from pathlib import Path

# Asegurar que el directorio del proyecto está en el path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from config import APP_TITLE, APP_ICON, APP_LAYOUT, ANTHROPIC_API_KEY, DB_PATH
from db.database import init_db
from db.models import get_all_processed_statements, get_all_inventory, get_latest_market_price
from data.fetcher import refresh_market_data
from ui.sidebar import render_sidebar
from ui.chat import render_chat
from ui.inventory import render_inventory
from ui.statement_view import render_statement_view

# --- Configuración de página ---
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=APP_LAYOUT,
    initial_sidebar_state="expanded",
)

# --- Inicializar base de datos ---
init_db()

# --- Auto-refresh de datos de mercado (una vez por sesión) ---
if "market_refreshed" not in st.session_state:
    with st.spinner("Cargando datos de mercado..."):
        try:
            refresh_market_data()
        except Exception:
            pass
    st.session_state.market_refreshed = True

# --- Sidebar + navegación ---
page = render_sidebar()

# --- Páginas ---
if page == "Chat":
    render_chat()

elif page == "Inventario":
    render_inventory()

elif page == "Statements":
    render_statement_view()

elif page == "Configuración":
    st.header("Configuración")

    st.subheader("API Key de Anthropic")
    if ANTHROPIC_API_KEY:
        masked = ANTHROPIC_API_KEY[:10] + "..." + ANTHROPIC_API_KEY[-4:]
        st.success(f"API Key configurada: {masked}")
    else:
        st.warning(
            "No se encontró ANTHROPIC_API_KEY. "
            "Crea un archivo `.env` en la carpeta cacaoq/ con:\n\n"
            "`ANTHROPIC_API_KEY=sk-ant-...`"
        )

    st.divider()

    st.subheader("Base de Datos")
    st.write(f"Ruta: `{DB_PATH}`")
    if DB_PATH.exists():
        size_kb = DB_PATH.stat().st_size / 1024
        st.write(f"Tamaño: {size_kb:.1f} KB")

    st.divider()

    st.subheader("Statements Procesados")
    processed = get_all_processed_statements()
    st.write(f"Total procesados: {len(processed)}")

    st.divider()

    st.subheader("Inventario")
    inventory = get_all_inventory()
    st.write(f"Total registros: {len(inventory)}")
