"""
Punto de entrada de la aplicación
"""
import os
from app import create_app, db

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Crear aplicación
config_name = os.environ.get('FLASK_ENV') or 'development'
app = create_app(config_name)

if __name__ == '__main__':
    with app.app_context():
        # Crear tablas si no existen
        db.create_all()
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG']
    )
