# Mejora del Modulo de Recepcion de Mercancia

**Fecha:** 2026-02-11
**Estado:** Implementado y testeado (31/31 tests pasando)

---

## Resumen

Se transformo el flujo de recepcion de mercancia de un registro basico a un sistema de compras completo. Los cambios incluyen: definicion de productos esperados al crear una orden, recepcion parcial, integracion del modelo Supplier (antes texto libre), costo unitario en lotes, lot codes legibles, y reemplazo de todos los `alert()` por toast notifications.

---

## Archivos Modificados

### 1. `app/models.py`

**Nuevo: `InboundOrderLineItem` (EmbeddedDocument)**
- `product` (ReferenceField a Product)
- `product_name` / `product_sku` (cache para evitar joins)
- `quantity_ordered` (lo que se pidio)
- `quantity_received` (lo que se ha recibido, default 0)
- `unit_cost` (costo unitario, default 0)

**Modificado: `InboundOrder`**
- Nuevo campo: `line_items = EmbeddedDocumentListField(InboundOrderLineItem)`
- Nuevo status valido: `partially_received`
- Nueva propiedad: `is_fully_received` - compara quantity_received vs quantity_ordered por item
- Nueva propiedad: `computed_total` - calcula total desde line items si existen
- Agregados indexes: `['tenant', 'status', '-created_at']`

**Modificado: `Lot`**
- Nuevo campo: `unit_cost = DecimalField(precision=2, default=0)`

**Modificado: `Supplier`**
- Nuevo campo: `abbreviation = StringField(max_length=10)` - para generar lot codes (ej: "COSM")
- Nuevo campo: `is_active = BooleanField(default=True)`
- Nuevo campo: `created_at = DateTimeField(default=utc_now)`

### 2. `app/__init__.py`

- Agregado `"partially_received": "Parcial"` al filtro Jinja2 `translate_status`

### 3. `app/routes/warehouse.py`

**Nuevas funciones/endpoints:**

| Endpoint | Metodo | Descripcion |
|----------|--------|-------------|
| `/warehouse/api/suppliers` | GET | Lista proveedores activos del tenant con busqueda `?q=texto` |
| `/warehouse/api/suppliers` | POST | Crea proveedor (name, rut, contact_info, abbreviation) |
| `/warehouse/api/orders/<id>/receiving-summary` | GET | Resumen con lotes creados, cantidades y costos |
| `generate_lot_code(supplier, product)` | helper | Genera `LOT-{PROV}-{SKU}-{YYMMDD}-{UUID4}` |

**Endpoints modificados:**

| Endpoint | Cambios |
|----------|---------|
| `GET /warehouse/api/orders` | Incluye `line_items` y `supplier_id` en respuesta |
| `POST /warehouse/api/orders` | Acepta `supplier_id` y array `items` opcionales |
| `PUT /warehouse/api/orders/<id>` | Permite editar line items si status es `pending` |
| `GET /warehouse/api/receiving/orders` | Filtra `status__in=['pending', 'partially_received']`, incluye line_items con progreso |
| `POST /warehouse/api/receiving/<id>` | Soporta recepcion parcial, lot codes legibles, unit_cost en lotes, retorna resumen de lotes creados |

**Vistas modificadas:**
- `receiving()`: Incluye pedidos `partially_received` ademas de `pending`
- `dashboard()`: Idem para el dashboard de warehouse

### 4. `app/templates/base.html`

- Componente Alpine.js `globalToast()` antes de `</body>`
- Escucha `@toast.window` para mostrar notificaciones
- Tipos: `success` (verde), `error` (rojo), `info` (azul), `warning` (amber)
- Auto-dismiss en 3 segundos con animacion fade
- Posicion: bottom-right, z-60, bottom-20 en mobile (para no tapar bottom nav)
- Uso: `this.$dispatch('toast', { message: 'Texto', type: 'success' })`

### 5. `app/templates/warehouse/orders.html`

- **Proveedor:** Input texto reemplazado por dropdown con busqueda en tiempo real
  - Fetch a `/warehouse/api/suppliers?q=` on keyup
  - Boton "+ Crear nuevo proveedor" con mini-form inline (nombre, RUT, abreviatura, contacto)
  - Proveedor seleccionado se muestra como badge removible
  - Si no seleccionan del dropdown, se usa como texto libre (backward compat)
- **Productos Esperados:** Nueva seccion en el modal de creacion/edicion
  - Grid por fila: producto (dropdown), cantidad, costo unitario, subtotal, boton eliminar
  - Total auto-calculado cuando hay items (campo total se hace read-only)
  - Responsive: grid en desktop, stack en mobile
- **Badge `partially_received`:** Naranja en DataTable y mobile cards
- **Columna Items:** Nueva columna en DataTable mostrando cantidad de productos esperados
- **Modal ampliado:** `max-w-lg` -> `max-w-3xl` con scroll interno `max-h-[90vh]`
- **Toasts:** Todos los `alert()` reemplazados por `$dispatch('toast', ...)`

### 6. `app/templates/warehouse/receiving.html`

- **Con line items:** Pre-llena grid desde order.line_items
  - Default quantity = ordered - already_received
  - Muestra barra de progreso por item (recibido/ordenado)
  - Campo unit_cost pre-llenado desde line item, editable
  - Producto bloqueado (disabled) para items que vienen del pedido
- **Sin line items (legacy):** Grid vacio, comportamiento identico al anterior
- **Badge status:** Muestra "Parcial" (naranja) o "Pendiente" (amarillo)
- **Progreso en lista:** Cada pedido muestra sus line items con barras de progreso
- **Post-recepcion:** Modal resumen con:
  - Tabla de lotes creados (codigo, producto, cantidad, costo, subtotal, vencimiento)
  - Totales acumulados
  - Boton "Imprimir" (CSS @media print)
  - Boton "Cerrar" que recarga la lista
- **Toasts:** Todos los `alert()` reemplazados por `$dispatch('toast', ...)`

### 7. `tests/test_models.py`

13 tests nuevos (31 total):

| Clase | Tests |
|-------|-------|
| `TestInboundOrderLineItem` | Creacion, valores por defecto |
| `TestInboundOrderModel` | Creacion con line_items, campo line_items existe, status partially_received, propiedad is_fully_received, propiedad computed_total, is_fully_received sin items |
| `TestLotModel` | unit_cost, unit_cost default |
| `TestSupplierModel` | Campos nuevos, is_active default, abbreviation opcional |

---

## Compatibilidad con Datos Existentes

- **Ordenes sin line_items:** Funcionan igual que antes (campo default `[]`)
- **Ordenes sin supplier ref:** Siguen mostrando `supplier_name` como texto
- **Lotes sin unit_cost:** Muestran $0
- **Proveedores sin is_active:** Query usa `is_active__ne=False` para incluirlos
- **Proveedores sin abbreviation:** Lot code usa nombre truncado o "GEN"
- **Status `partially_received`:** Solo aplica a ordenes con line_items
- **Flujo de armado de bundles:** No modificado

---

## Correcciones Post-Review

Despues de la implementacion inicial se hizo code review y se corrigieron:

1. **`@permission_required` en supplier endpoints** - GET requiere `orders.view`, POST requiere `orders.create`
2. **Capitalizacion de translate_status** - `"parcial"` -> `"Parcial"` (consistente con otros statuses)
3. **Lot code colisiones** - Reemplazado `hashlib.md5(timestamp)` por `uuid.uuid4()` para suffix unico
4. **Indexes en InboundOrder** - Agregados `['tenant', 'status', '-created_at']` para performance
5. **Abbreviation None vs ""** - Estandarizado a `None` para campos vacios (consistente con rut)

---

## Notas Conocidas

- **`PUT /warehouse/api/orders/<id>` usa `@permission_required('orders', 'edit')`** pero ningun rol en `ROLE_PERMISSIONS` tiene permiso `edit` para `orders`. Esto es pre-existente, no fue introducido por estos cambios. Para que funcione, habria que agregar `'edit'` a los roles en `ROLE_PERMISSIONS`.
- **Race condition en recepcion parcial:** Si dos usuarios reciben el mismo pedido simultaneamente, las cantidades `quantity_received` podrian incrementarse incorrectamente. El mismo patron existe en ventas y mermas (FIFO deduction). Una solucion robusta requeriria atomic updates a nivel de MongoDB, lo cual es un cambio arquitectural mayor.
- **Tests requieren venv del proyecto:** El entorno global tiene Flask 3.x incompatible con flask-mongoengine 1.0.0. Los tests corren con `./venv/bin/python -m pytest`.

---

## Verificacion Manual Recomendada

1. Crear orden SIN line items -> debe funcionar igual que antes
2. Crear orden CON line items (2-3 productos con cantidades y costos)
3. Recibir parcialmente (solo 1 producto) -> status debe ser "partially_received"
4. Recibir el resto -> status debe ser "received"
5. Verificar lot codes legibles (ej: `LOT-COSM-ARROZ5K-260211-A3F2`)
6. Verificar unit_cost en los lotes creados
7. Verificar toasts en lugar de alert() en orders y receiving
8. Verificar modal resumen post-recepcion con tabla de lotes
9. Probar creacion rapida de proveedor desde modal de orden
10. Probar en mobile (responsive)
