from app import create_app,db
from app.models import Product, Lot, Sale, SaleItem, InboundOrder
import json

app = create_app()

def verify_stock_logic():
    with app.app_context():
        # Setup
        print("--- Setting up Test Data ---")
        # Clean up previous test
        old_p = Product.query.filter_by(sku='TEST-STOCK-001').first()
        if old_p:
            print(f"Deleting old product {old_p.name}")
            # Delete related sale items and lots for cleanup if needed, but for now just ignore or reuse
            # Simple way: create new unique SKU
        
        import uuid
        sku = f'TEST-STOCK-{str(uuid.uuid4())[:8]}'
        
        p = Product(name='Stock Test Product', sku=sku, base_price=1000)
        db.session.add(p)
        db.session.commit()
        
        # Add Initial Stock (Lot)
        # We need a dummy supplier and inbound order for context if strict, but let's see if we can just create a Lot
        # Lot requires inbound_order_id, let's make a dummy one
        
        from app.models import Supplier
        sup = Supplier.query.first()
        if not sup:
            sup = Supplier(name='Test Supplier', rut='1-9')
            db.session.add(sup)
            db.session.commit()
            
        order = InboundOrder(supplier_id=sup.id, invoice_number='INV-001')
        db.session.add(order)
        db.session.commit()
        
        lot = Lot(
            product_id=p.id,
            inbound_order_id=order.id,
            lot_code='LOT-001',
            quantity_initial=10,
            quantity_current=10
        )
        db.session.add(lot)
        db.session.commit()
        
        print(f"Product created: {p.name} (ID: {p.id})")
        print(f"Initial Stock: {p.total_stock} (Expected: 10)")
        
        if p.total_stock != 10:
            print("FAILED: Initial stock is incorrect")
            return

        # Create Client
        client = app.test_client()
        
        # Test 1: Successful Sale
        print("\n--- Test 1: Sell 3 units ---")
        payload = {
            'customer': 'Test Client',
            'items': [
                {'product_id': p.id, 'quantity': 3}
            ]
        }
        
        resp = client.post('/api/sales', json=payload)
        if resp.status_code == 201:
            print("Sale created successfully.")
        else:
            print(f"FAILED: Sale creation failed. Status: {resp.status_code}, Body: {resp.get_json()}")
            return
            
        # Verify Stock Deduction
        db.session.expire(p) # Refresh
        # Also need to refresh the lot to get updated quantity
        # but p.total_stock property re-queries lots? 
        # Actually p.lots is a relationship, so we might need to refresh lots explicitly or re-query product
        
        p = Product.query.get(p.id)
        current_stock = p.total_stock
        print(f"Current Stock: {current_stock} (Expected: 7)")
        
        if current_stock != 7:
            print("FAILED: Stock not deducted correctly.")
            return
            
        # Test 2: Excessive Sale (Stock Validation)
        print("\n--- Test 2: Sell 8 units (Should Fail, only 7 left) ---")
        payload = {
            'customer': 'Test Client',
            'items': [
                {'product_id': p.id, 'quantity': 8}
            ]
        }
        
        resp = client.post('/api/sales', json=payload)
        if resp.status_code == 500 or resp.status_code == 400:
             print(f"Sale rejected correctly. Status: {resp.status_code}")
             print(f"Error Message: {resp.get_json().get('error')}")
        else:
            print(f"FAILED: Sale should have been rejected. Status: {resp.status_code}")
            return
            
        # Final Check
        p = Product.query.get(p.id)
        print(f"\nFinal Stock: {p.total_stock} (Expected: 7)")
        
        print("\n>>> VERIFICATION SUCCESS <<<")

if __name__ == '__main__':
    verify_stock_logic()
