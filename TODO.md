# TODO — SIPUD

> **Última actualización:** 2026-02-09
> **Estado:** En producción ✅

---

## 🔥 Prioridad Alta

### 1. Webhook ManyChat
**Estado:** ⏸️ Bloqueado (esperando Pablo)
- [ ] Validar endpoint con datos reales de ManyChat
- [ ] Testear flujo completo WhatsApp → SIPUD
- [ ] Verificar descuento de stock automático

### 2. Ventas Mayoristas
**Estado:** 🔴 Pendiente
- [ ] Agregar canal `mayorista` a `SALES_CHANNELS` en `models.py`
- [ ] Agregar filtro en vista de ventas para ver solo mayoristas
- [ ] Considerar campos adicionales (cliente mayorista, condiciones)

### 3. Integración Google Sheets (CRM → Clientes)
**Estado:** 🔴 Pendiente

**Contexto:** El Sheet tiene un sistema de semáforo para leads:
- 🔴 Poco interesados
- 🟡 Interesados  
- 🟢 **Calificados** ← estos se importan a SIPUD

**Tareas:**
- [ ] Obtener acceso al Sheet actual
- [ ] Mapear columnas del Sheet → campos de Cliente en SIPUD
- [ ] Implementar lectura de Sheet (API Google Sheets)
- [ ] Filtrar solo leads "Calificados" (semáforo verde)
- [ ] Crear/actualizar clientes en SIPUD automáticamente
- [ ] Evitar duplicados (match por email/teléfono)
- [ ] UI para ver estado de sync y logs

### 4. Flujo de Caja
**Estado:** 🔴 Pendiente
- [ ] Diseñar reporte de flujo de caja
- [ ] Basado en ventas + pagos registrados
- [ ] Exportable a Excel/PDF

### 5. Mejora Recepción de Mercancía
**Estado:** 🔴 Pendiente
- [ ] Revisar módulo actual de órdenes de entrada
- [ ] Consolidar proceso de recepción
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

## 🌐 Web puertodistribucion.cl

### 6. URLs Rotas (404)
**Estado:** 🔴 Pendiente
- [ ] Auditar sitio completo para encontrar URLs rotas
- [ ] Identificar enlaces internos rotos
- [ ] Configurar redirecciones 301 donde corresponda
- [ ] Implementar página 404 personalizada

### 7. SEO y Posicionamiento
**Estado:** 🔴 Pendiente
- [ ] Auditoría SEO completa del sitio
- [ ] Optimizar meta titles y descriptions
- [ ] Revisar estructura de URLs (slugs amigables)
- [ ] Agregar schema markup (productos, negocio local)
- [ ] Optimizar imágenes (alt text, compresión)
- [ ] Revisar velocidad de carga (Core Web Vitals)
- [ ] Crear/actualizar sitemap.xml
- [ ] Configurar Google Search Console
- [ ] Investigar keywords para otras áreas/búsquedas
- [ ] Considerar contenido de blog para posicionamiento

### 8. Revisión General Shopify
**Estado:** 🔴 Pendiente
- [ ] Revisar configuración actual de la tienda
- [ ] Verificar productos y precios actualizados
- [ ] Revisar flujo de checkout
- [ ] Verificar métodos de pago activos
- [ ] Revisar políticas (envío, devoluciones)
- [ ] Modificaciones pendientes según feedback cliente

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
**Estado:** ⏳ Pendiente
**Valor:** Alto — primera impresión del sistema
- [ ] Gráfico de ventas últimos 7/30 días (Chart.js)
- [ ] Top 5 productos más vendidos
- [ ] Comparativa con período anterior (%)
- [ ] Total clientes nuevos del mes
- [ ] Alertas de stock bajo

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
- [x] Actualización dependencias + tests (37 tests)
- [x] Fix datetime.utcnow() deprecated
- [x] Sync Shopify con preview
- [x] Sistema de pagos múltiples
- [x] Importación clientes desde Excel
- [x] Logging en exception handlers (2026-02-09)

---

## 📝 Notas

- **Stack:** Flask + MongoDB + Jinja2 + Alpine.js + Tailwind
- **Puerto local:** 5006
- **Producción:** sipud.cloud (VPS Hetzner 72.61.4.202)
- **Tenant:** puerto-distribucion

---

## 🎯 Siguiente Acción Sugerida

**Opción rápida:** Tarea 2 (arreglar except:pass) — mejora estabilidad
**Opción visible:** Tarea 6 (dashboard) — impacto visual alto
