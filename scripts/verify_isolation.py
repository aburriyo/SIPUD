from app import create_app, db
from app.models import Tenant, Product
import json

app = create_app()

def verify_isolation():
    with app.test_client() as client:
        with app.app_context():
            t1 = Tenant.query.filter_by(slug='puerto-distribucion').first()
            t2 = Tenant.query.filter_by(slug='copec-malcapower').first()
            
            # --- Step 1: Create Product in T1 ---
            print(f"--- Switching to {t1.name} ---")
            client.get(f'/switch-tenant/{t1.id}', follow_redirects=True)
            
            p1_sku = "ISO-TEST-T1"
            # Cleanup
            Product.query.filter_by(sku=p1_sku).delete()
            db.session.commit()
            
            print(f"Creating product {p1_sku} in {t1.name}")
            resp = client.post('/api/products', json={'name': 'T1 Product', 'sku': p1_sku, 'base_price': 100})
            if resp.status_code != 201:
                print(f"FAILED to create product in T1: {resp.get_json()}")
                return

            # Verify it's in the list
            resp = client.get('/api/products')
            products = resp.get_json()
            if not any(p['sku'] == p1_sku for p in products):
                print("FAILED: Product not found in T1 list")
                return
            print("Product confirmed in T1.")


            # --- Step 2: Switch to T2 ---
            print(f"\n--- Switching to {t2.name} ---")
            client.get(f'/switch-tenant/{t2.id}', follow_redirects=True)
            
            # Verify T1 product is NOT visible
            resp = client.get('/api/products')
            products = resp.get_json()
            if any(p['sku'] == p1_sku for p in products):
                print(f"FAILED: T1 Product {p1_sku} leaked into T2!")
                return
            print(f"SUCCESS: T1 Product {p1_sku} is NOT visible in T2.")
            
            # --- Step 3: Create Product in T2 ---
            p2_sku = "ISO-TEST-T2"
            # Cleanup
            Product.query.filter_by(sku=p2_sku).delete()
            db.session.commit()

            print(f"Creating product {p2_sku} in {t2.name}")
            resp = client.post('/api/products', json={'name': 'T2 Product', 'sku': p2_sku, 'base_price': 200})
            if resp.status_code != 201:
                 print(f"FAILED to create product in T2: {resp.get_json()}")
                 return

            # Verify it's in the list
            resp = client.get('/api/products')
            products = resp.get_json()
            if not any(p['sku'] == p2_sku for p in products):
                print("FAILED: Product not found in T2 list")
                return
            print("Product confirmed in T2.")


            # --- Step 4: Switch back to T1 ---
            print(f"\n--- Switching back to {t1.name} ---")
            client.get(f'/switch-tenant/{t1.id}', follow_redirects=True)
            
            # Verify T2 product is NOT visible
            resp = client.get('/api/products')
            products = resp.get_json()
            if any(p['sku'] == p2_sku for p in products):
                print(f"FAILED: T2 Product {p2_sku} leaked into T1!")
                return
            print(f"SUCCESS: T2 Product {p2_sku} is NOT visible in T1.")
            
            print("\n>>> ISOLATION VERIFICATION SUCCESS <<<")

if __name__ == '__main__':
    verify_isolation()
