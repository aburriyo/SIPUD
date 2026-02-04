from datetime import datetime
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


# ============================================
# PERMISSIONS CONFIGURATION
# ============================================
ROLE_PERMISSIONS = {
    'admin': {
        'users': ['view', 'create', 'edit', 'delete'],
        'products': ['view', 'create', 'edit', 'delete'],
        'sales': ['view', 'create', 'edit', 'cancel'],
        'orders': ['view', 'create', 'receive', 'delete'],
        'wastage': ['view', 'create', 'delete'],
        'reports': ['view', 'export'],
        'activity_log': ['view'],
        'customers': ['view', 'create', 'export', 'sync'],
    },
    'manager': {
        'users': ['view', 'create', 'edit'],  # No delete
        'products': ['view', 'create', 'edit', 'delete'],
        'sales': ['view', 'create', 'edit', 'cancel'],
        'orders': ['view', 'create', 'receive', 'delete'],
        'wastage': ['view', 'create', 'delete'],
        'reports': ['view', 'export'],
        'activity_log': [],  # No access
        'customers': ['view', 'create', 'export'],
    },
    'warehouse': {
        'users': [],
        'products': ['view'],
        'sales': ['view'],
        'orders': ['view', 'create', 'receive'],
        'wastage': ['view', 'create'],
        'reports': ['view'],
        'activity_log': [],
        'customers': [],
    },
    'sales': {
        'users': [],
        'products': ['view'],
        'sales': ['view', 'create'],
        'orders': [],
        'wastage': [],
        'reports': ['view', 'export'],
        'activity_log': [],
        'customers': ['view'],
    },
}

# ============================================
# STATUS CONSTANTS
# ============================================
DELIVERY_STATUSES = {
    'pendiente': 'Pendiente',
    'en_preparacion': 'En Preparación',
    'en_transito': 'En Tránsito',
    'entregado': 'Entregado',
    'con_observaciones': 'Entregado con Observaciones',
    'cancelado': 'Cancelado'
}

PAYMENT_STATUSES = {
    'pendiente': 'Pago Pendiente',
    'parcial': 'Pago Parcial',
    'pagado': 'Pagado'
}

SALE_TYPES = {
    'con_despacho': 'Con Despacho',
    'en_local': 'Venta en Local'
}

PAYMENT_VIAS = {
    'efectivo': 'Efectivo',
    'transferencia': 'Transferencia',
    'tarjeta': 'Tarjeta',
    'otro': 'Otro'
}

SALES_CHANNELS = {
    'manual': 'Manual (SIPUD)',
    'whatsapp': 'WhatsApp',
    'shopify': 'Shopify',
    'web': 'Web'
}


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

    def has_permission(self, module, action='view'):
        """
        Check if user role has specific permission for a module and action.

        Usage:
            user.has_permission('products', 'create')
            user.has_permission('users', 'delete')
            user.has_permission('activity_log', 'view')
        """
        role_perms = ROLE_PERMISSIONS.get(self.role, {})
        module_perms = role_perms.get(module, [])
        return action in module_perms

    def can(self, module, action='view'):
        """Alias for has_permission"""
        return self.has_permission(module, action)

    def get_permissions(self):
        """Get all permissions for this user's role"""
        return ROLE_PERMISSIONS.get(self.role, {})

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
    shopify_id = db.StringField(max_length=50)  # Link to Shopify product
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

    # Legacy fields (maintained for backward compatibility)
    status = db.StringField(max_length=20, default='pending')  # pending, assigned, in_transit, delivered, cancelled
    payment_method = db.StringField(max_length=200)  # DEPRECATED: use Payment model instead
    payment_confirmed = db.BooleanField(default=False)  # DEPRECATED: use payment_status instead

    # New fields
    sale_type = db.StringField(
        max_length=20,
        default='con_despacho',
        choices=['con_despacho', 'en_local']
    )

    # Sales channel (origin of the sale)
    sales_channel = db.StringField(
        max_length=20,
        default='manual',
        choices=['manual', 'whatsapp', 'shopify', 'web']
    )

    # Delivery fields
    delivery_status = db.StringField(
        max_length=20,
        default='pendiente',
        choices=['pendiente', 'en_preparacion', 'en_transito', 'entregado', 'con_observaciones', 'cancelado']
    )
    delivery_observations = db.StringField(max_length=500)
    date_delivered = db.DateTimeField()

    # Payment status (calculated from Payment collection)
    payment_status = db.StringField(
        max_length=20,
        default='pendiente',
        choices=['pendiente', 'pagado', 'parcial']
    )

    # Dates
    date_created = db.DateTimeField(default=datetime.utcnow)

    # Shopify link (read-only sync)
    shopify_order_id = db.StringField(max_length=50)  # Shopify order ID for sync tracking
    shopify_order_number = db.IntField()  # Shopify order number (#1001, etc.)

    # References
    tenant = db.ReferenceField(Tenant)
    route = db.ReferenceField('LogisticsRoute')  # Fleet - kept disabled but preserved

    meta = {'collection': 'sales'}

    @property
    def items(self):
        return SaleItem.objects(sale=self)

    @property
    def total_amount(self):
        """Calcula el monto total de la venta"""
        return sum(item.quantity * float(item.unit_price) for item in self.items)

    @property
    def total_paid(self):
        """Suma todos los pagos registrados"""
        from app.models import Payment  # Import here to avoid circular dependency
        return sum(float(p.amount) for p in Payment.objects(sale=self))

    @property
    def balance_pending(self):
        """Calcula saldo pendiente"""
        return self.total_amount - self.total_paid

    @property
    def computed_payment_status(self):
        """Calcula payment_status desde pagos registrados"""
        total = self.total_amount
        paid = self.total_paid

        if paid >= total:
            return 'pagado'
        elif paid > 0:
            return 'parcial'
        else:
            return 'pendiente'

    @property
    def computed_status(self):
        """Calcula status legacy desde delivery_status"""
        status_map = {
            'pendiente': 'pending',
            'en_preparacion': 'assigned',
            'en_transito': 'in_transit',
            'entregado': 'delivered',
            'con_observaciones': 'delivered',
            'cancelado': 'cancelled'
        }
        return status_map.get(self.delivery_status, 'pending')


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


class Payment(db.Document):
    """
    Registro de pagos para una venta.
    Permite múltiples abonos con historial completo.
    """
    sale = db.ReferenceField(Sale, required=True)
    tenant = db.ReferenceField(Tenant, required=True)

    # Detalles del pago
    amount = db.DecimalField(precision=2, required=True)
    payment_via = db.StringField(
        max_length=50,
        required=True,
        choices=['efectivo', 'transferencia', 'tarjeta', 'otro']
    )
    payment_reference = db.StringField(max_length=200)  # Número de transferencia, etc.
    notes = db.StringField(max_length=500)  # Notas adicionales

    # Auditoría
    date_created = db.DateTimeField(default=datetime.utcnow)
    created_by = db.ReferenceField(User)

    meta = {
        'collection': 'payments',
        'indexes': [
            'sale',
            'tenant',
            '-date_created'
        ],
        'ordering': ['-date_created']
    }


# ============================================
# ACTIVITY LOG - MONITOR DE ACTIVIDADES
# ============================================
class ActivityLog(db.Document):
    """
    Registro de todas las actividades del sistema.
    Solo visible para administradores.
    """
    user = db.ReferenceField('User', required=True)
    user_name = db.StringField(max_length=100)  # Cache del nombre
    user_role = db.StringField(max_length=20)   # Cache del rol
    action = db.StringField(max_length=50, required=True)  # create, update, delete, login, logout, etc.
    module = db.StringField(max_length=50, required=True)  # products, sales, users, orders, etc.
    description = db.StringField(max_length=500)
    details = db.DictField()  # JSON con detalles adicionales
    target_id = db.StringField(max_length=50)  # ID del objeto afectado
    target_type = db.StringField(max_length=50)  # Tipo de objeto (Product, Sale, etc.)
    ip_address = db.StringField(max_length=45)
    user_agent = db.StringField(max_length=500)
    tenant = db.ReferenceField(Tenant)
    created_at = db.DateTimeField(default=datetime.utcnow)
    meta = {
        'collection': 'activity_logs',
        'indexes': [
            '-created_at',
            'user',
            'action',
            'module',
            'tenant'
        ],
        'ordering': ['-created_at']
    }

    @classmethod
    def log(cls, user, action, module, description=None, details=None,
            target_id=None, target_type=None, request=None, tenant=None):
        """
        Método helper para crear logs fácilmente.

        Usage:
            ActivityLog.log(
                user=current_user,
                action='create',
                module='products',
                description='Creó producto "Pan Integral"',
                target_id=str(product.id),
                target_type='Product',
                request=request
            )
        """
        log_entry = cls(
            user=user,
            user_name=user.full_name or user.username,
            user_role=user.role,
            action=action,
            module=module,
            description=description,
            details=details or {},
            target_id=target_id,
            target_type=target_type,
            ip_address=request.remote_addr if request else None,
            user_agent=request.user_agent.string[:500] if request and request.user_agent else None,
            tenant=tenant or (user.tenant if user else None)
        )
        log_entry.save()
        return log_entry


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


# ============================================
# SHOPIFY INTEGRATION - CUSTOMERS & ORDERS
# ============================================
class ShopifyCustomer(db.Document):
    """Cliente (Shopify, manual o importado)"""
    name = db.StringField(max_length=200)
    email = db.StringField(max_length=200)
    phone = db.StringField(max_length=50)
    
    # Address fields
    address_city = db.StringField(max_length=100)
    address_province = db.StringField(max_length=100)
    address_country = db.StringField(max_length=100)
    
    # Source tracking
    source = db.StringField(max_length=20, default='shopify', choices=['shopify', 'manual', 'import'])
    
    # Shopify fields
    shopify_id = db.StringField(max_length=50, unique=True, sparse=True)
    tags = db.StringField(max_length=500)
    
    # Stats (calculated from orders)
    total_orders = db.IntField(default=0)
    total_spent = db.DecimalField(precision=2, default=0)
    first_order_date = db.DateTimeField()
    last_order_date = db.DateTimeField()
    
    # Metadata
    created_at = db.DateTimeField()
    updated_at = db.DateTimeField(default=datetime.utcnow)
    tenant = db.ReferenceField(Tenant)
    
    meta = {
        'collection': 'shopify_customers',
        'indexes': [
            'shopify_id',
            'email',
            'tenant',
            '-total_spent',
            '-created_at'
        ]
    }
    
    @property
    def orders(self):
        """Get all orders for this customer"""
        return ShopifyOrder.objects(customer=self).order_by('-created_at')
    
    @property
    def last_order(self):
        """Get the most recent order"""
        return ShopifyOrder.objects(customer=self).order_by('-created_at').first()


# ============================================
# BANK RECONCILIATION - Cuadratura Bancaria
# ============================================
class BankTransaction(db.Document):
    """
    Transacción bancaria importada desde cartola Excel.
    Se asocia (match) con una venta para cuadratura.
    """
    # Datos de la transacción
    date = db.DateTimeField(required=True)
    amount = db.DecimalField(precision=2, required=True)
    description = db.StringField(max_length=500)
    reference = db.StringField(max_length=100)  # Número de operación/referencia
    
    # Tipo de transacción
    transaction_type = db.StringField(
        max_length=20,
        default='credit',
        choices=['credit', 'debit']  # credit = ingreso, debit = egreso
    )
    
    # Estado de conciliación
    status = db.StringField(
        max_length=20,
        default='pending',
        choices=['pending', 'matched', 'ignored']
    )
    
    # Match con venta
    matched_sale = db.ReferenceField('Sale')
    matched_at = db.DateTimeField()
    matched_by = db.ReferenceField('User')
    match_type = db.StringField(max_length=20)  # 'manual' o 'auto'
    
    # Metadata
    source_file = db.StringField(max_length=200)  # Nombre del archivo importado
    row_number = db.IntField()  # Fila original en el Excel
    created_at = db.DateTimeField(default=datetime.utcnow)
    tenant = db.ReferenceField(Tenant)
    
    meta = {
        'collection': 'bank_transactions',
        'indexes': [
            'tenant',
            'date',
            'status',
            'matched_sale',
            '-created_at'
        ],
        'ordering': ['-date']
    }
    
    @property
    def is_matched(self):
        return self.status == 'matched' and self.matched_sale is not None


class ShopifyOrderLineItem(db.EmbeddedDocument):
    """Line item dentro de una orden de Shopify"""
    title = db.StringField(max_length=200)
    sku = db.StringField(max_length=100)
    quantity = db.IntField(default=1)
    price = db.DecimalField(precision=2)
    variant_title = db.StringField(max_length=200)
    product_shopify_id = db.StringField(max_length=50)


class ShopifyOrder(db.Document):
    """Orden sincronizada desde Shopify (solo lectura)"""
    order_number = db.IntField()
    shopify_id = db.StringField(max_length=50, unique=True, required=True)
    
    # Customer info
    customer = db.ReferenceField(ShopifyCustomer)
    customer_name = db.StringField(max_length=200)
    email = db.StringField(max_length=200)
    
    # Financial info
    total_price = db.DecimalField(precision=2)
    subtotal_price = db.DecimalField(precision=2)
    
    # Status
    financial_status = db.StringField(max_length=50)  # pending, paid, refunded, etc.
    fulfillment_status = db.StringField(max_length=50)  # fulfilled, partial, unfulfilled, etc.
    
    # Items
    line_items = db.EmbeddedDocumentListField(ShopifyOrderLineItem)
    
    # Shipping
    shipping_address1 = db.StringField(max_length=200)  # Calle y número
    shipping_address2 = db.StringField(max_length=200)  # Depto, oficina, etc.
    shipping_city = db.StringField(max_length=100)
    shipping_province = db.StringField(max_length=100)
    shipping_phone = db.StringField(max_length=50)
    note = db.StringField()
    
    @property
    def full_shipping_address(self):
        """Retorna la dirección completa de envío"""
        parts = []
        if self.shipping_address1:
            parts.append(self.shipping_address1)
        if self.shipping_address2:
            parts.append(self.shipping_address2)
        if self.shipping_city:
            parts.append(self.shipping_city)
        if self.shipping_province:
            parts.append(self.shipping_province)
        return ", ".join(parts) if parts else "Sin dirección"
    
    # Metadata
    created_at = db.DateTimeField()
    updated_at = db.DateTimeField(default=datetime.utcnow)
    tenant = db.ReferenceField(Tenant)
    
    meta = {
        'collection': 'shopify_orders',
        'indexes': [
            'shopify_id',
            'customer',
            'order_number',
            'tenant',
            '-created_at',
            'financial_status',
            'fulfillment_status'
        ],
        'ordering': ['-created_at']
    }
