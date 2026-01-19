from flask import Blueprint, send_file, g
from app.models import Sale, SaleItem, db
import io
from openpyxl import Workbook
from datetime import datetime

bp = Blueprint('reports', __name__, url_prefix='/reports')

@bp.route('/sales/excel')
def export_sales_excel():
    tenant_id = g.current_tenant.id if g.current_tenant else None
    
    # Query sales for current tenant
    sales = Sale.query.filter_by(tenant_id=tenant_id).order_by(Sale.date_created.desc()).all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Ventas"
    
    # Headers
    headers = ['ID', 'Fecha', 'Cliente', 'Estado', 'Items', 'Total', 'Método Pago']
    ws.append(headers)
    
    for sale in sales:
        # Calculate total and format items string
        items_str = []
        total = 0
        for item in sale.items:
            subtotal = item.quantity * item.unit_price
            total += subtotal
            items_str.append(f"{item.quantity}x {item.product.name}")
            
        ws.append([
            sale.id,
            sale.date_created.strftime('%Y-%m-%d %H:%M'),
            sale.customer_name,
            sale.status,
            ", ".join(items_str),
            total,
            sale.payment_method
        ])
        
    # Auto-adjust column widths (approximation)
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter # Get the column name
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
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
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
