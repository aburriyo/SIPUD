"""
Admin Blueprint
Gestión de usuarios y monitor de actividades
"""
from flask import Blueprint, render_template, request, jsonify, g, abort
from flask_login import login_required, current_user
from app.models import User, Tenant, ActivityLog, ROLE_PERMISSIONS, utc_now
from functools import wraps
from bson import ObjectId
from mongoengine import DoesNotExist

bp = Blueprint('admin', __name__, url_prefix='/admin')


def permission_required(module, action='view'):
    """Decorator to check permissions before accessing a route"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if not current_user.has_permission(module, action):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================
# USER MANAGEMENT
# ============================================

@bp.route('/users')
@login_required
@permission_required('users', 'view')
def users():
    """Vista de gestión de usuarios"""
    return render_template('admin/users.html', roles=list(ROLE_PERMISSIONS.keys()))


@bp.route('/api/users', methods=['GET'])
@login_required
@permission_required('users', 'view')
def get_users():
    """Obtener todos los usuarios"""
    tenant = g.current_tenant
    users = User.objects(tenant=tenant)

    return jsonify({
        'success': True,
        'users': [{
            'id': str(u.id),
            'username': u.username,
            'email': u.email,
            'full_name': u.full_name,
            'role': u.role,
            'is_active': u.is_active,
            'last_login': u.last_login.strftime('%d/%m/%Y %H:%M') if u.last_login else None,
            'created_at': u.created_at.strftime('%d/%m/%Y %H:%M') if u.created_at else None
        } for u in users]
    })


@bp.route('/api/users', methods=['POST'])
@login_required
@permission_required('users', 'create')
def create_user():
    """Crear nuevo usuario"""
    data = request.get_json()
    tenant = g.current_tenant

    if not data:
        return jsonify({'success': False, 'error': 'No se recibieron datos'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')
    email = data.get('email', '').strip() or None
    full_name = data.get('full_name', '').strip()
    role = data.get('role', 'sales')

    # Validations
    if not username or len(username) < 3:
        return jsonify({'success': False, 'error': 'El nombre de usuario debe tener al menos 3 caracteres'}), 400

    if not password or len(password) < 4:
        return jsonify({'success': False, 'error': 'La contraseña debe tener al menos 4 caracteres'}), 400

    if role not in ROLE_PERMISSIONS:
        return jsonify({'success': False, 'error': f'Rol inválido. Roles válidos: {list(ROLE_PERMISSIONS.keys())}'}), 400

    # Check if username exists
    if User.objects(username=username).first():
        return jsonify({'success': False, 'error': 'El nombre de usuario ya existe'}), 400

    # Check if email exists (if provided)
    if email and User.objects(email=email).first():
        return jsonify({'success': False, 'error': 'El email ya está registrado'}), 400

    try:
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            is_active=True,
            tenant=tenant
        )
        new_user.set_password(password)
        new_user.save()

        # Log activity
        ActivityLog.log(
            user=current_user,
            action='create',
            module='users',
            description=f'Creó usuario "{username}" con rol {role}',
            target_id=str(new_user.id),
            target_type='User',
            request=request,
            tenant=tenant
        )

        return jsonify({
            'success': True,
            'message': 'Usuario creado exitosamente',
            'user_id': str(new_user.id)
        }), 201

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/users/<user_id>', methods=['GET'])
@login_required
@permission_required('users', 'view')
def get_user(user_id):
    """Obtener un usuario específico"""
    tenant = g.current_tenant
    try:
        user = User.objects.get(id=ObjectId(user_id))
    except DoesNotExist:
        return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404

    # Validar que el usuario pertenece al tenant actual
    if user.tenant != tenant:
        return jsonify({'success': False, 'error': 'Acceso denegado'}), 403

    return jsonify({
        'success': True,
        'user': {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'is_active': user.is_active,
            'permissions': user.get_permissions()
        }
    })


@bp.route('/api/users/<user_id>', methods=['PUT'])
@login_required
@permission_required('users', 'edit')
def update_user(user_id):
    """Actualizar usuario"""
    tenant = g.current_tenant
    try:
        user = User.objects.get(id=ObjectId(user_id))
    except DoesNotExist:
        return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404

    # Validar que el usuario pertenece al tenant actual
    if user.tenant != tenant:
        return jsonify({'success': False, 'error': 'Acceso denegado'}), 403

    # Prevent editing yourself (for role changes)
    if str(user.id) == str(current_user.id):
        data = request.get_json()
        if 'role' in data and data['role'] != current_user.role:
            return jsonify({'success': False, 'error': 'No puedes cambiar tu propio rol'}), 400

    data = request.get_json()
    changes = []

    if 'email' in data:
        email = data['email'].strip() or None
        if email and email != user.email:
            if User.objects(email=email, id__ne=user.id).first():
                return jsonify({'success': False, 'error': 'El email ya está registrado'}), 400
        if user.email != email:
            changes.append(f'email: {user.email} → {email}')
        user.email = email

    if 'full_name' in data:
        if user.full_name != data['full_name']:
            changes.append(f'nombre: {user.full_name} → {data["full_name"]}')
        user.full_name = data['full_name']

    if 'role' in data:
        if data['role'] not in ROLE_PERMISSIONS:
            return jsonify({'success': False, 'error': 'Rol inválido'}), 400
        if user.role != data['role']:
            changes.append(f'rol: {user.role} → {data["role"]}')
        user.role = data['role']

    if 'is_active' in data:
        if user.is_active != data['is_active']:
            changes.append(f'activo: {user.is_active} → {data["is_active"]}')
        user.is_active = data['is_active']

    if 'password' in data and data['password']:
        if len(data['password']) < 4:
            return jsonify({'success': False, 'error': 'La contraseña debe tener al menos 4 caracteres'}), 400
        user.set_password(data['password'])
        changes.append('contraseña actualizada')

    user.save()

    # Log activity
    if changes:
        ActivityLog.log(
            user=current_user,
            action='update',
            module='users',
            description=f'Actualizó usuario "{user.username}": {", ".join(changes)}',
            target_id=str(user.id),
            target_type='User',
            details={'changes': changes},
            request=request,
            tenant=tenant
        )

    return jsonify({'success': True, 'message': 'Usuario actualizado'})


@bp.route('/api/users/<user_id>', methods=['DELETE'])
@login_required
@permission_required('users', 'delete')
def delete_user(user_id):
    """Eliminar usuario"""
    tenant = g.current_tenant
    try:
        user = User.objects.get(id=ObjectId(user_id))
    except DoesNotExist:
        return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404

    # Validar que el usuario pertenece al tenant actual
    if user.tenant != tenant:
        return jsonify({'success': False, 'error': 'Acceso denegado'}), 403

    # Prevent self-deletion
    if str(user.id) == str(current_user.id):
        return jsonify({'success': False, 'error': 'No puedes eliminarte a ti mismo'}), 400

    username = user.username

    # Instead of hard delete, deactivate the user
    user.is_active = False
    user.save()

    # Log activity
    ActivityLog.log(
        user=current_user,
        action='delete',
        module='users',
        description=f'Desactivó usuario "{username}"',
        target_id=str(user.id),
        target_type='User',
        request=request,
        tenant=tenant
    )

    return jsonify({'success': True, 'message': 'Usuario desactivado'})


@bp.route('/api/users/<user_id>/activate', methods=['POST'])
@login_required
@permission_required('users', 'edit')
def activate_user(user_id):
    """Reactivar usuario"""
    tenant = g.current_tenant
    try:
        user = User.objects.get(id=ObjectId(user_id))
    except DoesNotExist:
        return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404

    # Validar que el usuario pertenece al tenant actual
    if user.tenant != tenant:
        return jsonify({'success': False, 'error': 'Acceso denegado'}), 403

    user.is_active = True
    user.save()

    ActivityLog.log(
        user=current_user,
        action='activate',
        module='users',
        description=f'Reactivó usuario "{user.username}"',
        target_id=str(user.id),
        target_type='User',
        request=request,
        tenant=tenant
    )

    return jsonify({'success': True, 'message': 'Usuario activado'})


# ============================================
# ACTIVITY LOG / MONITOR
# ============================================

@bp.route('/activity')
@login_required
@permission_required('activity_log', 'view')
def activity_log():
    """Vista del monitor de actividades"""
    return render_template('admin/activity_log.html')


@bp.route('/api/activity', methods=['GET'])
@login_required
@permission_required('activity_log', 'view')
def get_activity_log():
    """Obtener log de actividades"""
    tenant = g.current_tenant

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    # Filters
    user_filter = request.args.get('user')
    action_filter = request.args.get('action')
    module_filter = request.args.get('module')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    query = ActivityLog.objects(tenant=tenant)

    if user_filter:
        query = query.filter(user=ObjectId(user_filter))
    if action_filter:
        query = query.filter(action=action_filter)
    if module_filter:
        query = query.filter(module=module_filter)
    if date_from:
        from datetime import datetime
        query = query.filter(created_at__gte=datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        from datetime import datetime, timedelta
        query = query.filter(created_at__lt=datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1))

    total = query.count()
    logs = query.order_by('-created_at').skip((page - 1) * per_page).limit(per_page)

    return jsonify({
        'success': True,
        'logs': [{
            'id': str(log.id),
            'user_name': log.user_name,
            'user_role': log.user_role,
            'action': log.action,
            'module': log.module,
            'description': log.description,
            'target_id': log.target_id,
            'target_type': log.target_type,
            'ip_address': log.ip_address,
            'created_at': log.created_at.strftime('%d/%m/%Y %H:%M:%S')
        } for log in logs],
        'total': total,
        'pages': (total + per_page - 1) // per_page,
        'current_page': page
    })


@bp.route('/api/activity/stats', methods=['GET'])
@login_required
@permission_required('activity_log', 'view')
def get_activity_stats():
    """Estadísticas de actividad"""
    tenant = g.current_tenant
    from datetime import datetime, timedelta

    # Last 24 hours
    since = utc_now() - timedelta(hours=24)
    recent_logs = ActivityLog.objects(tenant=tenant, created_at__gte=since)

    # Count by action
    action_counts = {}
    module_counts = {}
    user_counts = {}

    for log in recent_logs:
        action_counts[log.action] = action_counts.get(log.action, 0) + 1
        module_counts[log.module] = module_counts.get(log.module, 0) + 1
        user_counts[log.user_name] = user_counts.get(log.user_name, 0) + 1

    return jsonify({
        'success': True,
        'total_24h': recent_logs.count(),
        'by_action': action_counts,
        'by_module': module_counts,
        'by_user': user_counts
    })


# ============================================
# ROLES & PERMISSIONS INFO
# ============================================

@bp.route('/api/roles', methods=['GET'])
@login_required
@permission_required('users', 'view')
def get_roles():
    """Obtener información de roles y permisos"""
    return jsonify({
        'success': True,
        'roles': list(ROLE_PERMISSIONS.keys()),
        'permissions': ROLE_PERMISSIONS
    })


@bp.route('/api/my-permissions', methods=['GET'])
@login_required
def get_my_permissions():
    """Obtener permisos del usuario actual"""
    return jsonify({
        'success': True,
        'role': current_user.role,
        'permissions': current_user.get_permissions()
    })
