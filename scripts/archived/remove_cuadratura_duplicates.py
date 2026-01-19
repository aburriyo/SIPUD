#!/usr/bin/env python
"""
Remove duplicate cuadratura sales
The cuadratura data overlaps with the daily Pedidos imports.
This script removes all sales imported from cuadratura.
"""
import sys
sys.path.insert(0, '/Users/bchavez/Software Inventario 2026')

from app import create_app, db
from app.models import Tenant, Sale

app = create_app()

def remove_cuadratura_sales():
    with app.app_context():
        tenant = Tenant.query.filter_by(name="Puerto Distribución").first()
        if not tenant:
            print("ERROR: Puerto Distribución tenant not found!")
            return
        
        print(f"=== Removing Cuadratura duplicate sales for: {tenant.name} ===\n")
        
        # Find all cuadratura sales
        cuadratura_sales = Sale.query.filter(
            Sale.tenant_id == tenant.id,
            Sale.customer_name.like('%Cuadratura%')
        ).all()
        
        print(f"Found {len(cuadratura_sales)} cuadratura sales to remove")
        
        # Confirm
        response = input("Are you sure you want to delete these sales? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return
        
        # Delete them (and their items)
        count = 0
        for sale in cuadratura_sales:
            # Delete sale items first
            for item in sale.items:
                db.session.delete(item)
            # Then delete the sale
            db.session.delete(sale)
            count += 1
            if count % 50 == 0:
                print(f"  Deleted {count} sales...")
        
        db.session.commit()
        print(f"\n✅ Successfully removed {len(cuadratura_sales)} duplicate sales!")
        
        # Verify
        remaining = Sale.query.filter(
            Sale.tenant_id == tenant.id,
            Sale.customer_name.like('%Cuadratura%')
        ).count()
        
        total_sales = Sale.query.filter_by(tenant_id=tenant.id).count()
        
        print(f"Remaining cuadratura sales: {remaining}")
        print(f"Total sales now: {total_sales}")

if __name__ == '__main__':
    remove_cuadratura_sales()
