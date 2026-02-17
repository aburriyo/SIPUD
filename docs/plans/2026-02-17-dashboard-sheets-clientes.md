# Dashboard + Google Sheets + Clientes Mejorados — Plan de Implementacion

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redisenar el dashboard, agregar sistema de tags a clientes, e integrar Google Sheets de ManyChat para importar leads y crear ventas.

**Architecture:** Tres features independientes que comparten el modelo de clientes. Tags es la base (se modifica primero), luego Google Sheets (usa tags), y dashboard (independiente). El frontend usa Alpine.js + Tailwind + Chart.js existentes.

**Tech Stack:** Flask, MongoEngine, gspread, google-auth, Alpine.js, Tailwind CSS, Chart.js

---

## Lote 1: Sistema de Tags en Clientes

### Task 1: Migrar campo tags de StringField a ListField

**Files:**
- Modify: `app/models.py:534-572` (ShopifyCustomer model)

**Step 1:** Cambiar el campo `tags` en el modelo:

```python
# ANTES (linea 550):
tags = db.StringField(max_length=500)

# DESPUES:
tags = db.ListField(db.StringField(max_length=50), default=list)
```

**Step 2:** Agregar `'manychat'` a las choices de `source`:

```python
# ANTES (linea 546):
source = db.StringField(max_length=20, default='shopify', choices=['shopify', 'manual', 'import'])

# DESPUES:
source = db.StringField(max_length=20, default='shopify', choices=['shopify', 'manual', 'import', 'manychat'])
```

**Step 3:** Agregar index para tags:

```python
meta = {
    'collection': 'shopify_customers',
    'indexes': [
        'shopify_id',
        'email',
        'tenant',
        'tags',       # <-- NUEVO
        'phone',      # <-- NUEVO (para dedup ManyChat)
        '-total_spent',
        '-created_at'
    ]
}
```

**Step 4:** Migrar datos existentes en MongoDB. Los tags de Shopify vienen como string separado por comas. Crear script de migracion one-time:

```python
# Ejecutar manualmente una sola vez:
# python -c "
# from app import create_app; app = create_app()
# with app.app_context():
#     from app.models import ShopifyCustomer
#     for c in ShopifyCustomer.objects():
#         if isinstance(c.tags, str) and c.tags:
#             c.tags = [t.strip() for t in c.tags.split(',') if t.strip()]
#             c.save()
#         elif not c.tags:
#             c.tags = []
#             c.save()
#     print('Migration done')
# "
```

**Step 5:** Verificar que pytest pasa:

Run: `./venv/bin/python -m pytest tests/ -v`

**Step 6:** Commit:

```bash
git add app/models.py
git commit -m "feat: migrar tags de string a list, agregar source manychat"
```

---

### Task 2: API — Tags en respuestas y filtro por tag

**Files:**
- Modify: `app/routes/customers.py:72-125` (get_customers)
- Modify: `app/routes/customers.py:128-179` (get_customer_detail)

**Step 1:** Agregar `tags` a la respuesta de `get_customers()` (linea ~105-117). Agregar despues de `'created_at'`:

```python
'tags': c.tags or [],
```

**Step 2:** Agregar filtro por tag en `get_customers()`. Despues de `search` (linea ~80), agregar:

```python
tag_filter = request.args.get('tag', '').strip()
```

Y en el query builder, despues del bloque if/else de search, agregar:

```python
if tag_filter:
    customers = customers.filter(tags=tag_filter)
```

**Step 3:** En `get_customer_detail()`, el campo `tags` ya se retorna (linea 176). Verificar que funciona con ListField.

**Step 4:** Agregar endpoint para actualizar tags de un cliente:

```python
@bp.route('/api/customers/<customer_id>/tags', methods=['PUT'])
@login_required
@permission_required('customers', 'edit')
def update_customer_tags(customer_id):
    """Update customer tags"""
    tenant = g.current_tenant
    data = request.get_json()

    if not data or 'tags' not in data:
        return jsonify({'error': 'Tags requeridos'}), 400

    try:
        customer = ShopifyCustomer.objects.get(id=ObjectId(customer_id), tenant=tenant)
    except Exception:
        return jsonify({'error': 'Cliente no encontrado'}), 404

    customer.tags = [t.strip().lower() for t in data['tags'] if t.strip()]
    customer.updated_at = utc_now()
    customer.save()

    return jsonify({'success': True, 'tags': customer.tags})
```

**Step 5:** Agregar permiso `'edit'` a customers en `ROLE_PERMISSIONS` (`app/models.py`):
- admin: agregar `'edit'` a la lista de customers
- manager: agregar `'edit'` a la lista de customers

**Step 6:** Verificar pytest pasa.

**Step 7:** Commit:

```bash
git add app/routes/customers.py app/models.py
git commit -m "feat: API tags en clientes — filtro, respuesta, edicion"
```

---

### Task 3: UI — Tags visibles en tabla + filtro + edicion

**Files:**
- Modify: `app/templates/customers.html`

**Step 1:** Agregar columna "Tags" a la DataTable. En el `<thead>` (linea ~138-147), agregar columna entre "Ciudad" y "Pedidos":

```html
<th class="px-3 sm:px-6 py-3">Tags</th>
```

**Step 2:** En el JS `initTable()` (linea ~493), agregar columna de tags despues de `city`:

```javascript
{
    data: 'tags',
    render: function(data) {
        if (!data || data.length === 0) return '<span class="text-xs text-slate-400">—</span>';
        const tagColors = {
            'calificado': 'bg-green-100 text-green-800',
            'interesado': 'bg-yellow-100 text-yellow-800',
            'poco-interesado': 'bg-red-100 text-red-800',
        };
        return data.map(tag => {
            const cls = tagColors[tag] || 'bg-slate-100 text-slate-700';
            return `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${cls} mr-1">${tag}</span>`;
        }).join('');
    }
},
```

**Step 3:** Agregar dropdown de filtro por tag en el header. Despues de los botones de accion (linea ~60), agregar un select:

```html
<div class="flex items-center gap-2 mt-2 sm:mt-0">
    <select x-model="tagFilter" @change="filterByTag()"
        class="text-sm border-slate-300 rounded-lg focus:ring-primary-500 focus:border-primary-500">
        <option value="">Todos los tags</option>
        <option value="calificado">🟢 Calificado</option>
        <option value="interesado">🟡 Interesado</option>
        <option value="poco-interesado">🔴 Poco interesado</option>
    </select>
</div>
```

**Step 4:** Agregar variables y funciones Alpine. En `customersApp()`:

```javascript
tagFilter: '',

filterByTag() {
    const url = this.tagFilter
        ? `/customers/api/customers?tag=${this.tagFilter}`
        : '/customers/api/customers';
    this.table.ajax.url(url).load();
},
```

**Step 5:** En el modal de detalle de cliente, mostrar tags editables. Agregar despues del grid de info (linea ~213):

```html
<!-- Tags -->
<div class="mb-4">
    <p class="text-xs font-medium text-slate-500 mb-2">Etiquetas</p>
    <div class="flex flex-wrap gap-1">
        <template x-for="tag in (currentCustomer.tags || [])" :key="tag">
            <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium"
                  :class="getTagClass(tag)">
                <span x-text="tag"></span>
                <button @click="removeTag(currentCustomer.id, tag)" class="ml-1.5 text-current opacity-60 hover:opacity-100">
                    &times;
                </button>
            </span>
        </template>
        <button @click="showTagInput = !showTagInput"
            class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 hover:bg-slate-200">
            + Tag
        </button>
    </div>
    <div x-show="showTagInput" class="mt-2 flex gap-2">
        <input type="text" x-model="newTag" @keydown.enter="addTag(currentCustomer.id)"
            class="text-sm border-slate-300 rounded-lg flex-1" placeholder="Nuevo tag...">
        <button @click="addTag(currentCustomer.id)"
            class="px-3 py-1.5 bg-primary-600 text-white text-xs rounded-lg">Agregar</button>
    </div>
</div>
```

**Step 6:** Agregar funciones helper en Alpine:

```javascript
showTagInput: false,
newTag: '',

getTagClass(tag) {
    const classes = {
        'calificado': 'bg-green-100 text-green-800',
        'interesado': 'bg-yellow-100 text-yellow-800',
        'poco-interesado': 'bg-red-100 text-red-800',
    };
    return classes[tag] || 'bg-slate-100 text-slate-700';
},

addTag(customerId) {
    if (!this.newTag.trim()) return;
    const tags = [...(this.currentCustomer.tags || []), this.newTag.trim().toLowerCase()];
    fetch(`/customers/api/customers/${customerId}/tags`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tags })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            this.currentCustomer.tags = data.tags;
            this.newTag = '';
            this.showTagInput = false;
            this.$dispatch('toast', { message: 'Tag agregado', type: 'success' });
            this.table.ajax.reload(null, false);
        }
    });
},

removeTag(customerId, tag) {
    const tags = (this.currentCustomer.tags || []).filter(t => t !== tag);
    fetch(`/customers/api/customers/${customerId}/tags`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tags })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            this.currentCustomer.tags = data.tags;
            this.$dispatch('toast', { message: 'Tag eliminado', type: 'success' });
            this.table.ajax.reload(null, false);
        }
    });
},
```

**Step 7:** Reemplazar alert() por toasts en todo el template (mismos que ya se usan en reconciliation y warehouse). Buscar todos los `alert(` y reemplazar por `this.$dispatch('toast', ...)`. Reemplazar `confirm(` por modal custom (misma pattern que reconciliation.html).

**Step 8:** Commit:

```bash
git add app/templates/customers.html
git commit -m "feat: UI tags en clientes — badges, filtro, edicion, toasts"
```

---

### Task 4: Fix Shopify sync para tags como lista

**Files:**
- Modify: `app/routes/customers.py:614-615` (sync_shopify)

**Step 1:** En la funcion `sync_shopify()`, donde se asignan tags de Shopify (linea 615):

```python
# ANTES:
customer.tags = customer_data.get('tags')

# DESPUES:
raw_tags = customer_data.get('tags', '')
customer.tags = [t.strip().lower() for t in raw_tags.split(',') if t.strip()] if raw_tags else []
```

**Step 2:** Commit:

```bash
git add app/routes/customers.py
git commit -m "fix: Shopify sync parsea tags como lista"
```

---

## Lote 2: Integracion Google Sheets / ManyChat

### Task 5: Instalar dependencias Google Sheets

**Step 1:** Agregar a requirements.txt:

```
gspread==6.1.4
google-auth==2.37.0
```

**Step 2:** Instalar:

```bash
./venv/bin/pip install gspread google-auth
```

**Step 3:** Commit:

```bash
git add requirements.txt
git commit -m "deps: agregar gspread y google-auth para Google Sheets"
```

---

### Task 6: Endpoint sync-manychat

**Files:**
- Modify: `app/routes/customers.py` (nuevo endpoint al final)

**Step 1:** Agregar imports al inicio del archivo:

```python
import gspread
from google.oauth2.service_account import Credentials
```

**Step 2:** Agregar helper para conectar a Google Sheets:

```python
def get_google_sheet():
    """Connect to the ManyChat Google Sheet"""
    creds_file = os.environ.get('GOOGLE_SHEETS_CREDENTIALS_FILE')
    sheet_id = os.environ.get('GOOGLE_SHEETS_ID')

    if not creds_file or not sheet_id:
        raise RuntimeError('GOOGLE_SHEETS_CREDENTIALS_FILE y GOOGLE_SHEETS_ID son requeridos en .env')

    scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    credentials = Credentials.from_service_account_file(creds_file, scopes=scopes)
    client = gspread.authorize(credentials)

    return client.open_by_key(sheet_id).sheet1
```

**Step 3:** Agregar endpoint de sync:

```python
@bp.route('/api/customers/sync-manychat', methods=['POST'])
@login_required
@permission_required('customers', 'sync')
def sync_manychat():
    """Import leads from ManyChat Google Sheet"""
    tenant = g.current_tenant

    try:
        sheet = get_google_sheet()
    except Exception as e:
        return jsonify({'error': f'Error conectando a Google Sheets: {str(e)}'}), 500

    try:
        records = sheet.get_all_records()
    except Exception as e:
        return jsonify({'error': f'Error leyendo Sheet: {str(e)}'}), 500

    stats = {'created': 0, 'skipped': 0, 'sales_created': 0, 'errors': []}

    from app.models import Sale, SaleItem, Product

    for idx, row in enumerate(records):
        try:
            phone = str(row.get('User ID', '')).strip()
            name = str(row.get('Nombre', '')).strip()
            semaforo_raw = str(row.get('Semáforo', '')).strip()
            city = str(row.get('Ciudad', '')).strip()
            productos_raw = str(row.get('Productos interes', '')).strip()
            lugar_entrega = str(row.get('Lugar Entrega', '')).strip()
            hora_entrega = str(row.get('Hora Entrega estimada', '') or row.get('Hora Entrega', '')).strip()
            metodo_pago = str(row.get('Método de Pago', '')).strip()

            if not phone or not name:
                continue

            # Normalize phone
            phone_clean = phone.replace('+', '').replace(' ', '')

            # Check if already imported (dedup by phone)
            existing = ShopifyCustomer.objects(phone__in=[phone, phone_clean, f'+{phone_clean}'], tenant=tenant).first()
            if existing:
                stats['skipped'] += 1
                continue

            # Determine tag from semaforo
            semaforo = semaforo_raw.lower()
            if 'calificado' in semaforo:
                tag = 'calificado'
            elif 'interesado' in semaforo:
                tag = 'interesado'
            else:
                tag = 'poco-interesado'

            # Create customer
            customer = ShopifyCustomer(
                name=name,
                phone=phone_clean,
                address_city=city or None,
                source='manychat',
                shopify_id=f"MANYCHAT-{phone_clean}",
                tags=[tag],
                total_orders=0,
                total_spent=0,
                created_at=utc_now(),
                updated_at=utc_now(),
                tenant=tenant
            )
            customer.save()
            stats['created'] += 1

            # If calificado AND has products, create pending sale
            if tag == 'calificado' and productos_raw:
                try:
                    sale = Sale(
                        customer_name=name,
                        address=lugar_entrega or city or '',
                        phone=phone_clean,
                        sale_type='con_despacho',
                        sales_channel='whatsapp',
                        delivery_status='pendiente',
                        payment_status='pendiente',
                        payment_method=metodo_pago.lower() if metodo_pago else None,
                        date_created=utc_now(),
                        tenant=tenant
                    )
                    sale.save()

                    # Parse products: "Promo jurel x2 | Caja Mensual x1"
                    product_entries = [p.strip() for p in productos_raw.split('|') if p.strip()]
                    notes_lines = []

                    for entry in product_entries:
                        # Try to extract "Name xN" pattern
                        import re
                        match = re.match(r'(.+?)\s*x\s*(\d+)$', entry.strip(), re.IGNORECASE)
                        if match:
                            prod_name = match.group(1).strip()
                            qty = int(match.group(2))
                        else:
                            prod_name = entry.strip()
                            qty = 1

                        # Fuzzy search product by name
                        product = Product.objects(
                            tenant=tenant,
                            name__icontains=prod_name
                        ).first()

                        if product:
                            SaleItem(
                                sale=sale,
                                product=product,
                                quantity=qty,
                                unit_price=float(product.base_price) if product.base_price else 0
                            ).save()
                        else:
                            notes_lines.append(f'Producto no encontrado: {entry}')

                    if notes_lines:
                        sale.delivery_observations = '\n'.join(notes_lines)
                        sale.save()

                    stats['sales_created'] += 1

                except Exception as e:
                    stats['errors'].append(f'Error creando venta para {name}: {str(e)}')

        except Exception as e:
            stats['errors'].append(f'Fila {idx + 2}: {str(e)}')

    return jsonify(stats)
```

**Step 4:** Verificar pytest pasa.

**Step 5:** Commit:

```bash
git add app/routes/customers.py
git commit -m "feat: endpoint sync-manychat — importa leads de Google Sheets"
```

---

### Task 7: UI — Boton Sincronizar ManyChat

**Files:**
- Modify: `app/templates/customers.html`

**Step 1:** Agregar boton "Sincronizar ManyChat" en el header, al lado de "Sincronizar Shopify":

```html
{% if current_user.has_permission('customers', 'sync') %}
<button @click="syncManyChat()"
    :disabled="syncingManyChat"
    class="inline-flex items-center justify-center px-4 py-2.5 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
    <svg x-show="!syncingManyChat" class="w-5 h-5 sm:mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
    <svg x-show="syncingManyChat" class="animate-spin w-5 h-5 sm:mr-2" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
    <span class="hidden sm:inline" x-text="syncingManyChat ? 'Sincronizando...' : 'Sincronizar ManyChat'"></span>
</button>
{% endif %}
```

**Step 2:** Agregar data y funcion Alpine:

```javascript
syncingManyChat: false,

syncManyChat() {
    this.syncingManyChat = true;
    fetch('/customers/api/customers/sync-manychat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json().then(data => ({ ok: res.ok, data })))
    .then(({ ok, data }) => {
        this.syncingManyChat = false;
        if (!ok) {
            this.$dispatch('toast', { message: data.error || 'Error al sincronizar', type: 'error' });
            return;
        }
        let msg = `ManyChat: ${data.created} clientes creados, ${data.sales_created} ventas creadas`;
        if (data.skipped > 0) msg += `, ${data.skipped} ya existian`;
        this.$dispatch('toast', { message: msg, type: 'success' });
        this.loadStats();
        this.table.ajax.reload();
    })
    .catch(err => {
        this.syncingManyChat = false;
        this.$dispatch('toast', { message: 'Error de conexion al sincronizar', type: 'error' });
    });
},
```

**Step 3:** Commit:

```bash
git add app/templates/customers.html
git commit -m "feat: UI boton Sincronizar ManyChat en clientes"
```

---

### Task 8: Guia de configuracion Google API

**Step 1:** Crear guia en el .env.example o como comentario. Las instrucciones para el usuario:

1. Ir a https://console.cloud.google.com/
2. Crear proyecto (o usar existente)
3. Habilitar "Google Sheets API"
4. Crear Service Account (IAM & Admin > Service Accounts > Create)
5. Descargar JSON de credenciales
6. Guardar como `credentials/google-sheets.json` en el proyecto
7. Copiar el email del Service Account (ej: sipud@project.iam.gserviceaccount.com)
8. Abrir el Google Sheet de ManyChat
9. Compartir el Sheet con ese email (solo lectura)
10. Copiar el ID del Sheet de la URL (la parte entre /d/ y /edit)
11. Agregar al .env:

```env
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials/google-sheets.json
GOOGLE_SHEETS_ID=abc123...
```

**Step 2:** Agregar `credentials/` a `.gitignore`

**Step 3:** Commit:

```bash
git add .gitignore
git commit -m "chore: agregar credentials/ a gitignore"
```

---

## Lote 3: Rediseno Visual Dashboard

### Task 9: Redisenar dashboard.html

**Files:**
- Modify: `app/templates/dashboard.html`

**Alcance:** Solo cambios visuales/CSS. Mismo contenido, misma data, misma logica. Usar skill frontend-design para generar el template.

**Mejoras especificas:**
- Welcome card: mas compacto, mejor tipografia
- KPI cards: con micro-animacion de entrada, iconos mas refinados
- Quick access buttons: rediseno con iconos mas limpios, hover mas sutil
- Chart area: bordes mas suaves, spacing mejorado
- Top products: barras de progreso visuales en vez de solo numero
- Stock critico: mejor jerarquia visual
- Activity log: timeline style en vez de tabla plana
- Overall: spacing consistente, esquinas mas redondeadas, sombras mas sutiles

**Step 1:** Usar skill frontend-design para redisenar el template completo.

**Step 2:** Reemplazar dashboard.html con el nuevo diseno.

**Step 3:** Verificar que el dashboard carga correctamente en el navegador.

**Step 4:** Commit:

```bash
git add app/templates/dashboard.html
git commit -m "feat: rediseno visual del dashboard"
```

---

## Verificacion Final

1. **Tags**: Crear cliente manual, agregar tag, verificar en tabla. Filtrar por tag.
2. **ManyChat**: Configurar credenciales, sincronizar, verificar clientes creados con tags correctos.
3. **Ventas ManyChat**: Verificar que leads calificados con productos generaron ventas pendientes.
4. **Dashboard**: Abrir dashboard, verificar que se ve bien en desktop y mobile.
5. **Toasts**: Verificar que no quedan alert() en customers.html.
6. **Tests**: `./venv/bin/python -m pytest tests/ -v` pasa sin errores.

## Orden de ejecucion

| Lote | Tasks | Dependencias |
|------|-------|-------------|
| 1 | Tasks 1-4 | Ninguna |
| 2 | Tasks 5-8 | Lote 1 (necesita tags como lista) |
| 3 | Task 9 | Independiente (puede ir en paralelo con Lote 2) |
