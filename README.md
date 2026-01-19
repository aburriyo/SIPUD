# Sistema ERP de Inventario 2026

Sistema ERP integral multi-tenant desarrollado con Flask para la gestión completa de inventario, ventas, logística y almacén.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-orange)
![License](https://img.shields.io/badge/License-Private-red)

## Características Principales

### 🏢 Multi-Tenancy
- Soporte completo para múltiples empresas/organizaciones
- Aislamiento total de datos por tenant
- Cambio dinámico entre tenants

### 📦 Gestión de Almacén
- **Pedidos a Proveedores**: Control completo de órdenes de compra
- **Recepción de Mercancía**: Registro de entradas con lotes y fechas de vencimiento
- **Registro de Mermas**: Trazabilidad de pérdidas con FIFO automático
- **Gestión de Vencimientos**: Control y actualización de fechas de caducidad

### 💰 Módulo de Ventas
- Registro de ventas con múltiples productos
- Buscador inteligente de productos en móvil y escritorio
- Control de pagos y estados de entrega
- Exportación a Excel

### 📊 Catálogo de Productos
- Gestión completa de SKUs
- Categorización con emojis visuales
- Control de stock crítico
- Sistema de bundles/cajas (kitting)
- Precios base y descripción detallada

### 🚚 Gestión de Flota
- Monitoreo de vehículos
- Estado en tiempo real
- Capacidad de carga
- Geolocalización (lat/lng)

### 📈 Reportes
- Exportación de ventas a Excel
- Análisis de datos históricos
- Informes personalizables por tenant

## Tecnologías Utilizadas

### Backend
- **Flask 3.0.0**: Micro-framework web
- **SQLAlchemy 3.1.1**: ORM para base de datos
- **Flask-Login 0.6.3**: Autenticación de usuarios
- **Flask-Migrate 4.0.5**: Migraciones de base de datos
- **SQLite**: Base de datos (production-ready para pequeñas/medianas empresas)

### Frontend
- **Tailwind CSS**: Framework CSS utilitario
- **Alpine.js 2.8.2**: Framework JavaScript reactivo
- **DataTables**: Tablas avanzadas con búsqueda, ordenamiento y paginación
- **jQuery**: Requerido por DataTables

### Extras
- **OpenPyXL 3.1.2**: Generación de archivos Excel
- **Python-dotenv 1.0.0**: Manejo de variables de entorno

## Instalación

### Prerrequisitos
- Python 3.12 o superior
- pip (gestor de paquetes de Python)
- Git

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/aburriyo/inventario-2026.git
cd "Software Inventario 2026"
```

2. **Crear entorno virtual**
```bash
python -m venv venv
```

3. **Activar entorno virtual**

En macOS/Linux:
```bash
source venv/bin/activate
```

En Windows:
```bash
venv\Scripts\activate
```

4. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

5. **Configurar variables de entorno** (opcional)

Crear archivo `.env` en la raíz:
```env
SECRET_KEY=tu-clave-secreta-super-segura
DATABASE_URL=sqlite:///inventory.db
FLASK_ENV=development
```

6. **Inicializar la base de datos**
```bash
flask db upgrade
```

7. **Crear datos de prueba** (opcional)
```bash
# Crear tenants de ejemplo
python scripts/seed_tenants.py

# Crear usuarios de ejemplo
python scripts/create_users.py

# Crear flota de ejemplo
python scripts/create_demo_fleet.py
```

8. **Ejecutar la aplicación**
```bash
python run.py
```

La aplicación estará disponible en: `http://127.0.0.1:5000`

## Estructura del Proyecto

```
Software Inventario 2026/
├── app/
│   ├── __init__.py              # Inicialización de Flask
│   ├── models.py                # Modelos SQLAlchemy
│   ├── extensions.py            # Extensiones (db, login_manager)
│   ├── routes/
│   │   ├── auth.py             # Autenticación
│   │   ├── main.py             # Rutas principales
│   │   ├── api.py              # API REST
│   │   ├── warehouse.py        # Módulo de almacén
│   │   ├── logistics.py        # Gestión de flota
│   │   └── reports.py          # Reportes y exportaciones
│   ├── templates/
│   │   ├── base.html           # Template base
│   │   ├── dashboard.html      # Dashboard principal
│   │   ├── products.html       # Catálogo de productos
│   │   ├── sales.html          # Módulo de ventas
│   │   ├── fleet.html          # Gestión de flota
│   │   ├── logistics.html      # Logística
│   │   ├── auth/
│   │   │   └── login.html      # Página de login
│   │   └── warehouse/
│   │       ├── orders.html     # Pedidos a proveedores
│   │       ├── receiving.html  # Recepción de mercancía
│   │       ├── wastage.html    # Registro de mermas
│   │       └── expiry.html     # Gestión de vencimientos
│   └── static/
│       └── css/
│           └── styles.css      # Estilos personalizados
├── migrations/                  # Migraciones Alembic
├── scripts/                     # Scripts de utilidad
│   ├── create_users.py
│   ├── seed_tenants.py
│   ├── verify_isolation.py
│   └── archived/               # Scripts obsoletos
├── tests/                      # Tests unitarios
├── instance/
│   └── inventory.db           # Base de datos SQLite
├── ___documentos/             # Documentación de negocio
├── ___Planificación/          # Documentación técnica
├── config.py                  # Configuración de Flask
├── requirements.txt           # Dependencias Python
├── run.py                     # Punto de entrada
└── README.md                  # Este archivo
```

## Modelos de Base de Datos

### Principales Entidades

#### `Tenant`
- Organización/Empresa
- Aislamiento de datos

#### `User`
- Usuarios del sistema
- Roles: admin, bodega, driver
- Asociados a un tenant

#### `Product`
- Catálogo maestro de productos
- SKU, nombre, categoría, precio
- Stock total y stock crítico
- Soporte para bundles (cajas/packs)

#### `Lot`
- Trazabilidad por lotes
- Código de lote, fecha de vencimiento
- Cantidad disponible

#### `Sale` y `SaleItem`
- Cabecera y detalle de ventas
- Estados: pending, assigned, in_transit, delivered, cancelled
- Método de pago y confirmación

#### `InboundOrder`
- Pedidos a proveedores
- Número de factura, proveedor, total
- Estados: pending, received, cancelled

#### `Wastage`
- Registro de mermas/pérdidas
- Razones: vencido, dañado, perdido, robo, otro
- Descuento automático de stock

#### `Truck` y `VehicleMaintenance`
- Gestión de flota
- Mantenimientos programados

#### `LogisticsRoute`
- Rutas de despacho
- Asignación de ventas a conductores

## Uso del Sistema

### 1. Inicio de Sesión
- Acceder a `/login`
- Usar credenciales creadas con `scripts/create_users.py`
- Seleccionar tenant (si aplica)

### 2. Dashboard Principal
- Vista general de métricas
- Acceso rápido a todos los módulos

### 3. Gestión de Productos
- Crear, editar, eliminar productos
- Definir bundles (cajas compuestas)
- Monitorear stock crítico

### 4. Módulo de Almacén

**Pedidos a Proveedores:**
1. Click en "Nuevo Pedido"
2. Seleccionar proveedor
3. Ingresar número de factura y monto
4. Guardar

**Recepción de Mercancía:**
1. Seleccionar pedido pendiente
2. Agregar productos recibidos
3. Especificar cantidad, lote y fecha de vencimiento
4. Confirmar recepción (actualiza stock automáticamente)

**Registro de Mermas:**
1. Seleccionar producto afectado
2. Ingresar cantidad perdida
3. Especificar razón
4. El sistema descuenta usando FIFO

**Gestión de Vencimientos:**
1. Ver productos con fechas de caducidad
2. Actualizar fechas según necesidad
3. Alertas visuales (rojo ≤7 días, amarillo 8-30 días)

### 5. Módulo de Ventas

**Crear Nueva Venta:**
1. Click en "Nueva Venta"
2. Ingresar datos del cliente
3. Agregar productos (buscador inteligente en móvil)
4. Confirmar pago y estado de entrega
5. Guardar

**Exportar Ventas:**
- Click en "Exportar" para descargar Excel

### 6. Gestión de Flota
- Registrar nuevos camiones
- Monitorear estado (disponible/en uso)
- Ver ubicación actual

## API REST

### Productos
- `GET /api/products` - Listar productos
- `POST /api/products` - Crear producto
- `GET /api/products/<id>` - Obtener producto
- `PUT /api/products/<id>` - Actualizar producto
- `DELETE /api/products/<id>` - Eliminar producto

### Ventas
- `GET /api/sales` - Listar ventas
- `POST /api/sales` - Crear venta
- `GET /api/sales/<id>` - Obtener venta
- `POST /api/sales/bulk-delete` - Eliminar múltiples ventas

### Almacén
- `GET /warehouse/api/orders` - Pedidos a proveedores
- `POST /warehouse/api/orders` - Crear pedido
- `PUT /warehouse/api/orders/<id>` - Actualizar pedido
- `DELETE /warehouse/api/orders/<id>` - Eliminar pedido
- `POST /warehouse/api/receiving/<order_id>` - Confirmar recepción
- `POST /warehouse/api/wastage` - Registrar merma
- `GET /warehouse/api/expiry/products` - Productos con vencimiento

## Migraciones de Base de Datos

### Crear nueva migración
```bash
flask db migrate -m "Descripción del cambio"
```

### Aplicar migraciones
```bash
flask db upgrade
```

### Revertir migración
```bash
flask db downgrade
```

## Scripts de Utilidad

### Verificación de Aislamiento Multi-Tenant
```bash
python scripts/verify_isolation.py
```

### Verificación de Lógica de Stock
```bash
python scripts/verify_stock_logic.py
```

### Tests de Ensamblado (Bundles)
```bash
python scripts/test_assembly_logic.py
```

### Verificación de Logística
```bash
python scripts/verify_logistics.py
```

## Testing

```bash
# Ejecutar todos los tests
pytest

# Ejecutar test específico
pytest tests/test_fleet.py
```

## Deployment (Producción)

### Render.com / Railway
1. Conectar repositorio GitHub
2. Configurar variables de entorno:
   - `SECRET_KEY`: Clave secreta fuerte
   - `DATABASE_URL`: URL de base de datos (PostgreSQL recomendado)
3. Deploy automático desde branch `main`

### Configuración para PostgreSQL
En `config.py`, DATABASE_URL se lee automáticamente desde variables de entorno.

## Seguridad

- ✅ Autenticación con Flask-Login
- ✅ Contraseñas hasheadas (Werkzeug)
- ✅ CSRF protection (Flask-WTF recomendado)
- ✅ Aislamiento multi-tenant
- ✅ Validaciones server-side
- ⚠️ **Nota**: Para producción, configurar HTTPS y SECRET_KEY fuerte

## Troubleshooting

### Error: "No module named 'app'"
```bash
export FLASK_APP=run.py
```

### Error de base de datos corrupta
```bash
rm instance/inventory.db
flask db upgrade
```

### Problemas con migraciones
```bash
# Eliminar carpeta migrations
rm -rf migrations/

# Reinicializar
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Contribución

Este es un proyecto privado. Para contribuir:
1. Crear branch desde `main`
2. Implementar cambios
3. Crear Pull Request
4. Revisión de código requerida

## Convenciones de Código

- **Python**: PEP 8
- **Templates**: Jinja2 con indentación de 4 espacios
- **JavaScript**: Alpine.js conventions
- **CSS**: Tailwind utility-first

## Changelog

### v1.0.0 (Enero 2026)
- ✅ Sistema multi-tenant implementado
- ✅ Módulo de almacén completo (4 submódulos)
- ✅ Gestión de productos con bundles
- ✅ Módulo de ventas responsive
- ✅ Gestión de flota básica
- ✅ Exportación a Excel
- ✅ DataTables integrado

## Roadmap

### Próximas Funcionalidades
- [ ] Dashboard con gráficas (Chart.js)
- [ ] Reportes PDF
- [ ] Notificaciones de vencimientos (email/SMS)
- [ ] Escáner de códigos de barras
- [ ] App móvil (React Native)
- [ ] Integración con APIs de terceros
- [ ] Analytics avanzados

## Soporte

Para preguntas o problemas:
- 📧 Email: soporte@inventario2026.com
- 📝 Issues: https://github.com/aburriyo/inventario-2026/issues

## Licencia

Copyright © 2026 - Todos los derechos reservados.
Proyecto privado - No distribuir sin autorización.

---

**Desarrollado con ❤️ usando Flask y Tailwind CSS**
