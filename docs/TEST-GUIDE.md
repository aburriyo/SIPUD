# 🧪 Guía de Pruebas - Correcciones SIPUD

## ⚡ Inicio Rápido

```bash
# 1. Ir al directorio del proyecto
cd /Users/bchavez/Proyectos/SIPUD

# 2. Activar entorno virtual (si usas uno)
source venv/bin/activate

# 3. Iniciar la aplicación
python run.py
```

---

## 🐛 Bug #1: Stock Inicial en Productos

### Escenario de Prueba
**Objetivo:** Crear un producto nuevo con stock inicial

**Pasos:**
1. Abrir navegador en `http://localhost:5000`
2. Login con usuario admin
3. Ir a "Productos" (menú lateral)
4. Clic en "Nuevo Producto"
5. Llenar formulario:
   - **Nombre:** Producto de Prueba
   - **SKU:** TEST-001
   - **Categoría:** Otros
   - **Precio Base:** 1000
   - **Stock Crítico:** 10
   - **📦 Stock Inicial:** 50
   - **Código de Lote:** LOT-TEST-001 (opcional)
6. Clic en "Guardar"

**Resultado Esperado:**
- ✅ Producto creado exitosamente
- ✅ En la lista aparece "50 Unidades" (con badge verde)
- ✅ En el log de actividad: "Creó producto ... stock inicial: 50"

**Verificación Adicional:**
```python
# En consola Python
from app.models import Product, Lot
product = Product.objects(sku='TEST-001').first()
print(f"Stock total: {product.total_stock}")  # Debe ser 50
print(f"Lotes: {product.lots.count()}")  # Debe ser 1
lot = product.lots.first()
print(f"Lote: {lot.lot_code}, Cantidad: {lot.quantity_current}")
```

---

## 🐛 Bug #2: Recepción de Mercancía

### Escenario de Prueba
**Objetivo:** Confirmar recepción y seleccionar productos

**Pasos:**
1. Ir a "Bodega" → "Recepción de Mercancía"
2. Si no hay pedidos pendientes, crear uno:
   - Ir a "Bodega" → "Pedidos"
   - Clic "Nuevo Pedido"
   - Proveedor: "Proveedor Test"
   - Nº Factura: "FAC-001"
   - Total: 100000
   - Guardar
3. Volver a "Recepción de Mercancía"
4. Clic en "Confirmar Recepción" del pedido creado
5. Clic en "Agregar Producto"
6. **Verificar que el selector de productos NO está vacío**
7. Seleccionar un producto
8. Ingresar cantidad: 20
9. Código de lote: LOT-REC-001
10. Clic "Confirmar Recepción"

**Resultado Esperado:**
- ✅ El selector muestra todos los productos disponibles
- ✅ Se puede seleccionar un producto
- ✅ Recepción se confirma sin errores
- ✅ El stock del producto se incrementa en 20 unidades

**Verificación del Bug Anterior:**
Si el bug NO estuviera corregido:
- ❌ El selector de productos estaría vacío
- ❌ No se podría seleccionar ningún producto
- ❌ JavaScript console mostraría `this.products = undefined`

---

## 🔍 Verificación en Base de Datos

```python
# Abrir shell de Python
python
>>> from app import create_app
>>> from app.models import Product, Lot, InboundOrder
>>> app = create_app()
>>> with app.app_context():
...     # Ver productos con stock inicial
...     products = Product.objects()
...     for p in products:
...         print(f"{p.name}: {p.total_stock} unidades")
...     
...     # Ver órdenes de "Stock Inicial"
...     init_orders = InboundOrder.objects(supplier_name="Stock Inicial")
...     print(f"\nÓrdenes de Stock Inicial: {init_orders.count()}")
...     
...     # Ver lotes creados hoy
...     from datetime import datetime
...     today = datetime.now().date()
...     lots_today = Lot.objects(created_at__gte=today)
...     print(f"Lotes creados hoy: {lots_today.count()}")
```

---

## 🚨 Problemas Comunes

### Error: "No module named 'app'"
**Solución:**
```bash
export PYTHONPATH=/Users/bchavez/Proyectos/SIPUD:$PYTHONPATH
```

### Error: "MongoEngine connection error"
**Solución:** Verificar que MongoDB está corriendo:
```bash
# macOS con Homebrew
brew services start mongodb-community
```

### Los productos no se muestran en recepción
**Verificación:**
1. Abrir DevTools (F12) → Console
2. Buscar errores de JavaScript
3. Verificar que `/api/products` retorna datos:
```javascript
fetch('/api/products').then(r => r.json()).then(d => console.log(d))
```

---

## ✅ Checklist de Validación

- [ ] **Bug #1:** Crear producto con stock inicial funciona
- [ ] **Bug #1:** Stock se muestra correctamente en la lista
- [ ] **Bug #1:** Se crea un lote asociado al producto
- [ ] **Bug #1:** El log registra el stock inicial
- [ ] **Bug #2:** El selector de productos NO está vacío
- [ ] **Bug #2:** Se pueden seleccionar productos
- [ ] **Bug #2:** La recepción se confirma sin errores
- [ ] **Bug #2:** El stock se actualiza correctamente
- [ ] **General:** No hay errores en la consola del navegador
- [ ] **General:** No hay errores en el log de Flask

---

## 📸 Capturas Esperadas

### Bug #1 - Formulario con Stock Inicial
![Expected: Campo "📦 Stock Inicial (Opcional)" visible al crear producto]

### Bug #2 - Selector de Productos
![Expected: Dropdown con lista de productos disponibles]

---

## 🔄 Reversión (si algo falla)

```bash
cd /Users/bchavez/Proyectos/SIPUD

# Revertir todos los cambios
cp app/templates/products.html.backup app/templates/products.html
cp app/routes/api.py.backup app/routes/api.py
cp app/templates/warehouse/receiving.html.backup app/templates/warehouse/receiving.html

# Reiniciar Flask
# Ctrl+C y luego python run.py
```

---

**¡Listo para probar!** 🚀
