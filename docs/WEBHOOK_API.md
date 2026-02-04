# SIPUD Webhook API

API para crear ventas desde integraciones externas (ManyChat, Google Sheets, n8n, etc.)

## Autenticación

Todas las requests deben incluir el token en uno de estos headers:

```
X-Webhook-Token: <token>
```

o

```
Authorization: Bearer <token>
```

El token se configura en `.env` como `SIPUD_WEBHOOK_TOKEN`.

## Endpoints

### Test de conectividad

```
GET /api/sales/webhook/test
```

No requiere autenticación. Útil para verificar que el endpoint está accesible.

**Response:**
```json
{
  "status": "ok",
  "message": "Webhook endpoint disponible",
  "usage": "POST /api/sales/webhook con header X-Webhook-Token"
}
```

---

### Crear venta

```
POST /api/sales/webhook
```

Crea una nueva venta con los items especificados. Descuenta stock automáticamente (FIFO).

**Headers:**
- `Content-Type: application/json`
- `X-Webhook-Token: <token>`

**Body:**
```json
{
  "customer": "Juan Pérez",
  "phone": "+56912345678",
  "address": "Av. Principal 123, Puerto Montt",
  "items": [
    {"sku": "ARROZ-5KG", "quantity": 2},
    {"name": "Aceite Maravilla 1L", "quantity": 1}
  ],
  "notes": "Entregar después de las 14:00"
}
```

**Campos:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| customer | string | ✅ | Nombre del cliente |
| phone | string | ❌ | Teléfono de contacto |
| address | string | ❌ | Dirección de entrega |
| items | array | ✅ | Lista de productos |
| items[].sku | string | ❌* | SKU del producto |
| items[].name | string | ❌* | Nombre del producto (búsqueda parcial) |
| items[].quantity | int | ❌ | Cantidad (default: 1) |
| notes | string | ❌ | Notas adicionales |

*Al menos uno de `sku` o `name` es requerido por item.

**Response exitosa (201):**
```json
{
  "success": true,
  "message": "Venta creada exitosamente",
  "sale_id": "65abc123def456...",
  "customer": "Juan Pérez",
  "total": 25990,
  "items_processed": 2,
  "items": [
    {
      "product": "Arroz 5kg",
      "sku": "ARROZ-5KG",
      "quantity": 2,
      "unit_price": 8990
    },
    {
      "product": "Aceite Maravilla 1L",
      "sku": "ACE-MAR-1L",
      "quantity": 1,
      "unit_price": 8010
    }
  ]
}
```

**Response con warnings (201):**

Si algunos items fallan pero otros se procesan:

```json
{
  "success": true,
  "message": "Venta creada exitosamente",
  "sale_id": "65abc123def456...",
  "items_processed": 1,
  "warnings": [
    "Producto no encontrado: PRODUCTO-INEXISTENTE"
  ],
  "items": [...]
}
```

---

## Códigos de error

| Código | Descripción |
|--------|-------------|
| 400 | Datos inválidos (falta customer, items vacíos, stock insuficiente) |
| 401 | Token inválido o no proporcionado |
| 404 | Producto no encontrado (si todos los items fallan) |
| 429 | Rate limit excedido (ver sección Rate Limiting) |
| 500 | Error interno del servidor |

**Ejemplo error 400:**
```json
{
  "error": "Stock insuficiente para Arroz 5kg: disponible 3, solicitado 10"
}
```

**Ejemplo error 401:**
```json
{
  "error": "Token inválido o no proporcionado"
}
```

---

## Ejemplos de uso

### cURL

```bash
curl -X POST https://tu-dominio.com/api/sales/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Token: tu-token-secreto" \
  -d '{
    "customer": "María González",
    "phone": "+56987654321",
    "address": "Los Aromos 456",
    "items": [
      {"sku": "ARROZ-5KG", "quantity": 1}
    ]
  }'
```

### ManyChat (Custom Action)

1. En ManyChat, crear un bloque "External Request"
2. Configurar:
   - Method: POST
   - URL: `https://tu-dominio.com/api/sales/webhook`
   - Headers: `X-Webhook-Token: tu-token`
   - Body: JSON con datos del cliente y productos

### Google Sheets (Apps Script)

```javascript
function crearVenta(customer, phone, address, items) {
  const url = 'https://tu-dominio.com/api/sales/webhook';
  const options = {
    method: 'post',
    contentType: 'application/json',
    headers: {
      'X-Webhook-Token': 'tu-token-secreto'
    },
    payload: JSON.stringify({
      customer: customer,
      phone: phone,
      address: address,
      items: items
    })
  };
  
  const response = UrlFetchApp.fetch(url, options);
  return JSON.parse(response.getContentText());
}
```

### n8n (HTTP Request node)

1. Agregar nodo "HTTP Request"
2. Method: POST
3. URL: `https://tu-dominio.com/api/sales/webhook`
4. Authentication: Header Auth
   - Name: `X-Webhook-Token`
   - Value: `tu-token-secreto`
5. Body: JSON

---

## Notas importantes

1. **Canal de venta**: Las ventas creadas via webhook se marcan automáticamente con `sales_channel='whatsapp'`.

2. **Búsqueda de productos**: 
   - Primero busca por SKU exacto (case-insensitive)
   - Si no encuentra, busca por nombre exacto
   - Si no encuentra, busca por nombre parcial (contains)

3. **Stock FIFO**: El stock se descuenta de los lotes más antiguos primero.

4. **Rollback automático**: Si ocurre un error después de descontar stock, se revierte automáticamente.

5. **Logs de actividad**: Todas las ventas webhook quedan registradas en el monitor de actividades con `[Webhook]` como prefijo.

---

## Rate Limiting

Para proteger contra abuso, los endpoints tienen límites de requests:

| Endpoint | Límite |
|----------|--------|
| `POST /api/sales/webhook` | 10/minuto, 100/hora por IP |
| `GET /api/sales/webhook/test` | 30/minuto por IP |

**Response 429 (Too Many Requests):**
```json
{
  "error": "Rate limit exceeded",
  "message": "10 per 1 minute",
  "retry_after": "60"
}
```

El header `Retry-After` indica cuántos segundos esperar.

---

## Seguridad

- El token debe ser de al menos 32 caracteres
- Rotar el token periódicamente
- Usar HTTPS en producción
- No compartir el token en código público
- Rate limiting activo (10/min, 100/hora)
