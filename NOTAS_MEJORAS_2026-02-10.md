# Notas de Mejoras SIPUD
**Fecha:** 2026-02-10  
**Reunión/Conversación con cliente**

---

## 1. Recepción de Mercancía (Consolidación)
- Mejorar el flujo de recepción de mercancía en SIPUD
- Consolidar el proceso actual

---

## 2. Integración con Google Sheets
- Crear conexión entre un Google Sheet y SIPUD
- SIPUD debe **leer** información del Sheet
- Usar el Sheet como fuente de datos externa

**Posible implementación:**
- API de Google Sheets desde SIPUD
- Sync periódico o en tiempo real
- Sheet como "entrada" de datos

---

## 3. Flujo de Caja
- Generar flujo de caja basado en las ventas de SIPUD
- Relacionar con ventas registradas en el sistema

---

## 4. Ventas Mayoristas ⭐
**Problema:**
- Las ventas mayoristas NO pasan por Shopify ni WhatsApp
- Se derivan por otro canal
- Actualmente no hay registro en SIPUD

**Opciones discutidas:**
1. ~~Sección/módulo aparte para mayoristas~~
2. ~~Excel separado~~
3. ✅ **Etiqueta "Venta Mayorista"** en la sección de ventas existente

**Decisión del cliente:** Mantenerlo simple → usar etiqueta en ventas

**Implementación propuesta:**
- Agregar opción de canal: `mayorista` en `sales_channel`
- O crear campo `sale_category`: `minorista` / `mayorista`
- Filtro en ventas para ver solo mayoristas
- Posible Excel dominante para input

---

## 5. Excel "Dominante"
- Considerar un Excel central que alimente al sistema
- Podría usarse para:
  - Ventas mayoristas
  - Recepción de mercancía
  - Flujo de caja

---

## Resumen de Tareas

| # | Tarea | Prioridad | Complejidad |
|---|-------|-----------|-------------|
| 1 | Etiqueta "Mayorista" en ventas | Alta | Baja |
| 2 | Integración Google Sheets → SIPUD | Media | Media |
| 3 | Mejora recepción mercancía | Media | Media |
| 4 | Reporte flujo de caja | Media | Media |

---

## Próximos Pasos
1. Definir estructura del Sheet (columnas, formato)
2. Agregar `mayorista` como canal de venta
3. Diseñar pantalla de flujo de caja
4. Revisar módulo de recepción actual
