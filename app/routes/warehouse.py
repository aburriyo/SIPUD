"""
Warehouse Operations Blueprint
Gestiona operaciones diarias del almacén: pedidos, recepciones, mermas
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, g, abort
from flask_login import login_required, current_user
from app.models import Product, InboundOrder, Wastage, Lot, Supplier, ProductBundle, ActivityLog
from datetime import datetime, timedelta
from bson import ObjectId
from mongoengine import DoesNotExist
from functools import wraps

bp = Blueprint("warehouse", __name__, url_prefix="/warehouse")


def permission_required(module, action='view'):
    """Decorator to check permissions before accessing a route"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if not current_user.has_permission(module, action):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@bp.route("/")
@bp.route("/dashboard")
@login_required
def dashboard():
    """Dashboard de operaciones de almacén"""
    tenant = g.current_tenant

    # Productos próximos a vencer (30 días)
    thirty_days = datetime.now() + timedelta(days=30)
    expiring_soon = Product.objects(
        tenant=tenant,
        expiry_date__ne=None,
        expiry_date__lte=thirty_days.date(),
        expiry_date__gte=datetime.now().date()
    ).order_by('expiry_date').limit(10)

    # Productos con stock crítico
    all_products = Product.objects(tenant=tenant)

    # Filtrar y ordenar en Python ya que total_stock es una propiedad calculada
    low_stock = sorted(
        [p for p in all_products if p.total_stock <= p.critical_stock],
        key=lambda x: x.total_stock,
    )[:10]

    # Pedidos pendientes de recepción
    pending_orders = InboundOrder.objects(
        tenant=tenant,
        status='pending'
    ).order_by('-date_received').limit(10)

    return render_template(
        "warehouse/dashboard.html",
        expiring_soon=expiring_soon,
        low_stock=low_stock,
        pending_orders=pending_orders,
    )


@bp.route("/orders")
@login_required
def orders():
    """Gestión de pedidos a proveedores"""
    tenant = g.current_tenant
    orders = InboundOrder.objects(tenant=tenant).order_by('-created_at')
    return render_template("warehouse/orders.html", orders=orders)


@bp.route("/receiving")
@login_required
def receiving():
    """Recepción de mercancía"""
    tenant = g.current_tenant
    pending = InboundOrder.objects(
        tenant=tenant,
        status='pending'
    ).order_by('-created_at')
    return render_template("warehouse/receiving.html", pending_orders=pending)


@bp.route("/wastage")
@login_required
def wastage():
    """Registro de mermas"""
    tenant = g.current_tenant
    products = Product.objects(tenant=tenant).order_by('name')
    return render_template("warehouse/wastage.html", products=products)


@bp.route("/expiry")
@login_required
def expiry():
    """Gestión de vencimientos"""
    tenant = g.current_tenant
    products = Product.objects(tenant=tenant).order_by('expiry_date')
    return render_template(
        "warehouse/expiry.html", products=products, now=datetime.now().date()
    )


# API Endpoints
@bp.route("/api/orders", methods=["GET"])
@login_required
@permission_required('orders', 'view')
def get_orders():
    """Obtener todos los pedidos"""
    try:
        tenant = g.current_tenant
        orders = InboundOrder.objects(tenant=tenant).order_by('-created_at')

        return jsonify(
            {
                "success": True,
                "orders": [
                    {
                        "id": str(o.id),
                        "supplier": o.supplier_name,
                        "invoice_number": o.invoice_number,
                        "status": o.status,
                        "total": float(o.total) if o.total else 0,
                        "notes": o.notes,
                        "date_received": o.date_received.strftime("%d/%m/%Y %H:%M")
                        if o.date_received
                        else "",
                        "created_at": o.created_at.strftime("%d/%m/%Y %H:%M")
                        if o.created_at
                        else "",
                    }
                    for o in orders
                ],
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/orders", methods=["POST"])
@login_required
@permission_required('orders', 'create')
def create_order():
    """Crear nuevo pedido a proveedor"""
    try:
        data = request.get_json()
        tenant = g.current_tenant

        # Validaciones
        if not data:
            return jsonify({"success": False, "error": "No se recibieron datos"}), 400

        supplier_name = data.get("supplier", "").strip()
        invoice_number = data.get("invoice_number", "").strip()
        total = data.get("total", 0)

        if not supplier_name:
            return jsonify(
                {"success": False, "error": "El proveedor es obligatorio"}
            ), 400

        if not invoice_number:
            return jsonify(
                {"success": False, "error": "El número de factura es obligatorio"}
            ), 400

        try:
            total = float(total)
            if total < 0:
                return jsonify(
                    {"success": False, "error": "El total no puede ser negativo"}
                ), 400
        except (ValueError, TypeError):
            return jsonify(
                {"success": False, "error": "El total debe ser un número válido"}
            ), 400

        new_order = InboundOrder(
            supplier_name=supplier_name,
            invoice_number=invoice_number,
            notes=data.get("notes", "").strip(),
            status="pending",
            total=total,
            created_at=datetime.now(),
            tenant=tenant,
        )

        new_order.save()

        # Log activity
        ActivityLog.log(
            user=current_user,
            action='create',
            module='orders',
            description=f'Creó pedido a "{supplier_name}" - Factura: {invoice_number}, Total: ${total:,.0f}',
            target_id=str(new_order.id),
            target_type='InboundOrder',
            request=request,
            tenant=tenant
        )

        return jsonify(
            {
                "success": True,
                "message": "Pedido creado exitosamente",
                "order_id": str(new_order.id),
            }
        ), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/orders/<order_id>", methods=["PUT"])
@login_required
@permission_required('orders', 'edit')
def update_order(order_id):
    """Actualizar pedido existente"""
    try:
        tenant = g.current_tenant
        try:
            order = InboundOrder.objects.get(id=ObjectId(order_id))
        except DoesNotExist:
            return jsonify({"success": False, "error": "Pedido no encontrado"}), 404

        if order.tenant != tenant:
            return jsonify({"success": False, "error": "Acceso denegado"}), 403

        data = request.get_json()

        if "supplier" in data:
            order.supplier_name = data["supplier"]
        if "invoice_number" in data:
            order.invoice_number = data["invoice_number"]
        if "notes" in data:
            order.notes = data["notes"]
        if "total" in data:
            order.total = data["total"]
        if "status" in data:
            order.status = data["status"]

        order.save()

        # Log activity
        ActivityLog.log(
            user=current_user,
            action='update',
            module='orders',
            description=f'Actualizó pedido de "{order.supplier_name}" - Factura: {order.invoice_number}',
            target_id=str(order.id),
            target_type='InboundOrder',
            request=request,
            tenant=tenant
        )

        return jsonify(
            {"success": True, "message": "Pedido actualizado exitosamente"}
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/orders/<order_id>", methods=["DELETE"])
@login_required
@permission_required('orders', 'delete')
def delete_order(order_id):
    """Eliminar pedido"""
    try:
        tenant = g.current_tenant
        try:
            order = InboundOrder.objects.get(id=ObjectId(order_id))
        except DoesNotExist:
            return jsonify({"success": False, "error": "Pedido no encontrado"}), 404

        if order.tenant != tenant:
            return jsonify({"success": False, "error": "Acceso denegado"}), 403

        # Verificar que no tenga lotes asociados
        if Lot.objects(order=order).count() > 0:
            return jsonify(
                {
                    "success": False,
                    "error": "No se puede eliminar un pedido con lotes asociados",
                }
            ), 400

        # Log activity before deletion
        supplier_name = order.supplier_name
        invoice_number = order.invoice_number
        order_id_str = str(order.id)

        order.delete()

        ActivityLog.log(
            user=current_user,
            action='delete',
            module='orders',
            description=f'Eliminó pedido de "{supplier_name}" - Factura: {invoice_number}',
            target_id=order_id_str,
            target_type='InboundOrder',
            request=request,
            tenant=tenant
        )

        return jsonify(
            {"success": True, "message": "Pedido eliminado exitosamente"}
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/receiving/orders", methods=["GET"])
@login_required
def get_receiving_orders():
    """Obtener pedidos pendientes de recepción"""
    try:
        tenant = g.current_tenant
        orders = InboundOrder.objects(
            tenant=tenant,
            status='pending'
        ).order_by('-created_at')

        return jsonify(
            {
                "success": True,
                "orders": [
                    {
                        "id": str(o.id),
                        "supplier": o.supplier_name,
                        "invoice_number": o.invoice_number,
                        "status": o.status,
                        "total": float(o.total) if o.total else 0,
                        "notes": o.notes,
                        "created_at": o.created_at.strftime("%d/%m/%Y %H:%M")
                        if o.created_at
                        else "",
                    }
                    for o in orders
                ],
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/receiving/<order_id>", methods=["POST"])
@login_required
@permission_required('orders', 'receive')
def confirm_receiving(order_id):
    """Confirmar recepción de pedido con validaciones y procesamiento de lotes"""
    try:
        tenant = g.current_tenant
        try:
            order = InboundOrder.objects.get(id=ObjectId(order_id))
        except DoesNotExist:
            return jsonify({"success": False, "error": "Pedido no encontrado"}), 404

        # Verificar que pertenece al tenant actual
        if order.tenant != tenant:
            return jsonify({"success": False, "error": "Acceso denegado"}), 403

        # Verificar que el pedido no haya sido ya recibido
        if order.status == "received":
            return jsonify(
                {"success": False, "error": "Este pedido ya fue recibido"}
            ), 400

        # Obtener datos del request
        data = request.get_json()

        # Validar datos recibidos
        if not data:
            return jsonify({"success": False, "error": "No se recibieron datos"}), 400

        products = data.get("products", [])

        # Validar que hay al menos un producto
        if not products or len(products) == 0:
            return jsonify(
                {
                    "success": False,
                    "error": "Debe agregar al menos un producto a la recepción",
                }
            ), 400

        # Procesar cada producto
        for idx, item in enumerate(products):
            # Validar campos requeridos
            if not item.get("product_id"):
                return jsonify(
                    {
                        "success": False,
                        "error": f"Producto {idx + 1}: Debe seleccionar un producto",
                    }
                ), 400

            # Validar y convertir cantidad
            try:
                quantity = int(item.get("quantity", 0))
                if quantity <= 0:
                    return jsonify(
                        {
                            "success": False,
                            "error": f"Producto {idx + 1}: La cantidad debe ser mayor a 0",
                        }
                    ), 400
            except (ValueError, TypeError):
                return jsonify(
                    {
                        "success": False,
                        "error": f"Producto {idx + 1}: Cantidad inválida",
                    }
                ), 400

            # Validar que el producto existe y pertenece al tenant
            try:
                product = Product.objects.get(id=ObjectId(item["product_id"]))
            except DoesNotExist:
                return jsonify(
                    {
                        "success": False,
                        "error": f"Producto {idx + 1}: Producto no encontrado",
                    }
                ), 404

            if product.tenant != tenant:
                return jsonify(
                    {
                        "success": False,
                        "error": f"Producto {idx + 1}: Acceso denegado",
                    }
                ), 403

            # Validar código de lote (opcional pero debe ser string si se proporciona)
            lot_code = str(item.get("lot_code", "")).strip()
            if not lot_code:
                lot_code = f"LOT-{str(order.id)[-6:]}-{str(product.id)[-6:]}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Validar fecha de vencimiento (opcional)
            expiry_date = None
            if item.get("expiry_date"):
                try:
                    expiry_date = datetime.strptime(
                        str(item["expiry_date"]).strip(), "%Y-%m-%d"
                    ).date()
                    # Validar que no sea fecha pasada
                    if expiry_date < datetime.now().date():
                        return jsonify(
                            {
                                "success": False,
                                "error": f"Producto {idx + 1}: La fecha de vencimiento no puede ser en el pasado",
                            }
                        ), 400
                except (ValueError, TypeError):
                    return jsonify(
                        {
                            "success": False,
                            "error": f"Producto {idx + 1}: Formato de fecha de vencimiento inválido (use YYYY-MM-DD)",
                        }
                    ), 400

            # Crear lote de inventario
            # FIXED: Using 'order' instead of 'inbound_order_id' and adding tenant
            lot = Lot(
                product=product,
                order=order,
                tenant=tenant,  # FIXED: Added tenant_id
                lot_code=lot_code,
                quantity_initial=quantity,
                quantity_current=quantity,
                expiry_date=expiry_date,
            )
            lot.save()

            # FIXED: Removed product.stock += quantity (stock is calculated from Lots)

        # Actualizar estado del pedido
        order.status = "received"
        order.date_received = datetime.now()
        order.save()

        # Log activity
        ActivityLog.log(
            user=current_user,
            action='receive',
            module='orders',
            description=f'Recibió pedido de "{order.supplier_name}" - Factura: {order.invoice_number}, {len(products)} producto(s)',
            target_id=str(order.id),
            target_type='InboundOrder',
            request=request,
            tenant=tenant
        )

        return jsonify(
            {
                "success": True,
                "message": f"Recepción confirmada exitosamente. {len(products)} producto(s) agregado(s) al inventario.",
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/wastage", methods=["POST"])
@login_required
@permission_required('wastage', 'create')
def register_wastage():
    """Registrar merma de producto"""
    try:
        data = request.get_json()
        tenant = g.current_tenant

        # Validaciones
        if not data:
            return jsonify({"success": False, "error": "No se recibieron datos"}), 400

        product_id = data.get("product_id")
        quantity_str = data.get("quantity", 0)
        reason = data.get("reason", "").strip()

        if not product_id:
            return jsonify(
                {"success": False, "error": "Debe seleccionar un producto"}
            ), 400

        try:
            quantity = int(quantity_str)
            if quantity <= 0:
                return jsonify(
                    {"success": False, "error": "La cantidad debe ser mayor a 0"}
                ), 400
        except (ValueError, TypeError):
            return jsonify(
                {
                    "success": False,
                    "error": "La cantidad debe ser un número entero válido",
                }
            ), 400

        if not reason or reason not in ["vencido", "dañado", "perdido", "robo", "otro"]:
            return jsonify(
                {"success": False, "error": "Debe especificar una razón válida"}
            ), 400

        # Validar producto
        try:
            product = Product.objects.get(id=ObjectId(product_id))
        except DoesNotExist:
            return jsonify({"success": False, "error": "Producto no encontrado"}), 404

        if product.tenant != tenant:
            return jsonify({"success": False, "error": "Acceso denegado"}), 403

        # Verificar stock disponible
        if product.total_stock < quantity:
            return jsonify(
                {
                    "success": False,
                    "error": f"Stock insuficiente. Disponible: {product.total_stock}, solicitado: {quantity}",
                }
            ), 400

        # Registrar merma
        wastage_record = Wastage(
            product=product,
            quantity=quantity,
            reason=reason,
            notes=data.get("notes", "").strip(),
            tenant=tenant,
        )

        # Reducir stock (FIFO - del lote más antiguo)
        remaining_to_deduct = quantity
        available_lots = sorted(
            [l for l in product.lots if l.quantity_current > 0],
            key=lambda x: x.created_at,
        )

        if not available_lots:
            return jsonify(
                {
                    "success": False,
                    "error": "No hay lotes disponibles para este producto",
                }
            ), 400

        for lot in available_lots:
            if remaining_to_deduct <= 0:
                break
            deduct = min(lot.quantity_current, remaining_to_deduct)
            lot.quantity_current -= deduct
            remaining_to_deduct -= deduct
            lot.save()

        wastage_record.save()

        # Log activity
        reason_names = {
            'vencido': 'Vencido',
            'dañado': 'Dañado',
            'perdido': 'Perdido',
            'robo': 'Robo',
            'otro': 'Otro'
        }
        ActivityLog.log(
            user=current_user,
            action='create',
            module='wastage',
            description=f'Registró merma de "{product.name}" - {quantity} unidades ({reason_names.get(reason, reason)})',
            target_id=str(wastage_record.id),
            target_type='Wastage',
            request=request,
            tenant=tenant
        )

        return jsonify(
            {
                "success": True,
                "message": "Merma registrada exitosamente",
                "wastage_id": str(wastage_record.id),
            }
        ), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/wastage/history", methods=["GET"])
@login_required
@permission_required('wastage', 'view')
def wastage_history():
    """Obtener historial de mermas"""
    try:
        tenant = g.current_tenant
        wastages = Wastage.objects(tenant=tenant).order_by('-date_created')

        return jsonify(
            {
                "success": True,
                "wastages": [
                    {
                        "id": str(w.id),
                        "product_id": str(w.product.id) if w.product else None,
                        "product_name": w.product.name if w.product else 'N/A',
                        "quantity": w.quantity,
                        "reason": w.reason,
                        "notes": w.notes,
                        "date": w.date_created.strftime("%d/%m/%Y %H:%M"),
                    }
                    for w in wastages
                ],
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/wastage/<wastage_id>", methods=["DELETE"])
@login_required
@permission_required('wastage', 'delete')
def delete_wastage(wastage_id):
    """Eliminar registro de merma (NO REVIERTE STOCK)"""
    try:
        tenant = g.current_tenant
        try:
            wastage_record = Wastage.objects.get(id=ObjectId(wastage_id))
        except DoesNotExist:
            return jsonify({"success": False, "error": "Merma no encontrada"}), 404

        if wastage_record.tenant != tenant:
            return jsonify({"success": False, "error": "Acceso denegado"}), 403

        # Log activity before deletion
        product_name = wastage_record.product.name if wastage_record.product else 'N/A'
        quantity = wastage_record.quantity
        wastage_id_str = str(wastage_record.id)

        wastage_record.delete()

        ActivityLog.log(
            user=current_user,
            action='delete',
            module='wastage',
            description=f'Eliminó registro de merma de "{product_name}" - {quantity} unidades',
            target_id=wastage_id_str,
            target_type='Wastage',
            request=request,
            tenant=tenant
        )

        return jsonify({"success": True, "message": "Registro de merma eliminado"}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/expiry/products", methods=["GET"])
@login_required
def get_expiry_products():
    """Obtener productos con fechas de vencimiento"""
    try:
        tenant = g.current_tenant
        products = Product.objects(
            tenant=tenant,
            expiry_date__ne=None
        ).order_by('expiry_date')

        now = datetime.now().date()

        return jsonify(
            {
                "success": True,
                "products": [
                    {
                        "id": str(p.id),
                        "name": p.name,
                        "sku": p.sku,
                        "expiry_date": p.expiry_date.strftime("%Y-%m-%d")
                        if p.expiry_date
                        else None,
                        "days_until_expiry": (p.expiry_date - now).days
                        if p.expiry_date
                        else None,
                        "status": "expired"
                        if p.expiry_date and p.expiry_date < now
                        else (
                            "warning"
                            if p.expiry_date and (p.expiry_date - now).days <= 30
                            else "ok"
                        ),
                        "stock": p.total_stock,
                    }
                    for p in products
                ],
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/expiry/<product_id>", methods=["PUT"])
@login_required
def update_expiry(product_id):
    """Actualizar fecha de vencimiento de producto"""
    try:
        data = request.get_json()
        tenant = g.current_tenant

        if not data:
            return jsonify({"success": False, "error": "No se recibieron datos"}), 400

        try:
            product = Product.objects.get(id=ObjectId(product_id))
        except DoesNotExist:
            return jsonify({"success": False, "error": "Producto no encontrado"}), 404

        if product.tenant != tenant:
            return jsonify({"success": False, "error": "Acceso denegado"}), 403

        # Validar y actualizar fecha de vencimiento
        expiry_str = data.get("expiry_date", "").strip()

        if expiry_str:
            try:
                expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()

                # Validar que la fecha no esté en el pasado
                if expiry_date < datetime.now().date():
                    return jsonify(
                        {
                            "success": False,
                            "error": "La fecha de vencimiento no puede estar en el pasado",
                        }
                    ), 400

                product.expiry_date = expiry_date
            except ValueError:
                return jsonify(
                    {
                        "success": False,
                        "error": "Formato de fecha inválido. Use YYYY-MM-DD",
                    }
                ), 400
        else:
            product.expiry_date = None

        product.save()

        # Log activity
        ActivityLog.log(
            user=current_user,
            action='update',
            module='products',
            description=f'Actualizó fecha de vencimiento de "{product.name}" a {expiry_str or "sin fecha"}',
            target_id=str(product.id),
            target_type='Product',
            request=request,
            tenant=tenant
        )

        return jsonify(
            {"success": True, "message": "Fecha de vencimiento actualizada"}
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/alerts", methods=["GET"])
@login_required
def get_alerts():
    """Obtener alertas de vencimientos próximos y stock crítico"""
    try:
        tenant = g.current_tenant
        alerts = []
        now = datetime.now().date()

        # Alertas de vencimiento (próximos 30 días)
        thirty_days = now + timedelta(days=30)
        expiring_products = Product.objects(
            tenant=tenant,
            expiry_date__ne=None,
            expiry_date__lte=thirty_days,
            expiry_date__gte=now
        ).order_by('expiry_date')

        for product in expiring_products:
            days_left = (product.expiry_date - now).days
            severity = (
                "danger"
                if days_left <= 7
                else ("warning" if days_left <= 14 else "info")
            )

            alerts.append(
                {
                    "type": "expiry",
                    "severity": severity,
                    "product_id": str(product.id),
                    "product_name": product.name,
                    "message": f"El producto '{product.name}' vence en {days_left} días",
                    "days_left": days_left,
                    "expiry_date": product.expiry_date.strftime("%d/%m/%Y"),
                    "stock": product.total_stock,
                }
            )

        # Alertas de stock crítico
        all_products = Product.objects(tenant=tenant)
        for product in all_products:
            if product.total_stock <= product.critical_stock:
                alerts.append(
                    {
                        "type": "low_stock",
                        "severity": "danger" if product.total_stock == 0 else "warning",
                        "product_id": str(product.id),
                        "product_name": product.name,
                        "message": f"Stock bajo: '{product.name}' ({product.total_stock} unidades)",
                        "current_stock": product.total_stock,
                        "critical_stock": product.critical_stock,
                    }
                )

        # Ordenar por severidad (danger primero)
        severity_order = {"danger": 0, "warning": 1, "info": 2}
        alerts.sort(key=lambda x: severity_order.get(x["severity"], 3))

        return jsonify({"success": True, "alerts": alerts, "count": len(alerts)}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/assembly", methods=["POST"])
@login_required
@permission_required('orders', 'create')
def assemble_box():
    """
    Ensamblar cajas (Kitting).
    Descuenta stock de componentes y agrega stock al producto 'caja' (bundle).
    """
    try:
        data = request.get_json()
        tenant = g.current_tenant
        bundle_id = data.get("bundle_id")
        quantity = int(data.get("quantity", 0))

        if quantity <= 0:
            return jsonify(
                {"success": False, "error": "Cantidad debe ser mayor a 0"}
            ), 400

        # 1. Verificar producto bundle
        try:
            bundle_product = Product.objects.get(id=ObjectId(bundle_id))
        except DoesNotExist:
            return jsonify({"success": False, "error": "Producto no encontrado"}), 404

        if bundle_product.tenant != tenant:
            return jsonify({"success": False, "error": "Acceso denegado"}), 403

        if not bundle_product.is_bundle:
            return jsonify(
                {
                    "success": False,
                    "error": "El producto seleccionado no es un Kit/Caja",
                }
            ), 400

        # 2. Verificar componentes y stock
        components = ProductBundle.objects(bundle=bundle_product)

        if components.count() == 0:
            return jsonify(
                {"success": False, "error": "Este kit no tiene componentes definidos"}
            ), 400

        # Pre-chequeo de stock
        for comp_rel in components:
            comp_product = comp_rel.component
            needed_qty = comp_rel.quantity * quantity

            if comp_product.total_stock < needed_qty:
                return jsonify(
                    {
                        "success": False,
                        "error": f'Stock insuficiente de componente "{comp_product.name}". Requerido: {needed_qty}, Disponible: {comp_product.total_stock}',
                    }
                ), 400

        # 3. Descontar stock de componentes (FIFO)
        for comp_rel in components:
            comp_product = comp_rel.component
            total_needed = comp_rel.quantity * quantity
            remaining_to_deduct = total_needed

            # Obtener lotes disponibles ordenados por fecha (FIFO)
            available_lots = sorted(
                [l for l in comp_product.lots if l.quantity_current > 0],
                key=lambda x: x.created_at,
            )

            for lot in available_lots:
                if remaining_to_deduct <= 0:
                    break

                deduct = min(lot.quantity_current, remaining_to_deduct)
                lot.quantity_current -= deduct
                remaining_to_deduct -= deduct
                lot.save()

            if remaining_to_deduct > 0:
                raise Exception(
                    f"Error concurrente de inventario en {comp_product.name}"
                )

        # 4. Crear Lote para el Bundle
        # Buscamos o creamos una Orden de Entrada "interna" para asignar el lote
        internal_supplier_name = "Interno: Armado"
        today_assembly_order = InboundOrder.objects(
            tenant=tenant,
            supplier_name=internal_supplier_name,
            created_at__gte=datetime.combine(datetime.utcnow().date(), datetime.min.time()),
            created_at__lt=datetime.combine(datetime.utcnow().date() + timedelta(days=1), datetime.min.time())
        ).first()

        if not today_assembly_order:
            # Buscar o crear proveedor interno
            internal_supplier = Supplier.objects(
                rut="99999999-9", tenant=tenant
            ).first()
            if not internal_supplier:
                internal_supplier = Supplier.objects(
                    name="Interno", tenant=tenant
                ).first()

            if not internal_supplier:
                internal_supplier = Supplier(
                    name="Interno",
                    rut="99999999-9",
                    contact_info="Sistema",
                    tenant=tenant,
                )
                internal_supplier.save()

            today_assembly_order = InboundOrder(
                supplier=internal_supplier,
                supplier_name=internal_supplier_name,
                invoice_number=f"ARM-{datetime.utcnow().strftime('%Y%m%d-%H%M')}",
                status="received",
                date_received=datetime.utcnow(),
                notes="Generado automáticamente por proceso de armado de cajas",
                tenant=tenant,
            )
            today_assembly_order.save()

        # FIXED: Using 'order' instead of 'inbound_order_id' and adding tenant
        new_lot = Lot(
            product=bundle_product,
            order=today_assembly_order,
            tenant=tenant,  # FIXED: Added tenant
            lot_code=f"KIT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            quantity_initial=quantity,
            quantity_current=quantity,
            expiry_date=None,
            created_at=datetime.utcnow(),
        )
        new_lot.save()

        # Log activity
        ActivityLog.log(
            user=current_user,
            action='create',
            module='orders',
            description=f'Armó {quantity} unidades de "{bundle_product.name}" (Kit/Bundle)',
            target_id=str(new_lot.id),
            target_type='Lot',
            request=request,
            tenant=tenant
        )

        return jsonify(
            {
                "success": True,
                "message": f'Se armaron {quantity} unidades de "{bundle_product.name}" exitosamente',
            }
        ), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
