from flask import Blueprint, send_file, g
from app.models import Sale, SaleItem, db, Product, Wastage, InboundOrder
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime

bp = Blueprint("reports", __name__, url_prefix="/reports")


@bp.route("/sales/excel")
def export_sales_excel():
    tenant_id = g.current_tenant.id if g.current_tenant else None

    # Query sales for current tenant
    sales = (
        Sale.query.filter_by(tenant_id=tenant_id)
        .order_by(Sale.date_created.desc())
        .all()
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Ventas"

    # Headers con estilo
    headers = ["ID", "Fecha", "Cliente", "Estado", "Items", "Total", "Método Pago"]
    ws.append(headers)

    # Estilo para headers
    header_fill = PatternFill(
        start_color="4F81BD", end_color="4F81BD", fill_type="solid"
    )
    header_font = Font(bold=True, color="FFFFFF")

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for sale in sales:
        # Calculate total and format items string
        items_str = []
        total = 0
        for item in sale.items:
            subtotal = item.quantity * item.unit_price
            total += subtotal
            items_str.append(f"{item.quantity}x {item.product.name}")

        ws.append(
            [
                sale.id,
                sale.date_created.strftime("%Y-%m-%d %H:%M"),
                sale.customer_name,
                sale.status,
                ", ".join(items_str),
                total,
                sale.payment_method,
            ]
        )

    # Auto-adjust column widths (approximation)
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter  # Get the column name
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = max_length + 2
        ws.column_dimensions[column].width = adjusted_width

    # Save to buffer
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"ventas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@bp.route("/warehouse/wastage/excel")
def export_wastage_excel():
    """Exportar historial de mermas a Excel"""
    tenant_id = g.current_tenant.id if g.current_tenant else None

    wastages = (
        Wastage.query.filter_by(tenant_id=tenant_id)
        .order_by(Wastage.date_created.desc())
        .all()
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Mermas"

    # Headers
    headers = ["ID", "Fecha", "Producto", "SKU", "Cantidad", "Razón", "Notas"]
    ws.append(headers)

    # Estilo para headers
    header_fill = PatternFill(
        start_color="E74C3C", end_color="E74C3C", fill_type="solid"
    )
    header_font = Font(bold=True, color="FFFFFF")

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for wastage in wastages:
        ws.append(
            [
                wastage.id,
                wastage.date_created.strftime("%Y-%m-%d %H:%M"),
                wastage.product.name,
                wastage.product.sku,
                wastage.quantity,
                wastage.reason,
                wastage.notes or "-",
            ]
        )

    # Auto-adjust columns
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(50, max_length + 2)  # Max 50
        ws.column_dimensions[column].width = adjusted_width

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"mermas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@bp.route("/warehouse/inventory/excel")
def export_inventory_excel():
    """Exportar inventario completo a Excel"""
    tenant_id = g.current_tenant.id if g.current_tenant else None

    products = Product.query.filter_by(tenant_id=tenant_id).order_by(Product.name).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Inventario"

    # Headers
    headers = [
        "SKU",
        "Nombre",
        "Categoría",
        "Precio Base",
        "Stock Total",
        "Stock Crítico",
        "Estado",
        "Vencimiento",
    ]
    ws.append(headers)

    # Estilo para headers
    header_fill = PatternFill(
        start_color="27AE60", end_color="27AE60", fill_type="solid"
    )
    header_font = Font(bold=True, color="FFFFFF")

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for product in products:
        stock_status = (
            "CRÍTICO" if product.total_stock <= product.critical_stock else "OK"
        )
        expiry = (
            product.expiry_date.strftime("%Y-%m-%d") if product.expiry_date else "-"
        )

        row = ws.append(
            [
                product.sku,
                product.name,
                product.category or "-",
                product.base_price,
                product.total_stock,
                product.critical_stock,
                stock_status,
                expiry,
            ]
        )

        # Color para stock crítico
        if product.total_stock <= product.critical_stock:
            for cell in ws[ws.max_row]:
                cell.fill = PatternFill(
                    start_color="FFCCCC", end_color="FFCCCC", fill_type="solid"
                )

    # Auto-adjust columns
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(40, max_length + 2)
        ws.column_dimensions[column].width = adjusted_width

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"inventario_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@bp.route("/warehouse/orders/excel")
def export_orders_excel():
    """Exportar pedidos a proveedores a Excel"""
    tenant_id = g.current_tenant.id if g.current_tenant else None

    orders = (
        InboundOrder.query.filter_by(tenant_id=tenant_id)
        .order_by(InboundOrder.date_received.desc())
        .all()
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Pedidos"

    # Headers
    headers = [
        "ID",
        "Proveedor",
        "N° Factura",
        "Estado",
        "Total",
        "Fecha Creación",
        "Fecha Recepción",
        "Notas",
    ]
    ws.append(headers)

    # Estilo para headers
    header_fill = PatternFill(
        start_color="3498DB", end_color="3498DB", fill_type="solid"
    )
    header_font = Font(bold=True, color="FFFFFF")

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for order in orders:
        ws.append(
            [
                order.id,
                order.supplier,
                order.invoice_number,
                order.status,
                order.total,
                order.created_at.strftime("%Y-%m-%d %H:%M")
                if order.created_at
                else "-",
                order.date_received.strftime("%Y-%m-%d %H:%M")
                if order.date_received
                else "-",
                order.notes or "-",
            ]
        )

    # Auto-adjust columns
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(40, max_length + 2)
        ws.column_dimensions[column].width = adjusted_width

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"pedidos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
