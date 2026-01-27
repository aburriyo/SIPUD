# SIPUD Inventory MCP Server

Servidor MCP (Model Context Protocol) para el sistema de inventario SIPUD. Permite a Claude acceder en tiempo real a todos los datos del inventario, ventas, órdenes y almacén directamente desde MongoDB.

## Características

El servidor MCP expone 10 herramientas (tools) que permiten:

### Gestión de Productos
- **`get_products`**: Obtener lista de productos con stock actual
  - Filtros: categoría, búsqueda por nombre/SKU, solo productos con stock bajo
- **`get_product_detail`**: Detalles completos de un producto incluyendo lotes y componentes de bundle

### Gestión de Inventario (FIFO)
- **`get_lots`**: Consultar lotes de inventario con cantidades actuales
  - Filtros: por producto, solo lotes disponibles
- **`get_expiring_products`**: Productos próximos a vencer (configurable en días)

### Ventas
- **`get_sales`**: Lista de ventas con filtros
  - Filtros: rango de fechas, estado, límite de resultados
- **`get_sale_detail`**: Detalles completos de una venta con todos sus items

### Órdenes de Compra
- **`get_inbound_orders`**: Órdenes de entrada de proveedores
  - Filtros: estado (pending/received/paid), límite de resultados

### Mermas y Desperdicios
- **`get_wastage`**: Registro de mermas
  - Filtros: producto, razón (vencido/dañado/perdido/robo/otro), fechas

### Dashboard
- **`get_dashboard_stats`**: Estadísticas generales del sistema
  - Total de productos, alertas de stock bajo, órdenes pendientes, ventas recientes, valor del inventario

### Multi-Tenancy
- **`list_tenants`**: Listar todos los tenants disponibles

## Instalación

### 1. Instalar Dependencias

Desde el directorio `mcp_server`:

```bash
pip install -r requirements.txt
```

O instalar manualmente:

```bash
pip install mcp pymongo mongoengine python-dotenv
```

### 2. Configurar Variables de Entorno

Crea un archivo `.env` en el directorio raíz del proyecto (o configura las variables en el sistema):

```env
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=inventory_db
MCP_DEFAULT_TENANT=puerto-distribucion
```

### 3. Verificar MongoDB

Asegúrate de que MongoDB esté corriendo:

```bash
# Verificar que MongoDB esté activo
mongosh --eval "db.version()"
```

## Configuración en Claude Desktop

### Para Claude Desktop App

Edita o crea el archivo de configuración de Claude Desktop:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

Agrega la siguiente configuración:

```json
{
  "mcpServers": {
    "sipud-inventory": {
      "command": "python",
      "args": [
        "/ruta/completa/a/SIPUD/mcp_server/server.py"
      ],
      "env": {
        "MONGODB_HOST": "localhost",
        "MONGODB_PORT": "27017",
        "MONGODB_DB": "inventory_db",
        "MCP_DEFAULT_TENANT": "puerto-distribucion"
      }
    }
  }
}
```

**IMPORTANTE**: Reemplaza `/ruta/completa/a/SIPUD` con la ruta absoluta real al proyecto.

### Para Claude Code (CLI)

Crea o edita `~/.config/claude-code/config.json`:

```json
{
  "mcpServers": {
    "sipud-inventory": {
      "command": "python",
      "args": [
        "/Users/bchavez/Proyectos/SIPUD/mcp_server/server.py"
      ],
      "env": {
        "MONGODB_HOST": "localhost",
        "MONGODB_PORT": "27017",
        "MONGODB_DB": "inventory_db",
        "MCP_DEFAULT_TENANT": "puerto-distribucion"
      }
    }
  }
}
```

## Uso

### Verificar Conexión

Después de configurar, reinicia Claude Desktop o Claude Code. El servidor MCP se iniciará automáticamente cuando Claude lo necesite.

### Ejemplos de Uso con Claude

Una vez configurado, puedes preguntarle a Claude:

```
"¿Cuántos productos tenemos en stock?"
"Muéstrame los productos con stock bajo"
"¿Qué productos están próximos a vencer en los próximos 15 días?"
"Dame los detalles del producto con ID 507f1f77bcf86cd799439011"
"Muéstrame las ventas de la última semana"
"¿Cuántas órdenes de compra están pendientes?"
"Dame las estadísticas del dashboard"
```

Claude automáticamente usará las herramientas MCP apropiadas para consultar la base de datos en tiempo real.

## Multi-Tenancy

El servidor soporta múltiples tenants. Por defecto usa el tenant configurado en `MCP_DEFAULT_TENANT`, pero puedes especificar un tenant diferente en cada consulta:

```
"Muéstrame los productos del tenant 'otro-negocio'"
"Lista todos los tenants disponibles"
```

## Arquitectura

```
┌─────────────────┐
│  Claude Desktop │
│   Claude Code   │
└────────┬────────┘
         │ MCP Protocol
         │ (stdio)
┌────────▼────────┐
│  MCP Server     │
│  (server.py)    │
└────────┬────────┘
         │ MongoEngine
         │ ODM
┌────────▼────────┐
│    MongoDB      │
│ inventory_db    │
└─────────────────┘
```

## Características de Seguridad

- **Aislamiento por Tenant**: Todas las consultas filtran automáticamente por tenant
- **Solo Lectura**: El servidor MCP solo permite consultas (GET), no modificaciones
- **Validación de Datos**: Validación de ObjectIds y parámetros antes de consultar

## Troubleshooting

### Error: "Failed to connect to MongoDB"

- Verifica que MongoDB esté corriendo: `mongosh`
- Revisa las variables de entorno `MONGODB_HOST`, `MONGODB_PORT`, `MONGODB_DB`
- Verifica permisos de conexión a MongoDB

### Error: "Tenant 'xxx' not found"

- Verifica que el tenant existe en la base de datos
- Usa `list_tenants` para ver los tenants disponibles
- Configura `MCP_DEFAULT_TENANT` con un tenant válido

### Claude no muestra las herramientas MCP

- Reinicia Claude Desktop completamente
- Verifica que la ruta en `claude_desktop_config.json` sea absoluta y correcta
- Revisa los logs de Claude Desktop (Help > Show Logs)
- Verifica que Python esté en el PATH del sistema

### Error: "No module named 'mcp'"

- Instala las dependencias: `pip install -r mcp_server/requirements.txt`
- Verifica que estás usando el mismo Python que Claude Desktop

## Desarrollo

### Agregar Nuevas Herramientas

Para agregar una nueva herramienta MCP:

1. Define la herramienta en `handle_list_tools()`:
```python
types.Tool(
    name="mi_nueva_herramienta",
    description="Descripción de la herramienta",
    inputSchema={...}
)
```

2. Implementa el handler en `handle_call_tool()`:
```python
elif name == "mi_nueva_herramienta":
    # Implementación
    result = "..."
    return [types.TextContent(type="text", text=result)]
```

### Testing Manual

Prueba el servidor directamente:

```bash
cd /Users/bchavez/Proyectos/SIPUD
python mcp_server/server.py
```

El servidor usará stdio, así que necesitarás un cliente MCP para probarlo adecuadamente.

## Limitaciones Actuales

- **Solo Lectura**: No permite crear, actualizar o eliminar datos (por diseño de seguridad)
- **Paginación Básica**: Usa límites simples, no paginación completa
- **Sin Caché**: Cada consulta va directo a MongoDB (puede agregarse Redis en el futuro)

## Roadmap

- [ ] Agregar caché con Redis para consultas frecuentes
- [ ] Implementar paginación completa con cursores
- [ ] Agregar herramientas de escritura con permisos y validación
- [ ] Métricas y logging de uso del MCP server
- [ ] Soporte para agregaciones complejas de MongoDB

## Soporte

Para problemas o preguntas:
1. Revisa la sección de Troubleshooting arriba
2. Verifica los logs de Claude Desktop
3. Revisa que MongoDB esté corriendo y accesible

## Licencia

Este servidor MCP es parte del proyecto SIPUD.
