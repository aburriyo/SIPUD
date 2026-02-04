"""
Authentication Blueprint
Maneja login, logout, gestión de usuarios y recuperación de contraseña
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from app.models import User, ActivityLog, utc_now
from app.extensions import mail
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash
from datetime import datetime

bp = Blueprint('auth', __name__)


def generate_reset_token(email):
    """Genera un token firmado para reset de contraseña"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')


def verify_reset_token(token):
    """Verifica y decodifica el token de reset"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    max_age = current_app.config.get('PASSWORD_RESET_TOKEN_MAX_AGE', 3600)
    try:
        return serializer.loads(token, salt='password-reset-salt', max_age=max_age)
    except (SignatureExpired, BadSignature):
        return None


def send_reset_email(user, token):
    """Envía el email de recuperación de contraseña"""
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    msg = Message(
        subject='Recuperar Contraseña - Puerto Distribución',
        recipients=[user.email],
        html=render_template('auth/email/reset_password.html',
                           user=user, reset_url=reset_url)
    )
    mail.send(msg)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.objects(username=username).first()

        if user and user.check_password(password) and user.is_active:
            remember = request.form.get('remember') == 'on'
            login_user(user, remember=remember)
            user.last_login = utc_now()
            user.save()

            # Log successful login
            ActivityLog.log(
                user=user,
                action='login',
                module='auth',
                description=f'Inició sesión exitosamente',
                request=request,
                tenant=user.tenant
            )

            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('main.dashboard'))
        else:
            # Log failed login attempt
            if user:
                ActivityLog.log(
                    user=user,
                    action='login_failed',
                    module='auth',
                    description=f'Intento de login fallido para usuario "{username}"',
                    request=request,
                    tenant=user.tenant if user else None
                )
            flash('Usuario o contraseña incorrectos', 'error')

    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    # Log logout before clearing session
    ActivityLog.log(
        user=current_user,
        action='logout',
        module='auth',
        description='Cerró sesión',
        request=request,
        tenant=current_user.tenant
    )
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


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Solicitar recuperación de contraseña"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash('Por favor ingresa tu correo electrónico', 'error')
            return render_template('auth/forgot_password.html')

        # Buscar usuario por email
        user = User.objects(email=email).first()

        if user and user.is_active:
            try:
                token = generate_reset_token(email)
                send_reset_email(user, token)

                # Log the password reset request
                ActivityLog.log(
                    user=user,
                    action='password_reset_request',
                    module='auth',
                    description=f'Solicitó recuperación de contraseña',
                    request=request,
                    tenant=user.tenant
                )
            except Exception as e:
                current_app.logger.error(f'Error sending reset email: {e}')
                flash('Error al enviar el correo. Por favor intenta más tarde.', 'error')
                return render_template('auth/forgot_password.html')

        # Mensaje genérico para no revelar si el email existe
        flash('Si el correo está registrado, recibirás instrucciones para recuperar tu contraseña.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Restablecer contraseña con token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    # Verificar token
    email = verify_reset_token(token)
    if not email:
        flash('El enlace de recuperación es inválido o ha expirado.', 'error')
        return redirect(url_for('auth.forgot_password'))

    # Buscar usuario
    user = User.objects(email=email).first()
    if not user:
        flash('El enlace de recuperación es inválido.', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validaciones
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('auth/reset_password.html', token=token)

        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('auth/reset_password.html', token=token)

        # Actualizar contraseña
        user.password_hash = generate_password_hash(password)
        user.save()

        # Log password change
        ActivityLog.log(
            user=user,
            action='password_reset_complete',
            module='auth',
            description='Restableció su contraseña exitosamente',
            request=request,
            tenant=user.tenant
        )

        flash('Tu contraseña ha sido actualizada. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)


@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Configuración de cuenta del usuario"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not current_user.check_password(current_password):
            flash('La contraseña actual es incorrecta', 'error')
            return render_template('auth/settings.html')

        if len(new_password) < 6:
            flash('La nueva contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('auth/settings.html')

        if new_password != confirm_password:
            flash('Las contraseñas nuevas no coinciden', 'error')
            return render_template('auth/settings.html')

        current_user.password_hash = generate_password_hash(new_password)
        current_user.save()

        ActivityLog.log(
            user=current_user,
            action='password_change',
            module='auth',
            description='Cambió su contraseña desde configuración',
            request=request,
            tenant=current_user.tenant
        )

        flash('Contraseña actualizada exitosamente', 'success')
        return redirect(url_for('auth.settings'))

    return render_template('auth/settings.html')
