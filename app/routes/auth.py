"""
Authentication Blueprint
Maneja login, logout y gestión de usuarios
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User
from datetime import datetime

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('main.dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/api/check-session')
def check_session():
    """API para verificar si hay sesión activa"""
    return jsonify({
        'authenticated': current_user.is_authenticated,
        'user': {
            'username': current_user.username,
            'role': current_user.role,
            'full_name': current_user.full_name
        } if current_user.is_authenticated else None
    })
