from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from app.models import Truck, LogisticsRoute, db
from datetime import datetime

bp = Blueprint('logistics', __name__, url_prefix='/logistics')

@bp.route('/')
def dashboard():
    from flask import g
    tenant_id = g.current_tenant.id if g.current_tenant else None
    trucks = Truck.query.filter_by(tenant_id=tenant_id).all()
    # active_routes logic could also be filtered, but focusing on trucks first
    active_routes = LogisticsRoute.query.join(Truck).filter(Truck.tenant_id == tenant_id, LogisticsRoute.status == 'in_transit').all()
    return render_template('logistics.html', trucks=trucks, active_routes=active_routes)

@bp.route('/trucks', methods=['POST'])
def create_truck():
    from flask import g
    tenant_id = g.current_tenant.id if g.current_tenant else None
    data = request.form
    new_truck = Truck(
        license_plate=data['license_plate'],
        make_model=data['make_model'],
        capacity_kg=float(data['capacity_kg'] or 0),
        tenant_id=tenant_id
    )
    db.session.add(new_truck)
    db.session.commit()
    return redirect(url_for('logistics.dashboard'))

@bp.route('/api/trucks/<int:id>/location', methods=['POST'])
def update_location(id):
    from flask import g
    tenant_id = g.current_tenant.id if g.current_tenant else None
    truck = Truck.query.filter_by(id=id, tenant_id=tenant_id).first_or_404()
    data = request.get_json()
    truck.current_lat = data.get('lat')
    truck.current_lng = data.get('lng')
    truck.last_update = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Location updated'})
