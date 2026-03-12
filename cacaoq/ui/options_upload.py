"""CacaoQ — UI para carga y visualización del tablero de opciones."""

import streamlit as st
from datetime import date
from parser.options_board_parser import parse_options_board_image
from db.models import upsert_options_board, get_latest_options_board
import pandas as pd


def render_options_upload():
    """Renderiza la página de carga del tablero de opciones."""
    st.header("Tablero de Opciones")

    # --- Subir imagen ---
    st.subheader("Cargar tablero del día")
    uploaded = st.file_uploader(
        "Sube la captura del tablero de opciones del broker",
        type=["jpg", "jpeg", "png"],
        help="Captura de pantalla del tablero CCE (Cocoa ICE) con strikes, primas y deltas"
    )

    if uploaded:
        st.image(uploaded, caption="Tablero cargado", use_container_width=True)

        if st.button("Procesar con IA", type="primary"):
            with st.spinner("Analizando imagen con Claude Vision..."):
                try:
                    image_bytes = uploaded.getvalue()
                    mime = uploaded.type or "image/jpeg"
                    result = parse_options_board_image(image_bytes, mime)

                    if result:
                        today = date.today().isoformat()
                        board_id = upsert_options_board(
                            date=today,
                            contract_month=result["contract_month"],
                            underlying_price=result["underlying_price"],
                            dte=result["dte"],
                            expiration=result["expiration"],
                            volatility_calls=result.get("volatility_calls", 0),
                            volatility_puts=result.get("volatility_puts", 0),
                            interest_rate=result.get("interest_rate", 0),
                            strikes=result["strikes"],
                        )
                        st.success(
                            f"Tablero procesado: {result['contract_month']} | "
                            f"Underlying: USD {result['underlying_price']:,.0f} | "
                            f"{len(result['strikes'])} strikes | DTE: {result['dte']}"
                        )
                        st.rerun()
                    else:
                        st.error("No se pudo parsear la imagen")
                except Exception as e:
                    st.error(f"Error procesando imagen: {e}")

    st.divider()

    # --- Mostrar tablero actual ---
    board = get_latest_options_board()
    if board:
        st.subheader(f"Tablero vigente: {board['contract_month']} ({board['date']})")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Underlying", f"USD {board['underlying_price']:,.0f}")
        col2.metric("DTE", f"{board['dte']} días")
        col3.metric("Vol Calls", f"{board['volatility_calls']:.1f}%")
        col4.metric("Vol Puts", f"{board['volatility_puts']:.1f}%")

        # Tabla de opciones
        strikes = board["strikes"]
        if strikes:
            df = pd.DataFrame(strikes)[["strike", "call_premium", "call_delta", "put_premium", "put_delta"]]
            df.columns = ["Strike", "Call Prima", "Call Delta", "Put Prima", "Put Delta"]

            # Resaltar strikes cercanos al precio actual
            underlying = board["underlying_price"]

            st.dataframe(
                df.style.format({
                    "Strike": "{:,.0f}",
                    "Call Prima": "{:,.0f}",
                    "Call Delta": "{:.2f}",
                    "Put Prima": "{:,.0f}",
                    "Put Delta": "{:.2f}",
                }),
                use_container_width=True,
                height=500,
            )

            # Resumen rápido de opciones ATM
            atm = min(strikes, key=lambda s: abs(s["strike"] - underlying))
            st.info(
                f"**ATM (Strike {atm['strike']:,.0f})**: "
                f"Call = {atm['call_premium']:,.0f} (Δ{atm['call_delta']:.1f}) | "
                f"Put = {atm['put_premium']:,.0f} (Δ{atm['put_delta']:.1f})"
            )
    else:
        st.info("No hay tablero de opciones cargado. Sube una captura para comenzar.")
