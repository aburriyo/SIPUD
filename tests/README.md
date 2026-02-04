# Tests de SIPUD

Tests básicos para el proyecto SIPUD usando pytest.

## Estructura

- `conftest.py` - Configuración compartida y fixtures
- `test_app.py` - Tests de creación de app y blueprints
- `test_api.py` - Tests de API, autenticación y rate limiting
- `test_models.py` - Tests de modelos (User, Product, Sale)
- `test_fleet.py.old` - Test obsoleto (ignorado)

## Ejecutar Tests

```bash
# Todos los tests
pytest tests/ -v

# Un archivo específico
pytest tests/test_models.py -v

# Un test específico
pytest tests/test_models.py::TestUserModel::test_user_has_permission -v

# Con coverage
pytest tests/ --cov=app --cov-report=html
```

## Configuración

Los tests usan una configuración separada (`TestConfig` en `conftest.py`):
- Base de datos: `sipud_test` (local)
- CSRF deshabilitado
- Rate limiting deshabilitado
- Modo TESTING activo

## Estado Actual

✅ **37 tests pasando** (Feb 2026)

### Cobertura

- **test_app.py** (11 tests):
  - Creación de aplicación
  - Inicialización de extensiones
  - Registro de blueprints
  - Filtros Jinja2
  - Error handlers
  - Context processors

- **test_api.py** (10 tests):
  - Autenticación requerida
  - Validación de token en webhook
  - Rate limiting configurado
  - Validación de payloads
  - Formato JSON de respuestas

- **test_models.py** (16 tests):
  - User: creación, passwords, permisos por rol
  - Product: creación, SKU, stock tracking
  - Sale: creación, estados, canales
  - Tenant: multi-tenancy básico

## Notas

- Los tests NO requieren MongoDB corriendo (usan mocks/instancias en memoria)
- Los tests NO alteran la base de datos de producción
- Warnings de deprecación son normales (Python 3.13 + Werkzeug 2.2)
