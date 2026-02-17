# Diseno: Dashboard + Google Sheets/ManyChat + Clientes Mejorados

**Fecha:** 2026-02-17
**Estado:** Aprobado

---

## Contexto

Tres mejoras relacionadas:
1. Rediseno visual del dashboard (mismo contenido, mejor presentacion)
2. Integracion con Google Sheet que genera ManyChat (leads de WhatsApp)
3. Mejora del sistema de tags/etiquetas en clientes

## Feature 1: Integracion Google Sheets / ManyChat

### Estructura del Sheet

| Columna | Uso en SIPUD |
|---------|-------------|
| Fecha ingreso | `created_at` del cliente |
| User ID | `phone` (numero WhatsApp, clave para dedup) |
| Status | Informativo (no se usa directamente) |
| Semaforo | Determina accion: calificado/interesado/poco-interesado |
| Nombre | `name` del cliente |
| Fuente | Siempre "WhatsApp" -> `source = "manychat"` |
| Productos interes | Parsear para crear items de venta |
| Ciudad | `address_city` |
| Lugar Entrega | `address` en la venta |
| Hora Entrega | Nota en la venta |
| Metodo de Pago | `payment_method` en la venta |

### Flujo de importacion

```
Boton "Sincronizar ManyChat" en seccion Clientes
  -> Lee Sheet via Google Sheets API v4
  -> Para cada fila:
     1. Dedup por telefono (User ID) - si ya existe, skip
     2. Crear ShopifyCustomer con source="manychat"
     3. Asignar tag segun semaforo:
        - CALIFICADO -> tag "calificado"
        - INTERESADO -> tag "interesado"
        - POCO INTERESADO -> tag "poco-interesado"
     4. Si CALIFICADO + tiene productos:
        - Parsear "Promo jurel x2 | Caja Mensual x1"
        - Buscar producto por nombre (fuzzy match)
        - Crear venta pendiente (canal=whatsapp, sin descontar stock)
        - Si producto no encontrado: nota "Producto no encontrado: X"
```

### Conexion Google API

- Usar Service Account (archivo JSON de credenciales)
- Libreria: `gspread` + `google-auth`
- Credenciales en `.env`: `GOOGLE_SHEETS_CREDENTIALS_FILE` y `GOOGLE_SHEETS_ID`
- El Sheet se comparte con el email del Service Account

### Endpoint

`POST /customers/api/customers/sync-manychat`
- Permiso: `customers.sync`
- Retorna: `{ created, skipped, sales_created, errors }`

## Feature 2: Mejora Sistema de Tags en Clientes

### Cambios al modelo

- Campo `tags`: de `StringField` a `ListField(StringField)`
- Agregar `source` choices: agregar "manychat" a las opciones existentes
- Backward compat: migrar tags existentes (split por coma)

### Cambios a la UI

- Tags como badges de colores en la tabla de clientes
- Colores por tag: calificado=verde, interesado=amarillo, poco-interesado=rojo
- Tags custom en colores neutros (gris/azul)
- Filtro por tag en la tabla (dropdown multi-select)
- Edicion de tags: click en cliente -> agregar/quitar tags

### Tags predefinidos del semaforo ManyChat

| Tag | Color | Badge |
|-----|-------|-------|
| calificado | green | bg-green-100 text-green-800 |
| interesado | yellow | bg-yellow-100 text-yellow-800 |
| poco-interesado | red | bg-red-100 text-red-800 |

## Feature 3: Rediseno Visual Dashboard

### Alcance

Solo visual — mismo contenido y endpoints API existentes.

### Mejoras

- Cards con sombras y gradientes mas modernos
- Graficos Chart.js con colores consistentes y tooltips mejorados
- Layout grid responsive mejorado
- Mejor jerarquia visual (KPIs arriba, graficos medio, detalles abajo)
- Animaciones sutiles de entrada
- Tipografia y spacing mas profesional

### Sin cambios

- No se agregan metricas nuevas
- No se modifican endpoints API
- No se cambia logica de negocio

## Dependencias nuevas

- `gspread` - Cliente Google Sheets para Python
- `google-auth` - Autenticacion Google (Service Account)

## Orden de implementacion

1. **Tags en clientes** (base para todo lo demas)
2. **Google Sheets integration** (depende de tags)
3. **Dashboard rediseno** (independiente, puede ir en paralelo)
