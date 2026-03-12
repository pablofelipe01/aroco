"""CacaoQ — UI de inventario físico."""

import streamlit as st
import pandas as pd
from datetime import date, datetime
from config import REGIONES_CACAO, ESTADOS_INVENTARIO, PROVEEDORES_DEFAULT
from db.models import (
    insert_inventory, get_all_inventory, get_active_inventory,
    update_inventory, delete_inventory,
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
    st.subheader("Inventario")
    all_inv = get_all_inventory()
    if not all_inv:
        st.info("No hay registros de inventario. Registra tu primera compra arriba.")
        return

    # Mostrar cada registro como card editable
    for item in all_inv:
        item_id = item["id"]
        with st.expander(
            f"**#{item_id}** | {item['date']} | {item['tonnes']} ton | "
            f"{item['status'].upper()} | COP {item['price_cop_kg']:,.0f}/kg"
            f"{' — ' + item['supplier'] if item.get('supplier') else ''}"
        ):
            with st.form(f"edit_{item_id}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    edit_date = st.date_input(
                        "Fecha",
                        value=datetime.strptime(item["date"], "%Y-%m-%d").date(),
                        key=f"date_{item_id}",
                    )
                    edit_tonnes = st.number_input(
                        "Toneladas", min_value=0.1, max_value=1000.0,
                        value=float(item["tonnes"]), step=0.5,
                        key=f"ton_{item_id}",
                    )
                with col2:
                    edit_price = st.number_input(
                        "Precio (COP/kg)", min_value=1000, max_value=100000,
                        value=int(item["price_cop_kg"]), step=500,
                        key=f"price_{item_id}",
                    )
                    current_supplier = item.get("supplier") or ""
                    supplier_options = [""] + PROVEEDORES_DEFAULT
                    supplier_idx = supplier_options.index(current_supplier) if current_supplier in supplier_options else 0
                    edit_supplier = st.selectbox(
                        "Proveedor", supplier_options,
                        index=supplier_idx, key=f"sup_{item_id}",
                    )
                with col3:
                    current_region = item.get("region") or ""
                    region_options = [""] + REGIONES_CACAO
                    region_idx = region_options.index(current_region) if current_region in region_options else 0
                    edit_region = st.selectbox(
                        "Región", region_options,
                        index=region_idx, key=f"reg_{item_id}",
                    )
                    status_idx = ESTADOS_INVENTARIO.index(item["status"]) if item["status"] in ESTADOS_INVENTARIO else 0
                    edit_status = st.selectbox(
                        "Estado", ESTADOS_INVENTARIO,
                        index=status_idx, key=f"st_{item_id}",
                    )

                ship_val = None
                if item.get("shipment_date"):
                    try:
                        ship_val = datetime.strptime(item["shipment_date"], "%Y-%m-%d").date()
                    except ValueError:
                        pass
                edit_shipment = st.date_input(
                    "Fecha embarque", value=ship_val, key=f"ship_{item_id}",
                )
                edit_notes = st.text_area(
                    "Notas", value=item.get("notes") or "",
                    max_chars=500, key=f"notes_{item_id}",
                )

                btn_col1, btn_col2 = st.columns([3, 1])
                with btn_col1:
                    save = st.form_submit_button("Guardar cambios", type="primary")
                with btn_col2:
                    remove = st.form_submit_button("Eliminar", type="secondary")

                if save:
                    update_inventory(
                        inventory_id=item_id,
                        date=str(edit_date),
                        tonnes=edit_tonnes,
                        price_cop_kg=edit_price,
                        supplier=edit_supplier or None,
                        region=edit_region or None,
                        status=edit_status,
                        shipment_date=str(edit_shipment) if edit_shipment else None,
                        notes=edit_notes or None,
                    )
                    st.success(f"Registro #{item_id} actualizado")
                    st.rerun()

                if remove:
                    delete_inventory(item_id)
                    st.warning(f"Registro #{item_id} eliminado")
                    st.rerun()
