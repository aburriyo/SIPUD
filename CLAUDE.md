# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SIPUD is a multi-tenant ERP system built with Flask and MongoDB for managing inventory, sales, warehouse operations, and logistics. The system runs on `localhost:5006` and uses MongoEngine ODM for data persistence.

## Development Commands

### Running the Application
```bash
python run.py
# Application starts on http://localhost:5006
```

### MongoDB Setup
The application expects MongoDB running on:
- Host: `localhost` (or set `MONGODB_HOST` env var)
- Port: `27017` (or set `MONGODB_PORT` env var)
- Database: `inventory_db` (or set `MONGODB_DB` env var)

### Environment Variables
Create a `.env` file for configuration:
```env
SECRET_KEY=your-secret-key
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=inventory_db
```

### Dependencies
```bash
# Install all dependencies
pip install -r requirements.txt
```

**Key Dependencies** (see `requirements.txt`):
- Flask 2.1.3
- flask-mongoengine 1.0.0
- pymongo 4.6.1
- Flask-Login 0.6.3
- openpyxl 3.1.2 (for Excel exports)
- python-dotenv 1.0.0

## Architecture Overview

### Multi-Tenancy Pattern
**Critical**: All database queries MUST filter by tenant. The system uses Flask's `g.current_tenant` which is set by the `load_tenant()` middleware in `app/__init__.py`.

```python
# Always query with tenant filter
products = Product.objects(tenant=g.current_tenant)
```

The middleware chain:
1. `@app.before_request` decorator calls `load_tenant()`
2. Tenant loaded from: authenticated user → session → default "puerto-distribucion"
3. `g.current_tenant` available to all routes
4. All Jinja2 templates have access via `current_tenant` variable

### Blueprint Organization
All blueprints registered in `app/__init__.py:create_app()`.

- `auth` (`/`): Login/logout authentication
- `main` (`/`): Dashboard, products, sales views
- `api` (`/api`): REST endpoints for products, sales, stats
- `warehouse` (`/warehouse`): Warehouse operations UI + API (orders, receiving, wastage, expiry)
- `admin` (`/admin`): User management, activity log monitoring (admin-only access)
- `reports` (`/reports`): Excel export endpoints using openpyxl

### Permission System
Uses decorator-based authorization: `@permission_required(module, action)`

**Decorator Location**: Defined in `app/routes/admin.py` (though used across all blueprints).

**Usage Pattern**:
```python
@bp.route('/users')
@login_required
@permission_required('users', 'view')
def users():
    return render_template('admin/users.html')
```

**Role Hierarchy** (defined in `ROLE_PERMISSIONS` in `app/models.py`):
- **admin**: Full CRUD on all modules + activity log access
- **manager**: Limited user management (no delete), no activity log access
- **warehouse**: Orders/wastage only (view/create/receive), no user management
- **sales**: Sales creation/viewing only, basic reporting

**Permission Actions**: `view`, `create`, `edit`, `delete`, `cancel`, `receive`, `export`

**Permission Modules**: `users`, `products`, `sales`, `orders`, `wastage`, `reports`, `activity_log`

### Database Models (MongoEngine)

#### Core Document Structure
All models extend `mongoengine.Document` and include `tenant` reference field for isolation.

**Key Models:**
- `Tenant`: Organization with unique slug (multi-tenancy root)
- `Supplier`: Vendor/provider with RUT (Chilean tax ID) and contact info
- `User`: Flask-Login compatible with role-based permissions
- `Product`: Master catalog with computed `total_stock` property
- `Lot`: FIFO-tracked batches linked to InboundOrder
- `InboundOrder`: Purchase orders (status: pending → received → paid)
- `Sale` + `SaleItem`: Sales orders with line items
- `Wastage`: Loss tracking with automatic FIFO deduction
- `ProductBundle`: Kitting/bundle composition relationships
- `ActivityLog`: Comprehensive audit trail with optimized indexes

All models except `Tenant` include a `tenant` ReferenceField for isolation.

#### Computed Properties
Several models use `@property` decorators for dynamic data:
- `Product.total_stock`: Aggregates all Lot quantities
- `Product.is_bundle`: Checks if product has bundle components
- `InboundOrder.lots`: Retrieves all associated lots
- `Sale.items`: Retrieves all sale items

**Important**: These are NOT database fields. Don't try to query or filter by them.

### FIFO Stock Management
Used in: Sales, Wastage, Bundle Assembly

Pattern in `app/routes/warehouse.py`:
```python
available_lots = sorted(
    [l for l in product.lots if l.quantity_current > 0],
    key=lambda x: x.created_at
)
for lot in available_lots:
    deduct = min(lot.quantity_current, remaining)
    lot.quantity_current -= deduct
    lot.save()
    remaining -= deduct
```

Always deduct from oldest lots first (`created_at` ascending).

### Bundle/Kit Assembly
Endpoint: `POST /warehouse/api/assembly`

Process:
1. Validate bundle product exists and has components
2. Deduct component stock using FIFO
3. Create synthetic InboundOrder with `supplier_name="Interno: Armado"`
4. Create new Lot for assembled bundle
5. Log activity

### Activity Logging
**Critical**: Log ALL CRUD operations for audit compliance.

Pattern:
```python
ActivityLog.log(
    user=current_user,
    action='create',  # create/update/delete/login/logout
    module='products',  # products/sales/warehouse/users/etc
    description=f'Creó producto "{name}"',
    target_id=str(product.id),
    target_type='Product',
    request=request,
    tenant=g.current_tenant
)
```

Logs capture: user context, IP address, user agent, timestamp with optimized indexes.

## API Response Patterns

All API endpoints return JSON with consistent structure.

### Success Response
```json
{
  "success": true,
  "message": "Producto creado",
  "id": "507f1f77bcf86cd799439011"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Stock insuficiente para Pan. Disponible: 5, Solicitado: 10"
}
```

### List Response (with pagination)
```json
{
  "success": true,
  "users": [...],
  "total": 42,
  "pages": 3,
  "current_page": 1
}
```

**Important**: Error messages are in Spanish for end-user consumption. Keep this convention when adding new endpoints.

## Critical Stock Flow

### Creating a Sale
1. Validate products exist and belong to tenant
2. Check stock sufficiency using `product.total_stock`
3. Deduct from Lots using FIFO (oldest `created_at` first)
4. If bundle, recursively deduct component stock
5. Create SaleItem records linking Sale → Product
6. Log to ActivityLog
7. Return Sale ID

### Receiving Goods
Endpoint: `POST /warehouse/api/receiving/<order_id>`

1. For each product in payload:
   - Auto-generate lot code if missing
   - Validate expiry date not in past
   - Create Lot document with `quantity_initial` = `quantity_current`
2. Update InboundOrder status to "received"
3. Set `date_received` timestamp
4. Log activity
5. Stock immediately available for sales

### Wastage Recording
Endpoint: `POST /warehouse/api/wastage`

1. Create Wastage record with reason
2. Deduct stock using FIFO from Lots
3. Update `lot.quantity_current` (NOT `quantity_initial`)
4. Log activity
5. Return wastage ID

## Frontend Integration

### Template Context Injection
All templates have access to:
- `current_tenant`: The active Tenant object
- `tenants`: List of all Tenant objects for switching

Via `@app.context_processor` in `app/__init__.py`.

### Jinja2 Custom Filters
- `translate_status`: Converts status codes to Spanish labels
  - Defined in `app/__init__.py`
  - Used in templates: `{{ sale.status|translate_status }}`

### AJAX Integration
- DataTables for paginated lists
- Alpine.js for reactive components
- RESTful API enables SPA-like interactions

## Migration Context

**Recent Migration**: SQLite/SQLAlchemy → MongoDB/MongoEngine (completed January 2026)

- Legacy `/migrations` folder preserved but inactive (Alembic no longer used)
- Migration executed via `scripts/migrate_sqlite_to_mongo.py`
- Schema changes now handled via MongoEngine model updates (no migration commands needed)
- MongoDB is schemaless but MongoEngine provides structure validation

**Critical**: README.md is OUTDATED and still references SQLAlchemy/Flask-Migrate. Ignore those sections. The actual codebase uses:
- MongoEngine ODM (not SQLAlchemy)
- MongoDB (not SQLite)
- No Flask-Migrate (no `flask db` commands available)

## Testing & Verification Scripts

### Running Tests
```bash
# Run pytest tests (minimal test coverage currently)
pytest tests/

# Run specific test file
pytest tests/test_fleet.py
```

**Note**: Test coverage is currently minimal (only `tests/test_fleet.py` exists). Most verification is done via scripts.

### Verification & Seeding Scripts
Located in `/scripts`:
- `verify_isolation.py`: Test multi-tenant data isolation
- `verify_stock_logic.py`: Validate FIFO deduction logic
- `test_assembly_logic.py`: Test bundle assembly logic
- `create_users.py`: Seed initial users with roles
- `seed_tenants.py`: Create tenant data
- `create_demo_fleet.py`: Create sample fleet/trucks
- `verify_tenant_switch.py`: Test tenant switching
- `verify_logistics.py`: Verify logistics module
- `migrate_sqlite_to_mongo.py`: One-time migration script (already executed)

## Security Considerations

- Passwords hashed using Werkzeug's `generate_password_hash()`
- Flask-Login handles session management
- Multi-tenant isolation enforced at query level
- Server-side validation on all inputs
- ActivityLog captures IP addresses and user agents for forensics
- Soft-delete pattern for users (deactivate, don't delete)

## Code Conventions

### Python
- MongoEngine Document classes in `app/models.py`
- Route handlers in `app/routes/*.py`
- Use `g.current_tenant` for tenant context
- Always log activities for audit trail
- Use `@permission_required` decorator for protected routes
- Datetime handling:
  - Models use `datetime.utcnow` for `default` values
  - Display uses `.strftime()` for formatting (e.g., `'%d/%m/%Y %H:%M'`)
  - Import: `from datetime import datetime`

### API Development
- Return consistent JSON structure (success/error pattern)
- Include descriptive error messages in Spanish (user-facing)
- Use HTTP status codes: 200 (success), 400 (validation error), 404 (not found), 500 (server error)
- Validate tenant ownership before mutations
- Handle MongoEngine exceptions:
  - `DoesNotExist`: Return 404 or appropriate error message
  - `ValidationError`: Return 400 with field details
  - `NotUniqueError`: Return 400 with duplicate error message
- Always wrap ObjectId conversions in try/except for invalid IDs

### Template Development
- Extend `base.html` for consistency
- Use Tailwind CSS utility classes
- Alpine.js for interactivity
- DataTables for complex tables
- Mobile-responsive design required

## Common Gotchas

1. **Don't forget tenant filtering**: Always use `tenant=g.current_tenant` in queries
2. **Computed properties aren't queryable**: `Product.total_stock` is calculated, not stored
3. **FIFO is manual**: You must implement the sorted deduction pattern (see warehouse.py)
4. **Activity logging is required**: Don't skip logging CRUD operations for audit compliance
5. **MongoDB ObjectIds**:
   - Use `str(object.id)` when returning IDs in JSON responses
   - Use `ObjectId(id_string)` when querying by ID from request params
   - Import: `from bson import ObjectId`
   - Flask-Login user loader requires ObjectId conversion (see `app/__init__.py`)
6. **Port 5006**: Application runs on non-standard port (not 5000)
7. **Bundle components**: Use `product.bundle_components` property, not a direct field
8. **README.md is outdated**: Ignore SQLAlchemy/Flask-Migrate references in README

## Development Utilities

### Flask Shell
```bash
# Launch interactive shell with app context
flask shell
# or
python run.py shell
```

Shell context includes: `db`, `User`, `Product`, `Sale` (defined in `run.py`).

### MongoDB Shell Access
```bash
# Connect to MongoDB directly
mongosh inventory_db

# Common queries
db.products.find({tenant: ObjectId("...")})
db.users.countDocuments()
```

## File References

When working with specific functionality, refer to:
- Application factory: `app/__init__.py:create_app()`
- Multi-tenancy middleware: `app/__init__.py:load_tenant()`
- Template context injection: `app/__init__.py:inject_tenant()`
- Permissions system: `app/models.py:ROLE_PERMISSIONS`
- User permission checks: `app/models.py:User.has_permission()`
- FIFO stock logic: `app/routes/warehouse.py` (sales, wastage endpoints)
- Bundle assembly: `app/routes/warehouse.py:/api/assembly`
- Activity logging: `app/models.py:ActivityLog.log()`
- Authentication: `app/routes/auth.py`
- Excel exports: `app/routes/reports.py`
- Admin panel: `app/routes/admin.py`
