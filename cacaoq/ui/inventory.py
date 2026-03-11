"""CacaoQ — UI de inventario físico."""

import streamlit as st
import pandas as pd
from datetime import date
from config import REGIONES_CACAO, ESTADOS_INVENTARIO, PROVEEDORES_DEFAULT
from db.models import (
    insert_inventory, get_all_inventory, get_active_inventory,
    update_inventory_status, delete_inventory,
)


def render_inventory():
    """Renderiza la página de inventario físico."""
    st.header("Inventario Físico de Cacao")

    # --- Métricas resumen ---
    inventory = get_active_inventory()
    if inventory:
        df = pd.DataFrame(inventory)
        by_status = df.groupby("status")["tonnes"].sum()

        cols = st.columns(5)
        total = df["tonnes"].sum()
        cols[0].metric("Total Activo", f"{total:.1f} ton")
        for i, status in enumerate(["bodega", "tránsito", "puerto", "embarcado"], 1):
            val = by_status.get(status, 0)
            if i < len(cols):
                cols[i].metric(status.capitalize(), f"{val:.1f} ton")

    st.divider()

    # --- Formulario de nueva compra ---
    with st.expander("Registrar Nueva Compra", expanded=False):
        with st.form("new_purchase", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                purchase_date = st.date_input("Fecha de compra", value=date.today())
                tonnes = st.number_input("Toneladas", min_value=0.1, max_value=1000.0,
                                         value=1.0, step=0.5)
            with col2:
                price_cop = st.number_input("Precio (COP/kg)", min_value=1000,
                                            max_value=100000, value=12000, step=500)
                supplier = st.selectbox("Proveedor", [""] + PROVEEDORES_DEFAULT)
            with col3:
                region = st.selectbox("Región", [""] + REGIONES_CACAO)
                status = st.selectbox("Estado", ESTADOS_INVENTARIO)

            shipment_date = st.date_input("Fecha estimada de embarque",
                                          value=None)
            notes = st.text_area("Notas", max_chars=500)

            submitted = st.form_submit_button("Registrar Compra", type="primary")
            if submitted:
                insert_inventory(
                    date=str(purchase_date),
                    tonnes=tonnes,
                    price_cop_kg=price_cop,
                    supplier=supplier or None,
                    region=region or None,
                    status=status,
                    shipment_date=str(shipment_date) if shipment_date else None,
                    notes=notes or None,
                )
                st.success(f"Compra registrada: {tonnes} ton a COP {price_cop:,.0f}/kg")
                st.rerun()

    st.divider()

    # --- Tabla de inventario ---
    st.subheader("Inventario Activo")
    all_inv = get_all_inventory()
    if not all_inv:
        st.info("No hay registros de inventario. Registra tu primera compra arriba.")
        return

    df = pd.DataFrame(all_inv)
    display_cols = ["id", "date", "tonnes", "price_cop_kg", "supplier",
                    "region", "status", "shipment_date", "notes"]
    display_cols = [c for c in display_cols if c in df.columns]

    # Renombrar columnas para display
    col_names = {
        "id": "ID", "date": "Fecha", "tonnes": "Toneladas",
        "price_cop_kg": "Precio COP/kg", "supplier": "Proveedor",
        "region": "Región", "status": "Estado",
        "shipment_date": "Embarque", "notes": "Notas",
    }
    st.dataframe(
        df[display_cols].rename(columns=col_names),
        use_container_width=True,
        hide_index=True,
    )

    # --- Cambiar estado ---
    st.subheader("Actualizar Estado")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        inv_id = st.number_input("ID del registro", min_value=1, step=1)
    with col2:
        new_status = st.selectbox("Nuevo estado", ESTADOS_INVENTARIO,
                                   key="update_status")
    with col3:
        st.write("")  # spacer
        st.write("")
        if st.button("Actualizar"):
            update_inventory_status(inv_id, new_status)
            st.success(f"Registro {inv_id} actualizado a '{new_status}'")
            st.rerun()

    # --- Eliminar ---
    with st.expander("Eliminar registro"):
        del_id = st.number_input("ID a eliminar", min_value=1, step=1,
                                  key="del_id")
        if st.button("Eliminar", type="secondary"):
            delete_inventory(del_id)
            st.warning(f"Registro {del_id} eliminado")
            st.rerun()
