"""
Warehouse Operations Blueprint
Gestiona operaciones diarias del almacén: pedidos, recepciones, mermas
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, g
from flask_login import login_required
from app.models import db, Product, InboundOrder, Wastage, Lot, Supplier
from datetime import datetime, timedelta
from sqlalchemy import and_

bp = Blueprint("warehouse", __name__, url_prefix="/warehouse")


@bp.route("/")
@bp.route("/dashboard")
@login_required
def dashboard():
    """Dashboard de operaciones de almacén"""
    # Productos próximos a vencer (30 días)
    thirty_days = datetime.now() + timedelta(days=30)
    expiring_soon = (
        Product.query.filter(
            and_(
                Product.tenant_id == g.current_tenant.id,
                Product.expiry_date.isnot(None),
                Product.expiry_date <= thirty_days,
                Product.expiry_date >= datetime.now(),
            )
        )
        .order_by(Product.expiry_date)
        .limit(10)
        .all()
    )

    # Productos con stock crítico - ordenados por id ya que total_stock es una propiedad
    low_stock_products = Product.query.filter(
        Product.tenant_id == g.current_tenant.id
    ).all()

    # Filtrar y ordenar en Python ya que total_stock es una propiedad calculada
    low_stock = sorted(
        [p for p in low_stock_products if p.total_stock <= p.critical_stock],
        key=lambda x: x.total_stock,
    )[:10]

    # Pedidos pendientes de recepción
    pending_orders = (
        InboundOrder.query.filter(
            and_(
                InboundOrder.tenant_id == g.current_tenant.id
                if hasattr(InboundOrder, "tenant_id")
                else True,
                InboundOrder.status == "pending",
            )
        )
        .order_by(InboundOrder.date_received.desc())
        .limit(10)
        .all()
    )

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
    orders = InboundOrder.query.order_by(InboundOrder.date_received.desc()).all()
    return render_template("warehouse/orders.html", orders=orders)


@bp.route("/receiving")
@login_required
def receiving():
    """Recepción de mercancía"""
    pending = (
        InboundOrder.query.filter(InboundOrder.status == "pending")
        .order_by(InboundOrder.date_received.desc())
        .all()
    )
    return render_template("warehouse/receiving.html", pending_orders=pending)


@bp.route("/wastage")
@login_required
def wastage():
    """Registro de mermas"""
    products = (
        Product.query.filter_by(tenant_id=g.current_tenant.id)
        .order_by(Product.name)
        .all()
    )
    return render_template("warehouse/wastage.html", products=products)


@bp.route("/expiry")
@login_required
def expiry():
    """Gestión de vencimientos"""
    products = (
        Product.query.filter_by(tenant_id=g.current_tenant.id)
        .order_by(Product.expiry_date.asc())
        .all()
    )
    return render_template(
        "warehouse/expiry.html", products=products, now=datetime.now().date()
    )


# API Endpoints
@bp.route("/api/orders", methods=["GET"])
@login_required
def get_orders():
    """Obtener todos los pedidos"""
    try:
        orders = (
            InboundOrder.query.filter_by(tenant_id=g.current_tenant.id)
            .order_by(InboundOrder.date_received.desc())
            .all()
        )

        return jsonify(
            {
                "success": True,
                "orders": [
                    {
                        "id": o.id,
                        "supplier": o.supplier,
                        "invoice_number": o.invoice_number,
                        "status": o.status,
                        "total": o.total,
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
def create_order():
    """Crear nuevo pedido a proveedor"""
    try:
        data = request.get_json()

        # Validaciones
        if not data:
            return jsonify({"success": False, "error": "No se recibieron datos"}), 400

        supplier = data.get("supplier", "").strip()
        invoice_number = data.get("invoice_number", "").strip()
        total = data.get("total", 0)

        if not supplier:
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
            supplier=supplier,
            invoice_number=invoice_number,
            notes=data.get("notes", "").strip(),
            status="pending",
            total=total,
            created_at=datetime.now(),
            tenant_id=g.current_tenant.id
            if hasattr(g, "current_tenant") and g.current_tenant
            else None,
        )

        db.session.add(new_order)
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Pedido creado exitosamente",
                "order_id": new_order.id,
            }
        ), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/orders/<int:order_id>", methods=["PUT"])
@login_required
def update_order(order_id):
    """Actualizar pedido existente"""
    try:
        order = InboundOrder.query.get_or_404(order_id)

        if order.tenant_id != g.current_tenant.id:
            return jsonify({"success": False, "error": "Acceso denegado"}), 403

        data = request.get_json()

        if "supplier" in data:
            order.supplier = data["supplier"]
        if "invoice_number" in data:
            order.invoice_number = data["invoice_number"]
        if "notes" in data:
            order.notes = data["notes"]
        if "total" in data:
            order.total = data["total"]
        if "status" in data:
            order.status = data["status"]

        db.session.commit()

        return jsonify(
            {"success": True, "message": "Pedido actualizado exitosamente"}
        ), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/orders/<int:order_id>", methods=["DELETE"])
@login_required
def delete_order(order_id):
    """Eliminar pedido"""
    try:
        order = InboundOrder.query.get_or_404(order_id)

        if order.tenant_id != g.current_tenant.id:
            return jsonify({"success": False, "error": "Acceso denegado"}), 403

        # Verificar que no tenga lotes asociados
        if order.lots and len(order.lots) > 0:
            return jsonify(
                {
                    "success": False,
                    "error": "No se puede eliminar un pedido con lotes asociados",
                }
            ), 400

        db.session.delete(order)
        db.session.commit()

        return jsonify(
            {"success": True, "message": "Pedido eliminado exitosamente"}
        ), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/receiving/<int:order_id>", methods=["POST"])
@login_required
def confirm_receiving(order_id):
    """Confirmar recepción de pedido"""
    try:
        order = InboundOrder.query.get_or_404(order_id)

        # Verificar que pertenece al tenant actual
        if hasattr(order, "tenant_id") and order.tenant_id != g.current_tenant.id:
            return jsonify({"success": False, "error": "Acceso denegado"}), 403

        # Actualizar estado
        order.status = "received"
        order.date_received = datetime.now()

        db.session.commit()

        return jsonify(
            {"success": True, "message": "Recepción confirmada exitosamente"}
        ), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/wastage", methods=["POST"])
@login_required
def register_wastage():
    """Registrar merma de producto"""
    try:
        data = request.get_json()

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
        product = Product.query.get_or_404(product_id)

        if product.tenant_id != g.current_tenant.id:
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
        wastage = Wastage(
            product_id=product_id,
            quantity=quantity,
            reason=reason,
            notes=data.get("notes", "").strip(),
            tenant_id=g.current_tenant.id,
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

        db.session.add(wastage)
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Merma registrada exitosamente",
                "wastage_id": wastage.id,
            }
        ), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/wastage/history", methods=["GET"])
@login_required
def wastage_history():
    """Obtener historial de mermas"""
    try:
        wastages = (
            Wastage.query.filter_by(tenant_id=g.current_tenant.id)
            .order_by(Wastage.date_created.desc())
            .all()
        )

        return jsonify(
            {
                "success": True,
                "wastages": [
                    {
                        "id": w.id,
                        "product_id": w.product_id,
                        "product_name": w.product.name,
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


@bp.route("/api/wastage/<int:wastage_id>", methods=["DELETE"])
@login_required
def delete_wastage(wastage_id):
    """Eliminar registro de merma (NO REVIERTE STOCK)"""
    try:
        wastage = Wastage.query.get_or_404(wastage_id)

        if wastage.tenant_id != g.current_tenant.id:
            return jsonify({"success": False, "error": "Acceso denegado"}), 403

        db.session.delete(wastage)
        db.session.commit()

        return jsonify({"success": True, "message": "Registro de merma eliminado"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/expiry/products", methods=["GET"])
@login_required
def get_expiry_products():
    """Obtener productos con fechas de vencimiento"""
    try:
        products = (
            Product.query.filter_by(tenant_id=g.current_tenant.id)
            .filter(Product.expiry_date.isnot(None))
            .order_by(Product.expiry_date.asc())
            .all()
        )

        now = datetime.now().date()

        return jsonify(
            {
                "success": True,
                "products": [
                    {
                        "id": p.id,
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


@bp.route("/api/expiry/<int:product_id>", methods=["PUT"])
@login_required
def update_expiry(product_id):
    """Actualizar fecha de vencimiento de producto"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No se recibieron datos"}), 400

        product = Product.query.get_or_404(product_id)

        if product.tenant_id != g.current_tenant.id:
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

        db.session.commit()

        return jsonify(
            {"success": True, "message": "Fecha de vencimiento actualizada"}
        ), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/alerts", methods=["GET"])
@login_required
def get_alerts():
    """Obtener alertas de vencimientos próximos y stock crítico"""
    try:
        alerts = []
        now = datetime.now().date()

        # Alertas de vencimiento (próximos 30 días)
        thirty_days = now + timedelta(days=30)
        expiring_products = (
            Product.query.filter_by(tenant_id=g.current_tenant.id)
            .filter(Product.expiry_date.isnot(None))
            .filter(Product.expiry_date <= thirty_days)
            .filter(Product.expiry_date >= now)
            .order_by(Product.expiry_date.asc())
            .all()
        )

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
                    "product_id": product.id,
                    "product_name": product.name,
                    "message": f"El producto '{product.name}' vence en {days_left} días",
                    "days_left": days_left,
                    "expiry_date": product.expiry_date.strftime("%d/%m/%Y"),
                    "stock": product.total_stock,
                }
            )

        # Alertas de stock crítico
        all_products = Product.query.filter_by(tenant_id=g.current_tenant.id).all()
        for product in all_products:
            if product.total_stock <= product.critical_stock:
                alerts.append(
                    {
                        "type": "low_stock",
                        "severity": "danger" if product.total_stock == 0 else "warning",
                        "product_id": product.id,
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
def assemble_box():
    """
    Ensamblar cajas (Kitting).
    Descuenta stock de componentes y agrega stock al producto 'caja' (bundle).
    """
    try:
        data = request.get_json()
        bundle_id = data.get("bundle_id")
        quantity = int(data.get("quantity", 0))

        if quantity <= 0:
            return jsonify(
                {"success": False, "error": "Cantidad debe ser mayor a 0"}
            ), 400

        # 1. Verificar producto bundle
        bundle_product = Product.query.get_or_404(bundle_id)
        if bundle_product.tenant_id != g.current_tenant.id:
            return jsonify({"success": False, "error": "Acceso denegado"}), 403

        if not bundle_product.is_bundle:
            return jsonify(
                {
                    "success": False,
                    "error": "El producto seleccionado no es un Kit/Caja",
                }
            ), 400

        # 2. Verificar componentes y stock
        from app.models import ProductBundle, Lot

        components = ProductBundle.query.filter_by(bundle_id=bundle_product.id).all()

        if not components:
            return jsonify(
                {"success": False, "error": "Este kit no tiene componentes definidos"}
            ), 400

        # Pre-chequeo de stock
        for comp_rel in components:
            comp_product = Product.query.get(comp_rel.component_id)
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
            comp_product = Product.query.get(comp_rel.component_id)
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
                db.session.add(lot)  # Mark for update

            if remaining_to_deduct > 0:
                # Esto no debería pasar dado el pre-chequeo, pero por seguridad
                raise Exception(
                    f"Error concurrente de inventario en {comp_product.name}"
                )

        # 4. Crear Lote para el Bundle
        # Buscamos o creamos una Orden de Entrada "interna" para asignar el lote
        internal_supplier_name = "Interno: Armado"
        today_assembly_order = InboundOrder.query.filter(
            InboundOrder.tenant_id == g.current_tenant.id,
            InboundOrder.supplier == internal_supplier_name,
            db.func.date(InboundOrder.created_at) == datetime.utcnow().date(),
        ).first()

        if not today_assembly_order:
            # Buscar o crear proveedor interno
            from app.models import Supplier

            internal_supplier = Supplier.query.filter_by(
                rut="99999999-9", tenant_id=g.current_tenant.id
            ).first()
            if not internal_supplier:
                internal_supplier = Supplier.query.filter_by(
                    name="Interno", tenant_id=g.current_tenant.id
                ).first()

            if not internal_supplier:
                internal_supplier = Supplier(
                    name="Interno",
                    rut="99999999-9",
                    contact_info="Sistema",
                    tenant_id=g.current_tenant.id,
                )
                db.session.add(internal_supplier)
                db.session.flush()

            today_assembly_order = InboundOrder(
                supplier_id=internal_supplier.id,
                supplier=internal_supplier_name,
                invoice_number=f"ARM-{datetime.utcnow().strftime('%Y%m%d-%H%M')}",
                status="received",  # Ya "recibido"
                date_received=datetime.utcnow(),
                notes="Generado automáticamente por proceso de armado de cajas",
                tenant_id=g.current_tenant.id,
            )
            db.session.add(today_assembly_order)
            db.session.flush()  # Para obtener ID

        new_lot = Lot(
            product_id=bundle_product.id,
            inbound_order_id=today_assembly_order.id,
            lot_code=f"KIT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            quantity_initial=quantity,
            quantity_current=quantity,
            expiry_date=None,  # O calcular basado en el componente que vence primero? Por ahora None.
            created_at=datetime.utcnow(),
        )
        db.session.add(new_lot)

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": f'Se armaron {quantity} unidades de "{bundle_product.name}" exitosamente',
            }
        ), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
