import os
from flask import Blueprint, jsonify, request, g, render_template, send_file
from flask_login import login_required, current_user
from app.models import ShopifyCustomer, ShopifyOrder, ShopifyOrderLineItem, Tenant
from datetime import datetime, timedelta
from bson import ObjectId
from functools import wraps
import requests
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

bp = Blueprint('customers', __name__, url_prefix='/customers')

# Shopify API Configuration
SHOPIFY_STORE = os.environ.get('SHOPIFY_STORE_DOMAIN', '')
SHOPIFY_TOKEN = os.environ.get('SHOPIFY_ACCESS_TOKEN', '')
SHOPIFY_API_VERSION = '2026-01'
SHOPIFY_BASE_URL = f'https://{SHOPIFY_STORE}/admin/api/{SHOPIFY_API_VERSION}'


def permission_required(module, action='view'):
    """Decorator to check permissions before accessing a route"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'No autenticado'}), 401
            if not current_user.has_permission(module, action):
                return jsonify({'error': 'No tienes permisos para esta acción'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@bp.route('/')
@login_required
def customers_view():
    """Render customers view page"""
    if not current_user.has_permission('customers', 'view'):
        return "No tienes permisos para ver esta página", 403
    return render_template('customers.html')


@bp.route('/api/customers')
@login_required
@permission_required('customers', 'view')
def get_customers():
    """Get customers list with search and pagination"""
    tenant = g.current_tenant
    
    # Get query parameters
    search = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    
    # Build query
    if search:
        customers = ShopifyCustomer.objects(
            tenant=tenant
        ).filter(
            __raw__={'$or': [
                {'name': {'$regex': search, '$options': 'i'}},
                {'email': {'$regex': search, '$options': 'i'}},
                {'phone': {'$regex': search, '$options': 'i'}},
            ]}
        ).order_by('-total_spent')
    else:
        customers = ShopifyCustomer.objects(tenant=tenant).order_by('-total_spent')
    
    # Pagination
    total = customers.count()
    customers = customers.skip((page - 1) * per_page).limit(per_page)
    
    # Format results
    results = []
    for c in customers:
        results.append({
            'id': str(c.id),
            'name': c.name or 'Sin nombre',
            'email': c.email or '',
            'phone': c.phone or '',
            'city': c.address_city or '',
            'province': c.address_province or '',
            'country': c.address_country or '',
            'total_orders': c.total_orders or 0,
            'total_spent': float(c.total_spent) if c.total_spent else 0,
            'last_order_date': c.last_order_date.strftime('%Y-%m-%d') if c.last_order_date else None,
            'created_at': c.created_at.strftime('%Y-%m-%d') if c.created_at else None,
        })
    
    return jsonify({
        'customers': results,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })


@bp.route('/api/customers/<customer_id>')
@login_required
@permission_required('customers', 'view')
def get_customer_detail(customer_id):
    """Get customer detail with recent orders"""
    tenant = g.current_tenant
    
    try:
        customer = ShopifyCustomer.objects.get(id=ObjectId(customer_id), tenant=tenant)
    except:
        return jsonify({'error': 'Cliente no encontrado'}), 404
    
    # Get recent orders
    orders = ShopifyOrder.objects(customer=customer, tenant=tenant).order_by('-created_at').limit(10)
    
    orders_data = []
    for order in orders:
        orders_data.append({
            'id': str(order.id),
            'order_number': order.order_number,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else None,
            'total_price': float(order.total_price) if order.total_price else 0,
            'financial_status': order.financial_status,
            'fulfillment_status': order.fulfillment_status or 'unfulfilled',
            'line_items_count': len(order.line_items) if order.line_items else 0,
            'line_items': [
                {
                    'title': item.title,
                    'quantity': item.quantity,
                    'price': float(item.price) if item.price else 0,
                }
                for item in (order.line_items or [])
            ]
        })
    
    return jsonify({
        'customer': {
            'id': str(customer.id),
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'city': customer.address_city,
            'province': customer.address_province,
            'country': customer.address_country,
            'total_orders': customer.total_orders,
            'total_spent': float(customer.total_spent) if customer.total_spent else 0,
            'first_order_date': customer.first_order_date.strftime('%Y-%m-%d') if customer.first_order_date else None,
            'last_order_date': customer.last_order_date.strftime('%Y-%m-%d') if customer.last_order_date else None,
            'tags': customer.tags,
        },
        'orders': orders_data
    })


@bp.route('/api/customers/stats')
@login_required
@permission_required('customers', 'view')
def get_stats():
    """Get customer statistics"""
    tenant = g.current_tenant
    
    # Total customers
    total_customers = ShopifyCustomer.objects(tenant=tenant).count()
    
    # Total revenue
    from decimal import Decimal
    total_revenue = Decimal('0')
    for customer in ShopifyCustomer.objects(tenant=tenant).only('total_spent'):
        if customer.total_spent:
            total_revenue += customer.total_spent
    
    # Average ticket
    avg_ticket = float(total_revenue / total_customers) if total_customers > 0 else 0
    
    # New customers this month
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_this_month = ShopifyCustomer.objects(tenant=tenant, created_at__gte=start_of_month).count()
    
    return jsonify({
        'total_customers': total_customers,
        'total_revenue': float(total_revenue),
        'avg_ticket': avg_ticket,
        'new_this_month': new_this_month,
    })


@bp.route('/api/customers/export')
@login_required
@permission_required('customers', 'export')
def export_excel():
    """Export customers to Excel"""
    tenant = g.current_tenant
    
    # Get all customers
    customers = ShopifyCustomer.objects(tenant=tenant).order_by('-total_spent')
    
    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Clientes Shopify"
    
    # Header style
    header_fill = PatternFill(start_color="C85103", end_color="C85103", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    # Headers
    headers = ['Nombre', 'Email', 'Teléfono', 'Ciudad', 'Provincia', 'País', 
               'Total Pedidos', 'Total Gastado', 'Primer Pedido', 'Último Pedido']
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
    
    # Data rows
    for row_idx, customer in enumerate(customers, start=2):
        ws.cell(row=row_idx, column=1, value=customer.name or '')
        ws.cell(row=row_idx, column=2, value=customer.email or '')
        ws.cell(row=row_idx, column=3, value=customer.phone or '')
        ws.cell(row=row_idx, column=4, value=customer.address_city or '')
        ws.cell(row=row_idx, column=5, value=customer.address_province or '')
        ws.cell(row=row_idx, column=6, value=customer.address_country or '')
        ws.cell(row=row_idx, column=7, value=customer.total_orders or 0)
        ws.cell(row=row_idx, column=8, value=float(customer.total_spent) if customer.total_spent else 0)
        ws.cell(row=row_idx, column=9, value=customer.first_order_date.strftime('%Y-%m-%d') if customer.first_order_date else '')
        ws.cell(row=row_idx, column=10, value=customer.last_order_date.strftime('%Y-%m-%d') if customer.last_order_date else '')
    
    # Adjust column widths
    for col in range(1, len(headers) + 1):
        ws.column_dimensions[chr(64 + col)].width = 15
    
    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'clientes_shopify_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )


@bp.route('/api/customers/sync', methods=['POST'])
@login_required
@permission_required('customers', 'sync')
def sync_shopify():
    """Sync customers and orders from Shopify (admin only)"""
    tenant = g.current_tenant
    
    headers = {
        'X-Shopify-Access-Token': SHOPIFY_TOKEN,
        'Content-Type': 'application/json'
    }
    
    stats = {
        'customers_synced': 0,
        'orders_synced': 0,
        'errors': []
    }
    
    try:
        # Sync Customers
        customers_url = f'{SHOPIFY_BASE_URL}/customers.json'
        page_info = None
        
        while True:
            params = {'limit': 250}
            if page_info:
                params['page_info'] = page_info
            
            response = requests.get(customers_url, headers=headers, params=params)
            
            if response.status_code != 200:
                stats['errors'].append(f'Error al obtener clientes: {response.status_code}')
                break
            
            data = response.json()
            customers_data = data.get('customers', [])
            
            if not customers_data:
                break
            
            # Process customers
            for customer_data in customers_data:
                try:
                    shopify_id = str(customer_data['id'])
                    
                    # Get default address
                    default_address = customer_data.get('default_address') or {}
                    
                    # Upsert customer
                    customer = ShopifyCustomer.objects(shopify_id=shopify_id, tenant=tenant).first()
                    if not customer:
                        customer = ShopifyCustomer(shopify_id=shopify_id, tenant=tenant)
                    
                    customer.name = f"{customer_data.get('first_name', '')} {customer_data.get('last_name', '')}".strip()
                    customer.email = customer_data.get('email')
                    customer.phone = customer_data.get('phone') or default_address.get('phone')
                    customer.address_city = default_address.get('city')
                    customer.address_province = default_address.get('province')
                    customer.address_country = default_address.get('country')
                    customer.tags = customer_data.get('tags')
                    customer.total_orders = customer_data.get('orders_count', 0)
                    customer.total_spent = float(customer_data.get('total_spent', 0))
                    
                    # Parse dates
                    if customer_data.get('created_at'):
                        customer.created_at = datetime.fromisoformat(customer_data['created_at'].replace('Z', '+00:00'))
                    
                    customer.save()
                    stats['customers_synced'] += 1
                    
                except Exception as e:
                    stats['errors'].append(f'Error al procesar cliente {customer_data.get("id")}: {str(e)}')
            
            # Check for next page
            link_header = response.headers.get('Link', '')
            if 'rel="next"' in link_header:
                # Extract page_info from link header
                import re
                match = re.search(r'page_info=([^&>]+)', link_header)
                if match:
                    page_info = match.group(1)
                else:
                    break
            else:
                break
        
        # Sync Orders
        orders_url = f'{SHOPIFY_BASE_URL}/orders.json'
        page_info = None
        
        while True:
            params = {'limit': 250, 'status': 'any'}
            if page_info:
                params['page_info'] = page_info
            
            response = requests.get(orders_url, headers=headers, params=params)
            
            if response.status_code != 200:
                stats['errors'].append(f'Error al obtener órdenes: {response.status_code}')
                break
            
            data = response.json()
            orders_data = data.get('orders', [])
            
            if not orders_data:
                break
            
            # Process orders
            for order_data in orders_data:
                try:
                    shopify_id = str(order_data['id'])
                    
                    # Find customer
                    customer = None
                    if order_data.get('customer'):
                        customer_shopify_id = str(order_data['customer']['id'])
                        customer = ShopifyCustomer.objects(shopify_id=customer_shopify_id, tenant=tenant).first()
                    
                    # Upsert order
                    order = ShopifyOrder.objects(shopify_id=shopify_id, tenant=tenant).first()
                    if not order:
                        order = ShopifyOrder(shopify_id=shopify_id, tenant=tenant)
                    
                    order.order_number = order_data.get('order_number')
                    order.customer = customer
                    order.customer_name = order_data.get('customer', {}).get('first_name', '') + ' ' + order_data.get('customer', {}).get('last_name', '')
                    order.email = order_data.get('email')
                    order.total_price = float(order_data.get('total_price', 0))
                    order.subtotal_price = float(order_data.get('subtotal_price', 0))
                    order.financial_status = order_data.get('financial_status')
                    order.fulfillment_status = order_data.get('fulfillment_status')
                    
                    # Shipping address
                    shipping_address = order_data.get('shipping_address') or {}
                    order.shipping_city = shipping_address.get('city')
                    order.shipping_province = shipping_address.get('province')
                    order.note = order_data.get('note')
                    
                    # Line items
                    line_items = []
                    for item_data in order_data.get('line_items', []):
                        line_item = ShopifyOrderLineItem(
                            title=item_data.get('title'),
                            sku=item_data.get('sku'),
                            quantity=item_data.get('quantity', 1),
                            price=float(item_data.get('price', 0)),
                            variant_title=item_data.get('variant_title'),
                            product_shopify_id=str(item_data.get('product_id')) if item_data.get('product_id') else None
                        )
                        line_items.append(line_item)
                    order.line_items = line_items
                    
                    # Parse dates
                    if order_data.get('created_at'):
                        order.created_at = datetime.fromisoformat(order_data['created_at'].replace('Z', '+00:00'))
                    
                    order.save()
                    stats['orders_synced'] += 1
                    
                    # Update customer stats
                    if customer:
                        customer_orders = ShopifyOrder.objects(customer=customer, tenant=tenant)
                        customer.total_orders = customer_orders.count()
                        
                        # Calculate total spent and dates
                        total_spent = sum(float(o.total_price or 0) for o in customer_orders)
                        customer.total_spent = total_spent
                        
                        # Get first and last order dates
                        orders_by_date = customer_orders.order_by('created_at')
                        if orders_by_date:
                            customer.first_order_date = orders_by_date.first().created_at
                            customer.last_order_date = orders_by_date.order_by('-created_at').first().created_at
                        
                        customer.save()
                    
                except Exception as e:
                    stats['errors'].append(f'Error al procesar orden {order_data.get("id")}: {str(e)}')
            
            # Check for next page
            link_header = response.headers.get('Link', '')
            if 'rel="next"' in link_header:
                import re
                match = re.search(r'page_info=([^&>]+)', link_header)
                if match:
                    page_info = match.group(1)
                else:
                    break
            else:
                break
        
    except Exception as e:
        stats['errors'].append(f'Error general en clientes/órdenes: {str(e)}')
    
    # ==========================================
    # SYNC PRODUCTS + STOCK
    # ==========================================
    try:
        from app.models import Product, Lot, InboundOrder
        import re as re_mod
        from decimal import Decimal
        
        products_url = f'{SHOPIFY_BASE_URL}/products.json'
        resp = requests.get(products_url, headers=headers, params={'limit': 250})
        
        if resp.status_code == 200:
            products_data = resp.json().get('products', [])
            products_created = 0
            products_updated = 0
            
            for p_data in products_data:
                shopify_id = str(p_data['id'])
                variants = p_data.get('variants', [])
                variant = variants[0] if variants else {}
                sku = variant.get('sku', '')
                price = Decimal(str(variant.get('price', '0')))
                inv_qty = variant.get('inventory_quantity', 0)
                
                # Strip HTML
                desc_html = p_data.get('body_html', '') or ''
                description = re_mod.sub(r'<[^>]+>', '', desc_html).strip()
                
                # Find or create product
                existing = None
                if sku:
                    existing = Product.objects(sku=sku, tenant=tenant).first()
                if not existing:
                    existing = Product.objects(shopify_id=shopify_id, tenant=tenant).first()
                
                if existing:
                    existing.name = p_data.get('title', existing.name)
                    existing.base_price = price
                    existing.shopify_id = shopify_id
                    if description:
                        existing.description = description[:500]
                    existing.save()
                    products_updated += 1
                    product = existing
                else:
                    product = Product(
                        name=p_data.get('title', 'Sin nombre'),
                        sku=sku or f"SHP-{shopify_id[-6:]}",
                        base_price=price,
                        description=description[:500] if description else '',
                        category=p_data.get('product_type', 'Shopify'),
                        shopify_id=shopify_id,
                        critical_stock=10,
                        tenant=tenant
                    )
                    product.save()
                    products_created += 1
                
                # Update stock via Lot
                if inv_qty > 0:
                    lot = Lot.objects(product=product, lot_code=f'SHOPIFY-{product.sku}').first()
                    if lot:
                        lot.quantity_current = inv_qty
                        lot.quantity_initial = max(lot.quantity_initial, inv_qty)
                        lot.save()
                    else:
                        # Create inbound order if needed
                        today_str = datetime.utcnow().strftime('%Y%m%d')
                        order = InboundOrder.objects(
                            invoice_number=f'SHOPIFY-SYNC-{today_str}',
                            tenant=tenant
                        ).first()
                        if not order:
                            order = InboundOrder(
                                supplier_name='Sync Shopify',
                                invoice_number=f'SHOPIFY-SYNC-{today_str}',
                                status='received',
                                date_received=datetime.utcnow(),
                                notes='Stock sincronizado desde Shopify',
                                tenant=tenant,
                                created_at=datetime.utcnow()
                            )
                            order.save()
                        
                        lot = Lot(
                            product=product,
                            order=order,
                            tenant=tenant,
                            lot_code=f'SHOPIFY-{product.sku}',
                            quantity_initial=inv_qty,
                            quantity_current=inv_qty
                        )
                        lot.save()
            
            stats['products_created'] = products_created
            stats['products_updated'] = products_updated
    
    except Exception as e:
        stats['errors'].append(f'Error en sync productos: {str(e)}')
    
    # ==========================================
    # SYNC ORDERS → SALES
    # ==========================================
    try:
        from app.models import Sale, SaleItem
        
        sales_created = 0
        shopify_orders_all = ShopifyOrder.objects(tenant=tenant)
        
        for s_order in shopify_orders_all:
            existing_sale = Sale.objects(tenant=tenant, shopify_order_id=str(s_order.shopify_id)).first()
            if existing_sale:
                continue
            
            addr_parts = [s_order.shipping_city or '', s_order.shipping_province or '']
            address = ', '.join(p for p in addr_parts if p)
            
            new_sale = Sale(
                customer_name=s_order.customer_name or 'Cliente Shopify',
                address=address,
                sale_type='con_despacho',
                delivery_status='entregado' if s_order.fulfillment_status == 'fulfilled' else 'pendiente',
                payment_status='pagado' if s_order.financial_status == 'paid' else 'pendiente',
                date_created=s_order.created_at or datetime.utcnow(),
                shopify_order_id=str(s_order.shopify_id),
                shopify_order_number=s_order.order_number,
                tenant=tenant
            )
            new_sale.save()
            
            for item in s_order.line_items:
                product = None
                if item.sku:
                    product = Product.objects(sku=item.sku, tenant=tenant).first()
                if not product and item.product_shopify_id:
                    product = Product.objects(shopify_id=item.product_shopify_id, tenant=tenant).first()
                
                if product:
                    sale_item = SaleItem(
                        sale=new_sale,
                        product=product,
                        quantity=item.quantity or 1,
                        unit_price=float(item.price) if item.price else 0
                    )
                    sale_item.save()
            
            sales_created += 1
        
        stats['sales_created'] = sales_created
    
    except Exception as e:
        stats['errors'].append(f'Error en sync ventas: {str(e)}')
    
    return jsonify(stats)
