from flask import Flask
from config import Config
from app.extensions import db, migrate, login_manager

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'

    # User loader for Flask-Login
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from app.routes import main, api, logistics, reports, warehouse, auth
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(logistics.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(warehouse.bp)

    # Custom Jinja2 filters
    @app.template_filter('translate_status')
    def translate_status(status):
        translations = {
            'pending': 'pendiente',
            'delivered': 'entregado',
            'cancelled': 'cancelado',
            'assigned': 'asignado',
            'in_transit': 'en tránsito',
            'completed': 'completado',
            'overdue': 'vencido',
            'received': 'recibido',
            'paid': 'pagado'
        }
        return translations.get(status, status)

    # Middleware for Tenant Context
    from flask import session, g
    from app.models import Tenant
    from flask_login import current_user

    @app.before_request
    def load_tenant():
        # Si el usuario está autenticado, usar su tenant
        if current_user.is_authenticated and current_user.tenant_id:
            g.current_tenant = Tenant.query.get(current_user.tenant_id)
        else:
            tenant_id = session.get('tenant_id')
            if tenant_id:
                g.current_tenant = Tenant.query.get(tenant_id)
            else:
                # Default to first tenant or None
                g.current_tenant = Tenant.query.filter_by(slug='puerto-distribucion').first()
                if g.current_tenant:
                    session['tenant_id'] = g.current_tenant.id

    @app.context_processor
    def inject_tenant():
        return dict(current_tenant=g.get('current_tenant'), tenants=Tenant.query.all())

    return app
