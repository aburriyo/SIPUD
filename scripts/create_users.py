#!/usr/bin/env python
"""
Script para crear usuarios de prueba en el sistema
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db, User, Tenant
from datetime import datetime

app = create_app()

with app.app_context():
    # Verificar si ya existen usuarios
    existing_users = User.query.count()
    if existing_users > 0:
        print(f"⚠️  Ya existen {existing_users} usuarios en la base de datos.")
        response = input("¿Deseas recrear todos los usuarios? (s/n): ")
        if response.lower() != 's':
            print("❌ Operación cancelada")
            exit(0)
        else:
            # Eliminar usuarios existentes
            User.query.delete()
            db.session.commit()
            print("✓ Usuarios existentes eliminados")
    
    # Obtener el tenant por defecto (Puerto Distribución)
    tenant = Tenant.query.filter_by(slug='puerto-distribucion').first()
    if not tenant:
        print("⚠️  No se encontró el tenant 'puerto-distribucion'")
        print("   Creando tenant de prueba...")
        tenant = Tenant(
            name='Puerto Distribución',
            slug='puerto-distribucion'
        )
        db.session.add(tenant)
        db.session.commit()
        print("✓ Tenant creado")
    
    # Crear usuarios de prueba
    users_data = [
        {
            'username': 'admin',
            'password': 'admin123',
            'email': 'admin@inventario2026.cl',
            'full_name': 'Administrador del Sistema',
            'role': 'admin',
            'tenant_id': tenant.id
        },
        {
            'username': 'gerente',
            'password': 'gerente123',
            'email': 'gerente@inventario2026.cl',
            'full_name': 'Gerente de Operaciones',
            'role': 'manager',
            'tenant_id': tenant.id
        },
        {
            'username': 'bodega',
            'password': 'bodega123',
            'email': 'bodega@inventario2026.cl',
            'full_name': 'Operador de Bodega',
            'role': 'warehouse',
            'tenant_id': tenant.id
        },
        {
            'username': 'vendedor',
            'password': 'vendedor123',
            'email': 'vendedor@inventario2026.cl',
            'full_name': 'Ejecutivo de Ventas',
            'role': 'sales',
            'tenant_id': tenant.id
        }
    ]
    
    print("\n📝 Creando usuarios de prueba...\n")
    
    for user_data in users_data:
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            full_name=user_data['full_name'],
            role=user_data['role'],
            tenant_id=user_data['tenant_id'],
            is_active=True,
            created_at=datetime.utcnow()
        )
        user.set_password(user_data['password'])
        
        db.session.add(user)
        
        # Mostrar credenciales
        print(f"✓ {user_data['full_name']}")
        print(f"  Usuario: {user_data['username']}")
        print(f"  Contraseña: {user_data['password']}")
        print(f"  Rol: {user_data['role']}")
        print(f"  Email: {user_data['email']}\n")
    
    db.session.commit()
    
    print("=" * 60)
    print("✅ Usuarios creados exitosamente!")
    print("=" * 60)
    print("\n🔐 Puedes iniciar sesión con cualquiera de estos usuarios:")
    print("   - admin / admin123 (Acceso total)")
    print("   - gerente / gerente123 (Gestión operativa)")
    print("   - bodega / bodega123 (Operaciones de almacén)")
    print("   - vendedor / vendedor123 (Ventas y logística)")
    print("\n🌐 Ve a http://127.0.0.1:5000/login para iniciar sesión\n")
