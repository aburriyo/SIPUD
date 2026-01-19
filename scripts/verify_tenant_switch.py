from app import create_app, db
from app.models import Tenant

app = create_app()

def verify_switch():
    with app.test_client() as client:
        with app.app_context():
            t1 = Tenant.query.filter_by(slug='puerto-distribucion').first()
            t2 = Tenant.query.filter_by(slug='copec-malcapower').first()
            
            # Initial Request (Should default to t1)
            resp = client.get('/')
            # We can't easily check 'g' here without a request context, but we can check the rendered template
            # or the session. Let's check session implicitly by checking the switcher link text if we parsed HTML,
            # but simpler: check behaviors.
            
            # Let's hit the switch endpoint
            print(f"Switching to Tenant: {t2.name} (ID: {t2.id})")
            client.get(f'/switch-tenant/{t2.id}', follow_redirects=True)
            
            # Verify session
            with client.session_transaction() as sess:
                current_id = sess.get('tenant_id')
                print(f"Session Tenant ID: {current_id}")
                if current_id == t2.id:
                    print("SUCCESS: Tenant switched correctly in session.")
                else:
                    print(f"FAILED: Expected {t2.id}, got {current_id}")

            # Switch back
            print(f"Switching back to Tenant: {t1.name} (ID: {t1.id})")
            client.get(f'/switch-tenant/{t1.id}', follow_redirects=True)
            
            with client.session_transaction() as sess:
                current_id = sess.get('tenant_id')
                print(f"Session Tenant ID: {current_id}")
                if current_id == t1.id:
                    print("SUCCESS: Tenant switched back correctly.")
                else:
                    print("FAILED: Could not switch back.")

if __name__ == '__main__':
    verify_switch()
