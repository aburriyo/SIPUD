from flask import Blueprint, jsonify, request
from app.models import Product, Sale, SaleItem, Lot, InboundOrder, db
from datetime import datetime

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/products', methods=['GET'])
def get_products():
    from flask import g
    tenant_id = g.current_tenant.id if g.current_tenant else None
    products = Product.query.filter_by(tenant_id=tenant_id).all()
    results = []
    for p in products:
        results.append({
            'id': p.id,
            'name': p.name,
            'sku': p.sku,
            'description': p.description,
            'category': p.category,
            'base_price': p.base_price,
            'critical_stock': p.critical_stock,
            'stock': p.total_stock
        })
    return jsonify(results)

@bp.route('/products', methods=['POST'])
def create_product():
    from flask import g
    data = request.get_json()
    tenant_id = g.current_tenant.id if g.current_tenant else None
    
    # Basic validation
    if not data or 'name' not in data or 'sku' not in data:
        return jsonify({'error': 'Faltan datos requeridos (name, sku)'}), 400
        
    # Check if SKU exists within tenant
    if Product.query.filter_by(sku=data['sku'], tenant_id=tenant_id).first():
         return jsonify({'error': 'El SKU ya existe en esta organización'}), 400
    
    try:
        new_product = Product(
            name=data['name'],
            sku=data['sku'],
            description=data.get('description'),
            category=data.get('category', 'Otros'),
            base_price=data.get('base_price', 0),
            critical_stock=data.get('critical_stock', 10),
            tenant_id=tenant_id
        )
        db.session.add(new_product)
        db.session.flush()  # Get the ID before committing
        
        # Handle bundle components
        from app.models import ProductBundle
        if 'bundle_components' in data and data['bundle_components']:
            for component in data['bundle_components']:
                bundle_item = ProductBundle(
                    bundle_id=new_product.id,
                    component_id=component['component_id'],
                    quantity=component['quantity'],
                    tenant_id=tenant_id
                )
                db.session.add(bundle_item)
        
        db.session.commit()
        return jsonify({'message': 'Producto creado', 'id': new_product.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    from flask import g
    tenant_id = g.current_tenant.id if g.current_tenant else None
    product = Product.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    
    try:
        # Delete associated lots first
        for lot in product.lots:
            db.session.delete(lot)
        
        # Delete bundle relationships if this product is part of any bundles
        from app.models import ProductBundle
        ProductBundle.query.filter_by(component_id=product.id).delete()
        ProductBundle.query.filter_by(bundle_id=product.id).delete()
        
        # Delete the product
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Producto eliminado correctamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    from flask import g
    tenant_id = g.current_tenant.id if g.current_tenant else None
    product = Product.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    data = request.get_json()
    
    try:
        if 'name' in data:
            product.name = data['name']
        if 'sku' in data:
            # Check unique SKU if changing
            if data['sku'] != product.sku and Product.query.filter_by(sku=data['sku'], tenant_id=tenant_id).first():
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
            from app.models import ProductBundle
            # Delete existing components
            ProductBundle.query.filter_by(bundle_id=product.id).delete()
            # Add new components
            for component in data['bundle_components']:
                bundle_item = ProductBundle(
                    bundle_id=product.id,
                    component_id=component['component_id'],
                    quantity=component['quantity'],
                    tenant_id=tenant_id
                )
                db.session.add(bundle_item)
            
        db.session.commit()
        return jsonify({'message': 'Producto actualizado'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/sales', methods=['GET'])
def get_sales():
    from flask import g
    from datetime import datetime as dt
    import sqlalchemy as sa
    
    tenant_id = g.current_tenant.id if g.current_tenant else None
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    date_filter = request.args.get('date') # YYYY-MM-DD or YYYY-MM
    
    query = Sale.query.filter_by(tenant_id=tenant_id)
    
    if date_filter:
        # Check format length to decide day vs month
        if len(date_filter) == 10: # YYYY-MM-DD
            query = query.filter(db.func.date(Sale.date_created) == date_filter)
        elif len(date_filter) == 7: # YYYY-MM
            start_dt = dt.strptime(date_filter, '%Y-%m')
            # End of month calc
            if start_dt.month == 12:
                end_dt = start_dt.replace(year=start_dt.year+1, month=1)
            else:
                end_dt = start_dt.replace(month=start_dt.month+1)
            query = query.filter(Sale.date_created >= start_dt)\
                         .filter(Sale.date_created < end_dt)
    
    pagination = query.order_by(Sale.date_created.desc()).paginate(page=page, per_page=per_page, error_out=False)
    sales = pagination.items
    
    results = []
    for s in sales:
        items = []
        total = 0
        for item in s.items:
            subtotal = item.quantity * item.unit_price
            total += subtotal
            items.append({
                'product': item.product.name,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'subtotal': subtotal
            })
            
        results.append({
            'id': s.id,
            'customer': s.customer_name,
            'address': s.address,
            'status': s.status,
            'items': items,
            'total': total,
            'payment_method': s.payment_method,
            'date': s.date_created.strftime('%Y-%m-%d %H:%M')
        })
        
    return jsonify({
        'sales': results,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@bp.route('/dashboard', methods=['GET'])
def get_dashboard_stats():
    from flask import g
    from datetime import timedelta
    from dateutil.relativedelta import relativedelta
    import sqlalchemy as sa
    
    tenant_id = g.current_tenant.id if g.current_tenant else None
    range_type = request.args.get('range', 'last_7') # last_7, last_30, this_month, last_month, year
    
    total_sales = Sale.query.filter_by(tenant_id=tenant_id).count()
    total_products = Product.query.filter_by(tenant_id=tenant_id).count()
    
    # Calculate total revenue
    revenue = db.session.query(db.func.sum(SaleItem.quantity * SaleItem.unit_price))\
        .join(SaleItem.sale).filter(Sale.tenant_id == tenant_id).scalar() or 0
    
    recent_sales = Sale.query.filter_by(tenant_id=tenant_id).order_by(Sale.date_created.desc()).limit(5).all()
    recent_sales_data = [{
        'id': s.id, 
        'customer': s.customer_name, 
        'status': s.status
    } for s in recent_sales]

    # Chart Data Logic
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=6)
    group_by = 'day' # day, month
    
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
        # Find earliest sale
        earliest_sale = Sale.query.filter_by(tenant_id=tenant_id).order_by(Sale.date_created.asc()).first()
        if earliest_sale:
            start_date = earliest_sale.date_created.date().replace(day=1)
        else:
            start_date = end_date.replace(day=1)
        group_by = 'month'
    elif range_type == 'specific_month':
        month_str = request.args.get('month') # YYYY-MM
        if month_str:
            try:
                start_date = datetime.strptime(month_str, '%Y-%m').date()
                # Calculate end of month
                next_month = start_date + relativedelta(months=1)
                end_date = next_month - timedelta(days=1)
            except ValueError:
                # Fallback to this month if invalid
                start_date = end_date.replace(day=1)
        else:
             start_date = end_date.replace(day=1)
        group_by = 'day'
        
    chart_labels = []
    chart_values = []
    chart_keys = [] # Store raw filter values (YYYY-MM-DD or YYYY-MM)
    
    if group_by == 'day':
        # Generate all dates in range
        delta = (end_date - start_date).days
        dates = [start_date + timedelta(days=i) for i in range(delta + 1)]
        
        for d in dates:
            daily_revenue = db.session.query(db.func.sum(SaleItem.quantity * SaleItem.unit_price))\
                .join(SaleItem.sale)\
                .filter(Sale.tenant_id == tenant_id)\
                .filter(db.func.date(Sale.date_created) == d.strftime('%Y-%m-%d'))\
                .scalar() or 0
            
            # Format label: 'DD/MM' (Day/Month without year generally, or full date)
            # User asked: "implementar la fecha con el mes, sin el día" -> This might mean Month Name?
            # Or "if exact date not known". But here we have exact dates.
            # Let's use 'DD/MM' for daily.
            chart_labels.append(d.strftime('%d/%m')) 
            chart_values.append(daily_revenue)
            chart_keys.append(d.strftime('%Y-%m-%d'))
            
    elif group_by == 'month':
        # Aggregate by month
        # Iterate from start_date to end_date by month
        curr = start_date
        while curr <= end_date:
            next_month = curr + relativedelta(months=1)
            limit = min(next_month, end_date + timedelta(days=1)) # Upper bound exclusive
            
            # Sum for this month
            monthly_revenue = db.session.query(db.func.sum(SaleItem.quantity * SaleItem.unit_price))\
                .join(SaleItem.sale)\
                .filter(Sale.tenant_id == tenant_id)\
                .filter(Sale.date_created >= curr)\
                .filter(Sale.date_created < next_month)\
                .scalar() or 0
                
            chart_labels.append(curr.strftime('%B')) # Full Month Name
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

@bp.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    from flask import g
    from app.models import ProductBundle
    tenant_id = g.current_tenant.id if g.current_tenant else None
    product = Product.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    
    # Get bundle components if this is a bundle
    bundle_components = []
    for bundle_rel in ProductBundle.query.filter_by(bundle_id=product.id).all():
        component = Product.query.get(bundle_rel.component_id)
        if component:
            bundle_components.append({
                'id': bundle_rel.id,
                'component_id': component.id,
                'product_name': component.name,
                'quantity': bundle_rel.quantity
            })
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'sku': product.sku,
        'description': product.description,
        'category': product.category,
        'base_price': product.base_price,
        'critical_stock': product.critical_stock,
        'stock': product.total_stock,
        'bundle_components': bundle_components
    })

@bp.route('/sales/<int:id>', methods=['GET'])
def get_sale(id):
    from flask import g
    tenant_id = g.current_tenant.id if g.current_tenant else None
    sale = Sale.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    items = []
    total = 0
    for item in sale.items:
        subtotal = item.quantity * item.unit_price
        total += subtotal
        items.append({
            'product': item.product.name,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'subtotal': subtotal
        })
    return jsonify({
        'id': sale.id,
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
    from flask import g
    tenant_id = g.current_tenant.id if g.current_tenant else None
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
            tenant_id=tenant_id
        )
        db.session.add(new_sale)
        db.session.flush() # Get ID
        
        items_data = data.get('items', [])
        for item_data in items_data:
            product_id = item_data.get('product_id')
            quantity = int(item_data.get('quantity', 1))
            
            if not product_id:
                continue
                
            # Filter product by tenant to ensure valid access
            product = Product.query.filter_by(id=product_id, tenant_id=tenant_id).first()
            if not product:
                continue
            
            # Validar stock (Assuming we updated this earlier, re-applying with fix if needed, otherwise simplified here but safer to include stock check logic if I see it in original)
            # Checking original content... the original had stock check. I must preserve it.
            
            if product.total_stock < quantity:
                raise Exception(f'Stock insuficiente para {product.name}. Disponible: {product.total_stock}, Solicitado: {quantity}')

            # Deduct stock
            remaining_to_deduct = quantity
            available_lots = sorted([l for l in product.lots if l.quantity_current > 0], key=lambda x: x.created_at)
            
            for lot in available_lots:
                if remaining_to_deduct <= 0:
                    break
                deduct = min(lot.quantity_current, remaining_to_deduct)
                lot.quantity_current -= deduct
                remaining_to_deduct -= deduct
                db.session.add(lot)
            
            if remaining_to_deduct > 0:
                 raise Exception(f'Error de consistencia de inventario para {product.name}')

            # If this is a bundle product, also deduct stock from components
            from app.models import ProductBundle
            bundle_components = ProductBundle.query.filter_by(bundle_id=product.id).all()
            if bundle_components:
                for bundle_comp in bundle_components:
                    component_product = Product.query.get(bundle_comp.component_id)
                    if not component_product:
                        continue
                    
                    # Calculate total quantity needed (bundle quantity * component quantity * sale quantity)
                    total_component_qty = bundle_comp.quantity * quantity
                    
                    # Check if component has enough stock
                    if component_product.total_stock < total_component_qty:
                        raise Exception(f'Stock insuficiente del componente "{component_product.name}" en el bundle "{product.name}". Disponible: {component_product.total_stock}, Necesario: {total_component_qty}')
                    
                    # Deduct component stock
                    remaining_component = total_component_qty
                    available_component_lots = sorted([l for l in component_product.lots if l.quantity_current > 0], key=lambda x: x.created_at)
                    
                    for lot in available_component_lots:
                        if remaining_component <= 0:
                            break
                        deduct = min(lot.quantity_current, remaining_component)
                        lot.quantity_current -= deduct
                        remaining_component -= deduct
                        db.session.add(lot)
                    
                    if remaining_component > 0:
                        raise Exception(f'Error de consistencia de inventario para componente {component_product.name}')

            sale_item = SaleItem(
                sale_id=new_sale.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.base_price 
            )
            db.session.add(sale_item)
            
        db.session.commit()
        return jsonify({'message': 'Venta creada', 'id': new_sale.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Fleet Management APIs
@bp.route('/fleet/vehicles', methods=['GET'])
def get_fleet_vehicles():
    from flask import g
    from app.models import Truck
    tenant_id = g.current_tenant.id if g.current_tenant else None
    trucks = Truck.query.filter_by(tenant_id=tenant_id).all()
    
    results = []
    for truck in trucks:
        results.append({
            'id': truck.id,
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

@bp.route('/fleet/vehicles/<int:id>', methods=['GET'])
def get_fleet_vehicle(id):
    from flask import g
    from app.models import Truck, VehicleMaintenance
    tenant_id = g.current_tenant.id if g.current_tenant else None
    truck = Truck.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    
    # Get upcoming maintenances
    upcoming = VehicleMaintenance.query.filter_by(
        truck_id=truck.id,
        status='pending'
    ).order_by(VehicleMaintenance.scheduled_date).limit(3).all()
    
    return jsonify({
        'id': truck.id,
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
            'scheduled_date': m.scheduled_date.isoformat(),
            'odometer': m.odometer_reading
        } for m in upcoming]
    })
