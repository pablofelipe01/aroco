"""CacaoQ — Componente sidebar con métricas rápidas y navegación."""

import streamlit as st
from db.models import get_latest_market_price, get_latest_trm, get_latest_balance
from data.fx import get_usdcop_spot
from engine.risk import compute_risk


def render_sidebar() -> str:
    """Renderiza el sidebar y retorna la página seleccionada."""
    with st.sidebar:
        st.title("CacaoQ")
        st.caption("Gestión de Riesgo — AROCO SAS")

        st.divider()

        # --- Métricas rápidas ---
        market = get_latest_market_price("CC=F")
        trm_data = get_latest_trm()
        spot = get_usdcop_spot()
        balance = get_latest_balance()

        if market:
            st.metric("Cacao ICE NY", f"USD {market['close_price']:,.0f}/ton")

        if spot:
            delta_vs_trm = None
            if trm_data:
                delta_vs_trm = spot["rate"] - trm_data["trm"]
            st.metric(
                "USD/COP Spot",
                f"${spot['rate']:,.2f}",
                delta=f"{delta_vs_trm:+,.2f} vs TRM" if delta_vs_trm else None,
                delta_color="inverse",
            )
        elif trm_data:
            st.metric("TRM", f"COP {trm_data['trm']:,.2f}")

        if balance:
            nlv = balance.get("net_liquidating_value", 0)
            prior = balance.get("prior_net_liquidating_value", 0)
            delta = nlv - prior if prior else None
            st.metric(
                "Net Liq Value",
                f"USD {nlv:,.2f}",
                delta=f"USD {delta:,.2f}" if delta else None,
            )
            st.metric("Excess Equity", f"USD {balance.get('excess_equity', 0):,.2f}")

        # Cobertura
        try:
            risk = compute_risk()
            coverage = risk["hedge"]["coverage_pct"]
            total = risk["physical"]["total_tonnes"]
            if total > 0:
                st.metric("Cobertura", f"{coverage:.0f}%")
                st.progress(min(coverage / 100, 1.0))
        except Exception:
            pass

        st.divider()

        # --- Navegación ---
        page = st.radio(
            "Navegación",
            ["Chat", "Inventario", "Statements", "Configuración"],
            label_visibility="collapsed",
        )

        st.divider()

        # --- Actualizar datos ---
        if st.button("Actualizar Datos de Mercado", use_container_width=True):
            with st.spinner("Actualizando..."):
                try:
                    from data.fetcher import refresh_market_data
                    result = refresh_market_data()
                    if result["cacao"]:
                        st.success(f"Cacao: USD {result['cacao']['close']:,.0f}")
                    if result.get("usdcop_spot"):
                        st.success(f"USD/COP: ${result['usdcop_spot']['rate']:,.2f}")
                    elif result["trm"]:
                        st.success(f"TRM: {result['trm']['trm']:,.2f}")
                    if not result["cacao"] and not result["trm"]:
                        st.warning("No se pudieron obtener datos")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        return page
