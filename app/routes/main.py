from flask import Blueprint, render_template, request, g, session, redirect, url_for
from flask_login import login_required, current_user
from app.models import Product, Sale, SaleItem
from bson import ObjectId

bp = Blueprint("main", __name__)


@bp.route("/switch-tenant/<tenant_id>")
@login_required
def switch_tenant(tenant_id):
    session["tenant_id"] = tenant_id
    return redirect(request.referrer or url_for("main.dashboard"))


@bp.route("/")
@login_required
def dashboard():
    # Calculate stats for dashboard (Filtered by Tenant)
    tenant = g.current_tenant

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

    stats = {
        "total_sales": total_sales,
        "total_products": total_products,
        "total_revenue": revenue,
        "recent_sales": recent_sales_data,
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
