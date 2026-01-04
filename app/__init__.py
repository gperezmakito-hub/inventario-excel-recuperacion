"""
Aplicación Flask - Inventario de Tintas
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from config import config

# Inicializar extensiones
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, inicia sesión para acceder.'
login_manager.login_message_category = 'warning'


def create_app(config_name='default'):
    """Factory de la aplicación"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones con la app
    db.init_app(app)
    login_manager.init_app(app)
    
    # User loader para Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import Usuario
        return Usuario.query.get(int(user_id))
    
    # Registrar blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.productos import productos_bp
    from app.routes.movimientos import movimientos_bp
    from app.routes.proveedores import proveedores_bp
    from app.routes.compras import compras_bp
    from app.routes.reportes import reportes_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(productos_bp, url_prefix='/productos')
    app.register_blueprint(movimientos_bp, url_prefix='/movimientos')
    app.register_blueprint(proveedores_bp, url_prefix='/proveedores')
    app.register_blueprint(compras_bp, url_prefix='/compras')
    app.register_blueprint(reportes_bp, url_prefix='/reportes')
    
    # Contexto global para templates
    @app.context_processor
    def inject_globals():
        # Solo cargar datos si el usuario está autenticado
        if current_user.is_authenticated:
            from app.models import SolicitudCompra, Producto
            alertas_stock = Producto.query.filter(
                Producto.stock_actual <= Producto.stock_minimo,
                Producto.activo == True
            ).count()
            solicitudes_pendientes = SolicitudCompra.query.filter_by(
                estado='pendiente'
            ).count()
            return {
                'alertas_stock': alertas_stock,
                'solicitudes_pendientes': solicitudes_pendientes
            }
        return {
            'alertas_stock': 0,
            'solicitudes_pendientes': 0
        }
    
    return app
