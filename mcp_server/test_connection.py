#!/usr/bin/env python3
"""
Script de prueba para verificar la conexión del servidor MCP con MongoDB
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mongoengine import connect, disconnect
from dotenv import load_dotenv
from app.models import Tenant, Product

# Load environment variables
load_dotenv()

MONGODB_HOST = os.environ.get('MONGODB_HOST', 'localhost')
MONGODB_PORT = int(os.environ.get('MONGODB_PORT', '27017'))
MONGODB_DB = os.environ.get('MONGODB_DB', 'inventory_db')

def test_connection():
    """Test MongoDB connection and query basic data"""
    print("=" * 60)
    print("SIPUD MCP Server - Connection Test")
    print("=" * 60)

    try:
        # Connect to MongoDB
        print(f"\n1. Conectando a MongoDB...")
        print(f"   Host: {MONGODB_HOST}:{MONGODB_PORT}")
        print(f"   Database: {MONGODB_DB}")

        connect(
            db=MONGODB_DB,
            host=MONGODB_HOST,
            port=MONGODB_PORT,
        )
        print("   ✓ Conexión exitosa")

        # Test tenants
        print(f"\n2. Verificando tenants...")
        tenants = Tenant.objects.all()
        print(f"   Tenants encontrados: {len(tenants)}")
        for tenant in tenants:
            print(f"   - {tenant.name} (slug: {tenant.slug})")

        if len(tenants) == 0:
            print("   ⚠ No se encontraron tenants")
            print("   Asegúrate de que la base de datos tenga datos")
            return False

        # Test products for first tenant
        print(f"\n3. Verificando productos...")
        tenant = tenants[0]
        products = Product.objects(tenant=tenant)
        print(f"   Productos en tenant '{tenant.slug}': {len(products)}")

        if len(products) > 0:
            print(f"\n4. Ejemplo de producto:")
            product = products[0]
            print(f"   Nombre: {product.name}")
            print(f"   SKU: {product.sku}")
            print(f"   Stock total: {product.total_stock}")
            print(f"   Precio: ${product.base_price}")

        print("\n" + "=" * 60)
        print("✓ Todas las pruebas pasaron correctamente")
        print("=" * 60)
        print("\nEl servidor MCP está listo para usarse.")
        print("Configura claude_desktop_config.json y reinicia Claude Desktop.")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nPosibles soluciones:")
        print("1. Verifica que MongoDB esté corriendo: mongosh")
        print("2. Revisa las variables de entorno en .env")
        print("3. Verifica que la base de datos tenga datos")
        return False

    finally:
        disconnect()


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
