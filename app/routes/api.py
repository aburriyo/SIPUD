from flask import Blueprint, jsonify, request, g, abort, current_app
from flask_login import current_user, login_required
from app.models import Product, Sale, SaleItem, Lot, InboundOrder, ProductBundle, Truck, VehicleMaintenance, ActivityLog, Payment, Tenant, Wastage, User, utc_now
from app.extensions import limiter
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from bson import ObjectId
from mongoengine import DoesNotExist
from functools import wraps

bp = Blueprint('api', __name__, url_prefix='/api')

# Exempt authenticated routes from strict rate limiting
# (they still have global limits from extensions.py)
@bp.before_request
def exempt_authenticated_users():
    """Skip strict rate limits for authenticated users"""
    if current_user.is_authenticated:
        # Mark request as exempt from per-route limits
        request.environ['RATELIMIT_EXEMPT'] = True


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


@bp.route('/products', methods=['GET'])
@login_required
def get_products():
    tenant = g.current_tenant
    products = Product.objects(tenant=tenant)
    results = []
    for p in products:
        results.append({
            'id': str(p.id),
            'name': p.name,
            'sku': p.sku,
            'description': p.description,
            'category': p.category,
            'base_price': float(p.base_price) if p.base_price else 0,
            'critical_stock': p.critical_stock,
            'stock': p.total_stock
        })
    return jsonify(results)


@bp.route('/products', methods=['POST'])
@login_required
@permission_required('products', 'create')
def create_product():
    data = request.get_json()
    tenant = g.current_tenant

    # Basic validation
    if not data or 'name' not in data or 'sku' not in data:
        return jsonify({'error': 'Faltan datos requeridos (name, sku)'}), 400

    # Check if SKU exists within tenant
    if Product.objects(sku=data['sku'], tenant=tenant).first():
        return jsonify({'error': 'El SKU ya existe en esta organización'}), 400

    try:
        new_product = Product(
            name=data['name'],
            sku=data['sku'],
            description=data.get('description'),
            category=data.get('category', 'Otros'),
            base_price=data.get('base_price', 0),
            critical_stock=data.get('critical_stock', 10),
            tenant=tenant
        )
        new_product.save()

        # Handle initial stock: create a Lot if initial_stock > 0
        initial_stock = int(data.get('initial_stock', 0))
        if initial_stock > 0:
            # Generate lot code if not provided
            lot_code = data.get('initial_lot_code', '').strip()
            if not lot_code:
                lot_code = f"INIT-{new_product.sku}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Find or create an "Initial Stock" inbound order for today
            today_start = datetime.combine(datetime.now().date(), datetime.min.time())
            today_end = datetime.combine(datetime.now().date() + timedelta(days=1), datetime.min.time())
            
            initial_order = InboundOrder.objects(
                tenant=tenant,
                supplier_name="Stock Inicial",
                created_at__gte=today_start,
                created_at__lt=today_end
            ).first()
            
            if not initial_order:
                initial_order = InboundOrder(
                    supplier_name="Stock Inicial",
                    invoice_number=f"INIT-{datetime.now().strftime('%Y%m%d')}",
                    status="received",
                    date_received=datetime.now(),
                    notes="Orden automática para stock inicial de productos nuevos",
                    tenant=tenant,
                    created_at=datetime.now()
                )
                initial_order.save()
            
            # Create lot for initial stock
            initial_lot = Lot(
                product=new_product,
                order=initial_order,
                tenant=tenant,
                lot_code=lot_code,
                quantity_initial=initial_stock,
                quantity_current=initial_stock,
                expiry_date=None,
                created_at=datetime.now()
            )
            initial_lot.save()

        # Handle bundle components
        if 'bundle_components' in data and data['bundle_components']:
            for component in data['bundle_components']:
                bundle_item = ProductBundle(
                    bundle=new_product,
                    component=Product.objects.get(id=ObjectId(component['component_id'])),
                    quantity=component['quantity'],
                    tenant=tenant
                )
                bundle_item.save()

        # Log activity
        stock_msg = f', stock inicial: {initial_stock}' if initial_stock > 0 else ''
        ActivityLog.log(
            user=current_user,
            action='create',
            module='products',
            description=f'Creó producto "{data["name"]}" (SKU: {data["sku"]}{stock_msg})',
            target_id=str(new_product.id),
            target_type='Product',
            request=request,
            tenant=tenant
        )

        return jsonify({'message': 'Producto creado', 'id': str(new_product.id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/products/<id>', methods=['DELETE'])
@login_required
@permission_required('products', 'delete')
def delete_product(id):
    tenant = g.current_tenant
    try:
        product = Product.objects.get(id=ObjectId(id), tenant=tenant)
    except DoesNotExist:
        return jsonify({'error': 'Producto no encontrado'}), 404

    try:
        product_name = product.name
        product_sku = product.sku

        # Delete associated lots first
        Lot.objects(product=product).delete()

        # Delete bundle relationships if this product is part of any bundles
        ProductBundle.objects(component=product).delete()
        ProductBundle.objects(bundle=product).delete()

        # Delete the product
        product.delete()

        # Log activity
        ActivityLog.log(
            user=current_user,
            action='delete',
            module='products',
            description=f'Eliminó producto "{product_name}" (SKU: {product_sku})',
            target_id=id,
            target_type='Product',
            request=request,
            tenant=tenant
        )

        return jsonify({'message': 'Producto eliminado correctamente'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/products/<id>', methods=['PUT'])
@login_required
@permission_required('products', 'edit')
def update_product(id):
    tenant = g.current_tenant
    try:
        product = Product.objects.get(id=ObjectId(id), tenant=tenant)
    except DoesNotExist:
        return jsonify({'error': 'Producto no encontrado'}), 404

    data = request.get_json()
    changes = []

    try:
        if 'name' in data and data['name'] != product.name:
            changes.append(f'nombre: {product.name} → {data["name"]}')
            product.name = data['name']
        if 'sku' in data:
            # Check unique SKU if changing
            if data['sku'] != product.sku:
                existing = Product.objects(sku=data['sku'], tenant=tenant).first()
                if existing:
                    return jsonify({'error': 'El SKU ya existe'}), 400
                changes.append(f'SKU: {product.sku} → {data["sku"]}')
            product.sku = data['sku']
        if 'description' in data and data.get('description') != product.description:
            changes.append('descripción actualizada')
            product.description = data['description']
        if 'category' in data and data.get('category') != product.category:
            changes.append(f'categoría: {product.category} → {data["category"]}')
            product.category = data['category']
        if 'base_price' in data and float(data.get('base_price', 0)) != float(product.base_price or 0):
            changes.append(f'precio: {product.base_price} → {data["base_price"]}')
            product.base_price = data['base_price']
        if 'critical_stock' in data and data.get('critical_stock') != product.critical_stock:
            changes.append(f'stock crítico: {product.critical_stock} → {data["critical_stock"]}')
            product.critical_stock = data['critical_stock']

        # Handle bundle components update
        if 'bundle_components' in data:
            # Delete existing components
            ProductBundle.objects(bundle=product).delete()
            # Add new components
            for component in data['bundle_components']:
                bundle_item = ProductBundle(
                    bundle=product,
                    component=Product.objects.get(id=ObjectId(component['component_id'])),
                    quantity=component['quantity'],
                    tenant=tenant
                )
                bundle_item.save()
            changes.append('componentes de bundle actualizados')

        product.save()

        # Handle stock adjustment (optional)
        stock_adjustment_type = data.get('stock_adjustment_type', '')
        stock_adjustment_qty = int(data.get('stock_adjustment_quantity', 0))
        stock_adjustment_reason = data.get('stock_adjustment_reason', '').strip()

        if stock_adjustment_type and stock_adjustment_qty > 0:
            if stock_adjustment_type == 'add':
                # Add stock: create a new Lot
                lot_code = data.get('stock_adjustment_lot_code', '').strip()
                if not lot_code:
                    lot_code = f"ADJ-{product.sku}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

                # Find or create an "Ajuste de Inventario" inbound order for today
                today_start = datetime.combine(datetime.now().date(), datetime.min.time())
                today_end = datetime.combine(datetime.now().date() + timedelta(days=1), datetime.min.time())

                adj_order = InboundOrder.objects(
                    tenant=tenant,
                    supplier_name="Ajuste de Inventario",
                    created_at__gte=today_start,
                    created_at__lt=today_end
                ).first()

                if not adj_order:
                    adj_order = InboundOrder(
                        supplier_name="Ajuste de Inventario",
                        invoice_number=f"ADJ-{datetime.now().strftime('%Y%m%d')}",
                        status="received",
                        date_received=datetime.now(),
                        notes="Orden automática para ajustes de inventario",
                        tenant=tenant,
                        created_at=datetime.now()
                    )
                    adj_order.save()

                # Create lot for added stock
                new_lot = Lot(
                    product=product,
                    order=adj_order,
                    tenant=tenant,
                    lot_code=lot_code,
                    quantity_initial=stock_adjustment_qty,
                    quantity_current=stock_adjustment_qty,
                    expiry_date=None,
                    created_at=datetime.now()
                )
                new_lot.save()

                reason_text = f' ({stock_adjustment_reason})' if stock_adjustment_reason else ''
                changes.append(f'stock +{stock_adjustment_qty} unidades{reason_text}')

            elif stock_adjustment_type == 'subtract':
                # Subtract stock: validate and deduct from lots (FIFO), create Wastage record
                current_stock = product.total_stock
                if stock_adjustment_qty > current_stock:
                    return jsonify({
                        'error': f'No se puede restar {stock_adjustment_qty} unidades. Stock disponible: {current_stock}'
                    }), 400

                # Deduct from lots using FIFO
                remaining_to_deduct = stock_adjustment_qty
                available_lots = sorted(
                    [l for l in product.lots if l.quantity_current > 0],
                    key=lambda x: x.created_at
                )

                for lot in available_lots:
                    if remaining_to_deduct <= 0:
                        break
                    deduct = min(lot.quantity_current, remaining_to_deduct)
                    lot.quantity_current -= deduct
                    remaining_to_deduct -= deduct
                    lot.save()

                # Create wastage record for the adjustment
                wastage_reason = stock_adjustment_reason or 'Ajuste de inventario'
                wastage = Wastage(
                    product=product,
                    quantity=stock_adjustment_qty,
                    reason=wastage_reason,
                    notes=f'Ajuste manual desde edición de producto por {current_user.full_name or current_user.username}',
                    tenant=tenant,
                    date_created=datetime.now()
                )
                wastage.save()

                reason_text = f' ({stock_adjustment_reason})' if stock_adjustment_reason else ''
                changes.append(f'stock -{stock_adjustment_qty} unidades{reason_text}')

        # Log activity
        if changes:
            ActivityLog.log(
                user=current_user,
                action='update',
                module='products',
                description=f'Actualizó producto "{product.name}": {", ".join(changes)}',
                target_id=id,
                target_type='Product',
                details={'changes': changes},
                request=request,
                tenant=tenant
            )

        return jsonify({'message': 'Producto actualizado'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/sales', methods=['GET'])
@login_required
def get_sales():
    tenant = g.current_tenant
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    date_filter = request.args.get('date')  # YYYY-MM-DD or YYYY-MM

    query = Sale.objects(tenant=tenant)

    if date_filter:
        # Check format length to decide day vs month
        if len(date_filter) == 10:  # YYYY-MM-DD
            start_dt = datetime.strptime(date_filter, '%Y-%m-%d')
            end_dt = start_dt + timedelta(days=1)
            query = query.filter(date_created__gte=start_dt, date_created__lt=end_dt)
        elif len(date_filter) == 7:  # YYYY-MM
            start_dt = datetime.strptime(date_filter, '%Y-%m')
            if start_dt.month == 12:
                end_dt = start_dt.replace(year=start_dt.year + 1, month=1)
            else:
                end_dt = start_dt.replace(month=start_dt.month + 1)
            query = query.filter(date_created__gte=start_dt, date_created__lt=end_dt)

    # Pagination
    total = query.count()
    sales = query.order_by('-date_created').skip((page - 1) * per_page).limit(per_page)

    results = []
    for s in sales:
        items = []
        total_sale = 0
        for item in s.items:
            subtotal = item.quantity * float(item.unit_price)
            total_sale += subtotal
            items.append({
                'product': item.product.name if item.product else 'N/A',
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'subtotal': subtotal
            })

        results.append({
            'id': str(s.id),
            'customer': s.customer_name,
            'address': s.address,
            'status': s.status,
            'sale_type': s.sale_type or 'con_despacho',
            'sales_channel': s.sales_channel or 'manual',  # NEW
            'delivery_status': s.delivery_status or 'pendiente',
            'payment_status': s.payment_status or 'pendiente',
            'items': items,
            'total': total_sale,
            'payment_method': s.payment_method,
            'date': s.date_created.strftime('%Y-%m-%d %H:%M')
        })

    return jsonify({
        'sales': results,
        'total': total,
        'pages': (total + per_page - 1) // per_page,
        'current_page': page
    })


@bp.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard_stats():
    tenant = g.current_tenant
    range_type = request.args.get('range', 'last_7')

    total_sales = Sale.objects(tenant=tenant).count()
    total_products = Product.objects(tenant=tenant).count()

    # Calculate total revenue
    revenue = 0
    for sale in Sale.objects(tenant=tenant):
        for item in sale.items:
            revenue += item.quantity * float(item.unit_price)

    recent_sales = Sale.objects(tenant=tenant).order_by('-date_created').limit(5)
    recent_sales_data = [{
        'id': str(s.id),
        'customer': s.customer_name,
        'status': s.status
    } for s in recent_sales]

    # Chart Data Logic
    end_date = utc_now().date()
    start_date = end_date - timedelta(days=6)
    group_by = 'day'

    if range_type == 'last_30':
        start_date = end_date - timedelta(days=29)
    elif range_type == 'this_month':
        start_date = end_date.replace(day=1)
    elif range_type == 'last_month':
        start_date = (end_date.replace(day=1) - relativedelta(months=1))
        end_date = end_date.replace(day=1) - timedelta(days=1)
    elif range_type == 'year':
        start_date = end_date.replace(month=1, day=1)
        group_by = 'month'
    elif range_type == 'last_6_months':
        start_date = (end_date.replace(day=1) - relativedelta(months=5))
        group_by = 'month'
    elif range_type == 'all_time':
        earliest_sale = Sale.objects(tenant=tenant).order_by('date_created').first()
        if earliest_sale:
            start_date = earliest_sale.date_created.date().replace(day=1)
        else:
            start_date = end_date.replace(day=1)
        group_by = 'month'
    elif range_type == 'specific_month':
        month_str = request.args.get('month')
        if month_str:
            try:
                start_date = datetime.strptime(month_str, '%Y-%m').date()
                next_month = start_date + relativedelta(months=1)
                end_date = next_month - timedelta(days=1)
            except ValueError:
                start_date = end_date.replace(day=1)
        else:
            start_date = end_date.replace(day=1)
        group_by = 'day'

    chart_labels = []
    chart_values = []
    chart_keys = []

    if group_by == 'day':
        delta = (end_date - start_date).days
        dates = [start_date + timedelta(days=i) for i in range(delta + 1)]

        for d in dates:
            daily_revenue = 0
            day_start = datetime.combine(d, datetime.min.time())
            day_end = datetime.combine(d + timedelta(days=1), datetime.min.time())

            for sale in Sale.objects(tenant=tenant, date_created__gte=day_start, date_created__lt=day_end):
                for item in sale.items:
                    daily_revenue += item.quantity * float(item.unit_price)

            chart_labels.append(d.strftime('%d/%m'))
            chart_values.append(daily_revenue)
            chart_keys.append(d.strftime('%Y-%m-%d'))

    elif group_by == 'month':
        curr = start_date
        while curr <= end_date:
            next_month = curr + relativedelta(months=1)
            month_start = datetime.combine(curr, datetime.min.time())
            month_end = datetime.combine(next_month, datetime.min.time())

            monthly_revenue = 0
            for sale in Sale.objects(tenant=tenant, date_created__gte=month_start, date_created__lt=month_end):
                for item in sale.items:
                    monthly_revenue += item.quantity * float(item.unit_price)

            chart_labels.append(curr.strftime('%B'))
            chart_values.append(monthly_revenue)
            chart_keys.append(curr.strftime('%Y-%m'))
            curr = next_month

    return jsonify({
        'total_sales': total_sales,
        'total_products': total_products,
        'total_revenue': revenue,
        'recent_sales': recent_sales_data,
        'chart_data': {
            'labels': chart_labels,
            'values': chart_values,
            'keys': chart_keys
        }
    })


@bp.route('/products/<id>', methods=['GET'])
@login_required
def get_product(id):
    tenant = g.current_tenant
    try:
        product = Product.objects.get(id=ObjectId(id), tenant=tenant)
    except DoesNotExist:
        return jsonify({'error': 'Producto no encontrado'}), 404

    # Get bundle components if this is a bundle
    bundle_components = []
    for bundle_rel in ProductBundle.objects(bundle=product):
        if bundle_rel.component:
            bundle_components.append({
                'id': str(bundle_rel.id),
                'component_id': str(bundle_rel.component.id),
                'product_name': bundle_rel.component.name,
                'quantity': bundle_rel.quantity
            })

    return jsonify({
        'id': str(product.id),
        'name': product.name,
        'sku': product.sku,
        'description': product.description,
        'category': product.category,
        'base_price': float(product.base_price) if product.base_price else 0,
        'critical_stock': product.critical_stock,
        'stock': product.total_stock,
        'bundle_components': bundle_components
    })


@bp.route('/sales/<id>', methods=['GET'])
@login_required
def get_sale(id):
    tenant = g.current_tenant
    try:
        sale = Sale.objects.get(id=ObjectId(id), tenant=tenant)
    except DoesNotExist:
        return jsonify({'error': 'Venta no encontrada'}), 404

    items = []
    total = 0
    for item in sale.items:
        subtotal = item.quantity * float(item.unit_price)
        total += subtotal
        items.append({
            'product': item.product.name if item.product else 'N/A',
            'quantity': item.quantity,
            'unit_price': float(item.unit_price),
            'subtotal': subtotal
        })

    # Obtener historial de pagos
    payments = Payment.objects(sale=sale).order_by('-date_created')
    payments_list = []
    for p in payments:
        payments_list.append({
            'id': str(p.id),
            'amount': float(p.amount),
            'payment_via': p.payment_via,
            'payment_reference': p.payment_reference or '',
            'notes': p.notes or '',
            'date_created': p.date_created.strftime('%Y-%m-%d %H:%M'),
            'created_by': p.created_by.full_name if p.created_by else 'Sistema'
        })

    return jsonify({
        'id': str(sale.id),
        'customer': sale.customer_name,
        'address': sale.address,
        'phone': sale.phone,

        # Tipo de venta
        'sale_type': sale.sale_type or 'con_despacho',
        'sales_channel': sale.sales_channel or 'manual',  # NEW

        # Delivery
        'delivery_status': sale.delivery_status or 'pendiente',
        'delivery_observations': sale.delivery_observations or '',
        'date_delivered': sale.date_delivered.strftime('%Y-%m-%d %H:%M') if sale.date_delivered else None,

        # Payment summary
        'payment_status': sale.payment_status or 'pendiente',
        'total': total,
        'total_paid': float(sale.total_paid),
        'balance_pending': float(sale.balance_pending),

        # Historial de pagos
        'payments': payments_list,

        # Items
        'items': items,

        # Legacy fields
        'status': sale.status,
        'payment_method': sale.payment_method,

        # Dates
        'date_created': sale.date_created.strftime('%Y-%m-%d %H:%M')
    })


@bp.route('/sales', methods=['POST'])
@login_required
@permission_required('sales', 'create')
def create_sale():
    tenant = g.current_tenant
    data = request.get_json()

    if not data or 'customer' not in data:
        return jsonify({'error': 'Faltan datos requeridos (customer)'}), 400

    # Track modified lots for rollback
    modified_lots = []  # List of (lot, original_quantity) tuples

    def rollback_stock():
        """Restore stock to all modified lots"""
        for lot, original_qty in modified_lots:
            lot.quantity_current = original_qty
            lot.save()

    try:
        # Determinar tipo de venta
        sale_type = data.get('sale_type', 'con_despacho')

        # Lógica automática según tipo de venta
        if sale_type == 'en_local':
            # Venta en local: automáticamente entregada
            delivery_status = 'entregado'
            date_delivered = utc_now()
        else:
            # Venta con despacho: pendiente por defecto
            delivery_status = data.get('delivery_status', 'pendiente')
            date_delivered = None

        new_sale = Sale(
            customer_name=data['customer'],
            address=data.get('address', ''),
            phone=data.get('phone', ''),
            sale_type=sale_type,
            sales_channel=data.get('sales_channel', 'manual'),  # NEW: track origin
            delivery_status=delivery_status,
            delivery_observations=data.get('delivery_observations', ''),
            date_delivered=date_delivered,
            payment_status='pendiente',
            # Legacy fields (for backward compatibility)
            payment_method=data.get('payment_method', 'Efectivo'),
            payment_confirmed=data.get('payment_confirmed', False),
            status='pending',
            tenant=tenant
        )
        new_sale.save()

        items_data = data.get('items', [])
        for item_data in items_data:
            product_id = item_data.get('product_id')
            quantity = int(item_data.get('quantity', 1))

            if not product_id:
                continue

            # Filter product by tenant to ensure valid access
            try:
                product = Product.objects.get(id=ObjectId(product_id), tenant=tenant)
            except DoesNotExist:
                continue

            # Validate stock
            if product.total_stock < quantity:
                rollback_stock()
                new_sale.delete()
                return jsonify({
                    'error': f'Stock insuficiente para {product.name}. Disponible: {product.total_stock}, Solicitado: {quantity}'
                }), 400

            # Deduct stock (FIFO)
            remaining_to_deduct = quantity
            available_lots = sorted(
                [l for l in product.lots if l.quantity_current > 0],
                key=lambda x: x.created_at
            )

            for lot in available_lots:
                if remaining_to_deduct <= 0:
                    break
                # Track original quantity before modification
                modified_lots.append((lot, lot.quantity_current))
                deduct = min(lot.quantity_current, remaining_to_deduct)
                lot.quantity_current -= deduct
                remaining_to_deduct -= deduct
                lot.save()

            if remaining_to_deduct > 0:
                rollback_stock()
                new_sale.delete()
                return jsonify({'error': f'Error de consistencia de inventario para {product.name}'}), 400

            # If this is a bundle product, also deduct stock from components
            bundle_components = ProductBundle.objects(bundle=product)
            for bundle_comp in bundle_components:
                if not bundle_comp.component:
                    continue

                component_product = bundle_comp.component

                # Calculate total quantity needed
                total_component_qty = bundle_comp.quantity * quantity

                # Check if component has enough stock
                if component_product.total_stock < total_component_qty:
                    rollback_stock()
                    new_sale.delete()
                    return jsonify({
                        'error': f'Stock insuficiente del componente "{component_product.name}" en el bundle "{product.name}". Disponible: {component_product.total_stock}, Necesario: {total_component_qty}'
                    }), 400

                # Deduct component stock
                remaining_component = total_component_qty
                available_component_lots = sorted(
                    [l for l in component_product.lots if l.quantity_current > 0],
                    key=lambda x: x.created_at
                )

                for lot in available_component_lots:
                    if remaining_component <= 0:
                        break
                    # Track original quantity before modification
                    modified_lots.append((lot, lot.quantity_current))
                    deduct = min(lot.quantity_current, remaining_component)
                    lot.quantity_current -= deduct
                    remaining_component -= deduct
                    lot.save()

                if remaining_component > 0:
                    rollback_stock()
                    new_sale.delete()
                    return jsonify({
                        'error': f'Error de consistencia de inventario para componente {component_product.name}'
                    }), 400

            sale_item = SaleItem(
                sale=new_sale,
                product=product,
                quantity=quantity,
                unit_price=product.base_price or 0
            )
            sale_item.save()

        # Calculate total for logging
        total = sum(item.quantity * float(item.unit_price) for item in new_sale.items)
        items_count = new_sale.items.count()

        # Registrar pago inicial si existe
        if 'initial_payment' in data and data['initial_payment'].get('amount', 0) > 0:
            initial_payment = data['initial_payment']
            payment_amount = float(initial_payment['amount'])

            # Validar que no exceda el total
            if payment_amount > total:
                rollback_stock()
                new_sale.delete()
                return jsonify({
                    'error': f'El pago inicial (${payment_amount:,.0f}) no puede ser mayor al total de la venta (${total:,.0f})'
                }), 400

            # Crear registro de pago
            payment = Payment(
                sale=new_sale,
                tenant=tenant,
                amount=payment_amount,
                payment_via=initial_payment.get('payment_via', 'efectivo'),
                payment_reference=initial_payment.get('payment_reference', ''),
                notes='Pago inicial',
                created_by=current_user
            )
            payment.save()

            # Actualizar payment_status
            new_sale.payment_status = new_sale.computed_payment_status
            new_sale.save()

        # Tarea 4: Ventas en local con pago completo automático
        # Si es venta en local y se marcó auto_complete_payment (sin pago inicial explícito)
        elif sale_type == 'en_local' and data.get('auto_complete_payment'):
            # Crear pago por el total
            payment = Payment(
                sale=new_sale,
                tenant=tenant,
                amount=total,
                payment_via=data.get('payment_via', 'efectivo'),
                payment_reference=data.get('payment_reference', ''),
                notes='Pago completo en local',
                created_by=current_user
            )
            payment.save()
            new_sale.payment_status = 'pagado'
            new_sale.save()

        # Log activity
        ActivityLog.log(
            user=current_user,
            action='create',
            module='sales',
            description=f'Creó venta para "{data["customer"]}" - {items_count} items, total ${total:,.0f}',
            target_id=str(new_sale.id),
            target_type='Sale',
            request=request,
            tenant=tenant
        )

        return jsonify({'message': 'Venta creada', 'id': str(new_sale.id)}), 201
    except Exception as e:
        # Rollback stock on any unexpected error
        rollback_stock()
        if 'new_sale' in locals() and new_sale.id:
            try:
                new_sale.delete()
            except Exception as del_err:
                current_app.logger.error(f'Error eliminando venta fallida: {del_err}')
        return jsonify({'error': str(e)}), 500


@bp.route('/sales/<id>', methods=['PUT'])
@login_required
@permission_required('sales', 'edit')
def update_sale(id):
    """Actualizar estado de una venta (incluyendo cancelación)"""
    tenant = g.current_tenant
    try:
        sale = Sale.objects.get(id=ObjectId(id), tenant=tenant)
    except DoesNotExist:
        return jsonify({'error': 'Venta no encontrada'}), 404

    data = request.get_json()
    changes = []

    try:
        # Validación: Ventas en local no pueden cambiar estado de entrega
        if sale.sale_type == 'en_local' and 'delivery_status' in data:
            if data['delivery_status'] != 'entregado':
                return jsonify({'error': 'Las ventas en local deben estar siempre entregadas'}), 400

        # Actualizar delivery_status
        if 'delivery_status' in data and data['delivery_status'] != sale.delivery_status:
            old_delivery = sale.delivery_status
            new_delivery = data['delivery_status']

            # Auto-set date_delivered cuando se marca como entregado o con observaciones
            if new_delivery in ['entregado', 'con_observaciones'] and not sale.date_delivered:
                sale.date_delivered = utc_now()

            changes.append(f'estado entrega: {old_delivery} → {new_delivery}')
            sale.delivery_status = new_delivery

            # Sincronizar con status legacy
            sale.status = sale.computed_status

        # Actualizar delivery_observations
        if 'delivery_observations' in data:
            old_obs = sale.delivery_observations or ''
            new_obs = data['delivery_observations']
            if new_obs != old_obs:
                changes.append('observaciones actualizadas')
                sale.delivery_observations = new_obs

        # Legacy fields (mantener compatibilidad)
        if 'status' in data and data['status'] != sale.status:
            valid_statuses = ['pending', 'assigned', 'in_transit', 'delivered', 'cancelled']
            if data['status'] not in valid_statuses:
                return jsonify({'error': f'Estado inválido. Estados válidos: {valid_statuses}'}), 400
            changes.append(f'estado: {sale.status} → {data["status"]}')
            sale.status = data['status']

        if 'payment_confirmed' in data:
            if sale.payment_confirmed != data['payment_confirmed']:
                changes.append(f'pago confirmado: {sale.payment_confirmed} → {data["payment_confirmed"]}')
            sale.payment_confirmed = data['payment_confirmed']

        sale.save()

        # Log activity
        if changes:
            action = 'cancel' if data.get('status') == 'cancelled' else 'update'
            ActivityLog.log(
                user=current_user,
                action=action,
                module='sales',
                description=f'{"Canceló" if action == "cancel" else "Actualizó"} venta de "{sale.customer_name}": {", ".join(changes)}',
                target_id=id,
                target_type='Sale',
                details={'changes': changes, 'customer': sale.customer_name},
                request=request,
                tenant=tenant
            )

        return jsonify({'success': True, 'message': 'Venta actualizada'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/sales/<id>/payments', methods=['POST'])
@login_required
@permission_required('sales', 'edit')
def add_payment(id):
    """Registra un nuevo pago/abono para una venta"""
    tenant = g.current_tenant
    data = request.get_json()

    # Validar venta existe
    try:
        sale = Sale.objects.get(id=ObjectId(id), tenant=tenant)
    except DoesNotExist:
        return jsonify({'error': 'Venta no encontrada'}), 404

    # Validar monto
    amount = data.get('amount')
    if not amount or amount <= 0:
        return jsonify({'error': 'Monto inválido'}), 400

    # Validar que no exceda el total
    total_paid = sale.total_paid + amount
    if total_paid > sale.total_amount:
        return jsonify({
            'error': f'El monto total de pagos (${total_paid:,.0f}) excede el total de la venta (${sale.total_amount:,.0f})'
        }), 400

    try:
        # Crear Payment
        payment = Payment(
            sale=sale,
            tenant=tenant,
            amount=amount,
            payment_via=data.get('payment_via', 'efectivo'),
            payment_reference=data.get('payment_reference', ''),
            notes=data.get('notes', ''),
            created_by=current_user
        )
        payment.save()

        # Actualizar payment_status en Sale
        sale.payment_status = sale.computed_payment_status
        sale.save()

        # Log activity
        ActivityLog.log(
            user=current_user,
            action='create',
            module='sales',
            description=f'Registró pago de ${amount:,.0f} ({data.get("payment_via")}) para venta de "{sale.customer_name}"',
            target_id=str(payment.id),
            target_type='Payment',
            details={
                'sale_id': str(sale.id),
                'amount': float(amount),
                'via': data.get('payment_via'),
                'balance_pending': float(sale.balance_pending)
            },
            request=request,
            tenant=tenant
        )

        return jsonify({
            'success': True,
            'message': 'Pago registrado',
            'payment_id': str(payment.id),
            'balance_pending': float(sale.balance_pending),
            'payment_status': sale.payment_status
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/sales/<id>/payments', methods=['GET'])
@login_required
def get_sale_payments(id):
    """Obtiene historial de pagos de una venta"""
    tenant = g.current_tenant

    try:
        sale = Sale.objects.get(id=ObjectId(id), tenant=tenant)
    except DoesNotExist:
        return jsonify({'error': 'Venta no encontrada'}), 404

    payments = Payment.objects(sale=sale).order_by('-date_created')

    return jsonify({
        'success': True,
        'payments': [{
            'id': str(p.id),
            'amount': float(p.amount),
            'payment_via': p.payment_via,
            'payment_reference': p.payment_reference or '',
            'notes': p.notes or '',
            'date_created': p.date_created.strftime('%Y-%m-%d %H:%M'),
            'created_by': p.created_by.full_name if p.created_by else 'Sistema'
        } for p in payments],
        'total_paid': float(sale.total_paid),
        'balance_pending': float(sale.balance_pending)
    })


# Fleet Management APIs
@bp.route('/fleet/vehicles', methods=['GET'])
def get_fleet_vehicles():
    tenant = g.current_tenant
    trucks = Truck.objects(tenant=tenant)

    results = []
    for truck in trucks:
        results.append({
            'id': str(truck.id),
            'license_plate': truck.license_plate,
            'make_model': truck.make_model,
            'capacity_kg': truck.capacity_kg,
            'status': truck.status,
            'current_lat': truck.current_lat,
            'current_lng': truck.current_lng,
            'odometer_km': truck.odometer_km,
            'last_update': truck.last_update.isoformat() if truck.last_update else None
        })
    return jsonify(results)


@bp.route('/fleet/vehicles/<id>', methods=['GET'])
def get_fleet_vehicle(id):
    tenant = g.current_tenant
    try:
        truck = Truck.objects.get(id=ObjectId(id), tenant=tenant)
    except DoesNotExist:
        return jsonify({'error': 'Vehículo no encontrado'}), 404

    # Get upcoming maintenances
    upcoming = VehicleMaintenance.objects(
        truck=truck,
        status='pending'
    ).order_by('scheduled_date').limit(3)

    return jsonify({
        'id': str(truck.id),
        'license_plate': truck.license_plate,
        'make_model': truck.make_model,
        'capacity_kg': truck.capacity_kg,
        'status': truck.status,
        'current_lat': truck.current_lat,
        'current_lng': truck.current_lng,
        'odometer_km': truck.odometer_km,
        'last_maintenance_date': truck.last_maintenance_date.isoformat() if truck.last_maintenance_date else None,
        'next_maintenance_km': truck.next_maintenance_km,
        'last_update': truck.last_update.isoformat() if truck.last_update else None,
        'upcoming_maintenances': [{
            'type': m.maintenance_type,
            'scheduled_date': m.scheduled_date.isoformat() if m.scheduled_date else None,
            'odometer': m.odometer_reading
        } for m in upcoming]
    })


# ============================================
# WEBHOOK API - External Integrations
# ============================================
import os

def validate_webhook_token():
    """Validate webhook token from header"""
    token = request.headers.get('X-Webhook-Token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    expected = os.environ.get('SIPUD_WEBHOOK_TOKEN', '')
    if not expected or not token:
        return False
    return token == expected


def get_system_user(tenant):
    """Get or create system user for webhook operations"""
    system_user = User.objects(username='sistema', tenant=tenant).first()
    if not system_user:
        # Use first admin as fallback
        system_user = User.objects(role='admin', tenant=tenant).first()
    return system_user


@bp.route('/sales/webhook', methods=['POST'])
@limiter.limit("10 per minute")
@limiter.limit("100 per hour")
def webhook_create_sale():
    """
    Webhook endpoint for external integrations (ManyChat, Google Sheets, etc.)
    
    Rate limits: 10/min, 100/hour per IP
    
    Headers:
        X-Webhook-Token: <token>  OR  Authorization: Bearer <token>
    
    Body:
        {
            "customer": "Juan Pérez",
            "phone": "+56912345678",
            "address": "Av. Principal 123",
            "items": [
                {"sku": "ARROZ-5KG", "quantity": 2},
                {"name": "Aceite Maravilla 1L", "quantity": 1}
            ],
            "notes": "Entregar después de las 14:00"
        }
    
    Returns:
        201: Sale created successfully
        400: Validation error (missing data, insufficient stock)
        401: Invalid or missing token
        404: Product not found
        429: Rate limit exceeded
    """
    # Validate token
    if not validate_webhook_token():
        return jsonify({'error': 'Token inválido o no proporcionado'}), 401
    
    tenant = g.current_tenant
    data = request.get_json()
    
    # Basic validation
    if not data:
        return jsonify({'error': 'Body JSON requerido'}), 400
    
    customer_name = data.get('customer', '').strip()
    if not customer_name:
        return jsonify({'error': 'Campo "customer" es requerido'}), 400
    
    items_data = data.get('items', [])
    if not items_data:
        return jsonify({'error': 'Se requiere al menos un item'}), 400
    
    # Get system user for logging
    system_user = get_system_user(tenant)
    if not system_user:
        return jsonify({'error': 'No hay usuario administrador configurado'}), 500
    
    # Track modified lots for rollback
    modified_lots = []
    
    def rollback_stock():
        for lot, original_qty in modified_lots:
            lot.quantity_current = original_qty
            lot.save()
    
    try:
        # Create sale
        new_sale = Sale(
            customer_name=customer_name,
            address=data.get('address', ''),
            phone=data.get('phone', ''),
            sale_type='con_despacho',  # Webhook sales are always delivery
            sales_channel='whatsapp',  # Mark as WhatsApp origin
            delivery_status='pendiente',
            payment_status='pendiente',
            status='pending',
            tenant=tenant
        )
        new_sale.save()
        
        processed_items = []
        errors = []
        
        for item_data in items_data:
            sku = item_data.get('sku', '').strip()
            name = item_data.get('name', '').strip()
            quantity = int(item_data.get('quantity', 1))
            
            if quantity <= 0:
                errors.append(f'Cantidad inválida para item: {sku or name}')
                continue
            
            # Find product by SKU or name
            product = None
            if sku:
                product = Product.objects(sku__iexact=sku, tenant=tenant).first()
            if not product and name:
                product = Product.objects(name__iexact=name, tenant=tenant).first()
                if not product:
                    # Try partial match
                    product = Product.objects(name__icontains=name, tenant=tenant).first()
            
            if not product:
                errors.append(f'Producto no encontrado: {sku or name}')
                continue
            
            # Validate stock
            if product.total_stock < quantity:
                errors.append(f'Stock insuficiente para {product.name}: disponible {product.total_stock}, solicitado {quantity}')
                continue
            
            # Deduct stock (FIFO)
            remaining = quantity
            available_lots = sorted(
                [l for l in product.lots if l.quantity_current > 0],
                key=lambda x: x.created_at
            )
            
            for lot in available_lots:
                if remaining <= 0:
                    break
                modified_lots.append((lot, lot.quantity_current))
                deduct = min(lot.quantity_current, remaining)
                lot.quantity_current -= deduct
                remaining -= deduct
                lot.save()
            
            if remaining > 0:
                errors.append(f'Error de consistencia de inventario para {product.name}')
                continue
            
            # Create sale item
            sale_item = SaleItem(
                sale=new_sale,
                product=product,
                quantity=quantity,
                unit_price=product.base_price or 0
            )
            sale_item.save()
            
            processed_items.append({
                'product': product.name,
                'sku': product.sku,
                'quantity': quantity,
                'unit_price': float(product.base_price or 0)
            })
        
        # If no items were processed successfully, rollback and delete sale
        if not processed_items:
            rollback_stock()
            new_sale.delete()
            return jsonify({
                'error': 'No se pudo procesar ningún item',
                'details': errors
            }), 400
        
        # Calculate total
        total = sum(item['quantity'] * item['unit_price'] for item in processed_items)
        
        # Log activity
        ActivityLog.log(
            user=system_user,
            action='create',
            module='sales',
            description=f'[Webhook] Venta para "{customer_name}" - {len(processed_items)} items, total ${total:,.0f}',
            target_id=str(new_sale.id),
            target_type='Sale',
            details={
                'source': 'webhook',
                'channel': 'whatsapp',
                'items': processed_items,
                'errors': errors if errors else None
            },
            request=request,
            tenant=tenant
        )
        
        response = {
            'success': True,
            'message': 'Venta creada exitosamente',
            'sale_id': str(new_sale.id),
            'customer': customer_name,
            'total': total,
            'items_processed': len(processed_items),
            'items': processed_items
        }
        
        # Include warnings if some items failed
        if errors:
            response['warnings'] = errors
        
        return jsonify(response), 201
        
    except Exception as e:
        rollback_stock()
        if 'new_sale' in locals() and new_sale.id:
            try:
                new_sale.delete()
            except Exception as del_err:
                current_app.logger.error(f'Error eliminando venta webhook fallida: {del_err}')
        return jsonify({'error': f'Error interno: {str(e)}'}), 500


@bp.route('/sales/webhook/test', methods=['GET'])
@limiter.limit("30 per minute")
def webhook_test():
    """Test endpoint to verify webhook is accessible (no auth required)"""
    return jsonify({
        'status': 'ok',
        'message': 'Webhook endpoint disponible',
        'usage': 'POST /api/sales/webhook con header X-Webhook-Token',
        'rate_limits': '10/min, 100/hour'
    })
