#!/usr/bin/env python
"""
Standalone script to sync Shopify customers and orders to SIPUD database.
Run: python scripts/sync_shopify.py

Uses client credentials grant for authentication (tokens auto-refresh every 24h).
Required env vars: SHOPIFY_CLIENT_ID, SHOPIFY_CLIENT_SECRET, SHOPIFY_STORE_DOMAIN
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import ShopifyCustomer, ShopifyOrder, ShopifyOrderLineItem, Tenant, Product, Sale, SaleItem, Lot, InboundOrder
from datetime import datetime, timedelta
from decimal import Decimal
import requests
import re

# Import auth module for client credentials grant
from shopify_auth import get_auth_headers, get_token_info

# Shopify API Configuration
SHOPIFY_STORE = os.environ.get('SHOPIFY_STORE_DOMAIN', '')
SHOPIFY_API_VERSION = '2026-01'
SHOPIFY_BASE_URL = f'https://{SHOPIFY_STORE}/admin/api/{SHOPIFY_API_VERSION}'


def sync_shopify(tenant_slug='puerto-distribucion'):
    """Main sync function"""
    print(f"🚀 Iniciando sincronización de Shopify para tenant: {tenant_slug}")
    print(f"   Store: {SHOPIFY_STORE}")
    print(f"   API Version: {SHOPIFY_API_VERSION}")
    
    # Get auth token using client credentials grant
    print(f"🔐 Obteniendo token de acceso...")
    try:
        headers = get_auth_headers()
        token_info = get_token_info()
        print(f"   ✅ Token válido (expira en {token_info['expires_in_hours']}h)\n")
    except Exception as e:
        print(f"❌ Error obteniendo token: {str(e)}")
        print("   Verifica SHOPIFY_CLIENT_ID, SHOPIFY_CLIENT_SECRET y SHOPIFY_STORE_DOMAIN")
        return
    
    # Get tenant
    tenant = Tenant.objects(slug=tenant_slug).first()
    if not tenant:
        print(f"❌ Error: Tenant '{tenant_slug}' no encontrado")
        return
    
    print(f"✅ Tenant encontrado: {tenant.name}\n")
    
    stats = {
        'customers_synced': 0,
        'customers_updated': 0,
        'customers_created': 0,
        'orders_synced': 0,
        'orders_updated': 0,
        'orders_created': 0,
        'errors': []
    }
    
    # ==========================================
    # SYNC CUSTOMERS
    # ==========================================
    print("📥 Sincronizando clientes...")
    customers_url = f'{SHOPIFY_BASE_URL}/customers.json'
    page_info = None
    page_num = 1
    
    while True:
        params = {'limit': 250}
        if page_info:
            params['page_info'] = page_info
        
        try:
            response = requests.get(customers_url, headers=headers, params=params)
            
            if response.status_code == 403:
                print(f"⚠️  Sin acceso a clientes (scope read_customers no disponible)")
                print(f"   Los clientes se crearán automáticamente desde las órdenes")
                break
            elif response.status_code != 200:
                print(f"❌ Error al obtener clientes: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                break
            
            data = response.json()
            customers_data = data.get('customers', [])
            
            if not customers_data:
                print(f"   No hay más clientes para procesar")
                break
            
            print(f"   Página {page_num}: {len(customers_data)} clientes")
            
            # Process customers
            for idx, customer_data in enumerate(customers_data, 1):
                try:
                    shopify_id = str(customer_data['id'])
                    
                    # Get default address
                    default_address = customer_data.get('default_address') or {}
                    
                    # Upsert customer
                    customer = ShopifyCustomer.objects(shopify_id=shopify_id, tenant=tenant).first()
                    is_new = customer is None
                    
                    if not customer:
                        customer = ShopifyCustomer(shopify_id=shopify_id, tenant=tenant)
                        stats['customers_created'] += 1
                    else:
                        stats['customers_updated'] += 1
                    
                    # Update fields
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
                    
                    customer.updated_at = datetime.utcnow()
                    customer.save()
                    
                    stats['customers_synced'] += 1
                    
                    if idx % 50 == 0:
                        print(f"      Procesados: {idx}/{len(customers_data)}")
                    
                except Exception as e:
                    error_msg = f"Error procesando cliente {customer_data.get('id')}: {str(e)}"
                    stats['errors'].append(error_msg)
                    print(f"   ⚠️  {error_msg}")
            
            # Check for next page
            link_header = response.headers.get('Link', '')
            if 'rel="next"' in link_header:

                match = re.search(r'page_info=([^&>]+)', link_header)
                if match:
                    page_info = match.group(1)
                    page_num += 1
                else:
                    break
            else:
                break
                
        except Exception as e:
            error_msg = f"Error obteniendo página de clientes: {str(e)}"
            stats['errors'].append(error_msg)
            print(f"❌ {error_msg}")
            break
    
    print(f"\n✅ Clientes sincronizados: {stats['customers_synced']}")
    print(f"   - Nuevos: {stats['customers_created']}")
    print(f"   - Actualizados: {stats['customers_updated']}\n")
    
    # ==========================================
    # SYNC ORDERS
    # ==========================================
    print("📥 Sincronizando órdenes...")
    orders_url = f'{SHOPIFY_BASE_URL}/orders.json'
    page_info = None
    page_num = 1
    
    while True:
        params = {'limit': 250, 'status': 'any'}
        if page_info:
            params['page_info'] = page_info
        
        try:
            response = requests.get(orders_url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"❌ Error al obtener órdenes: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                break
            
            data = response.json()
            orders_data = data.get('orders', [])
            
            if not orders_data:
                print(f"   No hay más órdenes para procesar")
                break
            
            print(f"   Página {page_num}: {len(orders_data)} órdenes")
            
            # Process orders
            for idx, order_data in enumerate(orders_data, 1):
                try:
                    shopify_id = str(order_data['id'])
                    
                    # Find or create customer from order data
                    customer = None
                    if order_data.get('customer'):
                        customer_shopify_id = str(order_data['customer']['id'])
                        customer = ShopifyCustomer.objects(shopify_id=customer_shopify_id, tenant=tenant).first()
                        
                        # Create customer from order data if not exists (workaround for no read_customers scope)
                        if not customer:
                            cust_data = order_data['customer']
                            addr = order_data.get('shipping_address') or order_data.get('billing_address') or {}
                            customer = ShopifyCustomer(
                                shopify_id=customer_shopify_id,
                                name=f"{cust_data.get('first_name', '')} {cust_data.get('last_name', '')}".strip() or cust_data.get('email', 'Sin nombre'),
                                email=cust_data.get('email', ''),
                                phone=cust_data.get('phone', '') or addr.get('phone', ''),
                                address_city=addr.get('city', ''),
                                address_province=addr.get('province', ''),
                                address_country=addr.get('country', ''),
                                tags=cust_data.get('tags', ''),
                                total_orders=cust_data.get('orders_count', 0),
                                total_spent=float(cust_data.get('total_spent', '0')),
                                tenant=tenant,
                                created_at=datetime.fromisoformat(cust_data['created_at'].replace('Z', '+00:00')) if cust_data.get('created_at') else datetime.utcnow(),
                                updated_at=datetime.utcnow()
                            )
                            customer.save()
                            stats['customers_created'] = stats.get('customers_created', 0) + 1
                            print(f"      + Cliente creado desde orden: {customer.name}")
                    
                    # Upsert order
                    order = ShopifyOrder.objects(shopify_id=shopify_id, tenant=tenant).first()
                    is_new = order is None
                    
                    if not order:
                        order = ShopifyOrder(shopify_id=shopify_id, tenant=tenant)
                        stats['orders_created'] += 1
                    else:
                        stats['orders_updated'] += 1
                    
                    # Update fields
                    order.order_number = order_data.get('order_number')
                    order.customer = customer
                    
                    if order_data.get('customer'):
                        order.customer_name = f"{order_data['customer'].get('first_name', '')} {order_data['customer'].get('last_name', '')}".strip()
                    
                    order.email = order_data.get('email')
                    order.total_price = float(order_data.get('total_price', 0))
                    order.subtotal_price = float(order_data.get('subtotal_price', 0))
                    order.financial_status = order_data.get('financial_status')
                    order.fulfillment_status = order_data.get('fulfillment_status')
                    
                    # Shipping address (captura completa)
                    shipping_address = order_data.get('shipping_address') or {}
                    order.shipping_address1 = shipping_address.get('address1')
                    order.shipping_address2 = shipping_address.get('address2')
                    order.shipping_city = shipping_address.get('city')
                    order.shipping_province = shipping_address.get('province')
                    order.shipping_phone = shipping_address.get('phone')
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
                    
                    order.updated_at = datetime.utcnow()
                    order.save()
                    
                    stats['orders_synced'] += 1
                    
                    if idx % 50 == 0:
                        print(f"      Procesadas: {idx}/{len(orders_data)}")
                    
                except Exception as e:
                    error_msg = f"Error procesando orden {order_data.get('id')}: {str(e)}"
                    stats['errors'].append(error_msg)
                    print(f"   ⚠️  {error_msg}")
            
            # Check for next page
            link_header = response.headers.get('Link', '')
            if 'rel="next"' in link_header:

                match = re.search(r'page_info=([^&>]+)', link_header)
                if match:
                    page_info = match.group(1)
                    page_num += 1
                else:
                    break
            else:
                break
                
        except Exception as e:
            error_msg = f"Error obteniendo página de órdenes: {str(e)}"
            stats['errors'].append(error_msg)
            print(f"❌ {error_msg}")
            break
    
    print(f"\n✅ Órdenes sincronizadas: {stats['orders_synced']}")
    print(f"   - Nuevas: {stats['orders_created']}")
    print(f"   - Actualizadas: {stats['orders_updated']}\n")
    
    # ==========================================
    # UPDATE CUSTOMER STATS FROM ORDERS
    # ==========================================
    print("🔄 Actualizando estadísticas de clientes...")
    
    customers_to_update = ShopifyCustomer.objects(tenant=tenant)
    for idx, customer in enumerate(customers_to_update, 1):
        try:
            customer_orders = ShopifyOrder.objects(customer=customer, tenant=tenant)
            
            # Update stats
            customer.total_orders = customer_orders.count()
            
            # Calculate total spent
            total_spent = sum(float(o.total_price or 0) for o in customer_orders)
            customer.total_spent = total_spent
            
            # Get first and last order dates
            orders_by_date = customer_orders.order_by('created_at')
            if orders_by_date:
                first_order = orders_by_date.first()
                last_order = orders_by_date.order_by('-created_at').first()
                
                if first_order:
                    customer.first_order_date = first_order.created_at
                if last_order:
                    customer.last_order_date = last_order.created_at
            
            customer.save()
            
            if idx % 50 == 0:
                print(f"   Actualizados: {idx}/{customers_to_update.count()}")
                
        except Exception as e:
            error_msg = f"Error actualizando stats del cliente {customer.shopify_id}: {str(e)}"
            stats['errors'].append(error_msg)
            print(f"   ⚠️  {error_msg}")
    
    print(f"✅ Estadísticas actualizadas para {customers_to_update.count()} clientes\n")
    
    # ==========================================
    # SYNC PRODUCTS (Shopify → SIPUD Products)
    # ==========================================
    print("📥 Sincronizando productos Shopify → Productos SIPUD...")
    # Refresh headers (token auto-refreshes if needed)
    headers = get_auth_headers()
    
    products_url = f'{SHOPIFY_BASE_URL}/products.json'
    page_info = None
    page_num = 1
    products_created = 0
    products_updated = 0
    
    while True:
        params = {'limit': 250}
        if page_info:
            params['page_info'] = page_info
        
        try:
            response = requests.get(products_url, headers=headers, params=params)
            if response.status_code != 200:
                print(f"❌ Error al obtener productos: HTTP {response.status_code}")
                break
            
            data = response.json()
            products_data = data.get('products', [])
            
            if not products_data:
                break
            
            print(f"   Página {page_num}: {len(products_data)} productos")
            
            for p_data in products_data:
                shopify_id = str(p_data['id'])
                
                # Get first variant for price and SKU
                variants = p_data.get('variants', [])
                variant = variants[0] if variants else {}
                sku = variant.get('sku', '')
                price = Decimal(str(variant.get('price', '0')))
                
                # Strip HTML from description
                desc_html = p_data.get('body_html', '') or ''
                description = re.sub(r'<[^>]+>', '', desc_html).strip()
                
                # Try to find existing product by SKU or shopify_id
                existing = None
                if sku:
                    existing = Product.objects(sku=sku, tenant=tenant).first()
                if not existing:
                    existing = Product.objects(shopify_id=shopify_id, tenant=tenant).first()
                
                if existing:
                    # Update existing product
                    existing.name = p_data.get('title', existing.name)
                    existing.base_price = price
                    existing.description = description[:500] if description else existing.description
                    existing.shopify_id = shopify_id
                    if p_data.get('product_type'):
                        existing.category = p_data['product_type']
                    if p_data.get('tags'):
                        existing.tags = p_data['tags'][:200]
                    existing.save()
                    products_updated += 1
                else:
                    # Create new product
                    new_product = Product(
                        name=p_data.get('title', 'Sin nombre'),
                        sku=sku or f"SHP-{shopify_id[-6:]}",
                        base_price=price,
                        description=description[:500] if description else '',
                        category=p_data.get('product_type', 'Shopify'),
                        tags=p_data.get('tags', '')[:200],
                        shopify_id=shopify_id,
                        critical_stock=10,
                        tenant=tenant
                    )
                    new_product.save()
                    products_created += 1
                    print(f"      + Producto: {new_product.name} (SKU: {new_product.sku})")
            
            # Pagination
            link_header = response.headers.get('Link', '')
            if 'rel="next"' in link_header:
                match_pg = re.search(r'page_info=([^&>]+)', link_header)
                if match_pg:
                    page_info = match_pg.group(1)
                    page_num += 1
                else:
                    break
            else:
                break
                
        except Exception as e:
            print(f"❌ Error en sync de productos: {str(e)}")
            stats['errors'].append(f"Productos: {str(e)}")
            break
    
    print(f"✅ Productos: {products_created} nuevos, {products_updated} actualizados\n")
    stats['products_created'] = products_created
    stats['products_updated'] = products_updated
    
    # ==========================================
    # SYNC ORDERS → SIPUD SALES
    # ==========================================
    print("📥 Sincronizando órdenes Shopify → Ventas SIPUD...")
    
    sales_created = 0
    sales_skipped = 0
    
    # Get all ShopifyOrders and create Sales if not already linked
    shopify_orders = ShopifyOrder.objects(tenant=tenant)
    
    for s_order in shopify_orders:
        # Construir dirección completa
        addr_parts = [
            s_order.shipping_address1 or '',
            s_order.shipping_address2 or '',
            s_order.shipping_city or '',
            s_order.shipping_province or ''
        ]
        full_address = ', '.join(p for p in addr_parts if p)
        phone = s_order.shipping_phone or ''
        
        # Check if sale already exists for this Shopify order
        existing_sale = Sale.objects(
            tenant=tenant,
            shopify_order_id=str(s_order.shopify_id)
        ).first()
        
        if existing_sale:
            # Update address and phone if missing or incomplete
            updated = False
            if not existing_sale.address or len(existing_sale.address) < len(full_address):
                existing_sale.address = full_address
                updated = True
            if not existing_sale.phone and phone:
                existing_sale.phone = phone
                updated = True
            if updated:
                existing_sale.save()
                print(f"      ~ Actualizada venta #{s_order.order_number}: {full_address[:50]}...")
            sales_skipped += 1
            continue
        
        # Create new Sale from Shopify order
        try:
            address = full_address
            
            new_sale = Sale(
                customer_name=s_order.customer_name or 'Cliente Shopify',
                address=address,
                phone=s_order.shipping_phone or '',
                sale_type='con_despacho',
                delivery_status='entregado' if s_order.fulfillment_status == 'fulfilled' else 'pendiente',
                payment_status='pagado' if s_order.financial_status == 'paid' else 'pendiente',
                date_created=s_order.created_at or datetime.utcnow(),
                shopify_order_id=str(s_order.shopify_id),
                shopify_order_number=s_order.order_number,
                tenant=tenant
            )
            new_sale.save()
            
            # Create SaleItems from line items
            for item in s_order.line_items:
                # Find product by SKU
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
            
        except Exception as e:
            error_msg = f"Error creando venta para orden #{s_order.order_number}: {str(e)}"
            stats['errors'].append(error_msg)
            print(f"   ⚠️  {error_msg}")
    
    print(f"✅ Ventas: {sales_created} creadas, {sales_skipped} ya existían\n")
    stats['sales_created'] = sales_created
    stats['sales_skipped'] = sales_skipped
    
    # ==========================================
    # SUMMARY
    # ==========================================
    print("=" * 60)
    print("📊 RESUMEN DE SINCRONIZACIÓN")
    print("=" * 60)
    print(f"✅ Clientes: {stats.get('customers_created',0)} nuevos, {stats.get('customers_updated',0)} actualizados")
    print(f"✅ Órdenes: {stats.get('orders_created',0)} nuevas, {stats.get('orders_updated',0)} actualizadas")
    print(f"✅ Productos: {stats.get('products_created',0)} nuevos, {stats.get('products_updated',0)} actualizados")
    print(f"✅ Ventas: {stats.get('sales_created',0)} creadas, {stats.get('sales_skipped',0)} ya existían")
    
    if stats['errors']:
        print(f"\n⚠️  Errores encontrados: {len(stats['errors'])}")
        for error in stats['errors'][:10]:
            print(f"   - {error}")
    else:
        print(f"\n✅ Sin errores")
    
    print("=" * 60)


if __name__ == '__main__':
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        # Get tenant slug from command line or use default
        tenant_slug = sys.argv[1] if len(sys.argv) > 1 else 'puerto-distribucion'
        
        try:
            sync_shopify(tenant_slug)
        except KeyboardInterrupt:
            print("\n\n⚠️  Sincronización interrumpida por el usuario")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Error fatal: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
