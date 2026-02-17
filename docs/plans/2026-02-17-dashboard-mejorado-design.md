# Dashboard Mejorado — Design Doc

## Contexto
Dashboard actual tiene: stats cards, gráfico ventas (línea), donut estados, top productos, alertas stock, actividad reciente. Falta: comparativa periodos, ventas por canal, pagos pendientes, clientes nuevos.

## Decisión
Enfoque B: Dashboard con tabs. Reorganizar en 3 pestañas para separar visión ejecutiva de operativa sin sobrecargar la vista.

## Arquitectura

### Frontend: 3 Tabs (Alpine.js)
Variable `activeTab` controla qué sección es visible. Lazy load: cada tab hace fetch a su endpoint al activarse por primera vez.

**Tab "Resumen"** (default):
- Lo que ya existe, sin cambios
- Stats cards: Total ventas, Total productos, Ingresos, Stock crítico
- Gráfico ventas (línea) con selector rango
- Top 5 productos + Donut estados + Actividad reciente

**Tab "Finanzas"**:
- Cards comparativas: ventas este mes vs anterior (monto + %, flecha verde/roja)
- Gráfico barras: ventas por canal (WhatsApp, Shopify, Web, Manual, Mayorista)
- Card pagos pendientes: total $ por cobrar, cantidad ventas impagas, antigüedad promedio
- Lista: top 5 ventas impagas más antiguas (con link a venta)

**Tab "Operaciones"**:
- Card clientes nuevos: este mes + % cambio vs mes anterior
- Alertas stock crítico (expandido, todos los productos bajo mínimo)
- Pedidos pendientes de recepción (lista con estado)
- Ventas recientes (últimas 10)

### Backend: 2 nuevos endpoints API

**GET /api/dashboard/finances**
```json
{
  "comparison": {
    "current_month_sales": 15,
    "current_month_revenue": 450000,
    "prev_month_sales": 12,
    "prev_month_revenue": 380000,
    "sales_change_pct": 25.0,
    "revenue_change_pct": 18.4
  },
  "by_channel": {
    "manual": {"count": 5, "revenue": 150000},
    "whatsapp": {"count": 4, "revenue": 120000},
    "shopify": {"count": 3, "revenue": 100000},
    "web": {"count": 2, "revenue": 50000},
    "mayorista": {"count": 1, "revenue": 30000}
  },
  "pending_payments": {
    "total_pending": 320000,
    "count": 8,
    "avg_age_days": 5.2,
    "oldest_unpaid": [
      {"id": "...", "customer": "Juan", "total": 45000, "days_old": 12, "status": "pendiente"}
    ]
  }
}
```

**GET /api/dashboard/operations**
```json
{
  "new_customers": {
    "current_month": 8,
    "prev_month": 5,
    "change_pct": 60.0
  },
  "critical_stock": [
    {"id": "...", "name": "Arroz 5kg", "stock": 2, "critical": 10, "sku": "ARR5K"}
  ],
  "pending_orders": [
    {"id": "...", "supplier": "Dist. XY", "status": "pending", "created_at": "2026-02-15", "total": 150000}
  ],
  "recent_sales": [
    {"id": "...", "customer": "María", "total": 25000, "status": "delivered", "date": "2026-02-17"}
  ]
}
```

### Navegación de tabs
- Tabs debajo del welcome card, encima del content grid
- Estilo: pills con borde inferior activo (patrón del proyecto)
- Sin cambio de URL (Alpine.js client-side)
- Cada tab carga datos solo la primera vez, luego usa cache local

## Archivos a Modificar
| Archivo | Cambios |
|---------|---------|
| `app/routes/api.py` | 2 nuevos endpoints: finances + operations |
| `app/templates/dashboard.html` | Tabs UI, secciones Finanzas y Operaciones |

## Charts
- Gráfico barras (ventas por canal): Chart.js bar chart, colores por canal
- Cards comparativas: CSS puro con flechas SVG, sin chart extra
