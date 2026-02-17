# TODO — SIPUD

> **Última actualización:** 2026-02-17
> **Estado:** En producción ✅

---

## 🔥 Prioridad Alta

### 1. Webhook ManyChat
**Estado:** ⏸️ Bloqueado (esperando Pablo)
- [ ] Validar endpoint con datos reales de ManyChat
- [ ] Testear flujo completo WhatsApp → SIPUD
- [ ] Verificar descuento de stock automático/

### 2. Ventas Mayoristas
**Estado:** ✅ Completado (2026-02-11)
- [x] Agregar canal `mayorista` a `SALES_CHANNELS` en `models.py`
- [x] Agregar filtro en vista de ventas para ver solo mayoristas
- [x] Badge visual distintivo (amber) en tabla de ventas
- [ ] Considerar campos adicionales (cliente mayorista, condiciones)

### 3. Integración Google Sheets (CRM → Clientes)
**Estado:** ✅ Completado (2026-02-17)

**Contexto:** El Sheet tiene un sistema de semáforo para leads:
- 🔴 Poco interesados
- 🟡 Interesados
- 🟢 **Calificados** ← estos se importan a SIPUD

**Tareas:**
- [x] Obtener acceso al Sheet actual
- [x] Mapear columnas del Sheet → campos de Cliente en SIPUD
- [x] Implementar lectura de Sheet (API Google Sheets)
- [x] Filtrar solo leads "Calificados" (semáforo verde)
- [x] Crear/actualizar clientes en SIPUD automáticamente
- [x] Evitar duplicados (match por email/teléfono)
- [x] UI para ver estado de sync y logs (botón ManyChat en Clientes)

### 4. Flujo de Caja
**Estado:** 🔴 Pendiente
- [ ] Diseñar reporte de flujo de caja
- [ ] Basado en ventas + pagos registrados
- [ ] Exportable a Excel/PDF

### 5. Mejora Recepción de Mercancía
**Estado:** ✅ Completado (2026-02-11)
- [x] Revisar módulo actual de órdenes de entrada
- [x] Consolidar proceso de recepción (line items, recepción parcial, costos)
- [x] Proveedores integrados con dropdown + creación rápida
- [x] Lot codes legibles (LOT-PROV-SKU-FECHA-UUID)
- [x] Modal resumen post-recepción con tabla de lotes
- [x] Toasts en lugar de alert() en orders y receiving
- [ ] Posible conexión con Sheet externo

### 6. Notificaciones por Correo (Consolidado)
**Estado:** 🔴 Pendiente

**Email diario (cron ~19:00):**
- [ ] Consolidado de ventas del día
- [ ] Pedidos que quedaron pendientes
- [ ] Quiebres de stock (productos bajo mínimo)
- [ ] Horarios/estado de repartidores

**Implementación:**
- [ ] Crear template de email HTML bonito
- [ ] Configurar cron job para envío 19:00
- [ ] Usar Flask-Mail (ya configurado en .env)
- [ ] Definir destinatarios (admin/manager)

*Nota: NO un correo por cada venta, solo consolidado diario*

### 7. Bot Telegram — Ventas en Tiempo Real
**Estado:** 🔴 Pendiente

**Funcionalidad:**
- [ ] Bot que notifica nuevas ventas al instante
- [ ] Mensaje corto y bonito (emoji + cliente + total)
- [ ] Enviar a grupo de Telegram del equipo

**Implementación:**
- [ ] Crear bot en @BotFather
- [ ] Agregar bot al grupo de Puerto Distribución
- [ ] Hook en SIPUD al crear venta → enviar mensaje
- [ ] Formato: "🛒 Nueva venta: Juan Pérez - $25.000 (3 productos)"

### 8. Email Marketing a Clientes (Idea 💡)
**Estado:** 🔴 Pendiente

**Funcionalidad:**
- [ ] Envío de correos masivos a clientes
- [ ] Plantillas de promociones/ofertas
- [ ] Segmentación de clientes (todos, mayoristas, frecuentes, etc.)
- [ ] Diseño HTML bonito para emails

**Implementación:** Directo desde SIPUD (Flask-Mail)

**Consideraciones:**
- Cumplir con anti-spam (unsubscribe, consentimiento)
- No saturar a clientes
- Medir apertura/clicks

---

### 9. Gestión de Facturas y Gastos
**Estado:** 🔴 Pendiente

**Módulo de Facturas:**
- [ ] Modelo `Invoice` (proveedor, monto, fecha emisión, fecha vencimiento, estado)
- [ ] Subir/adjuntar PDF de factura
- [ ] SIPUD lee datos de factura (manual o OCR básico)
- [ ] Vista de facturas pendientes de pago

**Notificaciones de Vencimiento:**
- [ ] Alerta cuando factura está por vencer (ej: 7 días antes)
- [ ] Incluir en email consolidado diario
- [ ] Recordatorio de pago pendiente

**Consolidado de Gastos:**
- [ ] Reporte de gastos por período
- [ ] Categorización de gastos
- [ ] Comparativa con ingresos (flujo de caja)

---

### 💡 IDEA FUTURA: Simulador Financiero
**Estado:** 📋 Idea para más adelante

**Concepto:**
- Simular ventas basado en datos históricos
- Analizar comportamiento de clientes
- Cotización a empresa → calcular:
  - Punto de equilibrio
  - Tiempo para recuperar inversión (ROI)
  - Proyección de ganancias
- Simulaciones "what-if"

**Requiere:** Datos históricos suficientes para hacer proyecciones confiables

### 2. Arreglar errores silenciosos
**Estado:** ✅ Completado (2026-02-09)
**Commit:** c6834c9

Archivos arreglados:
- [x] `app/routes/delivery.py` (6 casos con logging)
- [x] `app/routes/reconciliation.py` (5 casos con logging)
- [x] `app/routes/reports.py` — OK, excepciones específicas con comentario
- [x] `app/routes/api.py` — OK, ya tenían logging
- [x] `app/routes/main.py` — OK
- [x] `app/routes/customers.py` — OK

### 3. Backup automático
**Estado:** 🔴 Pendiente
- [ ] Crear script `scripts/backup_mongo.sh`
- [ ] Configurar cron diario en VPS
- [ ] Guardar en carpeta con rotación (últimos 7 días)
- [ ] Opcionalmente subir a S3/GDrive

---

## 🛠️ Limpieza Técnica

### 4. Eliminar código muerto
**Estado:** ⏳ Pendiente
- [ ] Eliminar módulo Fleet/Logistics (`models.py`, `api.py`)
- [ ] Eliminar archivos `.backup`
- [ ] Eliminar carpeta `migrations/` (SQLite legacy)
- [ ] Limpiar `scripts/` — scripts obsoletos
- [ ] Revisar templates no usados

### 5. Mejorar logging
**Estado:** ⏳ Pendiente
- [ ] Configurar logger centralizado
- [ ] Agregar logs a operaciones críticas (ventas, pagos, stock)
- [ ] Logs con timestamp y usuario
- [ ] Rotación de logs en producción

---

## ✨ Features Nuevas

### 6. Dashboard mejorado
**Estado:** ✅ Completado (2026-02-17)
**Valor:** Alto — primera impresión del sistema
- [x] Gráfico de ventas últimos 7/30 días (Chart.js)
- [x] Top 5 productos más vendidos
- [x] Comparativa con período anterior (%)
- [x] Total clientes nuevos del mes
- [x] Alertas de stock bajo
- [x] 3 tabs: Resumen, Finanzas, Operaciones (lazy load)
- [x] Ventas por canal (bar chart)
- [x] Pagos pendientes + lista impagas más antiguas
- [x] Tabla últimas 10 ventas con canal y estado

### 7. Notificaciones automáticas
**Estado:** ⏳ Pendiente
- [ ] Alerta stock bajo (< crítico)
- [ ] Pedidos pendientes hace +24h
- [ ] Pagos parciales antiguos (+7 días)
- [ ] Email o WhatsApp (opcional)

### 8. Reportes exportables
**Estado:** ⏳ Pendiente
- [ ] Reporte de ventas por período (Excel/PDF)
- [ ] Reporte de inventario actual
- [ ] Reporte de clientes y compras
- [ ] Botón "Exportar" en cada sección

### 9. Mejoras UX
**Estado:** ⏳ Pendiente
- [ ] Búsqueda global (productos, clientes, ventas)
- [ ] Atajos de teclado
- [ ] Modo oscuro
- [ ] Tour/onboarding para usuarios nuevos

---

## 🚀 SIBAC (Producto Vendible)

### 10. Conversión a producto SaaS
**Estado:** 📋 Planificado
**Tiempo estimado:** 2 semanas
**Documento:** `PLAN_SIBAC.md`

- [ ] Clonar repo a `~/Proyectos/SIBAC`
- [ ] Renombrar referencias SIPUD → SIBAC
- [ ] Remover datos de Puerto Distribución
- [ ] Multi-tenant real (cada cliente su data)
- [ ] Panel super-admin
- [ ] Personalización por tenant (logo, colores)
- [ ] Sistema de planes (free, pro, enterprise)
- [ ] Landing page
- [ ] Onboarding automatizado
- [ ] Documentación para clientes

---

## 🐛 Bugs Conocidos

_Ninguno reportado actualmente_

---

## ✅ Completado

- [x] Deploy en VPS Hetzner (sipud.cloud)
- [x] Sprint Mejoras Ventas (campo sales_channel, filtros, cuadratura)
- [x] Actualización dependencias + tests
- [x] Fix datetime.utcnow() deprecated
- [x] Sync Shopify con preview
- [x] Sistema de pagos múltiples
- [x] Importación clientes desde Excel
- [x] Logging en exception handlers (2026-02-09)
- [x] Mejora Recepción de Mercancía — line items, recepción parcial, costos, proveedores integrados (2026-02-11)
- [x] Cuadratura Bancaria — permisos ROLE_PERMISSIONS, validación montos, Payment al conciliar/deshacer, ActivityLog, toasts, export Excel, batch ignore, búsqueda, detección duplicados importación (2026-02-17)
- [x] Tests ampliados: 50 tests pasando (2026-02-17)
- [x] Dashboard mejorado — 3 tabs (Resumen/Finanzas/Operaciones), lazy load, comparativa mes, ventas por canal, pagos pendientes, clientes nuevos, stock crítico expandido (2026-02-17)
- [x] Integración Google Sheets/ManyChat — service account, lectura Sheet, sync leads con semáforo, dedup por teléfono, creación ventas automática, botón UI (2026-02-17)

---

## 📝 Notas

- **Stack:** Flask + MongoDB + Jinja2 + Alpine.js + Tailwind
- **Puerto local:** 5006
- **Producción:** sipud.cloud (VPS Hetzner 72.61.4.202)
- **Tenant:** puerto-distribucion

---

## 🎯 Siguiente Acción Sugerida

**Opción rápida:** Tarea 3 (backup automático) — protección de datos
**Opción visible:** Tarea 6 (dashboard mejorado) — impacto visual alto
**Opción estratégica:** Tarea 4 (flujo de caja) — valor de negocio
