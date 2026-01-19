from datetime import datetime
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False) # subdomain or identifier
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rut = db.Column(db.String(20), unique=True)
    contact_info = db.Column(db.String(200))
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), nullable=False) # 'admin', 'manager', 'warehouse', 'sales'
    full_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
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
            'sales': ['sales', 'inventory_view', 'logistics']
        }
        user_perms = permissions.get(self.role, [])
        return 'all' in user_perms or permission in user_perms
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50), unique=True)
    base_price = db.Column(db.Integer)
    critical_stock = db.Column(db.Integer, default=10)
    category = db.Column(db.String(100), default='Otros')
    tags = db.Column(db.String(200))
    description = db.Column(db.Text)  # NEW: Product description
    expiry_date = db.Column(db.Date, nullable=True)  # NEW: Expiry date for perishable products
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)
    
    lots = db.relationship('Lot', backref='product', lazy=True)

    @property
    def total_stock(self):
        return sum(lot.quantity_current for lot in self.lots)
    
    @property
    def is_bundle(self):
        """Check if this product is a bundle containing other products"""
        return len(self.bundle_components) > 0

class ProductBundle(db.Model):
    """Relationship between bundle products and their component products"""
    __tablename__ = 'product_bundle'
    
    id = db.Column(db.Integer, primary_key=True)
    bundle_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)  # Quantity of component in bundle
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)
    
    # Relationships
    bundle = db.relationship('Product', foreign_keys=[bundle_id], backref='bundle_components')
    component = db.relationship('Product', foreign_keys=[component_id])


class InboundOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=True)
    supplier = db.Column(db.String(200))  # Nombre del proveedor (alternativa a supplier_id)
    invoice_number = db.Column(db.String(50))
    date_received = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Para consistencia
    total = db.Column(db.Integer, default=0)  # Total del pedido
    status = db.Column(db.String(20), default='pending') # pending, received, paid
    notes = db.Column(db.Text)  # Notas del pedido
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)
    
    lots = db.relationship('Lot', backref='inbound_order', lazy=True)

class Lot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    inbound_order_id = db.Column(db.Integer, db.ForeignKey('inbound_order.id'), nullable=False)
    lot_code = db.Column(db.String(50))
    quantity_initial = db.Column(db.Integer, nullable=False)
    quantity_current = db.Column(db.Integer, nullable=False)
    expiry_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Truck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    license_plate = db.Column(db.String(20), unique=True, nullable=False)
    make_model = db.Column(db.String(100))
    capacity_kg = db.Column(db.Float)
    status = db.Column(db.String(20), default='available') # available, on_route, maintenance
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)
    
    # GPS Location (Simulated for now)
    current_lat = db.Column(db.Float)
    current_lng = db.Column(db.Float)
    last_update = db.Column(db.DateTime)
    
    # Maintenance tracking
    odometer_km = db.Column(db.Integer, default=0)
    last_maintenance_date = db.Column(db.Date)
    next_maintenance_km = db.Column(db.Integer)

class VehicleMaintenance(db.Model):
    """Vehicle maintenance records and scheduling"""
    __tablename__ = 'vehicle_maintenance'
    
    id = db.Column(db.Integer, primary_key=True)
    truck_id = db.Column(db.Integer, db.ForeignKey('truck.id'), nullable=False)
    maintenance_type = db.Column(db.String(50))  # 'oil_change', 'preventive', 'tire_rotation', 'inspection', 'repair'
    scheduled_date = db.Column(db.Date)
    completed_date = db.Column(db.Date)
    odometer_reading = db.Column(db.Integer)
    cost = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'completed', 'overdue'
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    truck = db.relationship('Truck', backref='maintenances')

class LogisticsRoute(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    truck_id = db.Column(db.Integer, db.ForeignKey('truck.id'))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='planned') # planned, in_transit, completed
    
    truck = db.relationship('Truck', backref='routes', lazy=True)
    sales = db.relationship('Sale', backref='route', lazy=True)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    status = db.Column(db.String(20), default='pending') # pending, assigned, in_transit, delivered, cancelled
    payment_method = db.Column(db.String(50))
    payment_confirmed = db.Column(db.Boolean, default=False)
    delivery_status = db.Column(db.String(20), default='pending') # pending, in_transit, delivered
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)
    
    route_id = db.Column(db.Integer, db.ForeignKey('logistics_route.id'), nullable=True)
    items = db.relationship('SaleItem', backref='sale', lazy=True)

class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Integer, nullable=False)

    product = db.relationship('Product', backref='sale_items', lazy=True)
    
    @property
    def subtotal(self):
        return self.quantity * self.unit_price

class Wastage(db.Model):
    """Registro de mermas y pérdidas de productos"""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200), nullable=False)  # vencido, dañado, perdido, etc.
    notes = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)
    
    product = db.relationship('Product', backref='wastages', lazy=True)
