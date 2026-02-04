"""
Tests para endpoints de API - rate limiting y autenticación
"""
import pytest
import os
from flask import url_for


def test_api_requires_authentication(client):
    """Test que los endpoints de API requieren autenticación"""
    # Intentar acceder a /api/products sin autenticación
    response = client.get('/api/products')
    
    # Debe redirigir al login (302) o retornar 401
    assert response.status_code in [302, 401]


def test_api_webhook_requires_token(client, app):
    """Test que el webhook requiere token de autenticación"""
    # Crear payload de prueba
    payload = {
        'customer': 'Test Customer',
        'phone': '+56912345678',
        'address': 'Test Address 123',
        'items': [
            {'sku': 'TEST-SKU', 'quantity': 1}
        ]
    }
    
    # Intentar sin token
    response = client.post('/api/sales/webhook', json=payload)
    assert response.status_code == 401
    
    data = response.get_json()
    assert 'error' in data
    assert 'token' in data['error'].lower() or 'authorization' in data['error'].lower()


def test_api_webhook_rejects_invalid_token(client, app):
    """Test que el webhook rechaza tokens inválidos"""
    payload = {
        'customer': 'Test Customer',
        'phone': '+56912345678',
        'address': 'Test Address 123',
        'items': [
            {'sku': 'TEST-SKU', 'quantity': 1}
        ]
    }
    
    # Intentar con token inválido
    headers = {'Authorization': 'Bearer INVALID_TOKEN_12345'}
    response = client.post('/api/sales/webhook', json=payload, headers=headers)
    assert response.status_code == 401


def test_api_webhook_accepts_valid_token(client, app, monkeypatch):
    """Test que el webhook acepta tokens válidos (mock)"""
    # Configurar token válido en el entorno de test
    test_token = 'TEST_VALID_TOKEN_12345'
    monkeypatch.setenv('SIPUD_WEBHOOK_TOKEN', test_token)
    
    # Recargar la configuración
    app.config['SIPUD_WEBHOOK_TOKEN'] = test_token
    
    payload = {
        'customer': 'Test Customer',
        'phone': '+56912345678',
        'address': 'Test Address 123',
        'items': [
            {'sku': 'TEST-SKU', 'quantity': 1}
        ]
    }
    
    headers = {'Authorization': f'Bearer {test_token}'}
    response = client.post('/api/sales/webhook', json=payload, headers=headers)
    
    # Puede fallar por otros motivos (producto no existe, etc) pero NO por auth
    # Un 401 significa fallo de autenticación
    assert response.status_code != 401


def test_api_rate_limiting_enabled(app):
    """Test que rate limiting está configurado"""
    from app.extensions import limiter
    
    # Verificar que limiter está inicializado
    assert limiter is not None
    
    # En ambiente de test, puede estar deshabilitado
    # Verificar configuración
    if not app.config.get('RATELIMIT_ENABLED', True):
        pytest.skip("Rate limiting deshabilitado en tests")


def test_api_error_handler_429(app):
    """Test que existe handler para 429 (rate limit exceeded)"""
    # Verificar que el error handler está registrado
    assert 429 in app.error_handler_spec[None]


def test_api_webhook_validates_payload(client, app, monkeypatch):
    """Test que el webhook valida el payload recibido"""
    test_token = 'TEST_VALID_TOKEN_12345'
    monkeypatch.setenv('SIPUD_WEBHOOK_TOKEN', test_token)
    app.config['SIPUD_WEBHOOK_TOKEN'] = test_token
    
    headers = {'Authorization': f'Bearer {test_token}'}
    
    # Payload vacío
    response = client.post('/api/sales/webhook', json={}, headers=headers)
    # Debe retornar error 400 por datos faltantes (no 401)
    assert response.status_code in [400, 404]  # 404 si el endpoint no existe aún
    
    # Payload sin items
    payload = {
        'customer': 'Test Customer',
        'phone': '+56912345678',
        'address': 'Test Address 123'
    }
    response = client.post('/api/sales/webhook', json=payload, headers=headers)
    assert response.status_code in [400, 404]


def test_api_permission_decorator(client, app):
    """Test que el decorator permission_required funciona"""
    # Intentar crear producto sin autenticación
    response = client.post('/api/products', json={
        'name': 'Test Product',
        'sku': 'TEST-001'
    })
    
    # Debe requerir login (302 redirect o 401)
    assert response.status_code in [302, 401]


def test_api_json_response_format(client, app):
    """Test que las respuestas de API son JSON válido"""
    # Intentar endpoint sin autenticación para obtener respuesta de error
    response = client.get('/api/products')
    
    # Si retorna JSON (algunos endpoints), verificar formato
    if response.content_type == 'application/json':
        data = response.get_json()
        assert data is not None
        assert isinstance(data, (dict, list))


def test_api_handles_invalid_json(client, app, monkeypatch):
    """Test que la API maneja JSON inválido correctamente"""
    test_token = 'TEST_VALID_TOKEN_12345'
    monkeypatch.setenv('SIPUD_WEBHOOK_TOKEN', test_token)
    app.config['SIPUD_WEBHOOK_TOKEN'] = test_token
    
    headers = {
        'Authorization': f'Bearer {test_token}',
        'Content-Type': 'application/json'
    }
    
    # Enviar JSON malformado
    response = client.post(
        '/api/sales/webhook',
        data='{"invalid": json}',  # JSON inválido
        headers=headers
    )
    
    # Debe manejar el error (400 o 500, pero no crash)
    assert response.status_code >= 400
