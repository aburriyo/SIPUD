#!/usr/bin/env python
"""
Script para crear usuarios en el sistema.
Adaptado para MongoEngine después de la migración de SQLAlchemy.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import User, Tenant
from datetime import datetime

app = create_app()

with app.app_context():
    # Obtener o crear el tenant por defecto
    tenant = Tenant.objects(slug='puerto-distribucion').first()
    if not tenant:
        tenant = Tenant(name='Puerto Distribución', slug='puerto-distribucion')
        tenant.save()
        print("Tenant 'Puerto Distribución' creado.")

    # Verificar si ya existen usuarios
    existing = User.objects(tenant=tenant).count()
    if existing > 0:
        print(f"Ya existen {existing} usuarios en la base de datos.")
        print("Si deseas recrearlos, elimina los usuarios primero.")
        sys.exit(0)

    users_data = [
        {
            'username': 'admin',
            'password': 'admin123',
            'email': 'admin@inventario2026.cl',
            'full_name': 'Administrador del Sistema',
            'role': 'admin',
        },
        {
            'username': 'gerente',
            'password': 'gerente123',
            'email': 'gerente@inventario2026.cl',
            'full_name': 'Gerente de Operaciones',
            'role': 'manager',
        },
        {
            'username': 'bodega',
            'password': 'bodega123',
            'email': 'bodega@inventario2026.cl',
            'full_name': 'Operador de Bodega',
            'role': 'warehouse',
        },
        {
            'username': 'vendedor',
            'password': 'vendedor123',
            'email': 'vendedor@inventario2026.cl',
            'full_name': 'Ejecutivo de Ventas',
            'role': 'sales',
        }
    ]

    print("\nCreando usuarios...\n")

    for data in users_data:
        user = User(
            username=data['username'],
            email=data['email'],
            full_name=data['full_name'],
            role=data['role'],
            tenant=tenant,
            is_active=True,
            created_at=datetime.utcnow()
        )
        user.set_password(data['password'])
        user.save()

        print(f"  {data['full_name']}")
        print(f"  Usuario: {data['username']} / Rol: {data['role']}\n")

    print("Usuarios creados exitosamente.")
    print("\nCredenciales:")
    print("  admin / admin123")
    print("  gerente / gerente123")
    print("  bodega / bodega123")
    print("  vendedor / vendedor123")
