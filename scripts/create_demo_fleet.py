#!/usr/bin/env python
"""
Generate demo fleet data for Puerto Distribución
Creates trucks, drivers (users), and sample delivery routes with Chilean data
"""
import sys
sys.path.insert(0, '/Users/bchavez/Software Inventario 2026')

from app import create_app, db
from app.models import Tenant, Truck, User, LogisticsRoute, Sale
from datetime import datetime, timedelta
import random

app = create_app()

# Chilean realistic data
TRUCK_DATA = [
    {"plate": "CDZY-12", "model": "Hyundai H100 2018", "capacity": 1200},
    {"plate": "FHTX-34", "model": "Chevrolet N300 2020", "capacity": 800},
    {"plate": "BJKL-56", "model": "Kia K2700 2019", "capacity": 1500},
    {"plate": "RSTW-78", "model": "JAC X200 2021", "capacity": 1000},
]

DRIVER_DATA = [
    {"name": "Carlos Martínez", "phone": "+56 9 8765 4321"},
    {"name": "Pedro González", "phone": "+56 9 7654 3210"},
    {"name": "Juan Rojas", "phone": "+56 9 6543 2109"},
    {"name": "Miguel Vásquez", "phone": "+56 9 5432 1098"},
]

# Puerto Montt area coordinates (approximate)
PUERTO_MONTT_CENTER = {"lat": -41.4693, "lng": -72.9424}

def random_nearby_location(center, radius_km=5):
    """Generate random lat/lng near a center point"""
    # Rough conversion: 1 degree lat ≈ 111 km, 1 degree lng ≈ 111 km * cos(lat)
    lat_offset = (random.random() - 0.5) * (radius_km / 111) * 2
    lng_offset = (random.random() - 0.5) * (radius_km / 85) * 2  # Adjusted for latitude
    return {
        "lat": center["lat"] + lat_offset,
        "lng": center["lng"] + lng_offset
    }

def create_demo_fleet():
    with app.app_context():
        tenant = Tenant.query.filter_by(name="Puerto Distribución").first()
        if not tenant:
            print("ERROR: Puerto Distribución tenant not found!")
            return
        
        print(f"=== Creating Demo Fleet for: {tenant.name} ===\n")
        
        # Create trucks
        print("📦 Creating Trucks...")
        trucks = []
        for truck_data in TRUCK_DATA:
            existing = Truck.query.filter_by(license_plate=truck_data["plate"]).first()
            if existing:
                print(f"  ⚠️  Truck {truck_data['plate']} already exists, skipping")
                trucks.append(existing)
                continue
            
            location = random_nearby_location(PUERTO_MONTT_CENTER)
            truck = Truck(
                license_plate=truck_data["plate"],
                make_model=truck_data["model"],
                capacity_kg=truck_data["capacity"],
                status='available',
                tenant_id=tenant.id,
                current_lat=location["lat"],
                current_lng=location["lng"],
                last_update=datetime.utcnow()
            )
            db.session.add(truck)
            trucks.append(truck)
            print(f"  ✅ Created: {truck_data['plate']} - {truck_data['model']}")
        
        db.session.flush()
        
        # Create drivers (as users)
        print("\n👤 Creating Drivers...")
        drivers = []
        for driver_data in DRIVER_DATA:
            # Check if user exists
            username = driver_data["name"].lower().replace(" ", "")
            existing = User.query.filter_by(username=username).first()
            if existing:
                print(f"  ⚠️  Driver {driver_data['name']} already exists, skipping")
                drivers.append(existing)
                continue
            
            driver = User(
                username=username,
                role='driver',
                tenant_id=tenant.id
            )
            db.session.add(driver)
            drivers.append(driver)
            print(f"  ✅ Created: {driver_data['name']} ({driver_data['phone']})")
        
        db.session.flush()
        
        # Create sample routes
        print("\n🚛 Creating Sample Routes...")
        today = datetime.utcnow().date()
        
        # Route 1: Today, in progress
        if len(trucks) > 0 and len(drivers) > 0:
            route1 = LogisticsRoute(
                driver_id=drivers[0].id,
                truck_id=trucks[0].id,
                start_time=datetime.combine(today, datetime.min.time().replace(hour=8)),
                status='in_transit'
            )
            trucks[0].status = 'on_route'
            db.session.add(route1)
            print(f"  ✅ Route 1: {drivers[0].username} in {trucks[0].license_plate} (En tránsito)")
        
        # Route 2: Today, planned
        if len(trucks) > 1 and len(drivers) > 1:
            route2 = LogisticsRoute(
                driver_id=drivers[1].id,
                truck_id=trucks[1].id,
                start_time=datetime.combine(today, datetime.min.time().replace(hour=10)),
                status='planned'
            )
            db.session.add(route2)
            print(f"  ✅ Route 2: {drivers[1].username} in {trucks[1].license_plate} (Planificada)")
        
        # Route 3: Yesterday, completed
        if len(trucks) > 2 and len(drivers) > 2:
            yesterday = today - timedelta(days=1)
            route3 = LogisticsRoute(
                driver_id=drivers[2].id,
                truck_id=trucks[2].id,
                start_time=datetime.combine(yesterday, datetime.min.time().replace(hour=9)),
                end_time=datetime.combine(yesterday, datetime.min.time().replace(hour=17)),
                status='completed'
            )
            db.session.add(route3)
            print(f"  ✅ Route 3: {drivers[2].username} in {trucks[2].license_plate} (Completada ayer)")
        
        # Assign some pending sales to routes
        print("\n📋 Assigning Sales to Routes...")
        pending_sales = Sale.query.filter_by(
            tenant_id=tenant.id,
            status='pending'
        ).limit(10).all()
        
        routes = LogisticsRoute.query.filter_by().all()
        if routes and pending_sales:
            for i, sale in enumerate(pending_sales[:5]):
                route = routes[i % len(routes)]
                sale.route_id = route.id
                sale.status = 'assigned'
                print(f"  ✅ Assigned sale #{sale.id} to route #{route.id}")
        
        db.session.commit()
        print("\n✅ Demo fleet created successfully!")
        
        # Summary
        print("\n=== Summary ===")
        print(f"Trucks: {len(trucks)}")
        print(f"Drivers: {len(drivers)}")
        print(f"Routes: {LogisticsRoute.query.count()}")
        print(f"Assigned Sales: {Sale.query.filter_by(status='assigned').count()}")

if __name__ == '__main__':
    create_demo_fleet()
