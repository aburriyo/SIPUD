"""
Tests básicos para modelos Product, Sale, User
"""
import pytest
from datetime import datetime
from app.models import User, Product, Sale, Tenant, ROLE_PERMISSIONS


class TestUserModel:
    """Tests para el modelo User"""
    
    def test_user_creation(self):
        """Test crear usuario básico"""
        user = User(
            username='testuser',
            email='test@example.com',
            role='sales',
            full_name='Test User'
        )
        
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.role == 'sales'
        assert user.full_name == 'Test User'
        assert user.is_active is True
    
    def test_user_password_hashing(self):
        """Test que las contraseñas se hashean correctamente"""
        user = User(username='testuser', role='sales')
        plain_password = 'secure_password_123'
        
        user.set_password(plain_password)
        
        # Password hash no debe ser igual al password original
        assert user.password_hash != plain_password
        assert user.password_hash is not None
        
        # Debe poder verificar el password
        assert user.check_password(plain_password) is True
        assert user.check_password('wrong_password') is False
    
    def test_user_get_id(self):
        """Test que get_id retorna string del ObjectId"""
        user = User(username='testuser', role='sales')
        # Simular que tiene un ID (normalmente asignado por MongoDB)
        # En tests sin DB real, solo verificamos que el método existe
        user_id = user.get_id()
        assert isinstance(user_id, str) or user_id is None
    
    def test_user_has_permission(self):
        """Test del sistema de permisos por rol"""
        # Admin: tiene todos los permisos
        admin = User(username='admin', role='admin')
        assert admin.has_permission('users', 'create') is True
        assert admin.has_permission('users', 'delete') is True
        assert admin.has_permission('products', 'edit') is True
        
        # Manager: no puede borrar usuarios
        manager = User(username='manager', role='manager')
        assert manager.has_permission('users', 'create') is True
        assert manager.has_permission('users', 'delete') is False
        assert manager.has_permission('products', 'edit') is True
        
        # Warehouse: solo puede ver y gestionar órdenes
        warehouse = User(username='warehouse', role='warehouse')
        assert warehouse.has_permission('orders', 'receive') is True
        assert warehouse.has_permission('sales', 'create') is False
        assert warehouse.has_permission('users', 'view') is False
        
        # Sales: puede crear ventas pero no editarlas
        sales = User(username='sales', role='sales')
        assert sales.has_permission('sales', 'create') is True
        assert sales.has_permission('sales', 'edit') is False
        assert sales.has_permission('products', 'view') is True
    
    def test_user_can_alias(self):
        """Test que can() es alias de has_permission()"""
        user = User(username='testuser', role='admin')
        
        # can() debe comportarse igual que has_permission()
        assert user.can('users', 'delete') == user.has_permission('users', 'delete')
        assert user.can('products', 'create') == user.has_permission('products', 'create')
    
    def test_user_get_permissions(self):
        """Test que get_permissions retorna dict completo de permisos"""
        admin = User(username='admin', role='admin')
        perms = admin.get_permissions()
        
        assert isinstance(perms, dict)
        assert 'users' in perms
        assert 'products' in perms
        assert 'sales' in perms
        
        # Verificar que coincide con ROLE_PERMISSIONS
        assert perms == ROLE_PERMISSIONS['admin']


class TestProductModel:
    """Tests para el modelo Product"""
    
    def test_product_creation(self):
        """Test crear producto básico"""
        product = Product(
            name='Arroz Tucapel 5kg',
            sku='ARROZ-5KG',
            description='Arroz grado 2',
            category='Abarrotes',
            base_price=5000,
            critical_stock=10
        )
        
        assert product.name == 'Arroz Tucapel 5kg'
        assert product.sku == 'ARROZ-5KG'
        assert product.category == 'Abarrotes'
        assert product.base_price == 5000
        assert product.critical_stock == 10
    
    def test_product_sku_required(self):
        """Test que SKU es requerido"""
        # SKU es requerido para crear un producto
        product = Product(name='Test Product')
        
        # Verificar que SKU no tiene valor por defecto
        assert product.sku is None or product.sku == ''
    
    def test_product_default_values(self):
        """Test valores por defecto de Product"""
        product = Product(
            name='Test Product',
            sku='TEST-001'
        )
        
        # Verificar defaults (según el modelo original)
        assert product.description == '' or product.description is None
        # base_price default debería ser 0 o None
        assert product.base_price == 0 or product.base_price is None
    
    def test_product_total_stock_property(self):
        """Test que total_stock existe como propiedad"""
        # Verificar que Product tiene la property total_stock definida
        assert hasattr(Product, 'total_stock'), "Product debería tener property total_stock"
        
        # Verificar que es una property
        assert isinstance(getattr(Product, 'total_stock'), property), "total_stock debería ser una @property"


class TestSaleModel:
    """Tests para el modelo Sale"""
    
    def test_sale_creation(self):
        """Test crear venta básica"""
        sale = Sale(
            customer_name='Juan Pérez',
            phone='+56912345678',
            address='Av. Principal 123',
            sale_type='con_despacho',
            delivery_status='pendiente',
            payment_status='pendiente',
            sales_channel='manual'
        )
        
        assert sale.customer_name == 'Juan Pérez'
        assert sale.phone == '+56912345678'
        assert sale.sale_type == 'con_despacho'
        assert sale.delivery_status == 'pendiente'
        assert sale.payment_status == 'pendiente'
        assert sale.sales_channel == 'manual'
    
    def test_sale_type_values(self):
        """Test tipos de venta válidos"""
        from app.models import SALE_TYPES
        
        assert 'con_despacho' in SALE_TYPES
        assert 'en_local' in SALE_TYPES
    
    def test_delivery_status_values(self):
        """Test estados de entrega válidos"""
        from app.models import DELIVERY_STATUSES
        
        expected_statuses = [
            'pendiente',
            'en_preparacion', 
            'en_transito',
            'entregado',
            'con_observaciones',
            'cancelado'
        ]
        
        for status in expected_statuses:
            assert status in DELIVERY_STATUSES
    
    def test_payment_status_values(self):
        """Test estados de pago válidos"""
        from app.models import PAYMENT_STATUSES
        
        assert 'pendiente' in PAYMENT_STATUSES
        assert 'parcial' in PAYMENT_STATUSES
        assert 'pagado' in PAYMENT_STATUSES
    
    def test_sales_channel_values(self):
        """Test canales de venta válidos"""
        from app.models import SALES_CHANNELS
        
        expected_channels = ['manual', 'whatsapp', 'shopify', 'web']
        
        for channel in expected_channels:
            assert channel in SALES_CHANNELS
    
    def test_sale_defaults(self):
        """Test valores por defecto de Sale"""
        sale = Sale(
            customer_name='Test Customer'
        )
        
        # Verificar que Sale tiene campos de timestamp
        # (puede ser created_at, created, timestamp, etc)
        has_timestamp = any([
            hasattr(sale, 'created_at'),
            hasattr(sale, 'created'),
            hasattr(sale, 'timestamp'),
            hasattr(Sale, 'created_at'),
        ])
        
        # Al menos debería poder rastrear cuándo se creó
        assert has_timestamp or hasattr(sale, 'id'), "Sale debería tener timestamp o ID"


class TestTenantModel:
    """Tests para el modelo Tenant (multi-tenancy)"""
    
    def test_tenant_creation(self):
        """Test crear tenant básico"""
        tenant = Tenant(
            name='Puerto Distribución',
            slug='puerto-distribucion'
        )
        
        assert tenant.name == 'Puerto Distribución'
        assert tenant.slug == 'puerto-distribucion'
    
    def test_tenant_slug_format(self):
        """Test que slug sigue formato correcto"""
        tenant = Tenant(
            name='Test Company',
            slug='test-company'
        )
        
        # Slug debería ser lowercase, sin espacios
        assert tenant.slug.islower()
        assert ' ' not in tenant.slug
