"""CacaoQ — Configuración global y constantes."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Rutas ---
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data_db" / "cacaoq.db"
STATEMENTS_DIR = BASE_DIR / "statements"

# --- API Keys ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# --- Modelo Claude ---
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_MAX_TOKENS = 4096

# --- Cacao / ICE NY ---
CACAO_TICKER = "CC=F"  # Yahoo Finance ticker para cacao ICE NY
CACAO_CONTRACT_SIZE = 10  # Toneladas métricas por contrato
CACAO_TICK_SIZE = 1.0  # USD por tonelada
CACAO_TICK_VALUE = 10.0  # USD por tick por contrato

# --- CFTC (Commitments of Traders) ---
CFTC_CACAO_CODE = "073732"

# --- TRM (Tasa Representativa del Mercado — Colombia) ---
TRM_API_URL = "https://www.datos.gov.co/resource/32sa-8pi3.json"

# --- Regiones cacaoteras Colombia ---
REGIONES_CACAO = [
    "Santander",
    "Arauca",
    "Antioquia",
    "Huila",
    "Tolima",
    "Norte de Santander",
    "Nariño",
    "Meta",
    "Cesar",
    "Bolívar",
]

# --- Estados del inventario ---
ESTADOS_INVENTARIO = [
    "bodega",
    "tránsito",
    "puerto",
    "embarcado",
    "entregado",
]

# --- Proveedores (ejemplo, se pueden agregar desde la UI) ---
PROVEEDORES_DEFAULT = [
    "Cooperativa X",
    "Asociación Y",
    "Productor directo",
]

# --- Márgenes StoneX (estimados, actualizar según broker) ---
MARGIN_PER_CONTRACT = 1_950  # USD margen inicial por contrato (opción)
MARGIN_MAINTENANCE = 1_950   # USD margen de mantenimiento

# --- Streamlit ---
APP_TITLE = "CacaoQ — Gestión de Riesgo Cacao"
APP_ICON = "🫘"
APP_LAYOUT = "wide"
