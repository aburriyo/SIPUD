from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.models import Product, Sale, SaleItem
from app.extensions import db

bp = Blueprint('main', __name__)

@bp.route('/switch-tenant/<int:tenant_id>')
@login_required
def switch_tenant(tenant_id):
    from flask import session, redirect, url_for, request
    session['tenant_id'] = tenant_id
    return redirect(request.referrer or url_for('main.dashboard'))


@bp.route('/')
@login_required
def dashboard():
    from flask import g
    # Calculate stats for dashboard (Filtered by Tenant)
    tenant_id = g.current_tenant.id if g.current_tenant else None
    
    total_sales = Sale.query.filter_by(tenant_id=tenant_id).count()
    total_products = Product.query.filter_by(tenant_id=tenant_id).count()
    
    # Refactored: Use SQL to sum revenue
    revenue = db.session.query(db.func.sum(SaleItem.quantity * SaleItem.unit_price))\
        .join(SaleItem.sale).filter(Sale.tenant_id == tenant_id).scalar() or 0
    
    recent_sales = Sale.query.filter_by(tenant_id=tenant_id).order_by(Sale.date_created.desc()).limit(5).all()
    recent_sales_data = [{
        'id': s.id, 
        'customer': s.customer_name, 
        'status': s.status
    } for s in recent_sales]
    
    stats = {
        'total_sales': total_sales,
        'total_products': total_products,
        'total_revenue': revenue,
        'recent_sales': recent_sales_data
    }
    return render_template('dashboard.html', stats=stats)

@bp.route('/products')
@login_required
def products_view():
    from flask import g
    tenant_id = g.current_tenant.id if g.current_tenant else None
    products = Product.query.filter_by(tenant_id=tenant_id).all()
    return render_template('products.html', products=products)

@bp.route('/sales')
@login_required
def sales_view():
    from flask import g
    tenant_id = g.current_tenant.id if g.current_tenant else None
    # Get all sales, let DataTables handle pagination
    sales = Sale.query.filter_by(tenant_id=tenant_id).order_by(Sale.date_created.desc()).all()
    # Create dummy pagination object for template compatibility
    class DummyPagination:
        has_prev = False
        has_next = False
        page = 1
        pages = 1
    return render_template('sales.html', sales=sales, pagination=DummyPagination())

@bp.route('/fleet')
@login_required
def fleet_view():
    from flask import g
    from app.models import Truck
    tenant_id = g.current_tenant.id if g.current_tenant else None
    trucks = Truck.query.filter_by(tenant_id=tenant_id).all()
    
    # Convert trucks to dictionaries for JSON serialization
    trucks_data = []
    for truck in trucks:
        trucks_data.append({
            'id': truck.id,
            'license_plate': truck.license_plate,
            'make_model': truck.make_model,
            'capacity_kg': truck.capacity_kg,
            'status': truck.status,
            'current_lat': truck.current_lat,
            'current_lng': truck.current_lng,
            'odometer_km': truck.odometer_km or 0,
            'last_update': truck.last_update.isoformat() if truck.last_update else None
        })
    
    return render_template('fleet.html', trucks=trucks, trucks_data=trucks_data)

