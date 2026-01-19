#!/usr/bin/env python3
"""
Migration Script: SQLite to MongoDB
Migrates data from SQLite database to MongoDB preserving relationships.

Usage:
    python scripts/migrate_sqlite_to_mongo.py

Prerequisites:
    - MongoDB must be running
    - SQLite database must exist at instance/inventory.db
    - Install dependencies: pip install flask flask-mongoengine pymongo
"""

import os
import sys
import sqlite3
from datetime import datetime
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from mongoengine import connect, disconnect
from bson import ObjectId


def create_app_for_migration():
    """Create a minimal Flask app for migration purposes."""
    app = Flask(__name__)
    app.config['MONGODB_SETTINGS'] = {
        'db': os.environ.get('MONGODB_DB') or 'inventory_db',
        'host': os.environ.get('MONGODB_HOST') or 'localhost',
        'port': int(os.environ.get('MONGODB_PORT') or 27017),
    }
    return app


def get_sqlite_connection():
    """Get SQLite database connection."""
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'instance',
        'inventory.db'
    )
    if not os.path.exists(db_path):
        print(f"Error: SQLite database not found at {db_path}")
        sys.exit(1)
    return sqlite3.connect(db_path)


def dict_factory(cursor, row):
    """Convert SQLite row to dictionary."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def migrate_data():
    """Main migration function."""
    print("=" * 60)
    print("SQLite to MongoDB Migration Script")
    print("=" * 60)

    # Connect to MongoDB
    print("\n[1/2] Connecting to databases...")

    mongodb_host = os.environ.get('MONGODB_HOST') or 'localhost'
    mongodb_port = int(os.environ.get('MONGODB_PORT') or 27017)
    mongodb_db = os.environ.get('MONGODB_DB') or 'inventory_db'

    disconnect()  # Disconnect any existing connections
    connect(db=mongodb_db, host=mongodb_host, port=mongodb_port)
    print(f"  - MongoDB connected: {mongodb_host}:{mongodb_port}/{mongodb_db}")

    # Import models after connection
    from app.models import (
        Tenant, Supplier, User, Product, ProductBundle,
        InboundOrder, Lot, Sale, SaleItem, Wastage,
        Truck, VehicleMaintenance, LogisticsRoute
    )

    # Connect to SQLite
    sqlite_conn = get_sqlite_connection()
    sqlite_conn.row_factory = dict_factory
    cursor = sqlite_conn.cursor()
    print("  - SQLite connected")

    # Mapping of old IDs to new ObjectIds
    id_map = {
        'tenant': {},
        'supplier': {},
        'user': {},
        'product': {},
        'product_bundle': {},
        'inbound_order': {},
        'lot': {},
        'sale': {},
        'sale_item': {},
        'wastage': {},
        'truck': {},
        'vehicle_maintenance': {},
        'logistics_route': {},
    }

    print("\n[2/2] Migrating data...")

    # 1. Migrate Tenants
    print("\n  Migrating tenants...")
    cursor.execute("SELECT * FROM tenant")
    tenants = cursor.fetchall()
    for tenant_data in tenants:
        tenant = Tenant(
            name=tenant_data['name'],
            slug=tenant_data['slug'],
            created_at=datetime.fromisoformat(tenant_data['created_at']) if tenant_data.get('created_at') else datetime.utcnow()
        )
        tenant.save()
        id_map['tenant'][tenant_data['id']] = tenant
        print(f"    - Tenant: {tenant.name}")

    # 2. Migrate Suppliers
    print("\n  Migrating suppliers...")
    cursor.execute("SELECT * FROM supplier")
    suppliers = cursor.fetchall()
    for supplier_data in suppliers:
        tenant = id_map['tenant'].get(supplier_data.get('tenant_id'))
        supplier = Supplier(
            name=supplier_data['name'],
            rut=supplier_data.get('rut'),
            contact_info=supplier_data.get('contact_info'),
            tenant=tenant
        )
        supplier.save()
        id_map['supplier'][supplier_data['id']] = supplier
    print(f"    - Migrated {len(suppliers)} suppliers")

    # 3. Migrate Users
    print("\n  Migrating users...")
    cursor.execute("SELECT * FROM user")
    users = cursor.fetchall()
    for user_data in users:
        tenant = id_map['tenant'].get(user_data.get('tenant_id'))
        user = User(
            username=user_data['username'],
            email=user_data.get('email'),
            password_hash=user_data.get('password_hash'),
            role=user_data['role'],
            full_name=user_data.get('full_name'),
            is_active=bool(user_data.get('is_active', True)),
            tenant=tenant,
            created_at=datetime.fromisoformat(user_data['created_at']) if user_data.get('created_at') else datetime.utcnow(),
            last_login=datetime.fromisoformat(user_data['last_login']) if user_data.get('last_login') else None
        )
        user.save()
        id_map['user'][user_data['id']] = user
    print(f"    - Migrated {len(users)} users")

    # 4. Migrate Products
    print("\n  Migrating products...")
    cursor.execute("SELECT * FROM product")
    products = cursor.fetchall()
    for product_data in products:
        tenant = id_map['tenant'].get(product_data.get('tenant_id'))
        product = Product(
            name=product_data['name'],
            sku=product_data.get('sku'),
            base_price=Decimal(str(product_data.get('base_price', 0) or 0)),
            critical_stock=product_data.get('critical_stock', 10),
            category=product_data.get('category', 'Otros'),
            tags=product_data.get('tags'),
            description=product_data.get('description'),
            expiry_date=datetime.strptime(product_data['expiry_date'], '%Y-%m-%d').date() if product_data.get('expiry_date') else None,
            tenant=tenant
        )
        product.save()
        id_map['product'][product_data['id']] = product
    print(f"    - Migrated {len(products)} products")

    # 5. Migrate Product Bundles
    print("\n  Migrating product bundles...")
    cursor.execute("SELECT * FROM product_bundle")
    bundles = cursor.fetchall()
    for bundle_data in bundles:
        bundle_product = id_map['product'].get(bundle_data['bundle_id'])
        component_product = id_map['product'].get(bundle_data['component_id'])
        tenant = id_map['tenant'].get(bundle_data.get('tenant_id'))

        if bundle_product and component_product:
            product_bundle = ProductBundle(
                bundle=bundle_product,
                component=component_product,
                quantity=bundle_data.get('quantity', 1),
                tenant=tenant
            )
            product_bundle.save()
            id_map['product_bundle'][bundle_data['id']] = product_bundle
    print(f"    - Migrated {len(bundles)} product bundles")

    # 6. Migrate Inbound Orders
    print("\n  Migrating inbound orders...")
    cursor.execute("SELECT * FROM inbound_order")
    orders = cursor.fetchall()
    for order_data in orders:
        tenant = id_map['tenant'].get(order_data.get('tenant_id'))
        supplier = id_map['supplier'].get(order_data.get('supplier_id'))

        inbound_order = InboundOrder(
            supplier=supplier,
            supplier_name=order_data.get('supplier', ''),  # Old string field
            invoice_number=order_data.get('invoice_number'),
            date_received=datetime.fromisoformat(order_data['date_received']) if order_data.get('date_received') else None,
            created_at=datetime.fromisoformat(order_data['created_at']) if order_data.get('created_at') else datetime.utcnow(),
            total=Decimal(str(order_data.get('total', 0) or 0)),
            status=order_data.get('status', 'pending'),
            notes=order_data.get('notes'),
            tenant=tenant
        )
        inbound_order.save()
        id_map['inbound_order'][order_data['id']] = inbound_order
    print(f"    - Migrated {len(orders)} inbound orders")

    # 7. Migrate Lots
    print("\n  Migrating lots...")
    cursor.execute("SELECT * FROM lot")
    lots = cursor.fetchall()
    for lot_data in lots:
        product = id_map['product'].get(lot_data['product_id'])
        order = id_map['inbound_order'].get(lot_data.get('order_id'))
        tenant = id_map['tenant'].get(lot_data.get('tenant_id'))

        if product:
            lot = Lot(
                product=product,
                order=order,
                tenant=tenant,
                lot_code=lot_data.get('lot_code'),
                quantity_initial=lot_data['quantity_initial'],
                quantity_current=lot_data['quantity_current'],
                expiry_date=datetime.strptime(lot_data['expiry_date'], '%Y-%m-%d').date() if lot_data.get('expiry_date') else None,
                created_at=datetime.fromisoformat(lot_data['created_at']) if lot_data.get('created_at') else datetime.utcnow()
            )
            lot.save()
            id_map['lot'][lot_data['id']] = lot
    print(f"    - Migrated {len(lots)} lots")

    # 8. Migrate Trucks (Fleet - preserved)
    print("\n  Migrating trucks...")
    cursor.execute("SELECT * FROM truck")
    trucks = cursor.fetchall()
    for truck_data in trucks:
        tenant = id_map['tenant'].get(truck_data.get('tenant_id'))
        truck = Truck(
            license_plate=truck_data['license_plate'],
            make_model=truck_data.get('make_model'),
            capacity_kg=truck_data.get('capacity_kg'),
            status=truck_data.get('status', 'available'),
            tenant=tenant,
            current_lat=truck_data.get('current_lat'),
            current_lng=truck_data.get('current_lng'),
            last_update=datetime.fromisoformat(truck_data['last_update']) if truck_data.get('last_update') else None,
            odometer_km=truck_data.get('odometer_km', 0),
            last_maintenance_date=datetime.strptime(truck_data['last_maintenance_date'], '%Y-%m-%d').date() if truck_data.get('last_maintenance_date') else None,
            next_maintenance_km=truck_data.get('next_maintenance_km')
        )
        truck.save()
        id_map['truck'][truck_data['id']] = truck
    print(f"    - Migrated {len(trucks)} trucks")

    # 9. Migrate Logistics Routes
    print("\n  Migrating logistics routes...")
    cursor.execute("SELECT * FROM logistics_route")
    routes = cursor.fetchall()
    for route_data in routes:
        driver = id_map['user'].get(route_data.get('driver_id'))
        truck = id_map['truck'].get(route_data.get('truck_id'))

        logistics_route = LogisticsRoute(
            driver=driver,
            truck=truck,
            start_time=datetime.fromisoformat(route_data['start_time']) if route_data.get('start_time') else None,
            end_time=datetime.fromisoformat(route_data['end_time']) if route_data.get('end_time') else None,
            status=route_data.get('status', 'planned')
        )
        logistics_route.save()
        id_map['logistics_route'][route_data['id']] = logistics_route
    print(f"    - Migrated {len(routes)} logistics routes")

    # 10. Migrate Sales
    print("\n  Migrating sales...")
    cursor.execute("SELECT * FROM sale")
    sales = cursor.fetchall()
    for sale_data in sales:
        tenant = id_map['tenant'].get(sale_data.get('tenant_id'))
        route = id_map['logistics_route'].get(sale_data.get('route_id'))

        sale = Sale(
            customer_name=sale_data.get('customer_name'),
            address=sale_data.get('address'),
            phone=sale_data.get('phone'),
            status=sale_data.get('status', 'pending'),
            payment_method=sale_data.get('payment_method'),
            payment_confirmed=bool(sale_data.get('payment_confirmed', False)),
            delivery_status=sale_data.get('delivery_status', 'pending'),
            date_created=datetime.fromisoformat(sale_data['date_created']) if sale_data.get('date_created') else datetime.utcnow(),
            tenant=tenant,
            route=route
        )
        sale.save()
        id_map['sale'][sale_data['id']] = sale
    print(f"    - Migrated {len(sales)} sales")

    # 11. Migrate Sale Items
    print("\n  Migrating sale items...")
    cursor.execute("SELECT * FROM sale_item")
    sale_items = cursor.fetchall()
    for item_data in sale_items:
        sale = id_map['sale'].get(item_data['sale_id'])
        product = id_map['product'].get(item_data['product_id'])

        if sale and product:
            sale_item = SaleItem(
                sale=sale,
                product=product,
                quantity=item_data['quantity'],
                unit_price=Decimal(str(item_data.get('unit_price', 0) or 0))
            )
            sale_item.save()
            id_map['sale_item'][item_data['id']] = sale_item
    print(f"    - Migrated {len(sale_items)} sale items")

    # 12. Migrate Wastages
    print("\n  Migrating wastages...")
    cursor.execute("SELECT * FROM wastage")
    wastages = cursor.fetchall()
    for wastage_data in wastages:
        product = id_map['product'].get(wastage_data['product_id'])
        tenant = id_map['tenant'].get(wastage_data.get('tenant_id'))

        if product:
            wastage = Wastage(
                product=product,
                quantity=wastage_data['quantity'],
                reason=wastage_data['reason'],
                notes=wastage_data.get('notes'),
                date_created=datetime.fromisoformat(wastage_data['date_created']) if wastage_data.get('date_created') else datetime.utcnow(),
                tenant=tenant
            )
            wastage.save()
            id_map['wastage'][wastage_data['id']] = wastage
    print(f"    - Migrated {len(wastages)} wastage records")

    # 13. Migrate Vehicle Maintenance
    print("\n  Migrating vehicle maintenance records...")
    cursor.execute("SELECT * FROM vehicle_maintenance")
    maintenances = cursor.fetchall()
    for maint_data in maintenances:
        truck = id_map['truck'].get(maint_data['truck_id'])
        tenant = id_map['tenant'].get(maint_data.get('tenant_id'))

        if truck:
            maintenance = VehicleMaintenance(
                truck=truck,
                maintenance_type=maint_data.get('maintenance_type'),
                scheduled_date=datetime.strptime(maint_data['scheduled_date'], '%Y-%m-%d').date() if maint_data.get('scheduled_date') else None,
                completed_date=datetime.strptime(maint_data['completed_date'], '%Y-%m-%d').date() if maint_data.get('completed_date') else None,
                odometer_reading=maint_data.get('odometer_reading'),
                cost=Decimal(str(maint_data.get('cost', 0) or 0)),
                notes=maint_data.get('notes'),
                status=maint_data.get('status', 'pending'),
                tenant=tenant,
                created_at=datetime.fromisoformat(maint_data['created_at']) if maint_data.get('created_at') else datetime.utcnow()
            )
            maintenance.save()
            id_map['vehicle_maintenance'][maint_data['id']] = maintenance
    print(f"    - Migrated {len(maintenances)} maintenance records")

    # Close SQLite connection
    sqlite_conn.close()

    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("=" * 60)

    # Print summary
    print("\nMigration Summary:")
    print(f"  - Tenants: {len(id_map['tenant'])}")
    print(f"  - Suppliers: {len(id_map['supplier'])}")
    print(f"  - Users: {len(id_map['user'])}")
    print(f"  - Products: {len(id_map['product'])}")
    print(f"  - Product Bundles: {len(id_map['product_bundle'])}")
    print(f"  - Inbound Orders: {len(id_map['inbound_order'])}")
    print(f"  - Lots: {len(id_map['lot'])}")
    print(f"  - Sales: {len(id_map['sale'])}")
    print(f"  - Sale Items: {len(id_map['sale_item'])}")
    print(f"  - Wastages: {len(id_map['wastage'])}")
    print(f"  - Trucks: {len(id_map['truck'])}")
    print(f"  - Logistics Routes: {len(id_map['logistics_route'])}")
    print(f"  - Vehicle Maintenances: {len(id_map['vehicle_maintenance'])}")

    print("\nNext steps:")
    print("  1. Verify data integrity in MongoDB")
    print("  2. Update environment variables if needed")
    print("  3. Test the application")
    print("  4. Backup the SQLite database before removing it")


if __name__ == '__main__':
    migrate_data()
