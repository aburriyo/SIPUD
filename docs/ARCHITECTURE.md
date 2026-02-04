# ARQUITECTURA - SIPUD

## Descripción General

SIPUD es un ERP de gestión de inventario y ventas construido con **Flask** y **MongoDB**, diseñado para operaciones multi-tenant (multi-empresa).

## Stack Tecnológico

- **Backend:** Flask 3.x (Python)
- **Base de Datos:** MongoDB (MongoEngine ODM)
- **Autenticación:** Flask-Login
- **Email:** Flask-Mail
- **Rate Limiting:** Flask-Limiter (almacenamiento en memoria)
- **Templates:** Jinja2
- **Frontend:** HTML5, JavaScript vanilla, Bootstrap (estilizado en CSS custom)

---

## Estructura de Carpetas

```
SIPUD/
├── app/                          # Aplicación principal
│   ├── __init__.py              # Factory pattern (create_app)
│   ├── extensions.py            # Instancias de extensiones Flask
│   ├── models.py                # Modelos MongoDB (MongoEngine)
│   ├── routes/                  # Blueprints por módulo
│   │   ├── main.py             # Dashboard, vistas principales
│   │   ├── auth.py             # Login, logout, recuperación contraseña
│   │   ├── admin.py            # Gestión usuarios, activity log
│   │   ├── api.py              # API REST (productos, ventas, etc.)
│   │   ├── warehouse.py        # Operaciones bodega (pedidos, recepciones, mermas)
│   │   ├── customers.py        # CRM, sync Shopify
│   │   ├── delivery.py         # Hojas de reparto
│   │   ├── reports.py          # Exportación Excel
│   │   └── reconciliation.py  # Cuadratura bancaria
│   ├── static/                 # CSS, JS, imágenes
│   │   ├── css/
│   │   └── img/
│   └── templates/              # Templates Jinja2
│       ├── base.html
│       ├── dashboard.html
│       ├── admin/
│       ├── auth/
│       ├── delivery/
│       └── warehouse/
├── config.py                    # Configuración (MongoDB, Mail, JWT)
├── run.py                       # Punto de entrada (app runner)
├── requirements.txt             # Dependencias Python
├── scripts/                     # Scripts de utilidad
│   ├── seed_tenants.py
│   ├── create_users.py
│   ├── sync_shopify.py
│   └── clear_for_production.py
├── tests/                       # Tests unitarios (pytest)
├── docs/                        # Documentación técnica
├── backups/                     # Backups MongoDB
├── instance/                    # Archivos de instancia (SQLite legacy)
├── venv/                        # Entorno virtual Python
├── Dockerfile                   # Container Docker
├── docker-compose.yml           # Orquestación (Flask + MongoDB)
└── nginx/                       # Config NGINX (producción)
```

### Descripción de Carpetas Clave

| Carpeta | Propósito |
|---------|-----------|
| **app/routes/** | Blueprints modulares (cada archivo = módulo funcional) |
| **app/models.py** | Todos los modelos MongoDB (Tenant, User, Product, Sale, etc.) |
| **app/extensions.py** | Instancias de extensiones Flask (db, login_manager, mail, limiter) |
| **scripts/** | Scripts de mantenimiento, seed data, sincronización |
| **tests/** | Tests unitarios con pytest |
| **docs/** | Documentación técnica (este archivo) |

---

## Patrón de Arquitectura

### Factory Pattern (Application Factory)

**Archivo:** `app/__init__.py`

```python
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 1. Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    
    # 2. Configurar Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.objects.get(id=ObjectId(user_id))
    
    # 3. Registrar blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(api.bp)
    # ... más blueprints
    
    # 4. Middleware tenant context
    @app.before_request
    def load_tenant():
        # Lógica de tenant actual
        
    return app
```

**Ventajas:**
- Permite testing con diferentes configuraciones
- Instancias múltiples de la aplicación
- Configuración modular

### MVC (Model-View-Controller)

SIPUD sigue un patrón **MVC adaptado a Flask**:

| Componente | Implementación | Archivos |
|------------|----------------|----------|
| **Model** | MongoEngine Documents | `app/models.py` |
| **View** | Jinja2 Templates | `app/templates/` |
| **Controller** | Flask Blueprints (rutas) | `app/routes/` |

**Flujo de Request:**

```
1. Usuario → HTTP Request
2. NGINX (producción) → Flask App
3. app.before_request → Middleware (load tenant, load user)
4. Blueprint Route → Controller lógica
5. Model → MongoDB query/update
6. Template → Jinja2 render
7. HTTP Response → Usuario
```

---

## Extensiones Flask

### 1. MongoEngine (Base de Datos)

**Archivo:** `app/extensions.py`

```python
from flask_mongoengine import MongoEngine
db = MongoEngine()
```

**Configuración:** `config.py`

```python
MONGODB_SETTINGS = {
    'db': 'inventory_db',
    'host': 'localhost',
    'port': 27017
}
```

**Uso:**
- Todos los modelos heredan de `db.Document` o `db.EmbeddedDocument`
- Queries: `Product.objects(tenant=tenant)`

### 2. Flask-Login (Autenticación)

**Archivo:** `app/extensions.py`

```python
from flask_login import LoginManager
login_manager = LoginManager()
```

**Configuración:**

```python
login_manager.login_view = "auth.login"
login_manager.login_message = "Por favor inicia sesión para acceder a esta página."
```

**User Loader:**

```python
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.objects.get(id=ObjectId(user_id))
    except Exception:
        return None
```

**Modelo User:**
- Hereda de `UserMixin` (Flask-Login)
- Implementa `get_id()` para retornar `str(self.id)`

### 3. Flask-Mail (Emails)

**Archivo:** `app/extensions.py`

```python
from flask_mail import Mail
mail = Mail()
```

**Uso:**
- Recuperación de contraseñas (`auth.py`)
- Notificaciones (pendiente)

**Ejemplo:**

```python
from flask_mail import Message
msg = Message(
    subject='Recuperar Contraseña',
    recipients=[user.email],
    html=render_template('auth/email/reset_password.html', user=user, reset_url=reset_url)
)
mail.send(msg)
```

### 4. Flask-Limiter (Rate Limiting)

**Archivo:** `app/extensions.py`

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
```

**Aplicación:**
- Por defecto: 200/día, 50/hora por IP
- API Webhook: `@limiter.limit("10 per minute")`
- **Producción:** Se recomienda usar Redis como storage

**Error Handler:**

```python
@app.errorhandler(429)
def ratelimit_handler(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Rate limit exceeded'}), 429
    return e.get_response()
```

---

## Sistema Multi-Tenant

### Concepto

Cada **tenant** (organización/empresa) tiene sus datos aislados en MongoDB mediante el campo `tenant` (ReferenceField a `Tenant`).

### Modelo Tenant

```python
class Tenant(db.Document):
    name = db.StringField(max_length=100, unique=True, required=True)
    slug = db.StringField(max_length=50, unique=True, required=True)
    created_at = db.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'tenants'}
```

### Middleware: `g.current_tenant`

**Archivo:** `app/__init__.py`

```python
from flask import session, g
from flask_login import current_user

@app.before_request
def load_tenant():
    # Si el usuario está autenticado, usar su tenant
    if current_user.is_authenticated and current_user.tenant:
        g.current_tenant = current_user.tenant
    else:
        tenant_id = session.get("tenant_id")
        if tenant_id:
            g.current_tenant = Tenant.objects.get(id=ObjectId(tenant_id))
        else:
            # Default to first tenant or None
            g.current_tenant = Tenant.objects(slug="puerto-distribucion").first()
            if g.current_tenant:
                session["tenant_id"] = str(g.current_tenant.id)
```

**Uso en Rutas:**

```python
@bp.route('/api/products')
@login_required
def get_products():
    tenant = g.current_tenant  # ← Tenant actual
    products = Product.objects(tenant=tenant)
    return jsonify([...])
```

### Context Processor (Template Access)

```python
@app.context_processor
def inject_tenant():
    return dict(
        current_tenant=g.get("current_tenant"),
        tenants=list(Tenant.objects.all())
    )
```

**Uso en Templates:**

```jinja2
<h1>{{ current_tenant.name }}</h1>
```

---

## Middleware y Hooks

### `@app.before_request`

Ejecutado **antes de cada request**:

1. **`load_tenant()`** → Carga tenant actual en `g.current_tenant`

**Orden de ejecución:**
```
Request → load_tenant() → Blueprint Route → Response
```

### `@app.context_processor`

Inyecta variables globales en **todos los templates Jinja2**:

```python
@app.context_processor
def inject_tenant():
    return dict(
        current_tenant=g.get("current_tenant"),
        tenants=list(Tenant.objects.all())
    )
```

### `@app.errorhandler`

Maneja errores HTTP:

```python
@app.errorhandler(429)
def ratelimit_handler(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Rate limit exceeded'}), 429
    return e.get_response()
```

### Custom Jinja2 Filters

**Archivo:** `app/__init__.py`

```python
@app.template_filter("translate_status")
def translate_status(status):
    translations = {
        "pending": "pendiente",
        "delivered": "entregado",
        "cancelled": "cancelado",
        # ...
    }
    return translations.get(status, status)
```

**Uso:**

```jinja2
{{ sale.status|translate_status }}
```

---

## Flujo de Datos (Request → Response)

### 1. Request HTTP

```
Cliente → NGINX (puerto 80) → Flask (puerto 5000) → WSGI
```

### 2. Middleware

```python
@app.before_request
def load_tenant():
    # Carga tenant actual en g.current_tenant
```

### 3. Routing (Blueprints)

```python
@bp.route('/api/products', methods=['GET'])
@login_required
def get_products():
    tenant = g.current_tenant
    products = Product.objects(tenant=tenant)
    return jsonify([...])
```

### 4. Permisos (Decorator)

```python
def permission_required(module, action='view'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.has_permission(module, action):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@bp.route('/api/products', methods=['POST'])
@login_required
@permission_required('products', 'create')
def create_product():
    # Lógica de creación
```

### 5. Modelo (MongoDB)

```python
new_product = Product(
    name=data['name'],
    sku=data['sku'],
    tenant=tenant
)
new_product.save()
```

### 6. Respuesta

**JSON API:**
```python
return jsonify({'message': 'Producto creado', 'id': str(new_product.id)}), 201
```

**HTML Template:**
```python
return render_template('products.html', products=products)
```

### Diagrama Completo

```
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │ HTTP Request (GET /api/products)
       ▼
┌─────────────────────┐
│  NGINX (Reverse     │
│  Proxy)             │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Flask App          │
│  (WSGI)             │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Middleware         │
│  - load_tenant()    │
│  - check auth       │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Blueprint Route    │
│  @bp.route(...)     │
│  @login_required    │
│  @permission_required│
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Controller Logic   │
│  - Validar datos    │
│  - Acceso modelo    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  MongoDB            │
│  (MongoEngine)      │
│  Product.objects... │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Template/JSON      │
│  - Jinja2 render    │
│  - jsonify()        │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  HTTP Response      │
│  200/201/400/500    │
└─────────────────────┘
```

---

## Sistema de Permisos (RBAC)

### Roles

Definidos en `app/models.py`:

```python
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
    'manager': { ... },
    'warehouse': { ... },
    'sales': { ... },
}
```

### Verificación de Permisos

**Método en User:**

```python
def has_permission(self, module, action='view'):
    role_perms = ROLE_PERMISSIONS.get(self.role, {})
    module_perms = role_perms.get(module, [])
    return action in module_perms
```

**Decorator:**

```python
def permission_required(module, action='view'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.has_permission(module, action):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

**Uso:**

```python
@bp.route('/api/products', methods=['POST'])
@login_required
@permission_required('products', 'create')
def create_product():
    # Solo usuarios con permiso 'create' en 'products'
    ...
```

---

## Activity Log (Auditoría)

### Modelo

```python
class ActivityLog(db.Document):
    user = db.ReferenceField('User', required=True)
    user_name = db.StringField(max_length=100)
    user_role = db.StringField(max_length=20)
    action = db.StringField(max_length=50, required=True)  # create, update, delete, login, etc.
    module = db.StringField(max_length=50, required=True)  # products, sales, users, etc.
    description = db.StringField(max_length=500)
    details = db.DictField()  # JSON con detalles adicionales
    target_id = db.StringField(max_length=50)
    target_type = db.StringField(max_length=50)
    ip_address = db.StringField(max_length=45)
    user_agent = db.StringField(max_length=500)
    tenant = db.ReferenceField(Tenant)
    created_at = db.DateTimeField(default=datetime.utcnow)
```

### Helper Method

```python
@classmethod
def log(cls, user, action, module, description=None, details=None,
        target_id=None, target_type=None, request=None, tenant=None):
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
```

### Uso

```python
ActivityLog.log(
    user=current_user,
    action='create',
    module='products',
    description=f'Creó producto "{data["name"]}"',
    target_id=str(new_product.id),
    target_type='Product',
    request=request,
    tenant=tenant
)
```

---

## Configuración (Environment Variables)

**Archivo:** `config.py`

```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    MONGODB_SETTINGS = {
        'db': os.environ.get('MONGODB_DB') or 'inventory_db',
        'host': os.environ.get('MONGODB_HOST') or 'localhost',
        'port': int(os.environ.get('MONGODB_PORT') or 27017),
    }
    
    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Flask-Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Tokens
    PASSWORD_RESET_TOKEN_MAX_AGE = 3600  # 1 hora
```

**Variables de Entorno (`.env`):**

```bash
SECRET_KEY=your-secret-key-here
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=inventory_db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@sipud.com
SIPUD_WEBHOOK_TOKEN=your-webhook-token
SHOPIFY_STORE_DOMAIN=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxx
```

---

## Deployment

### Desarrollo

```bash
python run.py
```

### Producción (Docker)

**Dockerfile:**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-b", "0.0.0.0:5000", "run:app"]
```

**docker-compose.yml:**

```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:7
    volumes:
      - mongo_data:/data/db
    ports:
      - "27017:27017"
  
  flask:
    build: .
    ports:
      - "5000:5000"
    env_file:
      - .env
    depends_on:
      - mongodb

volumes:
  mongo_data:
```

**NGINX (Reverse Proxy):**

```nginx
server {
    listen 80;
    server_name sipud.example.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Performance & Scalability

### Optimizaciones Implementadas

1. **Índices MongoDB:**
   - User: `username`, `email`, `tenant`
   - Product: `sku`, `tenant`
   - Sale: `tenant`, `date_created`
   - ActivityLog: `user`, `module`, `tenant`, `created_at`

2. **Propiedades Calculadas (Caching):**
   - `Product.total_stock` → suma de lotes
   - `Sale.total_amount` → suma de items
   - `Sale.computed_payment_status` → calculado desde pagos

3. **Rate Limiting:**
   - API pública: 10/min, 100/hour
   - API autenticada: 200/día, 50/hora

### Escalabilidad Horizontal

**Pendiente:**
- Redis para rate limiting (multi-worker)
- Celery para tareas asíncronas (emails, sync Shopify)
- MongoDB replica set para alta disponibilidad

---

## Seguridad

### Implementado

1. **Autenticación:**
   - Flask-Login con sesiones seguras
   - Passwords hasheados (werkzeug.security)
   - Tokens JWT para reset password (itsdangerous)

2. **Autorización:**
   - RBAC (Role-Based Access Control)
   - Permisos granulares por módulo y acción

3. **Aislamiento Multi-Tenant:**
   - Filtrado automático por `tenant` en queries
   - Validación de pertenencia en updates/deletes

4. **Rate Limiting:**
   - Protección contra brute force
   - Límites por IP

5. **Validación de Datos:**
   - Validación server-side de inputs
   - Sanitización de datos antes de MongoDB

### Recomendaciones

- [ ] Implementar CSRF tokens (Flask-WTF)
- [ ] HTTPS obligatorio en producción
- [ ] Auditoría de logs (ActivityLog)
- [ ] Backups automáticos MongoDB
- [ ] Encriptación de datos sensibles

---

## Testing

**Framework:** pytest

**Estructura:**

```
tests/
├── conftest.py         # Fixtures compartidas
├── test_app.py         # Tests de aplicación general
├── test_models.py      # Tests de modelos
└── test_api.py         # Tests de endpoints API
```

**Ejecutar:**

```bash
pytest
pytest -v  # verbose
pytest tests/test_api.py  # archivo específico
```

---

## Conclusión

SIPUD sigue una arquitectura **modular y escalable** basada en:

- **Factory Pattern** para instanciación de app
- **Blueprint Pattern** para organización de rutas
- **Multi-Tenant** con middleware automático
- **RBAC** para control de acceso granular
- **Activity Log** para auditoría completa
- **Extensiones Flask** estándar (Login, Mail, Limiter)

Esta arquitectura permite:
- ✅ Agregar nuevos módulos fácilmente (nuevo blueprint)
- ✅ Testing independiente de cada módulo
- ✅ Escalabilidad horizontal (stateless, MongoDB)
- ✅ Mantenibilidad (código organizado, modular)
