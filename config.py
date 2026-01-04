"""
Configuración de la aplicación Inventario de Tintas
"""
import os
from datetime import timedelta

# Directorio base del proyecto
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Configuración base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-cambiar-en-produccion-2024'
    
    # Base de datos - SQLite por defecto, MySQL opcional
    # Para usar MySQL: establecer variable de entorno USE_MYSQL=1
    USE_MYSQL = os.environ.get('USE_MYSQL', '0') == '1'
    
    if USE_MYSQL:
        # MySQL Database
        MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
        MYSQL_PORT = os.environ.get('MYSQL_PORT') or 3306
        MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
        MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''
        MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'inventario_tintas'
        
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@"
            f"{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
        )
    else:
        # SQLite (no requiere instalación)
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'inventario.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
    
    # Sesión
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Paginación
    ITEMS_PER_PAGE = 25
    
    # Alertas de stock
    ALERTA_STOCK_MINIMO = True
    DIAS_REVISION_STOCK = 1  # Revisar stock cada día


class DevelopmentConfig(Config):
    """Configuración de desarrollo"""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Ver queries SQL en consola


class ProductionConfig(Config):
    """Configuración de producción"""
    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestConfig(Config):
    """Configuración de testing"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestConfig,
    'default': DevelopmentConfig
}
