"""
Script de limpieza para preparar SIPUD para producción.

Este script:
1. Elimina todos los datos de prueba (productos, ventas, lotes, órdenes, mermas)
2. Mantiene solo el tenant "puerto-distribucion"
3. Opcionalmente resetea usuarios a solo admin
4. Incluye confirmación antes de ejecutar

ADVERTENCIA: Este script elimina datos de forma PERMANENTE.
Solo ejecutar cuando estés seguro de querer limpiar la base de datos.
"""
import sys
from app import create_app
from app.models import (
    Tenant, User, Product, Sale, SaleItem, Lot, InboundOrder,
    Wastage, ProductBundle, Supplier, ActivityLog, Payment
)

app = create_app()


def get_stats():
    """Obtiene estadísticas actuales de la base de datos."""
    stats = {
        'tenants': Tenant.objects.count(),
        'users': User.objects.count(),
        'products': Product.objects.count(),
        'sales': Sale.objects.count(),
        'sale_items': SaleItem.objects.count(),
        'lots': Lot.objects.count(),
        'inbound_orders': InboundOrder.objects.count(),
        'wastages': Wastage.objects.count(),
        'product_bundles': ProductBundle.objects.count(),
        'suppliers': Supplier.objects.count(),
        'activity_logs': ActivityLog.objects.count(),
        'payments': Payment.objects.count(),
    }
    return stats


def print_stats(stats, title="Estadísticas de la Base de Datos"):
    """Imprime las estadísticas de forma legible."""
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")
    for key, value in stats.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    print(f"{'='*50}\n")


def clear_tenant_data(tenant, keep_admin=True):
    """Elimina todos los datos de un tenant específico."""
    print(f"\nLimpiando datos del tenant: {tenant.name} ({tenant.slug})")

    # Eliminar en orden para respetar dependencias

    # 1. Payments
    count = Payment.objects(tenant=tenant).count()
    Payment.objects(tenant=tenant).delete()
    print(f"  - Payments eliminados: {count}")

    # 2. ActivityLog
    count = ActivityLog.objects(tenant=tenant).count()
    ActivityLog.objects(tenant=tenant).delete()
    print(f"  - ActivityLogs eliminados: {count}")

    # 3. SaleItems (a través de Sales)
    sales = Sale.objects(tenant=tenant)
    sale_items_count = 0
    for sale in sales:
        count = SaleItem.objects(sale=sale).count()
        SaleItem.objects(sale=sale).delete()
        sale_items_count += count
    print(f"  - SaleItems eliminados: {sale_items_count}")

    # 4. Sales
    count = Sale.objects(tenant=tenant).count()
    Sale.objects(tenant=tenant).delete()
    print(f"  - Sales eliminados: {count}")

    # 5. Wastages
    count = Wastage.objects(tenant=tenant).count()
    Wastage.objects(tenant=tenant).delete()
    print(f"  - Wastages eliminados: {count}")

    # 6. Lots
    count = Lot.objects(tenant=tenant).count()
    Lot.objects(tenant=tenant).delete()
    print(f"  - Lots eliminados: {count}")

    # 7. ProductBundles
    count = ProductBundle.objects(tenant=tenant).count()
    ProductBundle.objects(tenant=tenant).delete()
    print(f"  - ProductBundles eliminados: {count}")

    # 8. InboundOrders
    count = InboundOrder.objects(tenant=tenant).count()
    InboundOrder.objects(tenant=tenant).delete()
    print(f"  - InboundOrders eliminados: {count}")

    # 9. Products
    count = Product.objects(tenant=tenant).count()
    Product.objects(tenant=tenant).delete()
    print(f"  - Products eliminados: {count}")

    # 10. Suppliers
    count = Supplier.objects(tenant=tenant).count()
    Supplier.objects(tenant=tenant).delete()
    print(f"  - Suppliers eliminados: {count}")

    # 11. Users (opcional, mantener admin)
    if keep_admin:
        # Eliminar todos excepto admins
        non_admin_users = User.objects(tenant=tenant, role__ne='admin')
        count = non_admin_users.count()
        non_admin_users.delete()
        print(f"  - Users no-admin eliminados: {count}")
        admin_count = User.objects(tenant=tenant, role='admin').count()
        print(f"  - Users admin preservados: {admin_count}")
    else:
        count = User.objects(tenant=tenant).count()
        User.objects(tenant=tenant).delete()
        print(f"  - Todos los Users eliminados: {count}")


def remove_other_tenants(main_tenant_slug='puerto-distribucion'):
    """Elimina todos los tenants excepto el principal."""
    main_tenant = Tenant.objects(slug=main_tenant_slug).first()
    if not main_tenant:
        print(f"ERROR: Tenant principal '{main_tenant_slug}' no encontrado.")
        return None

    other_tenants = Tenant.objects(slug__ne=main_tenant_slug)
    for tenant in other_tenants:
        print(f"\nEliminando tenant: {tenant.name} ({tenant.slug})")
        # Primero limpiar sus datos
        clear_tenant_data(tenant, keep_admin=False)
        # Luego eliminar el tenant
        tenant.delete()
        print(f"  Tenant '{tenant.name}' eliminado.")

    return main_tenant


def clear_for_production(keep_admin=True, clear_main_tenant_data=True):
    """
    Limpia la base de datos para producción.

    Args:
        keep_admin: Si True, mantiene los usuarios admin del tenant principal
        clear_main_tenant_data: Si True, también limpia los datos del tenant principal
    """
    with app.app_context():
        # Mostrar estadísticas antes
        before_stats = get_stats()
        print_stats(before_stats, "ANTES de la limpieza")

        # Eliminar tenants secundarios
        main_tenant = remove_other_tenants('puerto-distribucion')
        if not main_tenant:
            return

        # Limpiar datos del tenant principal si se solicita
        if clear_main_tenant_data:
            clear_tenant_data(main_tenant, keep_admin=keep_admin)

        # Mostrar estadísticas después
        after_stats = get_stats()
        print_stats(after_stats, "DESPUÉS de la limpieza")

        print("✓ Limpieza completada exitosamente.")
        print(f"  Tenant activo: {main_tenant.name} ({main_tenant.slug})")


def main():
    print("\n" + "="*60)
    print("  SIPUD - Script de Limpieza para Producción")
    print("="*60)
    print("\n⚠️  ADVERTENCIA: Este script eliminará datos PERMANENTEMENTE.")
    print("    Solo ejecutar si estás seguro de querer limpiar la base de datos.\n")

    # Opciones
    print("Opciones de limpieza:")
    print("  1. Limpiar TODO (datos de prueba + tenants secundarios)")
    print("  2. Solo eliminar tenants secundarios (mantener datos de Puerto Distribución)")
    print("  3. Cancelar")

    choice = input("\nSelecciona una opción (1/2/3): ").strip()

    if choice == '1':
        # Confirmación adicional
        confirm = input("\n¿Estás SEGURO de que deseas eliminar TODOS los datos? (escribe 'SI' para confirmar): ")
        if confirm.strip().upper() == 'SI':
            keep_admin = input("¿Mantener usuarios admin? (s/n): ").strip().lower() == 's'
            clear_for_production(keep_admin=keep_admin, clear_main_tenant_data=True)
        else:
            print("Operación cancelada.")

    elif choice == '2':
        confirm = input("\n¿Confirmas eliminar tenants secundarios? (escribe 'SI' para confirmar): ")
        if confirm.strip().upper() == 'SI':
            clear_for_production(keep_admin=True, clear_main_tenant_data=False)
        else:
            print("Operación cancelada.")

    else:
        print("Operación cancelada.")


if __name__ == '__main__':
    main()
