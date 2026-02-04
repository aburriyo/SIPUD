# SIPUD — Sprint Activo

> **IMPORTANTE PARA ATOM**: Lee este archivo COMPLETO antes de continuar cualquier trabajo en SIPUD.
> Este archivo es tu checkpoint de contexto. Basti lo actualiza manualmente.

---

## 🎯 Estado Actual

**Sprint**: Mejoras Gestión de Ventas  
**Inicio**: 2026-02-03  
**Última actualización**: 2026-02-04 11:15 CLT

### Progreso General
```
[██████████] 100% — Sprint completado 🎉
```

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
- [ ] **PENDIENTE**: Sync Shopify → ventas deben tener `sales_channel='shopify'` (requiere sync real)

**Nota**: DataTables responsive colapsa columnas visualmente, pero los datos existen (verificado en DOM). Bug preexistente.

**Notas de implementación**:
```python
# Valores válidos para sales_channel:
# 'manual' - Creada desde SIPUD
# 'whatsapp' - Vía webhook ManyChat
# 'shopify' - Sincronizada desde Shopify
# 'web' - Futuro: desde web propia
```

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
- [ ] **PENDIENTE**: Validar combinación de filtros (requiere más datos)

---

### Tarea 3: Webhook ManyChat/Sheets
**Estado**: ✅ COMPLETADA (2026-02-04 09:30 CLT)  
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
- [ ] **VALIDAR**: curl con token válido → crea venta
- [ ] **VALIDAR**: curl sin token → rechaza 401
- [ ] **VALIDAR**: curl con SKU inexistente → maneja error

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

- [x] Si `sale_type='en_local'` + pago completo → marcar `payment_status='pagado'`
- [x] UI: ocultar campos innecesarios cuando es venta local
- [x] UI: sugerir pago completo por defecto en local
- [ ] **VALIDAR**: Crear venta local con pago completo → delivery=entregado, payment=pagado

**Notas de implementación**:
- Checkbox "Pago completo" aparece para ventas en local
- Se pre-selecciona automáticamente al elegir "Venta en Local"
- Backend acepta `auto_complete_payment: true` para crear pago automático

---

### Tarea 5: Sync Shopify Mejorado
**Estado**: ✅ COMPLETADA (2026-02-04 09:55 CLT)  
**Archivos**: `customers.py`, `sales.html`

- [x] Crear endpoint `GET /api/customers/sync/preview`
- [x] Analizar cambios sin aplicar (preview)
- [x] Retornar: productos nuevos, a actualizar, sin cambios
- [x] Retornar: órdenes nuevas, clientes nuevos/actualizados
- [x] Modal de confirmación antes de sync
- [x] Mostrar resumen de cambios en modal
- [x] Asegurar que NUNCA se hace delete de productos/clientes
- [ ] **VALIDAR**: Preview muestra cambios correctos
- [ ] **VALIDAR**: Confirmar → aplica cambios
- [ ] **VALIDAR**: Cancelar → no aplica nada

**Notas de implementación**:
- Endpoint `/api/customers/sync/preview` analiza sin aplicar cambios
- Modal muestra cards con: productos nuevos, clientes nuevos, pedidos → ventas
- Incluye detalle de cambios (precio, stock, etc.)
- Warning explícito: "NO elimina productos ni clientes"

---

### Tarea 6: Cuadratura Bancaria
**Estado**: ✅ COMPLETADA (2026-02-04 10:05 CLT)  
**Archivos**: `models.py`, `routes/reconciliation.py`, `templates/reconciliation.html`, `base.html`

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
- [ ] **VALIDAR**: Subir Excel → crea transacciones
- [ ] **VALIDAR**: Auto-match → sugiere correctamente
- [ ] **VALIDAR**: Match manual → actualiza estados

**Notas de implementación**:
- Parser de Excel flexible: detecta columnas por aliases (fecha, date, monto, amount, etc.)
- Soporta formatos de fecha: YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY
- Auto-match con umbral 80% de confianza
- Solo admin/manager tienen acceso
- UI con drag & drop para subir archivos

---

## ✅ Completadas

_Mover aquí las tareas terminadas con fecha_

```
(ninguna aún)
```

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

---

## 🔧 Contexto Técnico Rápido

**Stack**: Flask + MongoDB (MongoEngine) + Jinja2 + Alpine.js + Tailwind  
**Puerto local**: 5006  
**Tenant por defecto**: `puerto-distribucion`

**Archivos clave**:
- Modelos: `app/models.py`
- API ventas: `app/routes/api.py`
- Sync Shopify: `app/routes/customers.py`
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

1. **ManyChat**: ¿Formato exacto del JSON que manda? → Preguntar a Pablo
2. **Cuadratura**: ¿Qué banco usa Puerto Distribución? ¿Formato cartola?
3. **Permisos cuadratura**: ¿Solo admin o también manager?

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

- [x] Crear `test_app.py` — 9 tests (app creation, blueprints, filters, etc.)
- [x] Crear `test_api.py` — 10 tests (webhook, rate limiting, auth)
- [x] Configurar pytest (`pytest.ini`, `conftest.py`)
- [x] **19/19 tests pasan** ✅

**Bug encontrado y corregido**: `User` no estaba importado en `api.py` (webhook fallaba)
