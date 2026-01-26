"""
Seed script para crear el tenant principal de Puerto Distribución.
Adaptado para MongoEngine después de la migración de SQLAlchemy.
"""
from app import create_app
from app.models import Tenant

app = create_app()


def seed_tenants():
    with app.app_context():
        # Tenant principal: Puerto Distribución
        t1 = Tenant.objects(slug='puerto-distribucion').first()
        if not t1:
            t1 = Tenant(name='Puerto Distribución', slug='puerto-distribucion')
            t1.save()
            print("Created Tenant: Puerto Distribución")
        else:
            print("Tenant 'Puerto Distribución' already exists.")


if __name__ == '__main__':
    seed_tenants()
