# Inicio Rápido - Servidor MCP de SIPUD

## Configuración en 3 Pasos

### 1. Verificar que todo funciona

Ya instalamos las dependencias y probamos la conexión. Verifica que MongoDB esté corriendo:

```bash
# Debe mostrar la versión de MongoDB
mongosh --eval "db.version()"
```

### 2. Configurar Claude Desktop

**Opción A: Usando Claude Desktop App**

Edita el archivo de configuración según tu sistema operativo:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Copia el contenido de `claude_desktop_config.json` (este directorio) en ese archivo.

**Opción B: Usando Claude Code CLI**

Edita: `~/.config/claude-code/config.json`

Agrega la sección de `mcpServers` del archivo `claude_desktop_config.json`.

### 3. Reiniciar Claude

- **Claude Desktop**: Cierra completamente y vuelve a abrir
- **Claude Code**: Simplemente ejecuta `claude` de nuevo

## Verificar que Funciona

Después de reiniciar, pregúntale a Claude:

```
"¿Cuántos productos tenemos en el inventario?"
```

Claude debería responder con los datos reales de tu base de datos MongoDB.

## Comandos de Ejemplo

Prueba estos comandos con Claude:

```
"Muéstrame los productos con stock bajo"
"¿Qué productos están próximos a vencer?"
"Dame las estadísticas del dashboard"
"Muéstrame las ventas de hoy"
"Lista todos los lotes disponibles"
"¿Cuántas órdenes de compra están pendientes?"
```

## Solución de Problemas

### Claude no responde con datos del inventario

1. Verifica que Claude Desktop/Code muestre el servidor MCP conectado
2. Revisa que la ruta en `claude_desktop_config.json` sea correcta
3. Reinicia Claude Desktop completamente

### Error de conexión a MongoDB

```bash
# Verifica que MongoDB esté corriendo
mongosh

# Si no está corriendo, inícialo según tu sistema
# macOS con Homebrew:
brew services start mongodb-community

# Linux con systemd:
sudo systemctl start mongod
```

### Configuración del Tenant

Por defecto usa `puerto-distribucion`. Si necesitas cambiar el tenant predeterminado, edita `MCP_DEFAULT_TENANT` en el archivo de configuración.

## Herramientas Disponibles

El servidor MCP expone 10 herramientas:

1. **get_products** - Lista de productos con stock
2. **get_product_detail** - Detalles de un producto específico
3. **get_lots** - Lotes de inventario (FIFO)
4. **get_expiring_products** - Productos próximos a vencer
5. **get_sales** - Ventas con filtros
6. **get_sale_detail** - Detalles de una venta
7. **get_inbound_orders** - Órdenes de compra
8. **get_wastage** - Registro de mermas
9. **get_dashboard_stats** - Estadísticas generales
10. **list_tenants** - Lista de tenants

## Características de Seguridad

- ✓ Solo lectura (no modifica datos)
- ✓ Aislamiento por tenant
- ✓ Validación de parámetros
- ✓ Conexión local a MongoDB

## Próximos Pasos

Para más información, consulta `README.md` en este mismo directorio.
