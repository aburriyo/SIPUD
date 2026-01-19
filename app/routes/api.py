from flask import Blueprint, jsonify, request, g
from app.models import Product, Sale, SaleItem, Lot, InboundOrder, ProductBundle, Truck, VehicleMaintenance
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from bson import ObjectId
from mongoengine import DoesNotExist

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/products', methods=['GET'])
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

        return jsonify({'message': 'Producto creado', 'id': str(new_product.id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/products/<id>', methods=['DELETE'])
def delete_product(id):
    tenant = g.current_tenant
    try:
        product = Product.objects.get(id=ObjectId(id), tenant=tenant)
    except DoesNotExist:
        return jsonify({'error': 'Producto no encontrado'}), 404

    try:
        # Delete associated lots first
        Lot.objects(product=product).delete()

        # Delete bundle relationships if this product is part of any bundles
        ProductBundle.objects(component=product).delete()
        ProductBundle.objects(bundle=product).delete()

        # Delete the product
        product.delete()
        return jsonify({'message': 'Producto eliminado correctamente'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/products/<id>', methods=['PUT'])
def update_product(id):
    tenant = g.current_tenant
    try:
        product = Product.objects.get(id=ObjectId(id), tenant=tenant)
    except DoesNotExist:
        return jsonify({'error': 'Producto no encontrado'}), 404

    data = request.get_json()

    try:
        if 'name' in data:
            product.name = data['name']
        if 'sku' in data:
            # Check unique SKU if changing
            if data['sku'] != product.sku:
                existing = Product.objects(sku=data['sku'], tenant=tenant).first()
                if existing:
                    return jsonify({'error': 'El SKU ya existe'}), 400
            product.sku = data['sku']
        if 'description' in data:
            product.description = data['description']
        if 'category' in data:
            product.category = data['category']
        if 'base_price' in data:
            product.base_price = data['base_price']
        if 'critical_stock' in data:
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

        product.save()
        return jsonify({'message': 'Producto actualizado'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/sales', methods=['GET'])
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
    end_date = datetime.utcnow().date()
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
    return jsonify({
        'id': str(sale.id),
        'customer': sale.customer_name,
        'address': sale.address,
        'phone': sale.phone,
        'status': sale.status,
        'payment_method': sale.payment_method,
        'items': items,
        'total': total,
        'date': sale.date_created.strftime('%Y-%m-%d %H:%M')
    })


@bp.route('/sales', methods=['POST'])
def create_sale():
    tenant = g.current_tenant
    data = request.get_json()

    if not data or 'customer' not in data:
        return jsonify({'error': 'Faltan datos requeridos (customer)'}), 400

    try:
        new_sale = Sale(
            customer_name=data['customer'],
            address=data.get('address', ''),
            payment_method=data.get('payment_method', 'Efectivo'),
            payment_confirmed=data.get('payment_confirmed', False),
            delivery_status=data.get('delivery_status', 'pending'),
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
                deduct = min(lot.quantity_current, remaining_to_deduct)
                lot.quantity_current -= deduct
                remaining_to_deduct -= deduct
                lot.save()

            if remaining_to_deduct > 0:
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
                    deduct = min(lot.quantity_current, remaining_component)
                    lot.quantity_current -= deduct
                    remaining_component -= deduct
                    lot.save()

                if remaining_component > 0:
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

        return jsonify({'message': 'Venta creada', 'id': str(new_sale.id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
