# Dashboard Mejorado — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Agregar tabs Finanzas y Operaciones al dashboard existente, con 2 nuevos endpoints API y lazy loading por tab.

**Architecture:** 3 tabs Alpine.js client-side (Resumen, Finanzas, Operaciones). Tab Resumen = contenido actual sin cambios. Tabs nuevos hacen fetch a `/api/dashboard/finances` y `/api/dashboard/operations` al activarse por primera vez. Chart.js bar chart para ventas por canal.

**Tech Stack:** Flask, MongoEngine, Alpine.js, Tailwind CSS, Chart.js

---

### Task 1: Backend — Endpoint GET /api/dashboard/finances

**Files:**
- Modify: `app/routes/api.py` (añadir imports + endpoint)

**Step 1: Añadir imports necesarios**

En `app/routes/api.py` línea 3, agregar `ShopifyCustomer, InboundOrder` a los imports existentes (si `InboundOrder` no está ya) y `Supplier`:

```python
from app.models import Product, Sale, SaleItem, Lot, InboundOrder, ProductBundle, Truck, VehicleMaintenance, ActivityLog, Payment, Tenant, Wastage, User, utc_now, ShopifyCustomer, SALES_CHANNELS
```

**Step 2: Implementar endpoint finances**

Agregar después del endpoint `get_dashboard_stats` (línea ~534):

```python
@bp.route('/dashboard/finances', methods=['GET'])
@login_required
def get_dashboard_finances():
    tenant = g.current_tenant

    now = utc_now()
    # Current month range
    current_month_start = datetime.combine(now.date().replace(day=1), datetime.min.time())
    next_month = current_month_start + relativedelta(months=1)

    # Previous month range
    prev_month_start = current_month_start - relativedelta(months=1)
    prev_month_end = current_month_start

    # === Comparison: current vs previous month ===
    current_sales = Sale.objects(tenant=tenant, date_created__gte=current_month_start, date_created__lt=next_month)
    prev_sales = Sale.objects(tenant=tenant, date_created__gte=prev_month_start, date_created__lt=prev_month_end)

    def calc_revenue(sales_qs):
        total = 0
        for sale in sales_qs:
            for item in sale.items:
                total += item.quantity * float(item.unit_price)
        return total

    current_count = current_sales.count()
    prev_count = prev_sales.count()
    current_revenue = calc_revenue(current_sales)
    prev_revenue = calc_revenue(prev_sales)

    sales_change_pct = ((current_count - prev_count) / prev_count * 100) if prev_count > 0 else (100.0 if current_count > 0 else 0)
    revenue_change_pct = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else (100.0 if current_revenue > 0 else 0)

    # === Sales by channel ===
    by_channel = {}
    for channel_key in SALES_CHANNELS:
        channel_sales = Sale.objects(tenant=tenant, date_created__gte=current_month_start, date_created__lt=next_month, sales_channel=channel_key)
        count = channel_sales.count()
        revenue = calc_revenue(channel_sales)
        by_channel[channel_key] = {'count': count, 'revenue': revenue}

    # === Pending payments ===
    unpaid_sales = Sale.objects(tenant=tenant, payment_status__in=['pendiente', 'parcial']).order_by('date_created')

    total_pending = 0
    unpaid_list = []
    for sale in unpaid_sales:
        sale_total = 0
        for item in sale.items:
            sale_total += item.quantity * float(item.unit_price)
        paid = float(sale.total_paid) if hasattr(sale, 'total_paid') else 0
        pending_amount = sale_total - paid
        if pending_amount > 0:
            total_pending += pending_amount
            days_old = (now - sale.date_created).days if sale.date_created else 0
            unpaid_list.append({
                'id': str(sale.id),
                'customer': sale.customer_name or 'Sin nombre',
                'total': sale_total,
                'pending': pending_amount,
                'days_old': days_old,
                'status': sale.payment_status
            })

    avg_age = sum(u['days_old'] for u in unpaid_list) / len(unpaid_list) if unpaid_list else 0

    return jsonify({
        'success': True,
        'comparison': {
            'current_month_sales': current_count,
            'current_month_revenue': current_revenue,
            'prev_month_sales': prev_count,
            'prev_month_revenue': prev_revenue,
            'sales_change_pct': round(sales_change_pct, 1),
            'revenue_change_pct': round(revenue_change_pct, 1)
        },
        'by_channel': by_channel,
        'pending_payments': {
            'total_pending': total_pending,
            'count': len(unpaid_list),
            'avg_age_days': round(avg_age, 1),
            'oldest_unpaid': unpaid_list[:5]
        }
    })
```

**Step 3: Verificar endpoint**

Run: `curl -s http://localhost:5006/api/dashboard/finances` (debería dar 401 sin auth — confirma que la ruta existe)

**Step 4: Commit**

```bash
git add app/routes/api.py
git commit -m "feat: add GET /api/dashboard/finances endpoint"
```

---

### Task 2: Backend — Endpoint GET /api/dashboard/operations

**Files:**
- Modify: `app/routes/api.py`

**Step 1: Implementar endpoint operations**

Agregar después del endpoint finances:

```python
@bp.route('/dashboard/operations', methods=['GET'])
@login_required
def get_dashboard_operations():
    tenant = g.current_tenant

    now = utc_now()
    current_month_start = datetime.combine(now.date().replace(day=1), datetime.min.time())
    next_month = current_month_start + relativedelta(months=1)
    prev_month_start = current_month_start - relativedelta(months=1)

    # === New customers this month vs previous ===
    current_customers = ShopifyCustomer.objects(
        tenant=tenant,
        created_at__gte=current_month_start,
        created_at__lt=next_month
    ).count()

    prev_customers = ShopifyCustomer.objects(
        tenant=tenant,
        created_at__gte=prev_month_start,
        created_at__lt=current_month_start
    ).count()

    customers_change_pct = ((current_customers - prev_customers) / prev_customers * 100) if prev_customers > 0 else (100.0 if current_customers > 0 else 0)

    # === Critical stock (all products below minimum) ===
    critical_stock = []
    for p in Product.objects(tenant=tenant):
        if hasattr(p, 'total_stock') and hasattr(p, 'critical_stock'):
            if p.total_stock <= p.critical_stock:
                critical_stock.append({
                    'id': str(p.id),
                    'name': p.name,
                    'stock': p.total_stock,
                    'critical': p.critical_stock,
                    'sku': p.sku or ''
                })

    # === Pending inbound orders ===
    pending_orders = []
    for order in InboundOrder.objects(tenant=tenant, status='pending').order_by('-created_at').limit(10):
        pending_orders.append({
            'id': str(order.id),
            'supplier': order.supplier_name or (order.supplier.name if order.supplier else 'Sin proveedor'),
            'status': order.status,
            'created_at': order.created_at.strftime('%Y-%m-%d') if order.created_at else '',
            'total': float(order.total) if order.total else 0
        })

    # === Recent sales (last 10) ===
    recent_sales = []
    for sale in Sale.objects(tenant=tenant).order_by('-date_created').limit(10):
        sale_total = 0
        for item in sale.items:
            sale_total += item.quantity * float(item.unit_price)
        recent_sales.append({
            'id': str(sale.id),
            'customer': sale.customer_name or 'Sin nombre',
            'total': sale_total,
            'status': sale.status,
            'channel': sale.sales_channel or 'manual',
            'date': sale.date_created.strftime('%Y-%m-%d') if sale.date_created else ''
        })

    return jsonify({
        'success': True,
        'new_customers': {
            'current_month': current_customers,
            'prev_month': prev_customers,
            'change_pct': round(customers_change_pct, 1)
        },
        'critical_stock': critical_stock,
        'pending_orders': pending_orders,
        'recent_sales': recent_sales
    })
```

**Step 2: Verificar endpoint**

Run: `curl -s http://localhost:5006/api/dashboard/operations` (debería dar 401)

**Step 3: Commit**

```bash
git add app/routes/api.py
git commit -m "feat: add GET /api/dashboard/operations endpoint"
```

---

### Task 3: Frontend — Tab navigation UI

**Files:**
- Modify: `app/templates/dashboard.html`

**Step 1: Envolver todo el contenido actual en Alpine.js y agregar tabs**

Después del cierre del `</div>` de Quick Access Buttons (línea 184), agregar la navegación de tabs:

```html
<!-- Dashboard Tabs -->
<div x-data="dashboardTabs()" class="mb-6">
    <div class="flex gap-1 bg-white rounded-xl shadow-sm border border-slate-200 p-1 w-fit">
        <button @click="switchTab('resumen')"
            :class="activeTab === 'resumen' ? 'bg-primary-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-800 hover:bg-slate-50'"
            class="px-5 py-2 rounded-lg text-sm font-medium transition-all">
            Resumen
        </button>
        <button @click="switchTab('finanzas')"
            :class="activeTab === 'finanzas' ? 'bg-primary-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-800 hover:bg-slate-50'"
            class="px-5 py-2 rounded-lg text-sm font-medium transition-all">
            Finanzas
        </button>
        <button @click="switchTab('operaciones')"
            :class="activeTab === 'operaciones' ? 'bg-primary-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-800 hover:bg-slate-50'"
            class="px-5 py-2 rounded-lg text-sm font-medium transition-all">
            Operaciones
        </button>
    </div>
```

**Step 2: Envolver contenido existente en x-show="activeTab === 'resumen'"**

Envolver desde Stats Grid hasta el final del contenido (líneas 186–433) en:

```html
    <!-- Tab: Resumen -->
    <div x-show="activeTab === 'resumen'" x-cloak>
        <!-- ... todo el contenido actual del dashboard ... -->
    </div>
```

**Step 3: Agregar placeholder para tabs Finanzas y Operaciones**

Después del cierre de tab Resumen:

```html
    <!-- Tab: Finanzas -->
    <div x-show="activeTab === 'finanzas'" x-cloak>
        <div x-show="loadingFinances" class="flex justify-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
        <div x-show="!loadingFinances" id="finanzas-content">
            <!-- Se llena en Task 4 -->
        </div>
    </div>

    <!-- Tab: Operaciones -->
    <div x-show="activeTab === 'operaciones'" x-cloak>
        <div x-show="loadingOperations" class="flex justify-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
        <div x-show="!loadingOperations" id="operaciones-content">
            <!-- Se llena en Task 5 -->
        </div>
    </div>
</div> <!-- cierre x-data="dashboardTabs()" -->
```

**Step 4: Agregar script Alpine.js dashboardTabs()**

Antes de `</script>` al final del archivo, agregar:

```javascript
function dashboardTabs() {
    return {
        activeTab: 'resumen',
        loadingFinances: false,
        loadingOperations: false,
        financesData: null,
        operationsData: null,
        channelChart: null,

        switchTab(tab) {
            this.activeTab = tab;
            if (tab === 'finanzas' && !this.financesData) {
                this.loadFinances();
            }
            if (tab === 'operaciones' && !this.operationsData) {
                this.loadOperations();
            }
        },

        async loadFinances() {
            this.loadingFinances = true;
            try {
                const res = await fetch('/api/dashboard/finances');
                this.financesData = await res.json();
                this.$nextTick(() => this.renderFinanzas());
            } catch (e) {
                console.error('Error loading finances:', e);
            }
            this.loadingFinances = false;
        },

        async loadOperations() {
            this.loadingOperations = true;
            try {
                const res = await fetch('/api/dashboard/operations');
                this.operationsData = await res.json();
            } catch (e) {
                console.error('Error loading operations:', e);
            }
            this.loadingOperations = false;
        },

        renderFinanzas() {
            // Channel bar chart - se implementa en Task 4
        },

        formatMoney(val) {
            return '$' + Math.round(val).toLocaleString('es-CL');
        }
    }
}
```

**Step 5: Verificar que las tabs se muestran y el contenido de Resumen aparece/desaparece**

Abrir `http://localhost:5006` en browser, hacer click en cada tab.

**Step 6: Commit**

```bash
git add app/templates/dashboard.html
git commit -m "feat: add tab navigation UI to dashboard with lazy loading"
```

---

### Task 4: Frontend — Tab Finanzas (contenido + chart)

**Files:**
- Modify: `app/templates/dashboard.html`

**Step 1: Implementar contenido del tab Finanzas**

Reemplazar el placeholder `<!-- Se llena en Task 4 -->` con:

```html
<!-- Comparison Cards -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8 mt-6">
    <!-- Ventas este mes -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <p class="text-xs font-medium text-slate-500 uppercase tracking-wide">Ventas Este Mes</p>
        <p class="text-2xl font-bold text-slate-800 mt-1" x-text="financesData?.comparison?.current_month_sales || 0"></p>
        <div class="flex items-center gap-1 mt-2">
            <template x-if="financesData?.comparison?.sales_change_pct >= 0">
                <span class="text-xs font-medium text-emerald-600 flex items-center gap-0.5">
                    <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clip-rule="evenodd"/></svg>
                    <span x-text="financesData?.comparison?.sales_change_pct + '%'"></span>
                </span>
            </template>
            <template x-if="financesData?.comparison?.sales_change_pct < 0">
                <span class="text-xs font-medium text-red-600 flex items-center gap-0.5">
                    <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
                    <span x-text="financesData?.comparison?.sales_change_pct + '%'"></span>
                </span>
            </template>
            <span class="text-xs text-slate-400">vs mes anterior</span>
        </div>
    </div>

    <!-- Ingresos este mes -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <p class="text-xs font-medium text-slate-500 uppercase tracking-wide">Ingresos Este Mes</p>
        <p class="text-2xl font-bold text-emerald-600 mt-1" x-text="formatMoney(financesData?.comparison?.current_month_revenue || 0)"></p>
        <div class="flex items-center gap-1 mt-2">
            <template x-if="financesData?.comparison?.revenue_change_pct >= 0">
                <span class="text-xs font-medium text-emerald-600 flex items-center gap-0.5">
                    <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clip-rule="evenodd"/></svg>
                    <span x-text="financesData?.comparison?.revenue_change_pct + '%'"></span>
                </span>
            </template>
            <template x-if="financesData?.comparison?.revenue_change_pct < 0">
                <span class="text-xs font-medium text-red-600 flex items-center gap-0.5">
                    <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
                    <span x-text="financesData?.comparison?.revenue_change_pct + '%'"></span>
                </span>
            </template>
            <span class="text-xs text-slate-400">vs mes anterior</span>
        </div>
    </div>

    <!-- Total por cobrar -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <p class="text-xs font-medium text-slate-500 uppercase tracking-wide">Por Cobrar</p>
        <p class="text-2xl font-bold text-amber-600 mt-1" x-text="formatMoney(financesData?.pending_payments?.total_pending || 0)"></p>
        <p class="text-xs text-slate-400 mt-2" x-text="(financesData?.pending_payments?.count || 0) + ' ventas pendientes'"></p>
    </div>

    <!-- Antigüedad promedio -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <p class="text-xs font-medium text-slate-500 uppercase tracking-wide">Antigüedad Promedio</p>
        <p class="text-2xl font-bold text-slate-800 mt-1" x-text="(financesData?.pending_payments?.avg_age_days || 0) + ' días'"></p>
        <p class="text-xs text-slate-400 mt-2">de ventas impagas</p>
    </div>
</div>

<!-- Charts + Pending -->
<div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
    <!-- Channel Bar Chart -->
    <div class="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200">
        <div class="px-6 py-4 border-b border-slate-100">
            <h3 class="font-bold text-slate-800">Ventas por Canal (Este Mes)</h3>
        </div>
        <div class="p-6">
            <div class="h-72">
                <canvas id="channelChart"></canvas>
            </div>
        </div>
    </div>

    <!-- Oldest Unpaid Sales -->
    <div class="bg-white rounded-xl shadow-sm border border-amber-200">
        <div class="px-5 py-4 border-b border-amber-100 bg-amber-50 rounded-t-xl">
            <h3 class="font-bold text-amber-800 text-sm flex items-center gap-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                Ventas Impagas Más Antiguas
            </h3>
        </div>
        <div class="divide-y divide-amber-100 max-h-72 overflow-y-auto">
            <template x-if="financesData?.pending_payments?.oldest_unpaid?.length === 0">
                <div class="px-5 py-8 text-center text-sm text-slate-400">Sin ventas pendientes de pago</div>
            </template>
            <template x-for="sale in (financesData?.pending_payments?.oldest_unpaid || [])" :key="sale.id">
                <a :href="'/sales/' + sale.id" class="px-5 py-3 flex justify-between items-center hover:bg-amber-50 transition-colors block">
                    <div>
                        <p class="text-sm font-medium text-slate-900" x-text="sale.customer"></p>
                        <p class="text-xs text-slate-500" x-text="'Hace ' + sale.days_old + ' días'"></p>
                    </div>
                    <div class="text-right">
                        <p class="text-sm font-bold text-amber-600" x-text="formatMoney(sale.pending)"></p>
                        <p class="text-xs text-slate-500" x-text="'Total: ' + formatMoney(sale.total)"></p>
                    </div>
                </a>
            </template>
        </div>
    </div>
</div>
```

**Step 2: Implementar renderFinanzas() para el bar chart**

Actualizar la función `renderFinanzas()` en el script:

```javascript
renderFinanzas() {
    if (!this.financesData?.by_channel) return;
    const ctx = document.getElementById('channelChart');
    if (!ctx) return;

    if (this.channelChart) this.channelChart.destroy();

    const channelLabels = {
        'manual': 'Manual',
        'whatsapp': 'WhatsApp',
        'shopify': 'Shopify',
        'web': 'Web',
        'mayorista': 'Mayorista'
    };
    const channelColors = {
        'manual': '#6366f1',
        'whatsapp': '#22c55e',
        'shopify': '#8b5cf6',
        'web': '#3b82f6',
        'mayorista': '#f59e0b'
    };

    const channels = Object.keys(this.financesData.by_channel);
    const labels = channels.map(c => channelLabels[c] || c);
    const revenues = channels.map(c => this.financesData.by_channel[c].revenue);
    const counts = channels.map(c => this.financesData.by_channel[c].count);
    const colors = channels.map(c => channelColors[c] || '#94a3b8');

    this.channelChart = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Ingresos ($)',
                data: revenues,
                backgroundColor: colors,
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1e293b',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const idx = context.dataIndex;
                            return [
                                'Ingresos: $' + context.parsed.y.toLocaleString('es-CL'),
                                'Ventas: ' + counts[idx]
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#f1f5f9' },
                    ticks: { callback: function(v) { return '$' + v.toLocaleString('es-CL'); } }
                },
                x: { grid: { display: false } }
            }
        }
    });
}
```

**Step 3: Verificar visualmente**

Abrir dashboard, click tab "Finanzas", verificar: 4 cards comparativas + bar chart + lista impagas.

**Step 4: Commit**

```bash
git add app/templates/dashboard.html
git commit -m "feat: add Finanzas tab content with comparison cards, channel chart, pending payments"
```

---

### Task 5: Frontend — Tab Operaciones (contenido)

**Files:**
- Modify: `app/templates/dashboard.html`

**Step 1: Implementar contenido del tab Operaciones**

Reemplazar `<!-- Se llena en Task 5 -->` con:

```html
<!-- New Customers Card -->
<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 mt-6">
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <p class="text-xs font-medium text-slate-500 uppercase tracking-wide">Clientes Nuevos (Este Mes)</p>
        <p class="text-2xl font-bold text-slate-800 mt-1" x-text="operationsData?.new_customers?.current_month || 0"></p>
        <div class="flex items-center gap-1 mt-2">
            <template x-if="operationsData?.new_customers?.change_pct >= 0">
                <span class="text-xs font-medium text-emerald-600 flex items-center gap-0.5">
                    <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clip-rule="evenodd"/></svg>
                    <span x-text="operationsData?.new_customers?.change_pct + '%'"></span>
                </span>
            </template>
            <template x-if="operationsData?.new_customers?.change_pct < 0">
                <span class="text-xs font-medium text-red-600 flex items-center gap-0.5">
                    <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
                    <span x-text="operationsData?.new_customers?.change_pct + '%'"></span>
                </span>
            </template>
            <span class="text-xs text-slate-400" x-text="'vs ' + (operationsData?.new_customers?.prev_month || 0) + ' mes anterior'"></span>
        </div>
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <p class="text-xs font-medium text-slate-500 uppercase tracking-wide">Pedidos por Recibir</p>
        <p class="text-2xl font-bold text-slate-800 mt-1" x-text="operationsData?.pending_orders?.length || 0"></p>
        <p class="text-xs text-slate-400 mt-2">órdenes de compra pendientes</p>
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5"
        :class="(operationsData?.critical_stock?.length || 0) > 0 ? 'border-red-300 bg-red-50' : ''">
        <p class="text-xs font-medium text-slate-500 uppercase tracking-wide">Stock Crítico</p>
        <p class="text-2xl font-bold mt-1" :class="(operationsData?.critical_stock?.length || 0) > 0 ? 'text-red-600' : 'text-slate-800'"
            x-text="operationsData?.critical_stock?.length || 0"></p>
        <p class="text-xs text-slate-400 mt-2">productos bajo mínimo</p>
    </div>
</div>

<!-- Bottom grid: Stock + Orders + Sales -->
<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- Critical Stock Expanded -->
    <div class="bg-white rounded-xl shadow-sm border border-red-200">
        <div class="px-5 py-4 border-b border-red-100 bg-red-50 rounded-t-xl flex items-center justify-between">
            <h3 class="font-bold text-red-800 text-sm flex items-center gap-2">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
                Productos con Stock Crítico
            </h3>
            <a href="/products" class="text-xs text-red-600 hover:underline">Ver todos →</a>
        </div>
        <div class="divide-y divide-red-100 max-h-80 overflow-y-auto">
            <template x-if="!operationsData?.critical_stock?.length">
                <div class="px-5 py-8 text-center text-sm text-slate-400">Todo el stock está en niveles normales</div>
            </template>
            <template x-for="item in (operationsData?.critical_stock || [])" :key="item.id">
                <div class="px-5 py-3 flex justify-between items-center hover:bg-red-50 transition-colors">
                    <div>
                        <p class="text-sm font-medium text-slate-900" x-text="item.name"></p>
                        <p class="text-xs text-slate-500" x-text="'SKU: ' + item.sku"></p>
                    </div>
                    <div class="text-right">
                        <p class="text-sm font-bold text-red-600" x-text="item.stock + ' uds'"></p>
                        <p class="text-xs text-slate-500" x-text="'Mín: ' + item.critical"></p>
                    </div>
                </div>
            </template>
        </div>
    </div>

    <!-- Pending Orders -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-200">
        <div class="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
            <h3 class="font-bold text-slate-800 text-sm">📦 Pedidos Pendientes de Recepción</h3>
            <a href="/warehouse/orders" class="text-xs text-primary-600 hover:underline">Ver todos →</a>
        </div>
        <div class="divide-y divide-slate-100 max-h-80 overflow-y-auto">
            <template x-if="!operationsData?.pending_orders?.length">
                <div class="px-5 py-8 text-center text-sm text-slate-400">Sin pedidos pendientes</div>
            </template>
            <template x-for="order in (operationsData?.pending_orders || [])" :key="order.id">
                <div class="px-5 py-3 flex justify-between items-center hover:bg-slate-50 transition-colors">
                    <div>
                        <p class="text-sm font-medium text-slate-900" x-text="order.supplier"></p>
                        <p class="text-xs text-slate-500" x-text="order.created_at"></p>
                    </div>
                    <p class="text-sm font-semibold text-slate-800" x-text="formatMoney(order.total)"></p>
                </div>
            </template>
        </div>
    </div>

    <!-- Recent Sales (last 10) -->
    <div class="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200">
        <div class="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
            <h3 class="font-bold text-slate-800 text-sm">🛒 Últimas 10 Ventas</h3>
            <a href="/sales" class="text-xs text-primary-600 hover:underline">Ver todas →</a>
        </div>
        <div class="overflow-x-auto">
            <table class="w-full text-sm">
                <thead class="bg-slate-50">
                    <tr>
                        <th class="px-5 py-2 text-left text-xs font-medium text-slate-500">Cliente</th>
                        <th class="px-5 py-2 text-left text-xs font-medium text-slate-500">Canal</th>
                        <th class="px-5 py-2 text-left text-xs font-medium text-slate-500">Estado</th>
                        <th class="px-5 py-2 text-right text-xs font-medium text-slate-500">Total</th>
                        <th class="px-5 py-2 text-right text-xs font-medium text-slate-500">Fecha</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                    <template x-for="sale in (operationsData?.recent_sales || [])" :key="sale.id">
                        <tr class="hover:bg-slate-50">
                            <td class="px-5 py-2.5 font-medium text-slate-900" x-text="sale.customer"></td>
                            <td class="px-5 py-2.5">
                                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700" x-text="sale.channel"></span>
                            </td>
                            <td class="px-5 py-2.5">
                                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                                    :class="{
                                        'bg-green-100 text-green-800': sale.status === 'delivered',
                                        'bg-yellow-100 text-yellow-800': sale.status === 'pending',
                                        'bg-blue-100 text-blue-800': sale.status === 'in_transit',
                                        'bg-red-100 text-red-800': sale.status === 'cancelled',
                                        'bg-slate-100 text-slate-800': !['delivered','pending','in_transit','cancelled'].includes(sale.status)
                                    }"
                                    x-text="sale.status"></span>
                            </td>
                            <td class="px-5 py-2.5 text-right font-semibold" x-text="formatMoney(sale.total)"></td>
                            <td class="px-5 py-2.5 text-right text-slate-500" x-text="sale.date"></td>
                        </tr>
                    </template>
                </tbody>
            </table>
        </div>
    </div>
</div>
```

**Step 2: Verificar visualmente**

Abrir dashboard, click tab "Operaciones", verificar: 3 cards + stock crítico + pedidos + ventas recientes tabla.

**Step 3: Commit**

```bash
git add app/templates/dashboard.html
git commit -m "feat: add Operaciones tab with customers, stock, orders, recent sales"
```

---

### Task 6: Pruebas end-to-end y ajustes finales

**Files:**
- Possibly fix: `app/routes/api.py`, `app/templates/dashboard.html`

**Step 1: Verificar backend endpoints en terminal**

```bash
pytest tests/ -v
```

**Step 2: Test manual completo en browser**

1. Login como admin
2. Tab Resumen: todo funciona como antes
3. Tab Finanzas: cards comparativas, bar chart con datos, lista impagas
4. Tab Operaciones: card clientes, stock crítico, pedidos, tabla ventas
5. Cambiar entre tabs rápido (verificar cache — solo carga una vez)
6. Verificar en mobile (responsive)

**Step 3: Commit final si hay ajustes**

```bash
git add -A
git commit -m "fix: dashboard tab adjustments after testing"
```

---

## Orden de Ejecución

1. **Task 1**: Backend finances endpoint
2. **Task 2**: Backend operations endpoint
3. **Task 3**: Frontend tab navigation
4. **Task 4**: Frontend Finanzas content
5. **Task 5**: Frontend Operaciones content
6. **Task 6**: Testing + ajustes

## Verificación Final

1. `pytest tests/` pasa sin errores
2. Tab Resumen muestra contenido existente sin cambios
3. Tab Finanzas carga datos por AJAX, muestra cards + bar chart + lista impagas
4. Tab Operaciones carga datos por AJAX, muestra cards + stock + pedidos + tabla ventas
5. Lazy loading funciona (cada tab carga solo la primera vez)
6. Responsive en mobile
