
import requests
import json
import sys
import datetime

# Configuration
BASE_URL = 'http://localhost:5000'
LOGIN_URL = f'{BASE_URL}/login'
PRODUCTS_URL = f'{BASE_URL}/api/products'
ASSEMBLY_URL = f'{BASE_URL}/warehouse/api/assembly'
WAREHOUSE_RECEIVING_URL = f'{BASE_URL}/warehouse/api/orders' # Create order
WAREHOUSE_CONFIRM_URL = f'{BASE_URL}/warehouse/api/receiving' # Confirm order

# Credentials (adjust if needed, assuming default admin/password from seed or typical dev environment)
# IMPORTANT: You might need to adjust this if you don't know a valid user.
# For now, I'll assume we can use the app context directly if I were running it as a script inside the app,
# but since I'm simulating external access, I need a user.
# Let's try to use a script that imports app context instead to avoid login issues if possible.
# Actually, let's write this as a script that runs within the flask app context to be safer and easier.

from app import create_app
from app.models import db, User, Product, ProductBundle, Lot, InboundOrder, Tenant, Supplier
from config import Config

app = create_app()
app.config['WTF_CSRF_ENABLED'] = False

def run_test():
    with app.app_context():
        print("Starting Verification...")
        
        # 1. Setup Data
        # Get or Create Tenant
        tenant = Tenant.query.first()
        if not tenant:
            tenant = Tenant(name="Test Tenant", slug="test")
            db.session.add(tenant)
            db.session.commit()
            
        # Create a dummy user context (flask-login is tricky in scripts, but we can simulate requests or just call logic directly?
        # The logic is in the route. To test the route properly, we should use the test client.
        
        client = app.test_client()

        # Cleanup potential leftovers
        print("Cleaning up matchin SKUs...")
        for sku in ['COMP-A', 'COMP-B', 'BOX-001']:
             p = Product.query.filter_by(sku=sku).first()
             if p:
                 # Delete dependencies manually if needed, or rely on cascade if configured (SQLite cascade support varies)
                 # Manual delete safe
                 ProductBundle.query.filter_by(bundle_id=p.id).delete()
                 ProductBundle.query.filter_by(component_id=p.id).delete()
                 for l in p.lots: db.session.delete(l)
                 db.session.delete(p)
        db.session.commit()
        
        # Login (Manual login simulation or force session)
        # Check if user exists
        user = User.query.filter_by(username='admin').first()
        if not user:
            user = User(username='admin', email='admin@example.com', role='admin', tenant_id=tenant.id)
            db.session.add(user)
        
        user.set_password('password')
        db.session.commit()
            
        login_resp = client.post('/login', data={'username': 'admin', 'password': 'password'}, follow_redirects=True)
        if b'Dashboard' not in login_resp.data and login_resp.status_code != 200:
             print("Login failed, cannot proceed with route testing.")
             # Setup manually login_user? No, test_client should handle cookies.
             
        # Create Component Products
        comp1 = Product(name="Component A", sku="COMP-A", base_price=100, tenant_id=tenant.id, critical_stock=10)
        comp2 = Product(name="Component B", sku="COMP-B", base_price=200, tenant_id=tenant.id, critical_stock=10)
        db.session.add_all([comp1, comp2])
        db.session.commit()
        
        # Create Supplier
        supplier = db.session.query(Supplier).filter_by(name="Test Supplier").first()
        if not supplier:
            supplier = Supplier(name="Test Supplier", rut="11111111-1", tenant_id=tenant.id)
            db.session.add(supplier)
            db.session.commit()

        # Add Stock to Components
        order = InboundOrder(supplier_id=supplier.id, supplier=supplier.name, status='received', date_received=datetime.datetime.utcnow(), tenant_id=tenant.id)
        db.session.add(order)
        db.session.commit()
        
        lot1 = Lot(product_id=comp1.id, inbound_order_id=order.id, lot_code="LOT-A", quantity_initial=100, quantity_current=100, created_at=datetime.datetime.utcnow())
        lot2 = Lot(product_id=comp2.id, inbound_order_id=order.id, lot_code="LOT-B", quantity_initial=100, quantity_current=100, created_at=datetime.datetime.utcnow())
        db.session.add_all([lot1, lot2])
        db.session.commit()
        
        print(f"Initial Stock: CompA={comp1.total_stock}, CompB={comp2.total_stock}")
        
        # Create Bundle Product
        bundle = Product(name="Box Bundle", sku="BOX-001", base_price=500, tenant_id=tenant.id, critical_stock=5)
        db.session.add(bundle)
        db.session.commit()
        
        # Define Bundle Logic (1 Box = 2 CompA + 1 CompB)
        pb1 = ProductBundle(bundle_id=bundle.id, component_id=comp1.id, quantity=2, tenant_id=tenant.id)
        pb2 = ProductBundle(bundle_id=bundle.id, component_id=comp2.id, quantity=1, tenant_id=tenant.id)
        db.session.add_all([pb1, pb2])
        db.session.commit()
        
        print("Bundle Created: 1 Box = 2 CompA + 1 CompB")
        
        # 2. Execute Assembly via Endpoint
        qty_to_assemble = 10
        print(f"Attempting to assemble {qty_to_assemble} bundles...")
        
        # We need to be logged in effectively. 
        # Since I am using test_client, let's trick login_required or just ensure previous login worked.
        
        response = client.post('/warehouse/api/assembly', json={
            'bundle_id': bundle.id,
            'quantity': qty_to_assemble
        })
        
        print(f"Response: {response.status_code} - {response.get_json()}")
        
        if response.status_code != 201:
            print("FAILED: Assembly endpoint returned error.")
            # Cleanup
            db.session.delete(pb1); db.session.delete(pb2); 
            db.session.delete(lot1); db.session.delete(lot2);
            db.session.delete(comp1); db.session.delete(comp2); db.session.delete(bundle);
            db.session.delete(order);
            db.session.commit()
            return
            
        # 3. Verify Stock
        # Refresh objects
        db.session.expire_all()
        
        expected_comp1 = 100 - (2 * qty_to_assemble) # 100 - 20 = 80
        expected_comp2 = 100 - (1 * qty_to_assemble) # 100 - 10 = 90
        expected_bundle = qty_to_assemble # 10
        
        print(f"New Stock: CompA={comp1.total_stock} (Expected {expected_comp1})")
        print(f"New Stock: CompB={comp2.total_stock} (Expected {expected_comp2})")
        print(f"New Stock: Bundle={bundle.total_stock} (Expected {expected_bundle})")
        
        success = True
        if comp1.total_stock != expected_comp1: success = False
        if comp2.total_stock != expected_comp2: success = False
        if bundle.total_stock != expected_bundle: success = False
        
        if success:
            print("SUCCESS: Stock logic verified correctly.")
        else:
            print("FAILURE: Stock mismatch.")
            
        # Cleanup (Optional, but good for repetitive runs)
        # For now, I'll leave data or delete it. Let's delete to keep clean.
        # Find the new lot for bundle
        bundle_lots = Lot.query.filter_by(product_id=bundle.id).all()
        for l in bundle_lots: db.session.delete(l)
        
        db.session.delete(pb1); db.session.delete(pb2); 
        db.session.delete(lot1); db.session.delete(lot2);
        db.session.delete(comp1); db.session.delete(comp2); db.session.delete(bundle);
        # Also delete the internal order if created? A bit complex to find exact one without ID, 
        # but safe to ignore for test environment.
        db.session.commit()

if __name__ == "__main__":
    run_test()
