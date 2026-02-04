# Plan de Mejoras - Gestión de Ventas SIPUD

> **Fecha:** 2026-02-03
> **Estado:** Planificación

---

## Resumen de Tareas

| # | Tarea | Complejidad | Dependencias |
|---|-------|-------------|--------------|
| 1 | Campo `sales_channel` en ventas | Baja | Ninguna |
| 2 | Filtros avanzados en Gestión de Ventas | Media | Tarea 1 |
| 3 | Endpoint webhook ManyChat/Sheets | Media | Tarea 1 |
| 4 | Pulir venta en local | Baja | Ninguna |
| 5 | Sincronización Shopify (solo updates) | Media | Ninguna |
| 6 | Cuadratura bancaria | Alta | Ninguna |

---

## Tarea 1: Campo `sales_channel` (Canal de Venta)

### Estado Actual
- El modelo `Sale` NO tiene campo para indicar el canal de venta
- No se sabe si una venta vino de WhatsApp, Shopify, manual, etc.
- Las ventas de Shopify se identifican solo por `shopify_order_id`

### Cambios Requeridos

#### 1.1 Modelo (`app/models.py`)
```python
# Agregar constante
SALES_CHANNELS = {
    'manual': 'Manual (SIPUD)',
    'whatsapp': 'WhatsApp',
    'shopify': 'Shopify',
    'web': 'Web',
}

# Agregar campo en clase Sale (después de sale_type)
sales_channel = db.StringField(
    max_length=20,
    default='manual',
    choices=['manual', 'whatsapp', 'shopify', 'web']
)
```

#### 1.2 API - Crear venta (`app/routes/api.py`)
```python
# En create_sale(), agregar:
new_sale = Sale(
    # ... campos existentes ...
    sales_channel=data.get('sales_channel', 'manual'),  # NUEVO
)
```

#### 1.3 API - Obtener venta
```python
# En get_sale(), agregar al response:
'sales_channel': sale.sales_channel or 'manual',
```

#### 1.4 Sync Shopify (`app/routes/customers.py`)
```python
# En la sección "SYNC ORDERS → SALES", agregar:
new_sale = Sale(
    # ... campos existentes ...
    sales_channel='shopify',  # NUEVO
)
```

#### 1.5 Template (`app/templates/sales.html`)
- Agregar columna "Canal" en la tabla
- Mostrar badge con icono según canal (WhatsApp verde, Shopify morado, etc.)

### Archivos a Modificar
- `app/models.py` (agregar campo + constante)
- `app/routes/api.py` (create_sale, get_sale, get_sales)
- `app/routes/customers.py` (sync_shopify)
- `app/templates/sales.html` (columna + badge)
- `app/__init__.py` (filtro Jinja para traducir canal)

### Estimación: 30-45 min

---

## Tarea 2: Filtros Avanzados en Gestión de Ventas

### Estado Actual
- La tabla usa DataTables con filtro básico de texto
- NO hay filtros por:
  - Estado de entrega (pendiente/entregado/etc)
  - Estado de pago (pendiente/pagado/parcial)
  - Tipo de venta (despacho/local)
  - Canal de venta (manual/whatsapp/shopify)

### Cambios Requeridos

#### 2.1 Template - Panel de Filtros (`app/templates/sales.html`)
Agregar antes de la tabla:
```html
<!-- Filtros Avanzados -->
<div class="bg-white p-4 rounded-lg border border-slate-200 mb-4" x-data="{ showFilters: false }">
    <button @click="showFilters = !showFilters" class="flex items-center text-sm font-medium text-slate-700">
        <svg class="w-4 h-4 mr-2" ...></svg>
        Filtros Avanzados
        <span x-show="activeFiltersCount > 0" class="ml-2 px-2 py-0.5 bg-primary-100 text-primary-700 rounded-full text-xs" x-text="activeFiltersCount"></span>
    </button>
    
    <div x-show="showFilters" class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
        <!-- Filtro: Estado de Entrega -->
        <div>
            <label class="block text-xs font-semibold text-slate-500 mb-1">Estado Entrega</label>
            <select x-model="filters.delivery_status" @change="applyFilters()" class="w-full text-sm rounded-md border-slate-300">
                <option value="">Todos</option>
                <option value="pendiente">Pendiente</option>
                <option value="en_preparacion">En Preparación</option>
                <option value="en_transito">En Tránsito</option>
                <option value="entregado">Entregado</option>
                <option value="con_observaciones">Con Observaciones</option>
                <option value="cancelado">Cancelado</option>
            </select>
        </div>
        
        <!-- Filtro: Estado de Pago -->
        <div>
            <label class="block text-xs font-semibold text-slate-500 mb-1">Estado Pago</label>
            <select x-model="filters.payment_status" @change="applyFilters()" class="w-full text-sm rounded-md border-slate-300">
                <option value="">Todos</option>
                <option value="pendiente">Pendiente</option>
                <option value="parcial">Parcial</option>
                <option value="pagado">Pagado</option>
            </select>
        </div>
        
        <!-- Filtro: Tipo de Venta -->
        <div>
            <label class="block text-xs font-semibold text-slate-500 mb-1">Tipo</label>
            <select x-model="filters.sale_type" @change="applyFilters()" class="w-full text-sm rounded-md border-slate-300">
                <option value="">Todos</option>
                <option value="con_despacho">Con Despacho</option>
                <option value="en_local">En Local</option>
            </select>
        </div>
        
        <!-- Filtro: Canal de Venta -->
        <div>
            <label class="block text-xs font-semibold text-slate-500 mb-1">Canal</label>
            <select x-model="filters.sales_channel" @change="applyFilters()" class="w-full text-sm rounded-md border-slate-300">
                <option value="">Todos</option>
                <option value="manual">Manual</option>
                <option value="whatsapp">WhatsApp</option>
                <option value="shopify">Shopify</option>
                <option value="web">Web</option>
            </select>
        </div>
    </div>
</div>
```

#### 2.2 JavaScript - Lógica de Filtros
```javascript
// En salesTable()
filters: {
    delivery_status: '',
    payment_status: '',
    sale_type: '',
    sales_channel: ''
},

get activeFiltersCount() {
    return Object.values(this.filters).filter(v => v !== '').length;
},

applyFilters() {
    // Filtrar DataTable usando columnas
    const table = $('#salesTable').DataTable();
    
    // Columna 2: Tipo
    table.column(2).search(this.filters.sale_type).draw();
    // Columna 3: Entrega
    table.column(3).search(this.filters.delivery_status).draw();
    // Columna 4: Pago
    table.column(4).search(this.filters.payment_status).draw();
    // Columna 5: Canal (nueva)
    table.column(5).search(this.filters.sales_channel).draw();
},

clearFilters() {
    this.filters = { delivery_status: '', payment_status: '', sale_type: '', sales_channel: '' };
    $('#salesTable').DataTable().search('').columns().search('').draw();
}
```

#### 2.3 Backend - Filtros en API (opcional, para server-side)
```python
# En get_sales(), agregar parámetros:
delivery_status = request.args.get('delivery_status')
payment_status = request.args.get('payment_status')
sale_type = request.args.get('sale_type')
sales_channel = request.args.get('sales_channel')

if delivery_status:
    query = query.filter(delivery_status=delivery_status)
if payment_status:
    query = query.filter(payment_status=payment_status)
# etc...
```

### Archivos a Modificar
- `app/templates/sales.html` (panel filtros + JS)
- `app/routes/api.py` (opcional: filtros server-side)

### Estimación: 1-1.5 hrs

---

## Tarea 3: Endpoint Webhook ManyChat/Sheets

### Estado Actual
- NO existe endpoint para recibir datos de ManyChat/Google Sheets
- Las ventas de WhatsApp se crean manualmente

### Cambios Requeridos

#### 3.1 Nueva Ruta (`app/routes/api.py`)
```python
@bp.route('/sales/webhook', methods=['POST'])
def webhook_create_sale():
    """
    Endpoint para crear ventas desde ManyChat/Google Sheets.
    No requiere autenticación (usa token en header).
    
    Headers:
        X-Webhook-Token: token_secreto_configurado
    
    Body (JSON):
    {
        "customer": "Nombre Cliente",
        "phone": "+56912345678",
        "address": "Dirección de entrega",
        "items": [
            {"sku": "PROD-001", "quantity": 2},
            {"product_name": "Producto X", "quantity": 1, "unit_price": 5000}
        ],
        "notes": "Notas del pedido",
        "source": "manychat"  // opcional: manychat, sheets, zapier
    }
    
    Response:
    {
        "success": true,
        "sale_id": "...",
        "sale_number": 123,
        "total": 15000,
        "message": "Venta creada exitosamente"
    }
    """
    # Validar token
    webhook_token = os.environ.get('SIPUD_WEBHOOK_TOKEN', '')
    provided_token = request.headers.get('X-Webhook-Token', '')
    
    if not webhook_token or provided_token != webhook_token:
        return jsonify({'error': 'Token inválido'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Body vacío'}), 400
    
    # Obtener tenant por defecto (o desde header si multi-tenant)
    tenant = Tenant.objects(slug='puerto-distribucion').first()
    if not tenant:
        return jsonify({'error': 'Tenant no configurado'}), 500
    
    # Validar campos requeridos
    if not data.get('customer'):
        return jsonify({'error': 'Campo "customer" requerido'}), 400
    if not data.get('items') or len(data['items']) == 0:
        return jsonify({'error': 'Se requiere al menos un item'}), 400
    
    try:
        # Crear venta
        new_sale = Sale(
            customer_name=data['customer'],
            phone=data.get('phone', ''),
            address=data.get('address', ''),
            sale_type='con_despacho',
            delivery_status='pendiente',
            payment_status='pendiente',
            sales_channel='whatsapp',  # Nuevo campo
            tenant=tenant
        )
        new_sale.save()
        
        # Procesar items
        total = 0
        for item_data in data['items']:
            product = None
            
            # Buscar producto por SKU
            if item_data.get('sku'):
                product = Product.objects(sku=item_data['sku'], tenant=tenant).first()
            
            # Si no se encuentra por SKU, buscar por nombre
            if not product and item_data.get('product_name'):
                product = Product.objects(
                    name__icontains=item_data['product_name'],
                    tenant=tenant
                ).first()
            
            if not product:
                # Crear producto placeholder o usar precio manual
                unit_price = item_data.get('unit_price', 0)
                # Podrías crear el producto o rechazar
                continue
            
            quantity = int(item_data.get('quantity', 1))
            unit_price = float(item_data.get('unit_price', product.base_price or 0))
            
            # Validar stock
            if product.total_stock < quantity:
                new_sale.delete()
                return jsonify({
                    'error': f'Stock insuficiente para {product.name}. Disponible: {product.total_stock}'
                }), 400
            
            # Descontar stock (FIFO)
            remaining = quantity
            for lot in sorted(product.lots, key=lambda x: x.created_at):
                if remaining <= 0:
                    break
                if lot.quantity_current > 0:
                    deduct = min(lot.quantity_current, remaining)
                    lot.quantity_current -= deduct
                    lot.save()
                    remaining -= deduct
            
            # Crear SaleItem
            sale_item = SaleItem(
                sale=new_sale,
                product=product,
                quantity=quantity,
                unit_price=unit_price
            )
            sale_item.save()
            total += quantity * unit_price
        
        # Log activity (usuario sistema)
        ActivityLog.log(
            user=User.objects(username='sistema').first() or User.objects.first(),
            action='create',
            module='sales',
            description=f'Venta creada via webhook ({data.get("source", "whatsapp")}) para "{data["customer"]}"',
            target_id=str(new_sale.id),
            target_type='Sale',
            tenant=tenant
        )
        
        return jsonify({
            'success': True,
            'sale_id': str(new_sale.id),
            'total': total,
            'message': 'Venta creada exitosamente'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

#### 3.2 Variable de Entorno
```bash
# .env
SIPUD_WEBHOOK_TOKEN=tu_token_secreto_aqui
```

#### 3.3 Documentación para ManyChat/Sheets
Crear archivo `docs/WEBHOOK_API.md`:
```markdown
# API Webhook para Ventas

## Endpoint
POST /api/sales/webhook

## Autenticación
Header: X-Webhook-Token: {token}

## Ejemplo con curl
curl -X POST https://sipud.tudominio.cl/api/sales/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Token: tu_token" \
  -d '{
    "customer": "Juan Pérez",
    "phone": "+56912345678",
    "address": "Av. Principal 123, Puerto Montt",
    "items": [
      {"sku": "ARROZ-5KG", "quantity": 2}
    ]
  }'
```

### Archivos a Modificar/Crear
- `app/routes/api.py` (nuevo endpoint)
- `.env` (agregar token)
- `docs/WEBHOOK_API.md` (documentación)

### Estimación: 1.5-2 hrs

---

## Tarea 4: Pulir Venta en Local

### Estado Actual
- Ya existe `sale_type` con valores `con_despacho` y `en_local`
- Las ventas `en_local` se marcan automáticamente como `entregado`
- El formulario de nueva venta ya tiene selector de tipo
- **Funciona correctamente**, solo falta:
  - Si es `en_local` y pago completo → marcar también como `pagado` automáticamente
  - Simplificar UI cuando es venta en local

### Cambios Requeridos

#### 4.1 API - Crear venta (`app/routes/api.py`)
```python
# En create_sale(), después de:
if sale_type == 'en_local':
    delivery_status = 'entregado'
    date_delivered = datetime.utcnow()

# Agregar:
    # Si hay pago inicial igual al total, marcar como pagado
    if 'initial_payment' in data:
        initial_amount = float(data['initial_payment'].get('amount', 0))
        # Calcular total aquí o después de crear items
```

#### 4.2 Template - Simplificar flujo
```javascript
// En handleSaleTypeChange()
handleSaleTypeChange() {
    if (this.newSale.sale_type === 'en_local') {
        this.newSale.address = '';
        this.newSale.delivery_observations = '';
        // Sugerir pago completo al contado
        // (El total se calcula dinámicamente)
    }
}
```

### Archivos a Modificar
- `app/routes/api.py` (lógica adicional)
- `app/templates/sales.html` (UI simplificada para local)

### Estimación: 30 min

---

## Tarea 5: Sincronización Shopify (Solo Updates)

### Estado Actual
- `sync_shopify()` en `customers.py` hace:
  - Sync de clientes ✅
  - Sync de órdenes ✅
  - Sync de productos ✅ (crea si no existe, actualiza si existe)
  - Sync de stock ✅
- **NO hay protección contra deletes**
- **NO hay confirmación visual de cambios**

### Cambios Requeridos

#### 5.1 Modo Preview antes de Sync
```python
@bp.route('/api/customers/sync/preview', methods=['GET'])
@login_required
@permission_required('customers', 'sync')
def sync_shopify_preview():
    """
    Preview de cambios antes de sincronizar.
    NO aplica cambios, solo muestra qué se modificaría.
    """
    tenant = g.current_tenant
    
    # ... llamar a Shopify API ...
    
    preview = {
        'products': {
            'to_create': [],   # Productos nuevos en Shopify
            'to_update': [],   # Productos con cambios
            'unchanged': 0     # Sin cambios
        },
        'orders': {
            'to_create': [],   # Órdenes nuevas
            'unchanged': 0
        },
        'customers': {
            'to_create': [],
            'to_update': [],
            'unchanged': 0
        }
    }
    
    # Analizar diferencias sin guardar
    # ...
    
    return jsonify(preview)
```

#### 5.2 Proteger contra Deletes
```python
# En sync_shopify(), NUNCA hacer:
# Product.objects(...).delete()  ❌
# ShopifyCustomer.objects(...).delete()  ❌

# Solo crear o actualizar:
if existing:
    existing.field = new_value
    existing.save()  # UPDATE
else:
    new_obj = Model(...)
    new_obj.save()  # CREATE
```

#### 5.3 Modal de Confirmación en Frontend
```html
<!-- Modal Preview Sync -->
<div x-show="showSyncPreview" class="fixed inset-0 z-50 ...">
    <div class="bg-white rounded-xl max-w-2xl ...">
        <h3>Vista Previa de Sincronización</h3>
        
        <div class="space-y-4">
            <!-- Productos -->
            <div>
                <h4>Productos</h4>
                <p x-show="syncPreview.products.to_create.length > 0">
                    <span class="text-green-600">+</span> 
                    <span x-text="syncPreview.products.to_create.length"></span> nuevos
                </p>
                <p x-show="syncPreview.products.to_update.length > 0">
                    <span class="text-blue-600">~</span> 
                    <span x-text="syncPreview.products.to_update.length"></span> a actualizar
                </p>
            </div>
            
            <!-- Órdenes, Clientes similar -->
        </div>
        
        <div class="flex justify-end gap-3">
            <button @click="showSyncPreview = false">Cancelar</button>
            <button @click="executeSyncConfirmed()" class="bg-primary-600 ...">
                Confirmar y Sincronizar
            </button>
        </div>
    </div>
</div>
```

### Archivos a Modificar
- `app/routes/customers.py` (agregar preview, proteger deletes)
- `app/templates/sales.html` o `customers.html` (modal confirmación)

### Estimación: 2-3 hrs

---

## Tarea 6: Cuadratura Bancaria

### Estado Actual
- NO existe módulo de cuadratura
- Las ventas tienen `payment_status` pero no se cruzan con datos bancarios
- El modelo `Payment` registra pagos pero sin referencia a transacción bancaria

### Cambios Requeridos

#### 6.1 Nuevo Modelo: BankTransaction
```python
class BankTransaction(db.Document):
    """Transacción bancaria importada desde cartola"""
    date = db.DateTimeField(required=True)
    description = db.StringField(max_length=500)
    amount = db.DecimalField(precision=2, required=True)
    reference = db.StringField(max_length=100)  # Número de operación
    
    # Estado de conciliación
    status = db.StringField(
        max_length=20,
        default='pending',
        choices=['pending', 'matched', 'unmatched', 'ignored']
    )
    
    # Venta asociada (si matched)
    matched_sale = db.ReferenceField(Sale)
    matched_payment = db.ReferenceField(Payment)
    
    # Metadata
    import_batch = db.StringField(max_length=50)  # ID del lote de importación
    tenant = db.ReferenceField(Tenant)
    created_at = db.DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'bank_transactions',
        'indexes': ['date', 'status', 'tenant', 'amount']
    }
```

#### 6.2 Nuevas Rutas (`app/routes/reconciliation.py`)
```python
bp = Blueprint('reconciliation', __name__, url_prefix='/reconciliation')

@bp.route('/')
@login_required
def reconciliation_view():
    """Vista principal de cuadratura"""
    return render_template('reconciliation.html')

@bp.route('/api/upload', methods=['POST'])
@login_required
def upload_bank_statement():
    """Importar cartola bancaria (Excel)"""
    # Parsear Excel
    # Crear BankTransaction por cada fila
    # Retornar resumen
    pass

@bp.route('/api/transactions')
@login_required
def get_transactions():
    """Listar transacciones con filtros"""
    pass

@bp.route('/api/match', methods=['POST'])
@login_required
def match_transaction():
    """Asociar transacción con venta manualmente"""
    pass

@bp.route('/api/auto-match', methods=['POST'])
@login_required
def auto_match():
    """Intentar match automático por monto y fecha"""
    # Buscar ventas con total similar ±5%
    # En rango de fecha ±3 días
    # Sugerir matches
    pass

@bp.route('/api/report')
@login_required
def reconciliation_report():
    """Generar reporte de cuadratura"""
    # Ventas sin match bancario
    # Transacciones sin match
    # Diferencias de monto
    pass
```

#### 6.3 Template (`app/templates/reconciliation.html`)
- Panel de subida de cartola (drag & drop Excel)
- Tabla de transacciones con columnas:
  - Fecha | Descripción | Monto | Estado | Venta Asociada | Acciones
- Filtros por estado (pendiente, matched, etc)
- Vista de "sugerencias" de match automático
- Resumen de cuadratura (matched vs pendiente)

#### 6.4 Lógica de Auto-Match
```python
def auto_match_transactions(tenant):
    """Intenta match automático"""
    unmatched = BankTransaction.objects(tenant=tenant, status='pending')
    
    for tx in unmatched:
        # Buscar ventas en rango de fecha
        date_start = tx.date - timedelta(days=3)
        date_end = tx.date + timedelta(days=3)
        
        candidates = Sale.objects(
            tenant=tenant,
            date_created__gte=date_start,
            date_created__lte=date_end,
            payment_status__ne='pagado'
        )
        
        for sale in candidates:
            # Comparar monto (tolerancia 1%)
            if abs(sale.total_amount - float(tx.amount)) / sale.total_amount < 0.01:
                # Match encontrado
                yield {
                    'transaction': tx,
                    'sale': sale,
                    'confidence': 'high' if sale.total_amount == float(tx.amount) else 'medium'
                }
```

### Archivos a Crear/Modificar
- `app/models.py` (nuevo modelo BankTransaction)
- `app/routes/reconciliation.py` (nuevo blueprint)
- `app/templates/reconciliation.html` (nueva vista)
- `app/__init__.py` (registrar blueprint)
- `app/templates/base.html` (agregar link en menú)

### Estimación: 4-6 hrs

---

## Orden de Implementación Recomendado

```
Día 1 (2-3 hrs):
├── Tarea 1: Campo sales_channel (30-45 min)
├── Tarea 4: Pulir venta en local (30 min)
└── Tarea 2: Filtros avanzados (1-1.5 hrs)

Día 2 (2-3 hrs):
└── Tarea 3: Webhook ManyChat (1.5-2 hrs)
    └── Testear con Postman/curl
    └── Documentar para Pablo

Día 3 (2-3 hrs):
└── Tarea 5: Sync Shopify mejorado (2-3 hrs)
    └── Preview antes de sync
    └── Confirmación visual

Día 4+ (4-6 hrs):
└── Tarea 6: Cuadratura bancaria
    └── Modelo + rutas
    └── UI básica
    └── Auto-match
```

---

## Preguntas Pendientes

1. **ManyChat**: ¿Qué formato exacto envía ManyChat? ¿Hay documentación de Pablo?
2. **Cuadratura**: ¿Qué banco usa Puerto Distribución? ¿Formato de cartola Excel?
3. **Shopify**: ¿Quieres que el sync sea manual (botón) o automático (cron)?
4. **Permisos**: ¿Quién puede ver/usar cuadratura? ¿Solo admin?

---

## Checklist Pre-Implementación

- [ ] Backup de base de datos
- [ ] Branch de desarrollo (`git checkout -b feature/sales-improvements`)
- [ ] Variables de entorno configuradas (.env)
- [ ] Servidor local corriendo (`python run.py`)
