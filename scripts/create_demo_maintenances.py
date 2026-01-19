#!/usr/bin/env python
"""
Create demo maintenance records for the fleet
"""
import sys
sys.path.insert(0, '/Users/bchavez/Software Inventario 2026')

from app import create_app, db
from app.models import Tenant, Truck, VehicleMaintenance
from datetime import datetime, timedelta, date
import random

app = create_app()

MAINTENANCE_TYPES = ['oil_change', 'preventive', 'tire_rotation', 'inspection', 'repair']

def create_demo_maintenances():
    with app.app_context():
        tenant = Tenant.query.filter_by(name="Puerto Distribución").first()
        if not tenant:
            print("ERROR: Tenant not found!")
            return
        
        trucks = Truck.query.filter_by(tenant_id=tenant.id).all()
        if not trucks:
            print("ERROR: No trucks found!")
            return
        
        print(f"=== Creating Demo Maintenance Records ===\n")
        
        count = 0
        for truck in trucks:
            # Update truck odometer
            truck.odometer_km = random.randint(30000, 80000)
            truck.next_maintenance_km = truck.odometer_km + 5000
            
            # Create past maintenance (completed)
            past_date = date.today() - timedelta(days=random.randint(15, 60))
            past_maint = VehicleMaintenance(
                truck_id=truck.id,
                maintenance_type='oil_change',
                scheduled_date=past_date,
                completed_date=past_date,
                odometer_reading=truck.odometer_km - random.randint(3000, 8000),
                cost=random.randint(25000, 45000),
                notes='Cambio de aceite y filtro. Todo OK.',
                status='completed',
                tenant_id=tenant.id
            )
            truck.last_maintenance_date = past_date
            db.session.add(past_maint)
            count += 1
            
            # Create upcoming maintenance (pending)
            future_date = date.today() + timedelta(days=random.randint(7, 30))
            future_maint = VehicleMaintenance(
                truck_id=truck.id,
                maintenance_type='preventive',
                scheduled_date=future_date,
                odometer_reading=truck.next_maintenance_km,
                cost=0,
                notes='Mantenimiento preventivo programado',
                status='pending',
                tenant_id=tenant.id
            )
            db.session.add(future_maint)
            count += 1
            
            print(f"✅ {truck.license_plate}: Odómetro {truck.odometer_km:,} km")
            print(f"   - Último mtto: {past_date} ({past_maint.odometer_reading:,} km)")
            print(f"   - Próximo mtto: {future_date} ({truck.next_maintenance_km:,} km)\n")
        
        db.session.commit()
        print(f"✅ Created {count} maintenance records!")

if __name__ == '__main__':
    create_demo_maintenances()
