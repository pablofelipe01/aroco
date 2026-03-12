"""CacaoQ — Inicialización y conexión a SQLite."""

import sqlite3
from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Retorna conexión a la base de datos con row_factory."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Crea todas las tablas si no existen."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    -- Inventario físico de cacao
    CREATE TABLE IF NOT EXISTS physical_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        tonnes REAL NOT NULL,
        price_cop_kg REAL NOT NULL,
        supplier TEXT,
        region TEXT,
        status TEXT NOT NULL DEFAULT 'bodega',
        shipment_date TEXT,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );

    -- Posiciones del broker (parseadas del PDF)
    CREATE TABLE IF NOT EXISTS broker_positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        statement_date TEXT NOT NULL,
        account TEXT NOT NULL,
        trade_date TEXT,
        card TEXT,
        long_qty INTEGER DEFAULT 0,
        short_qty INTEGER DEFAULT 0,
        option_type TEXT,           -- CALL, PUT, or NULL for futures
        contract_month TEXT,        -- e.g. 'MAY 26'
        exchange TEXT DEFAULT 'ICE COCOA',
        strike REAL,
        settle_price REAL,
        market_value REAL,
        dr_cr TEXT,                 -- DR or CR
        created_at TEXT DEFAULT (datetime('now'))
    );

    -- Balance de la cuenta del broker
    CREATE TABLE IF NOT EXISTS account_balance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        statement_date TEXT NOT NULL,
        account TEXT NOT NULL,
        beginning_balance REAL,
        ending_balance REAL,
        total_equity REAL,
        long_option_value REAL,
        short_option_value REAL,
        net_option_value REAL,
        net_liquidating_value REAL,
        prior_net_liquidating_value REAL,
        market_variance REAL,
        initial_margin REAL,
        maintenance_margin REAL,
        excess_equity REAL,
        created_at TEXT DEFAULT (datetime('now'))
    );

    -- Statements procesados (evitar duplicados)
    CREATE TABLE IF NOT EXISTS processed_statements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        statement_date TEXT NOT NULL,
        account TEXT NOT NULL,
        file_hash TEXT UNIQUE,
        num_positions INTEGER,
        processed_at TEXT DEFAULT (datetime('now'))
    );

    -- Datos de mercado (precios cacao)
    CREATE TABLE IF NOT EXISTS market_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        ticker TEXT NOT NULL,
        close_price REAL,
        open_price REAL,
        high REAL,
        low REAL,
        volume REAL,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(date, ticker)
    );

    -- Datos TRM (tasa de cambio USD/COP)
    CREATE TABLE IF NOT EXISTS trm_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL UNIQUE,
        trm REAL NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    );

    -- Historial de chat con Claude
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    );

    -- Snapshots de riesgo (foto diaria del estado)
    CREATE TABLE IF NOT EXISTS risk_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        total_physical_tonnes REAL,
        covered_tonnes REAL,
        coverage_pct REAL,
        cacao_price_usd REAL,
        trm REAL,
        net_liquidating_value REAL,
        unrealized_pnl_physical REAL,
        unrealized_pnl_hedge REAL,
        collar_floor REAL,
        collar_cap REAL,
        created_at TEXT DEFAULT (datetime('now'))
    );

    -- Ventas locales de cacao físico
    CREATE TABLE IF NOT EXISTS local_sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        inventory_id INTEGER,
        tonnes REAL NOT NULL,
        price_cop_kg REAL NOT NULL,
        buyer TEXT,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (inventory_id) REFERENCES physical_inventory(id)
    );

    -- Tablero de opciones diario del broker
    CREATE TABLE IF NOT EXISTS options_board (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        contract_month TEXT NOT NULL,
        underlying_price REAL,
        dte INTEGER,
        expiration TEXT,
        volatility_calls REAL,
        volatility_puts REAL,
        interest_rate REAL,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(date, contract_month)
    );

    CREATE TABLE IF NOT EXISTS options_chain (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        board_id INTEGER NOT NULL,
        strike REAL NOT NULL,
        call_premium REAL,
        call_delta REAL,
        put_premium REAL,
        put_delta REAL,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (board_id) REFERENCES options_board(id),
        UNIQUE(board_id, strike)
    );

    -- P&L del broker
    CREATE TABLE IF NOT EXISTS broker_pnl (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        statement_date TEXT NOT NULL,
        account TEXT NOT NULL,
        realized_pnl_mtd REAL,
        realized_pnl_ytd REAL,
        currency TEXT DEFAULT 'USD',
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Base de datos creada en {DB_PATH}")
