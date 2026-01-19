from flask import Flask
from config import Config
from app.extensions import db, login_manager
from bson import ObjectId


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor inicia sesión para acceder a esta página."
    login_manager.login_message_category = "info"

    # User loader for Flask-Login (using ObjectId for MongoDB)
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.objects.get(id=ObjectId(user_id))
        except Exception:
            return None

    # Register blueprints
    from app.routes import main, api, reports, warehouse, auth

    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(warehouse.bp)

    # Custom Jinja2 filters
    @app.template_filter("translate_status")
    def translate_status(status):
        translations = {
            "pending": "pendiente",
            "delivered": "entregado",
            "cancelled": "cancelado",
            "assigned": "asignado",
            "in_transit": "en tránsito",
            "completed": "completado",
            "overdue": "vencido",
            "received": "recibido",
            "paid": "pagado",
        }
        return translations.get(status, status)

    # Middleware for Tenant Context
    from flask import session, g
    from app.models import Tenant
    from flask_login import current_user

    @app.before_request
    def load_tenant():
        # Si el usuario está autenticado, usar su tenant
        if current_user.is_authenticated and current_user.tenant:
            g.current_tenant = current_user.tenant
        else:
            tenant_id = session.get("tenant_id")
            if tenant_id:
                try:
                    g.current_tenant = Tenant.objects.get(id=ObjectId(tenant_id))
                except Exception:
                    g.current_tenant = None
            else:
                # Default to first tenant or None
                g.current_tenant = Tenant.objects(slug="puerto-distribucion").first()
                if g.current_tenant:
                    session["tenant_id"] = str(g.current_tenant.id)

    @app.context_processor
    def inject_tenant():
        return dict(
            current_tenant=g.get("current_tenant"),
            tenants=list(Tenant.objects.all())
        )

    return app
