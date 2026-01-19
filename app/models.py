from datetime import datetime
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class Tenant(db.Document):
    name = db.StringField(max_length=100, unique=True, required=True)
    slug = db.StringField(max_length=50, unique=True, required=True)
    created_at = db.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'tenants'}


class Supplier(db.Document):
    name = db.StringField(max_length=100, required=True)
    rut = db.StringField(max_length=20, unique=True, sparse=True)
    contact_info = db.StringField(max_length=200)
    tenant = db.ReferenceField(Tenant)
    meta = {'collection': 'suppliers'}


class User(db.Document, UserMixin):
    username = db.StringField(max_length=64, unique=True, required=True)
    email = db.StringField(max_length=120, unique=True, sparse=True)
    password_hash = db.StringField(max_length=256)
    role = db.StringField(max_length=20, required=True)  # admin, manager, warehouse, sales
    full_name = db.StringField(max_length=100)
    is_active = db.BooleanField(default=True)
    tenant = db.ReferenceField(Tenant)
    created_at = db.DateTimeField(default=datetime.utcnow)
    last_login = db.DateTimeField()
    meta = {'collection': 'users'}

    def get_id(self):
        return str(self.id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_permission(self, permission):
        """Check if user role has specific permission"""
        permissions = {
            'admin': ['all'],
            'manager': ['inventory', 'sales', 'warehouse', 'reports'],
            'warehouse': ['warehouse', 'inventory_view'],
            'sales': ['sales', 'inventory_view', 'logistics'],
        }
        user_perms = permissions.get(self.role, [])
        return 'all' in user_perms or permission in user_perms

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Product(db.Document):
    name = db.StringField(max_length=100, required=True)
    sku = db.StringField(max_length=50, unique=True)
    base_price = db.DecimalField(precision=2, default=0)  # FIXED: Decimal for monetary precision
    critical_stock = db.IntField(default=10)
    category = db.StringField(max_length=100, default='Otros')
    tags = db.StringField(max_length=200)
    description = db.StringField()
    expiry_date = db.DateField()
    tenant = db.ReferenceField(Tenant)
    meta = {'collection': 'products'}

    @property
    def total_stock(self):
        lots = Lot.objects(product=self, quantity_current__gt=0)
        return sum(lot.quantity_current for lot in lots)

    @property
    def is_bundle(self):
        """Check if this product is a bundle containing other products"""
        return ProductBundle.objects(bundle=self).count() > 0

    @property
    def lots(self):
        return Lot.objects(product=self)

    @property
    def bundle_components(self):
        return ProductBundle.objects(bundle=self)


class ProductBundle(db.Document):
    """Relationship between bundle products and their component products"""
    bundle = db.ReferenceField(Product, required=True)
    component = db.ReferenceField(Product, required=True)
    quantity = db.IntField(default=1, required=True)
    tenant = db.ReferenceField(Tenant)
    meta = {'collection': 'product_bundles'}


class InboundOrder(db.Document):
    supplier = db.ReferenceField(Supplier)  # FIXED: Only reference to Supplier
    supplier_name = db.StringField(max_length=200)  # Cache of supplier name
    invoice_number = db.StringField(max_length=50)
    date_received = db.DateTimeField()
    created_at = db.DateTimeField(default=datetime.utcnow)
    total = db.DecimalField(precision=2, default=0)  # FIXED: Decimal for monetary precision
    status = db.StringField(max_length=20, default='pending')  # pending, received, paid
    notes = db.StringField()
    tenant = db.ReferenceField(Tenant)
    meta = {'collection': 'inbound_orders'}

    @property
    def lots(self):
        return Lot.objects(order=self)


class Lot(db.Document):
    product = db.ReferenceField(Product, required=True)
    order = db.ReferenceField(InboundOrder)
    tenant = db.ReferenceField(Tenant)
    lot_code = db.StringField(max_length=50)
    quantity_initial = db.IntField(required=True)
    quantity_current = db.IntField(required=True)
    expiry_date = db.DateField()
    created_at = db.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'lots'}


class Sale(db.Document):
    customer_name = db.StringField(max_length=100)
    address = db.StringField(max_length=200)
    phone = db.StringField(max_length=20)
    status = db.StringField(max_length=20, default='pending')  # pending, assigned, in_transit, delivered, cancelled
    payment_method = db.StringField(max_length=200)
    payment_confirmed = db.BooleanField(default=False)
    delivery_status = db.StringField(max_length=20, default='pending')  # pending, in_transit, delivered
    date_created = db.DateTimeField(default=datetime.utcnow)
    tenant = db.ReferenceField(Tenant)
    route = db.ReferenceField('LogisticsRoute')  # Fleet - kept disabled but preserved
    meta = {'collection': 'sales'}

    @property
    def items(self):
        return SaleItem.objects(sale=self)


class SaleItem(db.Document):
    sale = db.ReferenceField(Sale, required=True)
    product = db.ReferenceField(Product, required=True)
    quantity = db.IntField(required=True)
    unit_price = db.DecimalField(precision=2, required=True)  # FIXED: Decimal for monetary precision
    meta = {'collection': 'sale_items'}

    @property
    def subtotal(self):
        return self.quantity * float(self.unit_price)


class Wastage(db.Document):
    """Registro de mermas y pérdidas de productos"""
    product = db.ReferenceField(Product, required=True)
    quantity = db.IntField(required=True)
    reason = db.StringField(max_length=200, required=True)  # vencido, dañado, perdido, etc.
    notes = db.StringField()
    date_created = db.DateTimeField(default=datetime.utcnow)
    tenant = db.ReferenceField(Tenant)
    meta = {'collection': 'wastages'}


# ============================================
# FLEET/LOGISTICS - DISABLED BUT PRESERVED
# ============================================
# These models are kept for future implementation
# but are not actively used in the application

class Truck(db.Document):
    license_plate = db.StringField(max_length=20, unique=True, required=True)
    make_model = db.StringField(max_length=100)
    capacity_kg = db.FloatField()
    status = db.StringField(max_length=20, default='available')  # available, on_route, maintenance
    tenant = db.ReferenceField(Tenant)
    current_lat = db.FloatField()
    current_lng = db.FloatField()
    last_update = db.DateTimeField()
    odometer_km = db.IntField(default=0)
    last_maintenance_date = db.DateField()
    next_maintenance_km = db.IntField()
    meta = {'collection': 'trucks'}


class VehicleMaintenance(db.Document):
    """Vehicle maintenance records and scheduling"""
    truck = db.ReferenceField(Truck, required=True)
    maintenance_type = db.StringField(max_length=50)  # oil_change, preventive, tire_rotation, inspection, repair
    scheduled_date = db.DateField()
    completed_date = db.DateField()
    odometer_reading = db.IntField()
    cost = db.DecimalField(precision=2, default=0)
    notes = db.StringField()
    status = db.StringField(max_length=20, default='pending')  # pending, completed, overdue
    tenant = db.ReferenceField(Tenant)
    created_at = db.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'vehicle_maintenances'}


class LogisticsRoute(db.Document):
    driver = db.ReferenceField(User)
    truck = db.ReferenceField(Truck)
    start_time = db.DateTimeField()
    end_time = db.DateTimeField()
    status = db.StringField(max_length=20, default='planned')  # planned, in_transit, completed
    meta = {'collection': 'logistics_routes'}
