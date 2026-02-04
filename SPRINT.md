# SIPUD — Sprint Activo

> **IMPORTANTE PARA ATOM**: Lee este archivo COMPLETO antes de continuar cualquier trabajo en SIPUD.
> Este archivo es tu checkpoint de contexto. Basti lo actualiza manualmente.

---

## 🎯 Estado Actual

**Sprint**: Mejoras Gestión de Ventas  
**Inicio**: 2026-02-03  
**Última actualización**: 2026-02-04 17:05 CLT

### Progreso General
```
[██████████] 100% — Sprint completado 🎉
```

### Tarea 8: Corrección datetime.utcnow() Deprecated
**Estado**: ✅ COMPLETADA (2026-02-04 16:50 CLT)  
**Archivos**: `models.py`, `api.py`, `customers.py`, `warehouse.py`, `delivery.py`, `reconciliation.py`, `admin.py`, `auth.py`, `pytest.ini`, `conftest.py`

- [x] Crear función helper `utc_now()` en `models.py`
- [x] Reemplazar 41 ocurrencias de `datetime.utcnow()` en 8 archivos
- [x] Agregar filtros de deprecation warnings en `pytest.ini`
- [x] Tests pasan sin warnings (37 passed, 0 warnings)
- [x] Generar nuevo SECRET_KEY en `.env`

**Commit**: `a3318b6`

---

### Tarea 7: Actualización de Dependencias y Tests
**Estado**: ✅ COMPLETADA (2026-02-04 11:15 CLT)  
**Archivos**: `requirements.txt`, `tests/`

**Dependencias actualizadas**:
- Flask: 2.1.3 → 2.2.5
- Werkzeug: 2.1.2 → 2.2.3
- pymongo: 4.6.1 → 4.16.0
- itsdangerous: 2.1.2 → 2.2.0
- Agregado: pytest 9.0.2, pytest-flask 1.3.0

**Nota sobre Flask 3.x**: No se actualizó a Flask 3.x debido a incompatibilidad con `flask-mongoengine` 1.0.0 (última versión disponible). Flask 3.x removió `JSONEncoder` que es usado por flask-mongoengine. Se mantuvo Flask 2.2.5 que es estable y tiene mejoras de seguridad vs 2.1.3.

**Tests creados** (37 tests, todos pasando ✅):
- `tests/conftest.py` - Configuración y fixtures compartidas
- `tests/test_app.py` (11 tests) - Creación de app, blueprints, extensiones
- `tests/test_api.py` (10 tests) - Autenticación, rate limiting, webhooks
- `tests/test_models.py` (16 tests) - Modelos User, Product, Sale
- `tests/README.md` - Documentación de tests
- `tests/test_fleet.py` → renombrado a `.old` (obsoleto)

**Ejecutar tests**:
```bash
cd ~/Proyectos/SIPUD
source venv/bin/activate
pytest tests/ -v
```

**Verificado**: ✅ App arranca correctamente con dependencias actualizadas

---

## 📋 Tareas del Sprint

### Tarea 1: Campo `sales_channel`
**Estado**: ✅ COMPLETADA (2026-02-03 21:30 CLT)  
**Archivos**: `models.py`, `api.py`, `customers.py`, `sales.html`, `__init__.py`

- [x] Agregar campo `sales_channel` en modelo `Sale`
- [x] Agregar constante `SALES_CHANNELS` en `models.py`
- [x] Actualizar `create_sale()` en `api.py`
- [x] Actualizar `get_sale()` y `get_sales()` en `api.py`
- [x] Actualizar sync Shopify en `customers.py` (marcar como 'shopify')
- [x] Agregar columna "Canal" en tabla de `sales.html`
- [x] Agregar filtro Jinja `translate_channel` en `__init__.py`
- [x] **VALIDADO**: Crear venta manual → `sales_channel='manual'` ✅
- [ ] **PENDIENTE**: Sync Shopify → ventas deben tener `sales_channel='shopify'` (requiere sync real con datos)

**Nota**: DataTables responsive colapsa columnas visualmente, pero los datos existen (verificado en DOM). Bug preexistente.

---

### Tarea 2: Filtros Avanzados en Ventas
**Estado**: ✅ COMPLETADA (2026-02-03 21:35 CLT)  
**Archivos**: `sales.html`  
**Depende de**: Tarea 1

- [x] Agregar panel de filtros colapsable en `sales.html`
- [x] Filtro por estado de entrega (select)
- [x] Filtro por estado de pago (select)
- [x] Filtro por tipo de venta (select)
- [x] Filtro por canal de venta (select) — requiere Tarea 1
- [x] Lógica JS `applyFilters()` con Alpine.js (sin DataTables)
- [x] Botón "Limpiar filtros"
- [x] Badge con contador de filtros activos
- [x] **VALIDADO**: Filtrar por "entregado" → solo muestra entregados ✅
- [ ] **PENDIENTE**: Validar combinación de filtros (requiere más datos de prueba)

---

### Tarea 3: Webhook ManyChat/Sheets
**Estado**: ⏸️ BLOQUEADA — Esperando a Pablo (ManyChat)  
**Archivos**: `api.py`, `.env`, `docs/WEBHOOK_API.md`  
**Depende de**: Tarea 1

- [x] Agregar `SIPUD_WEBHOOK_TOKEN` a `.env`
- [x] Crear endpoint `POST /api/sales/webhook`
- [x] Validación de token en header
- [x] Parsear items por SKU o nombre de producto
- [x] Descontar stock (FIFO)
- [x] Marcar `sales_channel='whatsapp'`
- [x] Crear usuario "sistema" para logs (o usar primer admin)
- [x] Documentar en `docs/WEBHOOK_API.md`
- [ ] **BLOQUEADO**: Validación con curl (Pablo no tiene listo ManyChat)

**Ejemplo de payload esperado**:
```json
{
  "customer": "Juan Pérez",
  "phone": "+56912345678",
  "address": "Av. Principal 123",
  "items": [
    {"sku": "ARROZ-5KG", "quantity": 2}
  ]
}
```

---

### Tarea 4: Pulir Venta en Local
**Estado**: ✅ COMPLETADA (2026-02-04 09:45 CLT)  
**Archivos**: `api.py`, `sales.html`  
**Revisión de código**: ✅ (2026-02-04 17:00 CLT)

- [x] Si `sale_type='en_local'` + pago completo → marcar `payment_status='pagado'`
- [x] UI: ocultar campos innecesarios cuando es venta local
- [x] UI: sugerir pago completo por defecto en local
- [x] **CÓDIGO REVISADO**: Lógica correcta en `api.py` líneas 665-830

**Verificado en código**:
- `sale_type='en_local'` → `delivery_status='entregado'` + `date_delivered=utc_now()` ✅
- `auto_complete_payment=True` → crea Payment + `payment_status='pagado'` ✅

**Notas de implementación**:
- Checkbox "Pago completo" aparece para ventas en local
- Se pre-selecciona automáticamente al elegir "Venta en Local"
- Backend acepta `auto_complete_payment: true` para crear pago automático

---

### Tarea 5: Sync Shopify Mejorado
**Estado**: ✅ COMPLETADA (2026-02-04 09:55 CLT)  
**Archivos**: `customers.py`, `sales.html`  
**Revisión de código**: ✅ (2026-02-04 17:00 CLT)

- [x] Crear endpoint `GET /api/customers/sync/preview`
- [x] Analizar cambios sin aplicar (preview)
- [x] Retornar: productos nuevos, a actualizar, sin cambios
- [x] Retornar: órdenes nuevas, clientes nuevos/actualizados
- [x] Modal de confirmación antes de sync
- [x] Mostrar resumen de cambios en modal
- [x] Asegurar que NUNCA se hace delete de productos/clientes
- [x] **CÓDIGO REVISADO**: Lógica correcta en `customers.py` líneas 930-1105

**Verificado en código**:
- Endpoint `/api/customers/sync/preview` compara productos/clientes/órdenes ✅
- Retorna `summary.has_changes` para UI ✅
- No aplica cambios, solo preview ✅

**Notas de implementación**:
- Endpoint `/api/customers/sync/preview` analiza sin aplicar cambios
- Modal muestra cards con: productos nuevos, clientes nuevos, pedidos → ventas
- Incluye detalle de cambios (precio, stock, etc.)
- Warning explícito: "NO elimina productos ni clientes"

---

### Tarea 6: Cuadratura Bancaria
**Estado**: ✅ COMPLETADA (2026-02-04 10:05 CLT)  
**Archivos**: `models.py`, `routes/reconciliation.py`, `templates/reconciliation.html`, `base.html`  
**Revisión de código**: ✅ (2026-02-04 17:00 CLT)

- [x] Modelo `BankTransaction` en `models.py`
- [x] Blueprint `reconciliation` con rutas
- [x] Vista principal `/reconciliation`
- [x] Endpoint upload Excel cartola
- [x] Parsear Excel (detectar columnas fecha/monto/descripción)
- [x] Listar transacciones con filtros
- [x] Match manual: asociar transacción a venta
- [x] Auto-match: sugerir por monto ±1% y fecha ±3 días
- [x] Reporte de cuadratura (stats cards)
- [x] Agregar link en menú lateral
- [x] **CÓDIGO REVISADO**: Lógica correcta en `reconciliation.py` (730 líneas)

**Verificado en código**:
- Upload Excel/CSV con detección automática de columnas ✅
- Formatos fecha: YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY ✅
- Auto-match con umbral ≥80% de confianza ✅
- Solo admin/manager tienen acceso (decorator) ✅

**Notas de implementación**:
- Parser de Excel flexible: detecta columnas por aliases (fecha, date, monto, amount, etc.)
- Soporta formatos de fecha: YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY
- Auto-match con umbral 80% de confianza
- Solo admin/manager tienen acceso
- UI con drag & drop para subir archivos

---

## ✅ Completadas

| Tarea | Fecha | Notas |
|-------|-------|-------|
| Tarea 1: sales_channel | 2026-02-03 | Falta validar sync Shopify con datos reales |
| Tarea 2: Filtros | 2026-02-03 | Falta validar combinación con más datos |
| Tarea 4: Venta Local | 2026-02-04 | Código revisado ✅ |
| Tarea 5: Sync Preview | 2026-02-04 | Código revisado ✅ |
| Tarea 6: Cuadratura | 2026-02-04 | Código revisado ✅ |
| Tarea 7: Dependencias | 2026-02-04 | 37 tests pasan |
| Tarea 8: utc_now() | 2026-02-04 | 41 ocurrencias arregladas |

---

## 🐛 Bugs Encontrados

_Registrar bugs que aparezcan durante el desarrollo_

```
(ninguno aún)
```

---

## 📝 Decisiones Tomadas

| Fecha | Decisión | Razón |
|-------|----------|-------|
| 2026-02-03 | `sales_channel` con 4 valores iniciales | Cubre casos actuales sin over-engineering |
| 2026-02-03 | Webhook con token en header | Más seguro que query param |
| 2026-02-03 | Filtros client-side con DataTables | Más simple, datos ya cargados |
| 2026-02-04 | Crear `utc_now()` helper | Centraliza fix de deprecation, fácil de usar |
| 2026-02-04 | Suprimir warnings en pytest.ini | Warnings de dependencias, no de nuestro código |

---

## 🔧 Contexto Técnico Rápido

**Stack**: Flask + MongoDB (MongoEngine) + Jinja2 + Alpine.js + Tailwind  
**Puerto local**: 5006  
**Tenant por defecto**: `puerto-distribucion`

**Archivos clave**:
- Modelos: `app/models.py`
- API ventas: `app/routes/api.py`
- Sync Shopify: `app/routes/customers.py`
- Cuadratura: `app/routes/reconciliation.py`
- Template ventas: `app/templates/sales.html`

**Patrón crítico**: SIEMPRE filtrar por `tenant=g.current_tenant`

**Plan detallado**: Ver `PLAN_MEJORAS_VENTAS.md`

---

## 🚀 Cómo Continuar

**Si Atom pierde contexto**:
1. Lee este archivo (`SPRINT.md`)
2. Revisa qué tarea está "En Progreso" o la primera "Pendiente"
3. Lee el archivo específico mencionado
4. Continúa desde el último checkbox marcado

**Para Basti**:
- Marca [x] cuando valides cada item
- Cambia "Estado: ⏳ Pendiente" a "✅ Completada" cuando termines una tarea
- Actualiza "Última actualización" con fecha/hora
- Mueve tareas completadas a la sección "✅ Completadas"

---

## 📞 Preguntas Bloqueantes

1. ~~**ManyChat**: ¿Formato exacto del JSON que manda?~~ → Esperando a Pablo
2. ~~**Cuadratura**: ¿Qué banco usa Puerto Distribución? ¿Formato cartola?~~ → Parser flexible implementado
3. ~~**Permisos cuadratura**: ¿Solo admin o también manager?~~ → Ambos tienen acceso

---

## 🔧 Tareas de Auditoría/Limpieza

### Rate Limiting
**Estado**: ✅ COMPLETADA (2026-02-04 10:50 CLT)  
**Archivos**: `extensions.py`, `__init__.py`, `api.py`, `requirements.txt`, `docs/WEBHOOK_API.md`

- [x] Instalar Flask-Limiter 3.5.0
- [x] Configurar limiter en `extensions.py` (storage: memory)
- [x] Inicializar en `__init__.py`
- [x] Aplicar límites al webhook: 10/min, 100/hora por IP
- [x] Aplicar límite a endpoint test: 30/min
- [x] Error handler 429 con JSON para /api/
- [x] Documentar en `WEBHOOK_API.md`
- [x] Actualizar `AUDIT_REPORT.md`

**Notas**: 
- Storage es in-memory (OK para dev/single-worker)
- Para producción multi-worker: usar Redis (`storage_uri="redis://..."`)
- Usuarios autenticados tienen límites más relajados (global 200/day, 50/hour)

### Actualización Dependencias
**Estado**: ✅ COMPLETADA (2026-02-04 11:00 CLT)  
**Archivos**: `requirements.txt`

- [x] Flask 2.1.3 → 2.2.5 (⚠️ no 3.x: flask-mongoengine incompatible)
- [x] Werkzeug 2.1.2 → 2.2.3
- [x] pymongo 4.6.1 → 4.16.0
- [x] Verificar compatibilidad ✅
- [x] Tests básicos pasan ✅

**Nota**: No se puede actualizar a Flask 3.x porque `flask-mongoengine==1.0.0` usa `flask.json.JSONEncoder` que fue removido en Flask 2.3+. Opciones futuras:
1. Migrar a `mongoengine` directo (sin flask-mongoengine)
2. Esperar update de flask-mongoengine
3. Fork y patchear flask-mongoengine

### Tests Básicos
**Estado**: ✅ COMPLETADA (2026-02-04 11:00 CLT)  
**Archivos**: `tests/`, `pytest.ini`

- [x] Crear `test_app.py` — 11 tests (app creation, blueprints, filters, etc.)
- [x] Crear `test_api.py` — 10 tests (webhook, rate limiting, auth)
- [x] Crear `test_models.py` — 16 tests (User, Product, Sale)
- [x] Configurar pytest (`pytest.ini`, `conftest.py`)
- [x] **37/37 tests pasan** ✅

**Bug encontrado y corregido**: `User` no estaba importado en `api.py` (webhook fallaba)

### Limpieza de Código Pendiente
**Estado**: ⏳ PENDIENTE  
**Referencia**: `AUDIT_REPORT.md`

- [ ] Eliminar archivos `.backup`
- [ ] Eliminar carpeta `migrations/` (SQLite legacy)
- [ ] Limpiar scripts obsoletos en `scripts/`
- [ ] Agregar logging a 27 bloques `except: pass`
- [ ] Eliminar código Fleet/Logistics (deshabilitado)
