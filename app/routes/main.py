from flask import Blueprint, render_template, request, g, session, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models import Product, Sale, SaleItem, ActivityLog
from bson import ObjectId
from datetime import datetime

bp = Blueprint("main", __name__)


@bp.route("/switch-tenant/<tenant_id>")
@login_required
def switch_tenant(tenant_id):
    session["tenant_id"] = tenant_id
    return redirect(request.referrer or url_for("main.dashboard"))


@bp.route("/")
@login_required
def dashboard():
    """Enhanced dashboard with role-specific data"""
    tenant = g.current_tenant
    user_role = current_user.role
    
    # Basic stats
    total_sales = Sale.objects(tenant=tenant).count()
    total_products = Product.objects(tenant=tenant).count()

    # Calculate revenue using aggregation
    pipeline = [
        {"$lookup": {
            "from": "sales",
            "localField": "sale",
            "foreignField": "_id",
            "as": "sale_doc"
        }},
        {"$unwind": "$sale_doc"},
        {"$match": {"sale_doc.tenant": tenant.id if tenant else None}},
        {"$group": {
            "_id": None,
            "total": {"$sum": {"$multiply": ["$quantity", "$unit_price"]}}
        }}
    ]

    revenue_result = list(SaleItem.objects.aggregate(pipeline))
    revenue = revenue_result[0]["total"] if revenue_result else 0

    recent_sales = Sale.objects(tenant=tenant).order_by("-date_created").limit(5)
    recent_sales_data = [
        {"id": str(s.id), "customer": s.customer_name, "status": s.status}
        for s in recent_sales
    ]
    
    # === NEW DATA FOR ENHANCED DASHBOARD ===
    
    # 1. User info for welcome card
    user_info = {
        "name": current_user.full_name or current_user.username,
        "role": user_role,
        "role_display": {
            "admin": "Administrador",
            "manager": "Gerente",
            "warehouse": "Encargado de Bodega",
            "sales": "Ejecutivo de Ventas"
        }.get(user_role, user_role.capitalize())
    }
    
    # Time-based greeting
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Buenos días"
    elif hour < 19:
        greeting = "Buenas tardes"
    else:
        greeting = "Buenas noches"
    
    # 2. Critical stock products (where stock < critical_stock)
    critical_stock_products = []
    if user_role in ['admin', 'manager', 'warehouse']:
        products_with_low_stock = Product.objects(tenant=tenant)
        for p in products_with_low_stock:
            if hasattr(p, 'total_stock') and hasattr(p, 'critical_stock'):
                if p.total_stock <= p.critical_stock:
                    critical_stock_products.append({
                        "id": str(p.id),
                        "name": p.name,
                        "stock": p.total_stock,
                        "critical": p.critical_stock,
                        "sku": p.sku
                    })
    
    # 3. Top 5 best-selling products
    top_products = []
    try:
        top_pipeline = [
            {"$lookup": {
                "from": "sales",
                "localField": "sale",
                "foreignField": "_id",
                "as": "sale_doc"
            }},
            {"$unwind": "$sale_doc"},
            {"$match": {"sale_doc.tenant": tenant.id if tenant else None}},
            {"$group": {
                "_id": "$product",
                "total_quantity": {"$sum": "$quantity"},
                "total_revenue": {"$sum": {"$multiply": ["$quantity", "$unit_price"]}}
            }},
            {"$sort": {"total_quantity": -1}},
            {"$limit": 5}
        ]
        top_result = list(SaleItem.objects.aggregate(top_pipeline))
        
        for item in top_result:
            try:
                product = Product.objects.get(id=item["_id"])
                top_products.append({
                    "name": product.name[:25] + "..." if len(product.name) > 25 else product.name,
                    "quantity": item["total_quantity"],
                    "revenue": item["total_revenue"]
                })
            except Exception as e:
                current_app.logger.debug(f'Producto {item["_id"]} no encontrado: {e}')
    except Exception as e:
        print(f"Error getting top products: {e}")
    
    # 4. Sales distribution by status
    sales_distribution = {"pending": 0, "delivered": 0, "cancelled": 0, "in_transit": 0}
    if user_role in ['admin', 'manager']:
        for status in sales_distribution.keys():
            sales_distribution[status] = Sale.objects(tenant=tenant, status=status).count()
    
    # 5. Recent activity for current user (last 5)
    user_activity = []
    if user_role in ['admin', 'manager']:
        try:
            logs = ActivityLog.objects(tenant=tenant).order_by("-created_at").limit(5)
            for log in logs:
                user_activity.append({
                    "action": log.action,
                    "description": log.description,
                    "module": log.module,
                    "time": log.created_at.strftime("%H:%M") if log.created_at else ""
                })
        except Exception as e:
            current_app.logger.debug(f'Error cargando actividad reciente: {e}')
    
    # 6. Pending orders count (for warehouse)
    pending_orders = 0
    if user_role in ['admin', 'manager', 'warehouse']:
        from app.models import InboundOrder
        try:
            pending_orders = InboundOrder.objects(tenant=tenant, status="pending").count()
        except Exception as e:
            current_app.logger.debug(f'Error contando pedidos pendientes: {e}')

    stats = {
        "total_sales": total_sales,
        "total_products": total_products,
        "total_revenue": revenue,
        "recent_sales": recent_sales_data,
        # New data
        "user_info": user_info,
        "greeting": greeting,
        "critical_stock": critical_stock_products,
        "critical_stock_count": len(critical_stock_products),
        "top_products": top_products,
        "sales_distribution": sales_distribution,
        "user_activity": user_activity,
        "pending_orders": pending_orders,
        "user_role": user_role
    }
    return render_template("dashboard.html", stats=stats)


@bp.route("/products")
@login_required
def products_view():
    tenant = g.current_tenant
    products = Product.objects(tenant=tenant)
    return render_template("products.html", products=products)


@bp.route("/sales")
@login_required
def sales_view():
    tenant = g.current_tenant
    # Get all sales, let DataTables handle pagination
    sales = Sale.objects(tenant=tenant).order_by("-date_created")

    # Create dummy pagination object for template compatibility
    class DummyPagination:
        has_prev = False
        has_next = False
        page = 1
        pages = 1

    return render_template("sales.html", sales=sales, pagination=DummyPagination())
