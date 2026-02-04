# API DOCUMENTATION - SIPUD

## Índice

1. [**Main (Dashboard)**](#main-dashboard)
2. [**Auth (Autenticación)**](#auth-autenticación)
3. [**Admin (Gestión Usuarios)**](#admin-gestión-usuarios)
4. [**API (REST Endpoints)**](#api-rest-endpoints)
5. [**Warehouse (Bodega)**](#warehouse-bodega)
6. [**Customers (CRM/Shopify)**](#customers-crmshopify)
7. [**Delivery (Hojas de Reparto)**](#delivery-hojas-de-reparto)
8. [**Reports (Exportación)**](#reports-exportación)
9. [**Reconciliation (Cuadratura Bancaria)**](#reconciliation-cuadratura-bancaria)

---

## Convenciones

### Autenticación

- **Auth requerida:** `@login_required` (Flask-Login)
- **Permisos:** `@permission_required(module, action)` (RBAC)
- **Session:** Cookie HTTP-only, 30 días si "Remember me"

### Rate Limits

- **Default:** 200/día, 50/hora por IP
- **Webhook:** 10/min, 100/hora por IP
- **Storage:** Memory (cambiar a Redis en producción)

### Formato de Respuesta

**Éxito:**
```json
{
  "success": true,
  "message": "Operación exitosa",
  "data": { ... }
}
```

**Error:**
```json
{
  "error": "Descripción del error",
  "details": { ... }
}
```

### Códigos HTTP

| Código | Significado |
|--------|-------------|
| 200 | OK - Operación exitosa |
| 201 | Created - Recurso creado |
| 400 | Bad Request - Datos inválidos |
| 401 | Unauthorized - No autenticado |
| 403 | Forbidden - Sin permisos |
| 404 | Not Found - Recurso no existe |
| 429 | Too Many Requests - Rate limit excedido |
| 500 | Internal Server Error - Error del servidor |

---

## Main (Dashboard)

### GET `/`
**Descripción:** Dashboard principal con estadísticas

**Auth:** ✅ Required

**Permisos:** Ninguno (todos los roles)

**Response:**
- HTML Template: `dashboard.html`
- Variables context:
  - `stats`: Dict con estadísticas
  - `user_info`: Info del usuario actual
  - `critical_stock`: Productos con stock crítico
  - `top_products`: Top 5 productos más vendidos
  - `sales_distribution`: Distribución de ventas por estado
  - `user_activity`: Últimas 5 actividades

---

### GET `/products`
**Descripción:** Vista de productos

**Auth:** ✅ Required

**Response:**
- HTML Template: `products.html`
- Variables: `products` (lista de productos del tenant)

---

### GET `/sales`
**Descripción:** Vista de ventas (con DataTables)

**Auth:** ✅ Required

**Response:**
- HTML Template: `sales.html`
- Variables: `sales`, `pagination`

---

### GET `/switch-tenant/<tenant_id>`
**Descripción:** Cambiar tenant activo

**Auth:** ✅ Required

**Response:** Redirect a `/`

---

## Auth (Autenticación)

### GET/POST `/login`
**Descripción:** Login de usuario

**Auth:** ❌ No required

**Request (POST):**
```json
{
  "username": "admin",
  "password": "contraseña",
  "remember": "on"  // opcional
}
```

**Response:**
- **Éxito:** Redirect a `/` (dashboard)
- **Error:** Flash message + redirect a `/login`

**Activity Log:** `login` / `login_failed`

---

### GET `/logout`
**Descripción:** Cerrar sesión

**Auth:** ✅ Required

**Response:** Redirect a `/login`

**Activity Log:** `logout`

---

### GET/POST `/forgot-password`
**Descripción:** Solicitar recuperación de contraseña

**Auth:** ❌ No required

**Request (POST):**
```json
{
  "email": "usuario@example.com"
}
```

**Response:**
- HTML Template: `auth/forgot_password.html`
- Flash message (genérico para no revelar si email existe)

**Activity Log:** `password_reset_request`

---

### GET/POST `/reset-password/<token>`
**Descripción:** Restablecer contraseña con token

**Auth:** ❌ No required

**Request (POST):**
```json
{
  "password": "nueva_contraseña",
  "confirm_password": "nueva_contraseña"
}
```

**Response:**
- **Éxito:** Redirect a `/login`
- **Error:** Flash message

**Validaciones:**
- Token válido y no expirado (1 hora)
- Contraseña mínimo 6 caracteres
- Contraseñas coinciden

**Activity Log:** `password_reset_complete`

---

### GET/POST `/settings`
**Descripción:** Configuración de cuenta (cambio de contraseña)

**Auth:** ✅ Required

**Request (POST):**
```json
{
  "current_password": "contraseña_actual",
  "new_password": "nueva_contraseña",
  "confirm_password": "nueva_contraseña"
}
```

**Response:**
- HTML Template: `auth/settings.html`

**Activity Log:** `password_change`

---

### GET `/api/check-session`
**Descripción:** Verificar si hay sesión activa (API)

**Auth:** ❌ No required

**Response:**
```json
{
  "authenticated": true,
  "user": {
    "username": "admin",
    "role": "admin",
    "full_name": "Administrador"
  }
}
```

---

## Admin (Gestión Usuarios)

### GET `/admin/users`
**Descripción:** Vista de gestión de usuarios

**Auth:** ✅ Required

**Permisos:** `users:view`

**Response:**
- HTML Template: `admin/users.html`

---

### GET `/admin/api/users`
**Descripción:** Obtener lista de usuarios (JSON)

**Auth:** ✅ Required

**Permisos:** `users:view`

**Response:**
```json
{
  "success": true,
  "users": [
    {
      "id": "507f1f77bcf86cd799439011",
      "username": "admin",
      "email": "admin@example.com",
      "full_name": "Administrador",
      "role": "admin",
      "is_active": true,
      "last_login": "04/02/2026 10:30",
      "created_at": "01/01/2026 08:00"
    }
  ]
}
```

---

### POST `/admin/api/users`
**Descripción:** Crear nuevo usuario

**Auth:** ✅ Required

**Permisos:** `users:create`

**Request:**
```json
{
  "username": "nuevo_usuario",
  "password": "contraseña123",
  "email": "usuario@example.com",
  "full_name": "Nombre Completo",
  "role": "sales"
}
```

**Validaciones:**
- Username mínimo 3 caracteres
- Password mínimo 4 caracteres
- Email único (si se proporciona)
- Role válido: `admin`, `manager`, `warehouse`, `sales`

**Response:**
```json
{
  "success": true,
  "message": "Usuario creado exitosamente",
  "user_id": "507f1f77bcf86cd799439011"
}
```

**Activity Log:** `create:users`

---

### GET `/admin/api/users/<user_id>`
**Descripción:** Obtener detalle de un usuario

**Auth:** ✅ Required

**Permisos:** `users:view`

**Response:**
```json
{
  "success": true,
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "Administrador",
    "role": "admin",
    "is_active": true,
    "permissions": {
      "users": ["view", "create", "edit", "delete"],
      "products": ["view", "create", "edit", "delete"],
      ...
    }
  }
}
```

---

### PUT `/admin/api/users/<user_id>`
**Descripción:** Actualizar usuario

**Auth:** ✅ Required

**Permisos:** `users:edit`

**Request:**
```json
{
  "email": "nuevo@example.com",
  "full_name": "Nuevo Nombre",
  "role": "manager",
  "is_active": true,
  "password": "nueva_contraseña"  // opcional
}
```

**Restricciones:**
- No puedes cambiar tu propio rol
- Password opcional (mínimo 4 caracteres si se proporciona)

**Response:**
```json
{
  "success": true,
  "message": "Usuario actualizado"
}
```

**Activity Log:** `update:users`

---

### DELETE `/admin/api/users/<user_id>`
**Descripción:** Desactivar usuario (soft delete)

**Auth:** ✅ Required

**Permisos:** `users:delete`

**Restricciones:**
- No puedes eliminarte a ti mismo

**Response:**
```json
{
  "success": true,
  "message": "Usuario desactivado"
}
```

**Activity Log:** `delete:users`

---

### POST `/admin/api/users/<user_id>/activate`
**Descripción:** Reactivar usuario

**Auth:** ✅ Required

**Permisos:** `users:edit`

**Response:**
```json
{
  "success": true,
  "message": "Usuario activado"
}
```

**Activity Log:** `activate:users`

---

### GET `/admin/activity`
**Descripción:** Vista del monitor de actividades

**Auth:** ✅ Required

**Permisos:** `activity_log:view`

**Response:**
- HTML Template: `admin/activity_log.html`

---

### GET `/admin/api/activity`
**Descripción:** Obtener log de actividades (JSON)

**Auth:** ✅ Required

**Permisos:** `activity_log:view`

**Query Params:**
- `page`: Número de página (default: 1)
- `per_page`: Registros por página (default: 50)
- `user`: Filtrar por user_id
- `action`: Filtrar por acción (create, update, delete, etc.)
- `module`: Filtrar por módulo (products, sales, etc.)
- `date_from`: Fecha desde (YYYY-MM-DD)
- `date_to`: Fecha hasta (YYYY-MM-DD)

**Response:**
```json
{
  "success": true,
  "logs": [
    {
      "id": "507f1f77bcf86cd799439011",
      "user_name": "Admin",
      "user_role": "admin",
      "action": "create",
      "module": "products",
      "description": "Creó producto \"Pan Integral\"",
      "target_id": "507f1f77bcf86cd799439012",
      "target_type": "Product",
      "ip_address": "192.168.1.1",
      "created_at": "04/02/2026 10:30:45"
    }
  ],
  "total": 150,
  "pages": 3,
  "current_page": 1
}
```

---

### GET `/admin/api/activity/stats`
**Descripción:** Estadísticas de actividad (últimas 24h)

**Auth:** ✅ Required

**Permisos:** `activity_log:view`

**Response:**
```json
{
  "success": true,
  "total_24h": 45,
  "by_action": {
    "create": 15,
    "update": 20,
    "delete": 5,
    "login": 5
  },
  "by_module": {
    "products": 10,
    "sales": 25,
    "users": 5
  },
  "by_user": {
    "Admin": 30,
    "Manager": 15
  }
}
```

---

### GET `/admin/api/roles`
**Descripción:** Obtener roles y permisos del sistema

**Auth:** ✅ Required

**Permisos:** `users:view`

**Response:**
```json
{
  "success": true,
  "roles": ["admin", "manager", "warehouse", "sales"],
  "permissions": {
    "admin": {
      "users": ["view", "create", "edit", "delete"],
      "products": ["view", "create", "edit", "delete"],
      ...
    },
    ...
  }
}
```

---

### GET `/admin/api/my-permissions`
**Descripción:** Obtener permisos del usuario actual

**Auth:** ✅ Required

**Response:**
```json
{
  "success": true,
  "role": "admin",
  "permissions": {
    "users": ["view", "create", "edit", "delete"],
    "products": ["view", "create", "edit", "delete"],
    ...
  }
}
```

---

## API (REST Endpoints)

### GET `/api/products`
**Descripción:** Obtener lista de productos

**Auth:** ✅ Required

**Response:**
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "name": "Pan Integral",
    "sku": "PAN-INT-500G",
    "description": "Pan integral 500g",
    "category": "Panadería",
    "base_price": 2500.00,
    "critical_stock": 10,
    "stock": 50
  }
]
```

---

### GET `/api/products/<id>`
**Descripción:** Obtener detalle de un producto

**Auth:** ✅ Required

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "Pan Integral",
  "sku": "PAN-INT-500G",
  "description": "Pan integral 500g",
  "category": "Panadería",
  "base_price": 2500.00,
  "critical_stock": 10,
  "stock": 50,
  "bundle_components": [
    {
      "id": "507f1f77bcf86cd799439012",
      "component_id": "507f1f77bcf86cd799439013",
      "product_name": "Harina Integral",
      "quantity": 2
    }
  ]
}
```

---

### POST `/api/products`
**Descripción:** Crear nuevo producto

**Auth:** ✅ Required

**Permisos:** `products:create`

**Request:**
```json
{
  "name": "Arroz 5kg",
  "sku": "ARROZ-5KG",
  "description": "Arroz grado 1, 5 kilogramos",
  "category": "Abarrotes",
  "base_price": 5000,
  "critical_stock": 20,
  "initial_stock": 100,
  "initial_lot_code": "LOT-2026-001",
  "bundle_components": [
    {
      "component_id": "507f1f77bcf86cd799439013",
      "quantity": 2
    }
  ]
}
```

**Response:**
```json
{
  "message": "Producto creado",
  "id": "507f1f77bcf86cd799439011"
}
```

**Activity Log:** `create:products`

---

### PUT `/api/products/<id>`
**Descripción:** Actualizar producto

**Auth:** ✅ Required

**Permisos:** `products:edit`

**Request:**
```json
{
  "name": "Arroz Premium 5kg",
  "sku": "ARROZ-5KG",
  "description": "Arroz premium grado 1",
  "category": "Abarrotes",
  "base_price": 5500,
  "critical_stock": 15,
  "stock_adjustment_type": "add",
  "stock_adjustment_quantity": 50,
  "stock_adjustment_reason": "Compra adicional",
  "stock_adjustment_lot_code": "LOT-2026-002",
  "bundle_components": [...]
}
```

**Stock Adjustment:**
- `stock_adjustment_type`: `"add"` o `"subtract"`
- `add`: Crea nuevo Lot con stock adicional
- `subtract`: Deduce de lotes existentes (FIFO) y crea registro Wastage

**Response:**
```json
{
  "message": "Producto actualizado"
}
```

**Activity Log:** `update:products`

---

### DELETE `/api/products/<id>`
**Descripción:** Eliminar producto

**Auth:** ✅ Required

**Permisos:** `products:delete`

**Response:**
```json
{
  "message": "Producto eliminado correctamente"
}
```

**Nota:** También elimina lotes y relaciones bundle asociadas.

**Activity Log:** `delete:products`

---

### GET `/api/sales`
**Descripción:** Obtener lista de ventas

**Auth:** ✅ Required

**Query Params:**
- `page`: Número de página (default: 1)
- `per_page`: Registros por página (default: 20)
- `date`: Filtro fecha (YYYY-MM-DD o YYYY-MM)

**Response:**
```json
{
  "sales": [
    {
      "id": "507f1f77bcf86cd799439011",
      "customer": "Juan Pérez",
      "address": "Av. Principal 123",
      "status": "pending",
      "sale_type": "con_despacho",
      "sales_channel": "manual",
      "delivery_status": "pendiente",
      "payment_status": "pendiente",
      "items": [
        {
          "product": "Pan Integral",
          "quantity": 5,
          "unit_price": 2500,
          "subtotal": 12500
        }
      ],
      "total": 12500,
      "payment_method": "Efectivo",
      "date": "2026-02-04 10:30"
    }
  ],
  "total": 150,
  "pages": 8,
  "current_page": 1
}
```

---

### GET `/api/sales/<id>`
**Descripción:** Obtener detalle de una venta

**Auth:** ✅ Required

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "customer": "Juan Pérez",
  "address": "Av. Principal 123",
  "phone": "+56912345678",
  "sale_type": "con_despacho",
  "sales_channel": "manual",
  "delivery_status": "pendiente",
  "delivery_observations": "",
  "date_delivered": null,
  "payment_status": "pendiente",
  "total": 12500,
  "total_paid": 0,
  "balance_pending": 12500,
  "payments": [],
  "items": [
    {
      "product": "Pan Integral",
      "quantity": 5,
      "unit_price": 2500,
      "subtotal": 12500
    }
  ],
  "status": "pending",
  "payment_method": "Efectivo",
  "date_created": "2026-02-04 10:30"
}
```

---

### POST `/api/sales`
**Descripción:** Crear nueva venta

**Auth:** ✅ Required

**Permisos:** `sales:create`

**Request:**
```json
{
  "customer": "Juan Pérez",
  "address": "Av. Principal 123",
  "phone": "+56912345678",
  "sale_type": "con_despacho",
  "sales_channel": "manual",
  "delivery_status": "pendiente",
  "delivery_observations": "",
  "payment_method": "Efectivo",
  "items": [
    {
      "product_id": "507f1f77bcf86cd799439012",
      "quantity": 5
    }
  ],
  "initial_payment": {
    "amount": 5000,
    "payment_via": "efectivo",
    "payment_reference": "",
    "notes": "Pago inicial"
  },
  "auto_complete_payment": false
}
```

**Validaciones:**
- Stock suficiente para cada producto
- Si es bundle, stock de componentes
- Pago inicial no mayor al total
- `sale_type`: `"con_despacho"` o `"en_local"`
- Si `sale_type == "en_local"` y `auto_complete_payment == true`: crea pago automático por el total

**Lógica:**
- Deduce stock de lotes (FIFO)
- Si es bundle, también deduce componentes
- Si `sale_type == "en_local"`: `delivery_status = "entregado"`
- Crea registro Payment si hay pago inicial

**Response:**
```json
{
  "message": "Venta creada",
  "id": "507f1f77bcf86cd799439011"
}
```

**Activity Log:** `create:sales`

---

### PUT `/api/sales/<id>`
**Descripción:** Actualizar estado de venta

**Auth:** ✅ Required

**Permisos:** `sales:edit`

**Request:**
```json
{
  "delivery_status": "entregado",
  "delivery_observations": "Entregado sin novedad",
  "status": "delivered",
  "payment_confirmed": true
}
```

**Validaciones:**
- Ventas en local no pueden cambiar `delivery_status` (siempre `"entregado"`)
- `delivery_status`: `pendiente`, `en_preparacion`, `en_transito`, `entregado`, `con_observaciones`, `cancelado`

**Response:**
```json
{
  "success": true,
  "message": "Venta actualizada"
}
```

**Activity Log:** `update:sales` o `cancel:sales`

---

### GET `/api/sales/<id>/payments`
**Descripción:** Obtener historial de pagos de una venta

**Auth:** ✅ Required

**Response:**
```json
{
  "success": true,
  "payments": [
    {
      "id": "507f1f77bcf86cd799439013",
      "amount": 5000,
      "payment_via": "efectivo",
      "payment_reference": "",
      "notes": "Pago inicial",
      "date_created": "2026-02-04 10:30",
      "created_by": "Admin"
    }
  ],
  "total_paid": 5000,
  "balance_pending": 7500
}
```

---

### POST `/api/sales/<id>/payments`
**Descripción:** Registrar pago/abono para una venta

**Auth:** ✅ Required

**Permisos:** `sales:edit`

**Request:**
```json
{
  "amount": 5000,
  "payment_via": "transferencia",
  "payment_reference": "TRF-12345",
  "notes": "Segundo abono"
}
```

**Validaciones:**
- `amount > 0`
- Total pagos no puede exceder el total de la venta
- `payment_via`: `efectivo`, `transferencia`, `tarjeta`, `otro`

**Response:**
```json
{
  "success": true,
  "message": "Pago registrado",
  "payment_id": "507f1f77bcf86cd799439014",
  "balance_pending": 2500,
  "payment_status": "parcial"
}
```

**Activity Log:** `create:sales` (pago)

---

### GET `/api/dashboard`
**Descripción:** Estadísticas del dashboard con gráfico

**Auth:** ✅ Required

**Query Params:**
- `range`: Rango de tiempo
  - `last_7` (default): últimos 7 días
  - `last_30`: últimos 30 días
  - `this_month`: mes actual
  - `last_month`: mes pasado
  - `year`: año actual
  - `last_6_months`: últimos 6 meses
  - `all_time`: todo el historial
  - `specific_month`: mes específico (requiere `month=YYYY-MM`)

**Response:**
```json
{
  "total_sales": 150,
  "total_products": 45,
  "total_revenue": 2500000,
  "recent_sales": [
    {
      "id": "...",
      "customer": "Juan Pérez",
      "status": "pending"
    }
  ],
  "chart_data": {
    "labels": ["01/02", "02/02", "03/02", "04/02", "05/02", "06/02", "07/02"],
    "values": [150000, 200000, 180000, 220000, 190000, 210000, 250000],
    "keys": ["2026-02-01", "2026-02-02", ...]
  }
}
```

---

### POST `/api/sales/webhook`
**Descripción:** Webhook para crear ventas desde integraciones externas (ManyChat, Google Sheets, etc.)

**Auth:** ❌ No required (Token en header)

**Headers:**
- `X-Webhook-Token: <token>` O `Authorization: Bearer <token>`

**Rate Limit:** 10/min, 100/hora por IP

**Request:**
```json
{
  "customer": "Juan Pérez",
  "phone": "+56912345678",
  "address": "Av. Principal 123",
  "items": [
    {
      "sku": "ARROZ-5KG",
      "quantity": 2
    },
    {
      "name": "Aceite Maravilla 1L",
      "quantity": 1
    }
  ],
  "notes": "Entregar después de las 14:00"
}
```

**Validaciones:**
- Token válido (env: `SIPUD_WEBHOOK_TOKEN`)
- `customer` requerido
- Al menos 1 item
- Producto existe (busca por SKU o nombre)
- Stock disponible

**Response (Éxito):**
```json
{
  "success": true,
  "message": "Venta creada exitosamente",
  "sale_id": "507f1f77bcf86cd799439011",
  "customer": "Juan Pérez",
  "total": 15000,
  "items_processed": 2,
  "items": [
    {
      "product": "Arroz 5kg",
      "sku": "ARROZ-5KG",
      "quantity": 2,
      "unit_price": 5000
    },
    {
      "product": "Aceite Maravilla 1L",
      "sku": "ACEITE-1L",
      "quantity": 1,
      "unit_price": 5000
    }
  ],
  "warnings": []
}
```

**Response (Error Stock):**
```json
{
  "error": "No se pudo procesar ningún item",
  "details": [
    "Stock insuficiente para Arroz 5kg: disponible 1, solicitado 2",
    "Producto no encontrado: Aceite Oliva 1L"
  ]
}
```

**Activity Log:** `create:sales` (source: webhook, channel: whatsapp)

---

### GET `/api/sales/webhook/test`
**Descripción:** Test endpoint para verificar webhook (sin auth)

**Auth:** ❌ No required

**Rate Limit:** 30/min

**Response:**
```json
{
  "status": "ok",
  "message": "Webhook endpoint disponible",
  "usage": "POST /api/sales/webhook con header X-Webhook-Token",
  "rate_limits": "10/min, 100/hour"
}
```

---

## Warehouse (Bodega)

### GET `/warehouse/`
**Descripción:** Dashboard de operaciones de almacén

**Auth:** ✅ Required

**Response:**
- HTML Template: `warehouse/dashboard.html`
- Variables:
  - `expiring_soon`: Productos próximos a vencer (30 días)
  - `low_stock`: Productos con stock crítico
  - `pending_orders`: Pedidos pendientes de recepción

---

### GET `/warehouse/orders`
**Descripción:** Gestión de pedidos a proveedores

**Auth:** ✅ Required

**Response:**
- HTML Template: `warehouse/orders.html`

---

### GET `/warehouse/api/orders`
**Descripción:** Obtener lista de pedidos (JSON)

**Auth:** ✅ Required

**Permisos:** `orders:view`

**Response:**
```json
{
  "success": true,
  "orders": [
    {
      "id": "507f1f77bcf86cd799439011",
      "supplier": "Proveedor ABC",
      "invoice_number": "F-12345",
      "status": "pending",
      "total": 500000,
      "notes": "Pedido urgente",
      "date_received": "",
      "created_at": "04/02/2026 10:00"
    }
  ]
}
```

---

### POST `/warehouse/api/orders`
**Descripción:** Crear pedido a proveedor

**Auth:** ✅ Required

**Permisos:** `orders:create`

**Request:**
```json
{
  "supplier": "Proveedor ABC",
  "invoice_number": "F-12345",
  "total": 500000,
  "notes": "Pedido mensual"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Pedido creado exitosamente",
  "order_id": "507f1f77bcf86cd799439011"
}
```

**Activity Log:** `create:orders`

---

### PUT `/warehouse/api/orders/<order_id>`
**Descripción:** Actualizar pedido

**Auth:** ✅ Required

**Permisos:** `orders:edit`

**Request:**
```json
{
  "supplier": "Proveedor ABC",
  "invoice_number": "F-12345",
  "total": 550000,
  "status": "received",
  "notes": "Actualizado"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Pedido actualizado exitosamente"
}
```

**Activity Log:** `update:orders`

---

### DELETE `/warehouse/api/orders/<order_id>`
**Descripción:** Eliminar pedido

**Auth:** ✅ Required

**Permisos:** `orders:delete`

**Restricciones:**
- No se puede eliminar si tiene lotes asociados

**Response:**
```json
{
  "success": true,
  "message": "Pedido eliminado exitosamente"
}
```

**Activity Log:** `delete:orders`

---

### POST `/warehouse/api/receiving/<order_id>`
**Descripción:** Confirmar recepción de pedido

**Auth:** ✅ Required

**Permisos:** `orders:receive`

**Request:**
```json
{
  "products": [
    {
      "product_id": "507f1f77bcf86cd799439012",
      "quantity": 100,
      "lot_code": "LOT-2026-001",
      "expiry_date": "2027-12-31"
    },
    {
      "product_id": "507f1f77bcf86cd799439013",
      "quantity": 50,
      "lot_code": "LOT-2026-002",
      "expiry_date": "2027-06-30"
    }
  ]
}
```

**Validaciones:**
- Pedido existe y está `pending`
- Al menos 1 producto
- Cantidad > 0
- Producto existe
- Fecha vencimiento no en el pasado

**Lógica:**
- Crea lotes (Lot) para cada producto
- Actualiza estado pedido a `received`
- Genera `lot_code` automático si no se proporciona

**Response:**
```json
{
  "success": true,
  "message": "Recepción confirmada exitosamente. 2 producto(s) agregado(s) al inventario."
}
```

**Activity Log:** `receive:orders`

---

### POST `/warehouse/api/wastage`
**Descripción:** Registrar merma de producto

**Auth:** ✅ Required

**Permisos:** `wastage:create`

**Request:**
```json
{
  "product_id": "507f1f77bcf86cd799439012",
  "quantity": 10,
  "reason": "vencido",
  "notes": "Lote vencido, descartar"
}
```

**Validaciones:**
- `quantity > 0`
- Stock suficiente
- `reason`: `vencido`, `dañado`, `perdido`, `robo`, `otro`

**Lógica:**
- Deduce stock de lotes (FIFO)
- Crea registro Wastage

**Response:**
```json
{
  "success": true,
  "message": "Merma registrada exitosamente",
  "wastage_id": "507f1f77bcf86cd799439014"
}
```

**Activity Log:** `create:wastage`

---

### GET `/warehouse/api/wastage/history`
**Descripción:** Obtener historial de mermas

**Auth:** ✅ Required

**Permisos:** `wastage:view`

**Response:**
```json
{
  "success": true,
  "wastages": [
    {
      "id": "507f1f77bcf86cd799439014",
      "product_id": "507f1f77bcf86cd799439012",
      "product_name": "Pan Integral",
      "quantity": 10,
      "reason": "vencido",
      "notes": "Lote vencido",
      "date": "04/02/2026 10:30"
    }
  ]
}
```

---

### DELETE `/warehouse/api/wastage/<wastage_id>`
**Descripción:** Eliminar registro de merma (no revierte stock)

**Auth:** ✅ Required

**Permisos:** `wastage:delete`

**Response:**
```json
{
  "success": true,
  "message": "Registro de merma eliminado"
}
```

**Activity Log:** `delete:wastage`

---

### POST `/warehouse/api/assembly`
**Descripción:** Ensamblar kits/bundles (Kitting)

**Auth:** ✅ Required

**Permisos:** `orders:create`

**Request:**
```json
{
  "bundle_id": "507f1f77bcf86cd799439015",
  "quantity": 10
}
```

**Validaciones:**
- `quantity > 0`
- Producto es un bundle (tiene componentes)
- Stock suficiente de todos los componentes

**Lógica:**
- Deduce stock de componentes (FIFO)
- Crea lote del bundle con la cantidad ensamblada
- Crea/usa InboundOrder "Interno: Armado"

**Response:**
```json
{
  "success": true,
  "message": "Se armaron 10 unidades de \"Caja Regalo\" exitosamente"
}
```

**Activity Log:** `create:orders` (armado)

---

### GET `/warehouse/api/alerts`
**Descripción:** Obtener alertas de vencimientos y stock crítico

**Auth:** ✅ Required

**Response:**
```json
{
  "success": true,
  "alerts": [
    {
      "type": "expiry",
      "severity": "danger",
      "product_id": "507f1f77bcf86cd799439012",
      "product_name": "Pan Integral",
      "message": "El producto 'Pan Integral' vence en 3 días",
      "days_left": 3,
      "expiry_date": "07/02/2026",
      "stock": 15
    },
    {
      "type": "low_stock",
      "severity": "warning",
      "product_id": "507f1f77bcf86cd799439013",
      "product_name": "Arroz 5kg",
      "message": "Stock bajo: 'Arroz 5kg' (5 unidades)",
      "current_stock": 5,
      "critical_stock": 20
    }
  ],
  "count": 2
}
```

---

## Customers (CRM/Shopify)

### GET `/customers/`
**Descripción:** Vista de clientes

**Auth:** ✅ Required

**Permisos:** `customers:view`

**Response:**
- HTML Template: `customers.html`

---

### GET `/customers/api/customers`
**Descripción:** Obtener lista de clientes

**Auth:** ✅ Required

**Permisos:** `customers:view`

**Query Params:**
- `q`: Búsqueda por nombre/email/teléfono
- `page`: Número de página (default: 1)
- `per_page`: Registros por página (default: 50)

**Response:**
```json
{
  "customers": [
    {
      "id": "507f1f77bcf86cd799439016",
      "name": "Juan Pérez",
      "email": "juan@example.com",
      "phone": "+56912345678",
      "city": "Santiago",
      "province": "Región Metropolitana",
      "country": "Chile",
      "total_orders": 5,
      "total_spent": 125000,
      "last_order_date": "2026-02-04",
      "created_at": "2026-01-01"
    }
  ],
  "total": 150,
  "page": 1,
  "per_page": 50,
  "pages": 3
}
```

---

### GET `/customers/api/customers/<customer_id>`
**Descripción:** Obtener detalle de cliente con pedidos recientes

**Auth:** ✅ Required

**Permisos:** `customers:view`

**Response:**
```json
{
  "customer": {
    "id": "507f1f77bcf86cd799439016",
    "name": "Juan Pérez",
    "email": "juan@example.com",
    "phone": "+56912345678",
    "city": "Santiago",
    "province": "Región Metropolitana",
    "country": "Chile",
    "total_orders": 5,
    "total_spent": 125000,
    "first_order_date": "2026-01-15",
    "last_order_date": "2026-02-04",
    "tags": "vip,mayorista"
  },
  "orders": [
    {
      "id": "507f1f77bcf86cd799439017",
      "order_number": 1001,
      "created_at": "2026-02-04 10:30",
      "total_price": 25000,
      "financial_status": "paid",
      "fulfillment_status": "fulfilled",
      "line_items_count": 3,
      "line_items": [
        {
          "title": "Pan Integral",
          "quantity": 5,
          "price": 2500
        }
      ]
    }
  ]
}
```

---

### POST `/customers/api/customers`
**Descripción:** Crear cliente manual

**Auth:** ✅ Required

**Permisos:** `customers:create`

**Request:**
```json
{
  "name": "María González",
  "email": "maria@example.com",
  "phone": "+56987654321",
  "address_city": "Santiago",
  "address_province": "Región Metropolitana",
  "address_country": "Chile"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Cliente creado exitosamente",
  "customer": {
    "id": "507f1f77bcf86cd799439018",
    "name": "María González",
    "email": "maria@example.com",
    "source": "manual"
  }
}
```

---

### POST `/customers/api/customers/import`
**Descripción:** Importar clientes desde archivo Excel

**Auth:** ✅ Required

**Permisos:** `customers:sync`

**Request:** Multipart form-data
- `file`: Archivo Excel (.xlsx)

**Excel Format:**
- Columnas: Nombre, Email, Teléfono, Ciudad, Provincia, País
- Nombre es requerido

**Response:**
```json
{
  "success": true,
  "created": 45,
  "total_rows": 50,
  "errors": [
    "Fila 3: Nombre es requerido",
    "Fila 10: Email duplicado"
  ]
}
```

---

### POST `/customers/api/customers/sync`
**Descripción:** Sincronizar clientes y órdenes desde Shopify

**Auth:** ✅ Required

**Permisos:** `customers:sync`

**Lógica:**
- Sincroniza clientes desde Shopify API
- Sincroniza órdenes desde Shopify API
- Sincroniza productos (SKU, precio, stock)
- Crea ventas (Sale) desde órdenes Shopify
- Actualiza estadísticas de clientes

**Response:**
```json
{
  "customers_synced": 50,
  "orders_synced": 120,
  "sales_created": 30,
  "products_created": 15,
  "products_updated": 25,
  "errors": [
    "Sin permiso read_customers - extrayendo clientes desde órdenes"
  ]
}
```

**Activity Log:** `create:customers` (sync)

---

### GET `/customers/api/customers/sync/preview`
**Descripción:** Preview de cambios antes de sincronizar con Shopify

**Auth:** ✅ Required

**Permisos:** `customers:sync`

**Response:**
```json
{
  "products": {
    "new": [
      {
        "sku": "NEW-PROD",
        "name": "Producto Nuevo",
        "price": 5000,
        "stock": 10
      }
    ],
    "update": [
      {
        "sku": "ARROZ-5KG",
        "name": "Arroz 5kg",
        "price": 5500,
        "stock": 50,
        "changes": ["precio: $5000 → $5500", "stock: 45 → 50"]
      }
    ],
    "unchanged": 30
  },
  "customers": {
    "new": [...],
    "update": [...],
    "unchanged": 45
  },
  "orders": {
    "new": [...],
    "unchanged": 100
  },
  "summary": {
    "products_new": 5,
    "products_update": 10,
    "customers_new": 8,
    "orders_new": 20,
    "has_changes": true
  }
}
```

---

### GET `/customers/api/customers/stats`
**Descripción:** Estadísticas de clientes

**Auth:** ✅ Required

**Permisos:** `customers:view`

**Response:**
```json
{
  "total_customers": 150,
  "total_revenue": 2500000,
  "avg_ticket": 16666.67,
  "new_this_month": 12
}
```

---

### GET `/customers/api/customers/export`
**Descripción:** Exportar clientes a Excel

**Auth:** ✅ Required

**Permisos:** `customers:export`

**Response:**
- Archivo Excel (.xlsx)
- Headers: Nombre, Email, Teléfono, Ciudad, Provincia, País, Total Pedidos, Total Gastado, Primer Pedido, Último Pedido

---

## Delivery (Hojas de Reparto)

### GET `/delivery/`
**Descripción:** Lista de hojas de reparto

**Auth:** ✅ Required

**Response:**
- HTML Template: `delivery/index.html`
- Variables:
  - `sheets`: Hojas de reparto
  - `drivers`: Usuarios disponibles como repartidores
  - `pending_sales`: Ventas pendientes de asignar

---

### GET `/delivery/sheet/<sheet_id>`
**Descripción:** Ver detalle de hoja de reparto

**Auth:** ✅ Required

**Response:**
- HTML Template: `delivery/sheet.html`
- Variables:
  - `sheet`: Hoja de reparto
  - `sales_data`: Ventas con links a mapas (Google Maps, Waze, Apple Maps)

---

### POST `/delivery/api/sheets`
**Descripción:** Crear hoja de reparto

**Auth:** ✅ Required

**Request:**
```json
{
  "name": "Reparto Zona Norte",
  "date": "2026-02-05",
  "driver_name": "Pedro López",
  "driver_phone": "+56912345678",
  "driver_user_id": "507f1f77bcf86cd799439019",
  "sale_ids": [
    "507f1f77bcf86cd799439020",
    "507f1f77bcf86cd799439021"
  ],
  "notes": "Ruta optimizada"
}
```

**Lógica:**
- Crea hoja de reparto
- Asigna ventas
- Actualiza `delivery_status` de ventas a `en_preparacion`

**Response:**
```json
{
  "success": true,
  "sheet_id": "507f1f77bcf86cd799439022",
  "message": "Hoja de reparto creada con 2 ventas"
}
```

---

### PUT `/delivery/api/sheets/<sheet_id>`
**Descripción:** Actualizar hoja de reparto

**Auth:** ✅ Required

**Request:**
```json
{
  "status": "en_ruta",
  "driver_name": "Pedro López",
  "driver_phone": "+56912345678",
  "notes": "Actualizado"
}
```

**Lógica:**
- Si `status == "en_ruta"`: actualiza ventas a `en_transito`

**Response:**
```json
{
  "success": true,
  "message": "Hoja actualizada"
}
```

---

### DELETE `/delivery/api/sheets/<sheet_id>`
**Descripción:** Eliminar hoja de reparto

**Auth:** ✅ Required

**Lógica:**
- Revierte estado de ventas a `pendiente` si estaban `en_preparacion`

**Response:**
```json
{
  "success": true,
  "message": "Hoja eliminada"
}
```

---

### PUT `/delivery/api/sheets/<sheet_id>/update-sale/<sale_id>`
**Descripción:** Actualizar estado de una venta dentro de la hoja

**Auth:** ✅ Required

**Request:**
```json
{
  "address": "Av. Principal 123, Depto 5B",
  "phone": "+56912345678",
  "delivery_status": "entregado",
  "delivery_observations": "Entregado sin novedad"
}
```

**Lógica:**
- Actualiza datos de la venta
- Si todas las ventas están completadas, marca hoja como `completado`

**Response:**
```json
{
  "success": true,
  "message": "Venta actualizada"
}
```

---

## Reports (Exportación)

Todos los endpoints de reportes requieren autenticación y permisos `reports:export`.

### GET `/reports/sales/excel`
**Descripción:** Exportar ventas a Excel

**Auth:** ✅ Required

**Permisos:** `reports:export`

**Response:**
- Archivo Excel (.xlsx)
- Headers: ID, Fecha, Cliente, Estado, Items, Total, Método Pago
- Filename: `ventas_YYYYMMDD_HHMM.xlsx`

---

### GET `/reports/warehouse/wastage/excel`
**Descripción:** Exportar mermas a Excel

**Auth:** ✅ Required

**Permisos:** `reports:export`

**Response:**
- Archivo Excel (.xlsx)
- Headers: ID, Fecha, Producto, SKU, Cantidad, Razón, Notas
- Filename: `mermas_YYYYMMDD_HHMM.xlsx`

---

### GET `/reports/warehouse/inventory/excel`
**Descripción:** Exportar inventario a Excel

**Auth:** ✅ Required

**Permisos:** `reports:export`

**Response:**
- Archivo Excel (.xlsx)
- Headers: SKU, Nombre, Categoría, Precio Base, Stock Total, Stock Crítico, Estado, Vencimiento
- Filename: `inventario_YYYYMMDD_HHMM.xlsx`
- Filas con stock crítico destacadas en rojo

---

### GET `/reports/warehouse/orders/excel`
**Descripción:** Exportar pedidos a proveedores a Excel

**Auth:** ✅ Required

**Permisos:** `reports:export`

**Response:**
- Archivo Excel (.xlsx)
- Headers: ID, Proveedor, N° Factura, Estado, Total, Fecha Creación, Fecha Recepción, Notas
- Filename: `pedidos_YYYYMMDD_HHMM.xlsx`

---

## Reconciliation (Cuadratura Bancaria)

### GET `/reconciliation/`
**Descripción:** Vista de cuadratura bancaria

**Auth:** ✅ Required

**Permisos:** Solo `admin` y `manager`

**Response:**
- HTML Template: `reconciliation.html`

---

### GET `/reconciliation/api/transactions`
**Descripción:** Obtener transacciones bancarias

**Auth:** ✅ Required

**Permisos:** Solo `admin` y `manager`

**Query Params:**
- `status`: Filtro por estado (`pending`, `matched`, `ignored`)
- `date_from`: Fecha desde (YYYY-MM-DD)
- `date_to`: Fecha hasta (YYYY-MM-DD)
- `page`: Número de página (default: 1)
- `per_page`: Registros por página (default: 50)

**Response:**
```json
{
  "transactions": [
    {
      "id": "507f1f77bcf86cd799439023",
      "date": "2026-02-04",
      "amount": 25000,
      "description": "Transferencia Juan Pérez",
      "reference": "TRF-12345",
      "transaction_type": "credit",
      "status": "pending",
      "matched_sale_id": null,
      "matched_sale_customer": null,
      "match_type": null
    }
  ],
  "total": 150,
  "page": 1,
  "per_page": 50,
  "pages": 3
}
```

---

### POST `/reconciliation/api/transactions/upload`
**Descripción:** Importar transacciones desde cartola Excel

**Auth:** ✅ Required

**Permisos:** Solo `admin` y `manager`

**Request:** Multipart form-data
- `file`: Archivo Excel (.xlsx)

**Excel Format:**
- Detección automática de columnas (Fecha, Monto, Descripción, Referencia)
- Soporta formatos de fecha comunes
- Monto puede ser positivo (crédito) o negativo (débito)

**Response:**
```json
{
  "success": true,
  "created": 45,
  "errors": [
    "Fila 3: formato de fecha no reconocido",
    "Fila 10: monto inválido"
  ],
  "total_errors": 2
}
```

**Activity Log:** `create:reconciliation`

---

### POST `/reconciliation/api/transactions/<tx_id>/match`
**Descripción:** Conciliar transacción con venta manualmente

**Auth:** ✅ Required

**Permisos:** Solo `admin` y `manager`

**Request:**
```json
{
  "sale_id": "507f1f77bcf86cd799439020"
}
```

**Lógica:**
- Marca transacción como `matched`
- Actualiza venta a `payment_status = "pagado"`
- Registra `match_type = "manual"`

**Response:**
```json
{
  "success": true,
  "message": "Transacción conciliada exitosamente"
}
```

**Activity Log:** `update:reconciliation`

---

### POST `/reconciliation/api/transactions/<tx_id>/unmatch`
**Descripción:** Remover conciliación

**Auth:** ✅ Required

**Permisos:** Solo `admin` y `manager`

**Response:**
```json
{
  "success": true,
  "message": "Conciliación removida"
}
```

---

### POST `/reconciliation/api/transactions/<tx_id>/ignore`
**Descripción:** Marcar transacción como ignorada

**Auth:** ✅ Required

**Permisos:** Solo `admin` y `manager`

**Response:**
```json
{
  "success": true,
  "message": "Transacción ignorada"
}
```

---

### GET `/reconciliation/api/transactions/<tx_id>/suggestions`
**Descripción:** Obtener sugerencias de conciliación automática

**Auth:** ✅ Required

**Permisos:** Solo `admin` y `manager`

**Lógica:**
- Busca ventas no conciliadas con:
  - Monto similar (±1%)
  - Fecha cercana (±3 días)
- Calcula confianza (0-100%)

**Response:**
```json
{
  "transaction_id": "507f1f77bcf86cd799439023",
  "transaction_amount": 25000,
  "suggestions": [
    {
      "sale_id": "507f1f77bcf86cd799439020",
      "customer": "Juan Pérez",
      "total": 25000,
      "date": "2026-02-04",
      "confidence": 95,
      "amount_diff": 0,
      "date_diff": 0
    },
    {
      "sale_id": "507f1f77bcf86cd799439021",
      "customer": "María González",
      "total": 24500,
      "date": "2026-02-03",
      "confidence": 80,
      "amount_diff": 2,
      "date_diff": 1
    }
  ]
}
```

---

### POST `/reconciliation/api/transactions/auto-match`
**Descripción:** Conciliar automáticamente todas las transacciones pendientes

**Auth:** ✅ Required

**Permisos:** Solo `admin` y `manager`

**Lógica:**
- Procesa todas las transacciones `pending` y tipo `credit`
- Busca mejor match con confianza ≥80%
- Concilia automáticamente (`match_type = "auto"`)

**Response:**
```json
{
  "success": true,
  "matched": 15,
  "errors": [
    "TX 507f1f77bcf86cd799439024: No se encontró match"
  ]
}
```

**Activity Log:** `update:reconciliation` (auto-match)

---

### GET `/reconciliation/api/stats`
**Descripción:** Estadísticas de conciliación

**Auth:** ✅ Required

**Permisos:** Solo `admin` y `manager`

**Response:**
```json
{
  "total": 150,
  "pending": 30,
  "matched": 110,
  "ignored": 10,
  "pending_amount": 750000,
  "matched_amount": 2750000,
  "match_rate": 73.3
}
```

---

### GET `/reconciliation/api/sales/unmatched`
**Descripción:** Obtener ventas no conciliadas

**Auth:** ✅ Required

**Permisos:** Solo `admin` y `manager`

**Response:**
```json
{
  "sales": [
    {
      "id": "507f1f77bcf86cd799439020",
      "customer": "Juan Pérez",
      "total": 25000,
      "date": "2026-02-04",
      "payment_status": "pendiente"
    }
  ]
}
```

---

## Resumen de Endpoints

| Módulo | Endpoints | Auth | Permisos RBAC |
|--------|-----------|------|---------------|
| **Main** | 4 | ✅ | Ninguno |
| **Auth** | 7 | ❌/✅ | Ninguno |
| **Admin** | 12 | ✅ | users, activity_log |
| **API** | 17 | ✅ | products, sales |
| **Warehouse** | 13 | ✅ | orders, wastage |
| **Customers** | 10 | ✅ | customers |
| **Delivery** | 6 | ✅ | Ninguno |
| **Reports** | 4 | ✅ | reports |
| **Reconciliation** | 10 | ✅ | admin/manager only |

**Total:** 83 endpoints

---

## Notas Finales

### Rate Limiting

- **Default:** 200/día, 50/hora
- **Webhook:** 10/min, 100/hora
- **Test Webhook:** 30/min
- **Storage:** Memory (usar Redis en producción para multi-worker)

### Activity Log

Casi todas las operaciones CUD (Create, Update, Delete) registran actividad en `ActivityLog` para auditoría completa.

### Multi-Tenant

Todos los endpoints filtran automáticamente por `g.current_tenant` en el middleware `@app.before_request`.

### Webhooks

El endpoint `/api/sales/webhook` permite integrar con ManyChat, Zapier, Google Sheets, etc. usando token de autenticación en headers.

### Shopify Sync

La sincronización con Shopify (`/customers/api/customers/sync`) es completa:
- Clientes
- Órdenes
- Productos (SKU, precio, stock)
- Ventas (creadas desde órdenes)
