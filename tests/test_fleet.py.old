#!/usr/bin/env python
"""
Script rápido para crear vehículos de prueba con coordenadas GPS
"""
from app import create_app, db
from app.models import Truck, Tenant
from datetime import datetime

app = create_app()

with app.app_context():
    # Obtener el tenant actual
    tenant = Tenant.query.first()
    if not tenant:
        print("❌ No hay tenants en la base de datos")
        exit(1)
    
    print(f"✅ Tenant encontrado: {tenant.name}")
    
    # Verificar vehículos existentes
    existing_trucks = Truck.query.filter_by(tenant_id=tenant.id).all()
    print(f"📊 Vehículos existentes: {len(existing_trucks)}")
    
    if len(existing_trucks) == 0:
        print("\n🚛 Creando vehículos de prueba...")
        
        trucks_data = [
            {
                "plate": "CDZY-12",
                "model": "Hyundai H100 2018",
                "capacity": 1200,
                "lat": -41.4693,
                "lng": -72.9424,
                "status": "available"
            },
            {
                "plate": "FHTX-34",
                "model": "Chevrolet N300 2020",
                "capacity": 800,
                "lat": -41.4750,
                "lng": -72.9380,
                "status": "on_route"
            },
            {
                "plate": "BJKL-56",
                "model": "Kia K2700 2019",
                "capacity": 1500,
                "lat": -41.4620,
                "lng": -72.9500,
                "status": "available"
            },
            {
                "plate": "RSTW-78",
                "model": "JAC X200 2021",
                "capacity": 1000,
                "lat": -41.4800,
                "lng": -72.9300,
                "status": "maintenance"
            },
        ]
        
        for truck_data in trucks_data:
            truck = Truck(
                license_plate=truck_data["plate"],
                make_model=truck_data["model"],
                capacity_kg=truck_data["capacity"],
                status=truck_data["status"],
                current_lat=truck_data["lat"],
                current_lng=truck_data["lng"],
                odometer_km=50000,
                last_update=datetime.utcnow(),
                tenant_id=tenant.id
            )
            db.session.add(truck)
            print(f"  ✅ Creado: {truck_data['plate']} en ({truck_data['lat']}, {truck_data['lng']})")
        
        db.session.commit()
        print("\n✅ Vehículos de prueba creados exitosamente!")
    else:
        print("\n📍 Actualizando coordenadas de vehículos existentes...")
        coords = [
            (-41.4693, -72.9424),
            (-41.4750, -72.9380),
            (-41.4620, -72.9500),
            (-41.4800, -72.9300),
        ]
        
        for i, truck in enumerate(existing_trucks[:4]):
            if i < len(coords):
                truck.current_lat = coords[i][0]
                truck.current_lng = coords[i][1]
                truck.last_update = datetime.utcnow()
                print(f"  ✅ Actualizado: {truck.license_plate} -> ({coords[i][0]}, {coords[i][1]})")
        
        db.session.commit()
        print("\n✅ Coordenadas actualizadas!")
    
    # Mostrar resumen
    print("\n" + "="*60)
    print("RESUMEN DE VEHÍCULOS CON GPS")
    print("="*60)
    all_trucks = Truck.query.filter_by(tenant_id=tenant.id).all()
    for truck in all_trucks:
        gps_status = "✅ GPS OK" if truck.current_lat and truck.current_lng else "❌ Sin GPS"
        print(f"{truck.license_plate:12} | {truck.make_model:25} | {gps_status}")
        if truck.current_lat and truck.current_lng:
            print(f"             | Coordenadas: ({truck.current_lat}, {truck.current_lng})")
    print("="*60)
