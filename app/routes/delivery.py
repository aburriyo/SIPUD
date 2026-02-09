"""
Módulo de Hojas de Reparto
- Crear hojas de reparto asignando ventas a repartidores
- Visualizar hojas con links a mapas
- Generar PDF para impresión
"""

from flask import Blueprint, render_template, request, jsonify, g, make_response, current_app
from flask_login import login_required, current_user
from app.models import Sale, User, Tenant, utc_now
from app.extensions import db
from bson import ObjectId
from datetime import datetime
from urllib.parse import quote
import json
import logging

logger = logging.getLogger(__name__)

bp = Blueprint("delivery", __name__, url_prefix="/delivery")


# ============================================
# MODELO: Hoja de Reparto (embedded in this file for simplicity)
# ============================================
class DeliverySheet(db.Document):
    """Hoja de reparto que agrupa ventas para un repartidor"""
    name = db.StringField(max_length=100)  # Nombre descriptivo opcional
    date = db.DateField(required=True)  # Fecha de reparto
    
    # Repartidor (puede ser User del sistema o nombre libre)
    driver_user = db.ReferenceField(User)  # Si es usuario del sistema
    driver_name = db.StringField(max_length=100)  # Nombre libre si no es usuario
    driver_phone = db.StringField(max_length=20)
    
    # Ventas asignadas
    sales = db.ListField(db.ReferenceField(Sale))
    
    # Estado
    status = db.StringField(
        max_length=20, 
        default='pendiente',
        choices=['pendiente', 'en_ruta', 'completado', 'cancelado']
    )
    
    # Metadata
    notes = db.StringField(max_length=500)
    created_at = db.DateTimeField(default=utc_now)
    created_by = db.ReferenceField(User)
    tenant = db.ReferenceField(Tenant)
    
    meta = {
        'collection': 'delivery_sheets',
        'indexes': [
            'date',
            'status',
            'tenant',
            '-created_at'
        ],
        'ordering': ['-date', '-created_at']
    }
    
    @property
    def total_sales(self):
        return len(self.sales)
    
    @property
    def total_amount(self):
        total = 0
        for sale in self.sales:
            if sale:
                total += sale.total_amount
        return total
    
    @property
    def driver_display_name(self):
        if self.driver_user:
            return self.driver_user.full_name or self.driver_user.username
        return self.driver_name or "Sin asignar"


# ============================================
# VISTAS
# ============================================

@bp.route("/")
@login_required
def index():
    """Lista de hojas de reparto"""
    tenant = g.current_tenant
    sheets = DeliverySheet.objects(tenant=tenant).order_by('-date', '-created_at')
    
    # Obtener repartidores disponibles (usuarios con rol warehouse o todos)
    drivers = User.objects(tenant=tenant, is_active=True)
    
    # Ventas pendientes de asignar (con despacho, no entregadas, sin hoja)
    assigned_sale_ids = []
    for sheet in DeliverySheet.objects(tenant=tenant, status__in=['pendiente', 'en_ruta']):
        assigned_sale_ids.extend([str(s.id) for s in sheet.sales if s])
    
    pending_sales = Sale.objects(
        tenant=tenant,
        sale_type='con_despacho',
        delivery_status__in=['pendiente', 'en_preparacion']
    ).order_by('-date_created')
    
    # Filtrar las que ya están asignadas
    pending_sales = [s for s in pending_sales if str(s.id) not in assigned_sale_ids]
    
    return render_template(
        "delivery/index.html",
        sheets=sheets,
        drivers=drivers,
        pending_sales=pending_sales
    )


@bp.route("/sheet/<sheet_id>")
@login_required  
def view_sheet(sheet_id):
    """Ver detalle de una hoja de reparto"""
    tenant = g.current_tenant
    
    try:
        sheet = DeliverySheet.objects.get(id=sheet_id, tenant=tenant)
    except Exception as e:
        logger.warning(f"view_sheet: Hoja no encontrada {sheet_id} - {e}")
        return jsonify({"error": "Hoja no encontrada"}), 404
    
    # Preparar datos de ventas con links a mapas
    sales_data = []
    for idx, sale in enumerate(sheet.sales, 1):
        if sale:
            # Crear links para mapas
            address = sale.address or ""
            address_encoded = quote(address)
            
            sales_data.append({
                "order": idx,
                "id": str(sale.id),
                "customer_name": sale.customer_name,
                "address": address,
                "phone": sale.phone or "No especificado",
                "products": [{"name": item.product.name, "qty": item.quantity} for item in sale.items],
                "total": sale.total_amount,
                "payment_status": sale.payment_status,
                "delivery_status": sale.delivery_status,
                "observations": sale.delivery_observations,
                # Links a mapas
                "maps_google": f"https://www.google.com/maps/search/?api=1&query={address_encoded}",
                "maps_waze": f"https://waze.com/ul?q={address_encoded}",
                "maps_apple": f"https://maps.apple.com/?q={address_encoded}",
            })
    
    return render_template(
        "delivery/sheet.html",
        sheet=sheet,
        sales_data=sales_data
    )


# ============================================
# API ENDPOINTS
# ============================================

@bp.route("/api/sheets", methods=["POST"])
@login_required
def create_sheet():
    """Crear nueva hoja de reparto"""
    tenant = g.current_tenant
    data = request.json
    
    # Validar datos requeridos
    if not data.get('date'):
        return jsonify({"error": "Fecha requerida"}), 400
    
    if not data.get('sale_ids') or len(data['sale_ids']) == 0:
        return jsonify({"error": "Debe seleccionar al menos una venta"}), 400
    
    # Parsear fecha
    try:
        date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    except Exception as e:
        logger.warning(f"create_sheet: Formato de fecha inválido '{data.get('date')}' - {e}")
        return jsonify({"error": "Formato de fecha inválido"}), 400
    
    # Obtener ventas
    sales = []
    for sale_id in data['sale_ids']:
        try:
            sale = Sale.objects.get(id=sale_id, tenant=tenant)
            sales.append(sale)
        except Exception as e:
            current_app.logger.warning(f'Venta {sale_id} no encontrada: {e}')
    
    if not sales:
        return jsonify({"error": "No se encontraron ventas válidas"}), 400
    
    # Crear hoja
    sheet = DeliverySheet(
        name=data.get('name', f"Reparto {date.strftime('%d/%m/%Y')}"),
        date=date,
        driver_name=data.get('driver_name'),
        driver_phone=data.get('driver_phone'),
        sales=sales,
        notes=data.get('notes'),
        created_by=current_user._get_current_object(),
        tenant=tenant
    )
    
    # Si se especificó un driver_user_id
    if data.get('driver_user_id'):
        try:
            driver = User.objects.get(id=data['driver_user_id'], tenant=tenant)
            sheet.driver_user = driver
            sheet.driver_name = driver.full_name or driver.username
        except Exception as e:
            current_app.logger.warning(f'Driver {data["driver_user_id"]} no encontrado: {e}')
    
    sheet.save()
    
    # Actualizar estado de las ventas a "en_preparacion"
    for sale in sales:
        if sale.delivery_status == 'pendiente':
            sale.delivery_status = 'en_preparacion'
            sale.save()
    
    return jsonify({
        "success": True,
        "sheet_id": str(sheet.id),
        "message": f"Hoja de reparto creada con {len(sales)} ventas"
    })


@bp.route("/api/sheets/<sheet_id>", methods=["PUT"])
@login_required
def update_sheet(sheet_id):
    """Actualizar hoja de reparto"""
    tenant = g.current_tenant
    data = request.json
    
    try:
        sheet = DeliverySheet.objects.get(id=sheet_id, tenant=tenant)
    except Exception as e:
        logger.warning(f"update_sheet: Hoja no encontrada {sheet_id} - {e}")
        return jsonify({"error": "Hoja no encontrada"}), 404
    
    # Actualizar campos
    if 'status' in data:
        sheet.status = data['status']
        
        # Si se marca como en_ruta, actualizar ventas
        if data['status'] == 'en_ruta':
            for sale in sheet.sales:
                if sale and sale.delivery_status in ['pendiente', 'en_preparacion']:
                    sale.delivery_status = 'en_transito'
                    sale.save()
    
    if 'driver_name' in data:
        sheet.driver_name = data['driver_name']
    
    if 'driver_phone' in data:
        sheet.driver_phone = data['driver_phone']
    
    if 'notes' in data:
        sheet.notes = data['notes']
    
    sheet.save()
    
    return jsonify({"success": True, "message": "Hoja actualizada"})


@bp.route("/api/sheets/<sheet_id>", methods=["DELETE"])
@login_required
def delete_sheet(sheet_id):
    """Eliminar hoja de reparto"""
    tenant = g.current_tenant
    
    try:
        sheet = DeliverySheet.objects.get(id=sheet_id, tenant=tenant)
    except Exception as e:
        logger.warning(f"delete_sheet: Hoja no encontrada {sheet_id} - {e}")
        return jsonify({"error": "Hoja no encontrada"}), 404
    
    # Revertir estado de ventas si estaban en preparación
    for sale in sheet.sales:
        if sale and sale.delivery_status == 'en_preparacion':
            sale.delivery_status = 'pendiente'
            sale.save()
    
    sheet.delete()
    
    return jsonify({"success": True, "message": "Hoja eliminada"})


@bp.route("/api/sheets/<sheet_id>/update-sale/<sale_id>", methods=["PUT"])
@login_required
def update_sale_in_sheet(sheet_id, sale_id):
    """Actualizar estado de una venta dentro de la hoja"""
    tenant = g.current_tenant
    data = request.json
    
    try:
        sheet = DeliverySheet.objects.get(id=sheet_id, tenant=tenant)
        sale = Sale.objects.get(id=sale_id, tenant=tenant)
    except Exception as e:
        logger.warning(f"update_sale_in_sheet: No encontrado sheet={sheet_id} sale={sale_id} - {e}")
        return jsonify({"error": "No encontrado"}), 404
    
    # Verificar que la venta esté en esta hoja
    if sale not in sheet.sales:
        return jsonify({"error": "Esta venta no está en esta hoja"}), 400
    
    # Actualizar dirección y teléfono
    if 'address' in data:
        sale.address = data['address']
    
    if 'phone' in data:
        sale.phone = data['phone']
    
    # Actualizar estado de entrega
    if 'delivery_status' in data:
        sale.delivery_status = data['delivery_status']
        
        if data['delivery_status'] in ['entregado', 'con_observaciones']:
            sale.date_delivered = utc_now()
    
    if 'delivery_observations' in data:
        sale.delivery_observations = data['delivery_observations']
    
    sale.save()
    
    # Verificar si todas las ventas están completadas
    all_delivered = all(
        s.delivery_status in ['entregado', 'con_observaciones', 'cancelado'] 
        for s in sheet.sales if s
    )
    
    if all_delivered and sheet.status != 'completado':
        sheet.status = 'completado'
        sheet.save()
    
    return jsonify({"success": True, "message": "Venta actualizada"})


@bp.route("/api/sheets/<sheet_id>/pdf")
@login_required
def generate_pdf(sheet_id):
    """Generar PDF de la hoja de reparto"""
    tenant = g.current_tenant
    
    try:
        sheet = DeliverySheet.objects.get(id=sheet_id, tenant=tenant)
    except Exception as e:
        logger.warning(f"generate_pdf: Hoja no encontrada {sheet_id} - {e}")
        return jsonify({"error": "Hoja no encontrada"}), 404
    
    # Preparar datos
    sales_data = []
    for idx, sale in enumerate(sheet.sales, 1):
        if sale:
            products_text = ", ".join([f"{item.product.name} x{item.quantity}" for item in sale.items])
            sales_data.append({
                "order": idx,
                "customer": sale.customer_name,
                "address": sale.address or "No especificada",
                "phone": sale.phone or "No especificado",
                "products": products_text,
                "total": f"${sale.total_amount:,.0f}",
                "payment": "✓ Pagado" if sale.payment_status == 'pagado' else "Pendiente",
            })
    
    # Generar HTML para el PDF
    html = render_template(
        "delivery/pdf_template.html",
        sheet=sheet,
        sales_data=sales_data,
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M")
    )
    
    return html  # Por ahora retorna HTML, después se puede convertir a PDF con weasyprint
