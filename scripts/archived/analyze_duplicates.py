#!/usr/bin/env python
"""
Analyze potential duplicate sales between cuadratura import and daily Pedidos import
"""
import sys
sys.path.insert(0, '/Users/bchavez/Software Inventario 2026')

from app import create_app, db
from app.models import Tenant, Sale, SaleItem
from sqlalchemy import func, and_
from datetime import datetime
from collections import defaultdict

app = create_app()

def analyze_duplicates():
    with app.app_context():
        tenant = Tenant.query.filter_by(name="Puerto Distribución").first()
        if not tenant:
            print("ERROR: Puerto Distribución tenant not found!")
            return
        
        print(f"=== Analyzing sales for: {tenant.name} ===\n")
        
        # Get all sales grouped by date
        sales_by_date = defaultdict(list)
        all_sales = Sale.query.filter_by(tenant_id=tenant.id).order_by(Sale.date_created).all()
        
        for sale in all_sales:
            date_key = sale.date_created.date()
            
            # Calculate total
            total = sum(item.quantity * item.unit_price for item in sale.items)
            
            sales_by_date[date_key].append({
                'id': sale.id,
                'customer': sale.customer_name,
                'total': total,
                'items_count': len(sale.items),
                'created': sale.date_created
            })
        
        print(f"Total unique dates with sales: {len(sales_by_date)}")
        print(f"Total sales: {len(all_sales)}\n")
        
        # Identify dates with multiple sales
        print("=== Dates with multiple sales (potential duplicates): ===\n")
        
        duplicate_dates = []
        for date, sales in sorted(sales_by_date.items()):
            if len(sales) > 1:
                duplicate_dates.append(date)
                print(f"📅 {date.strftime('%Y-%m-%d')} - {len(sales)} sales:")
                
                cuadratura_sales = [s for s in sales if 'Cuadratura' in s['customer']]
                pedidos_sales = [s for s in sales if 'Cuadratura' not in s['customer']]
                
                print(f"   - Cuadratura imports: {len(cuadratura_sales)}")
                print(f"   - Daily Pedidos imports: {len(pedidos_sales)}")
                
                if cuadratura_sales and pedidos_sales:
                    print(f"   ⚠️  POTENTIAL OVERLAP!")
                
                for sale in sales:
                    print(f"      #{sale['id']}: {sale['customer'][:30]} - ${sale['total']:,.0f} ({sale['items_count']} items)")
                print()
        
        # Statistics
        print(f"\n=== Summary ===")
        print(f"Dates with potential duplicates: {len(duplicate_dates)}")
        
        cuadratura_count = Sale.query.filter(
            Sale.tenant_id == tenant.id,
            Sale.customer_name.like('%Cuadratura%')
        ).count()
        
        pedidos_count = Sale.query.filter(
            Sale.tenant_id == tenant.id,
            ~Sale.customer_name.like('%Cuadratura%')
        ).count()
        
        print(f"Total Cuadratura sales: {cuadratura_count}")
        print(f"Total Pedidos sales: {pedidos_count}")
        print(f"Grand total: {cuadratura_count + pedidos_count}")
        
        # Check date ranges
        cuadratura_sales = Sale.query.filter(
            Sale.tenant_id == tenant.id,
            Sale.customer_name.like('%Cuadratura%')
        ).order_by(Sale.date_created).all()
        
        if cuadratura_sales:
            print(f"\nCuadratura date range: {cuadratura_sales[0].date_created.date()} to {cuadratura_sales[-1].date_created.date()}")
        
        pedidos_sales = Sale.query.filter(
            Sale.tenant_id == tenant.id,
            ~Sale.customer_name.like('%Cuadratura%')
        ).order_by(Sale.date_created).all()
        
        if pedidos_sales:
            print(f"Pedidos date range: {pedidos_sales[0].date_created.date()} to {pedidos_sales[-1].date_created.date()}")

if __name__ == '__main__':
    analyze_duplicates()
