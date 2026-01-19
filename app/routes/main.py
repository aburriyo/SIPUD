from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.models import Product, Sale, SaleItem
from app.extensions import db

bp = Blueprint("main", __name__)


@bp.route("/switch-tenant/<int:tenant_id>")
@login_required
def switch_tenant(tenant_id):
    from flask import session, redirect, url_for, request

    session["tenant_id"] = tenant_id
    return redirect(request.referrer or url_for("main.dashboard"))


@bp.route("/")
@login_required
def dashboard():
    from flask import g

    # Calculate stats for dashboard (Filtered by Tenant)
    tenant_id = g.current_tenant.id if g.current_tenant else None

    total_sales = Sale.query.filter_by(tenant_id=tenant_id).count()
    total_products = Product.query.filter_by(tenant_id=tenant_id).count()

    # Refactored: Use SQL to sum revenue
    revenue = (
        db.session.query(db.func.sum(SaleItem.quantity * SaleItem.unit_price))
        .join(SaleItem.sale)
        .filter(Sale.tenant_id == tenant_id)
        .scalar()
        or 0
    )

    recent_sales = (
        Sale.query.filter_by(tenant_id=tenant_id)
        .order_by(Sale.date_created.desc())
        .limit(5)
        .all()
    )
    recent_sales_data = [
        {"id": s.id, "customer": s.customer_name, "status": s.status}
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
    from flask import g

    tenant_id = g.current_tenant.id if g.current_tenant else None
    products = Product.query.filter_by(tenant_id=tenant_id).all()
    return render_template("products.html", products=products)


@bp.route("/sales")
@login_required
def sales_view():
    from flask import g

    tenant_id = g.current_tenant.id if g.current_tenant else None
    # Get all sales, let DataTables handle pagination
    sales = (
        Sale.query.filter_by(tenant_id=tenant_id)
        .order_by(Sale.date_created.desc())
        .all()
    )

    # Create dummy pagination object for template compatibility
    class DummyPagination:
        has_prev = False
        has_next = False
        page = 1
        pages = 1

    return render_template("sales.html", sales=sales, pagination=DummyPagination())
