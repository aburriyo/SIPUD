"""
Tests básicos para creación de la aplicación y blueprints
"""
import pytest
from app import create_app
from app.extensions import db, login_manager, mail, limiter


def test_app_creation(app):
    """Test que la app se crea correctamente"""
    assert app is not None
    assert app.config['TESTING'] is True


def test_app_config(app):
    """Test que la configuración de test está activa"""
    assert app.config['WTF_CSRF_ENABLED'] is False
    # Rate limiting stays enabled in tests (can test 429 responses)


def test_extensions_initialized(app):
    """Test que las extensiones se inicializan correctamente"""
    with app.app_context():
        # Verificar que las extensiones están inicializadas
        assert db is not None
        assert login_manager is not None
        assert mail is not None
        assert limiter is not None


def test_blueprints_registered(app):
    """Test que todos los blueprints están registrados"""
    blueprint_names = [bp.name for bp in app.blueprints.values()]
    
    # Verificar que los blueprints principales están registrados
    expected_blueprints = [
        'auth',
        'main', 
        'api',
        'reports',
        'warehouse',
        'admin',
        'customers',
        'delivery',
        'reconciliation'
    ]
    
    for bp_name in expected_blueprints:
        assert bp_name in blueprint_names, f"Blueprint '{bp_name}' no está registrado"


def test_blueprint_url_prefixes(app):
    """Test que los blueprints tienen los prefijos de URL correctos"""
    blueprints = app.blueprints
    
    # Verificar prefijos esperados
    assert blueprints['api'].url_prefix == '/api'
    assert blueprints['reports'].url_prefix == '/reports'
    assert blueprints['warehouse'].url_prefix == '/warehouse'
    assert blueprints['admin'].url_prefix == '/admin'
    assert blueprints['customers'].url_prefix == '/customers'
    assert blueprints['delivery'].url_prefix == '/delivery'
    assert blueprints['reconciliation'].url_prefix == '/reconciliation'


def test_template_filters_registered(app):
    """Test que los filtros de Jinja2 están registrados"""
    assert 'translate_status' in app.jinja_env.filters
    assert 'translate_channel' in app.jinja_env.filters


def test_error_handlers_registered(app):
    """Test que los error handlers están registrados"""
    # Verificar que existe handler para 429 (rate limit)
    assert 429 in app.error_handler_spec[None]


def test_before_request_hooks(app):
    """Test que los hooks before_request están registrados"""
    # Verificar que hay funciones registradas en before_request
    assert len(app.before_request_funcs[None]) > 0


def test_context_processors(app):
    """Test que los context processors están registrados"""
    with app.test_request_context():
        context = {}
        # Ejecutar context processors
        for func in app.template_context_processors[None]:
            context.update(func())
        
        # Verificar que inject_tenant está funcionando
        assert 'current_tenant' in context
        assert 'tenants' in context
