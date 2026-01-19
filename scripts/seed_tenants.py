from app import create_app, db
from app.models import Tenant

app = create_app()

def seed_tenants():
    with app.app_context():
        # Tenant 1: Puerto Distribución
        t1 = Tenant.query.filter_by(slug='puerto-distribucion').first()
        if not t1:
            t1 = Tenant(name='Puerto Distribución', slug='puerto-distribucion')
            db.session.add(t1)
            print("Created Tenant: Puerto Distribución")
        else:
            print("Tenant 'Puerto Distribución' already exists.")

        # Tenant 2: Copec MalcaPower
        t2 = Tenant.query.filter_by(slug='copec-malcapower').first()
        if not t2:
            t2 = Tenant(name='Copec MalcaPower', slug='copec-malcapower')
            db.session.add(t2)
            print("Created Tenant: Copec MalcaPower")
        else:
            print("Tenant 'Copec MalcaPower' already exists.")

        db.session.commit()

if __name__ == '__main__':
    seed_tenants()
