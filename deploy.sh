#!/bin/bash

# Script de deploy para servidor Ubuntu/Debian
# Uso: bash deploy.sh

echo "🚀 Iniciando deploy del Inventario Tintas..."

# Variables
APP_DIR="/root/inventario-excel-recuperacion"
REPO_URL="https://github.com/gperezmakito-hub/inventario-excel-recuperacion.git"
DB_NAME="inventario_tintas"
DB_USER="inventario_user"
DB_PASSWORD="Makito2024!"  # Cambiar por password seguro

# Actualizar sistema
echo "📦 Actualizando sistema..."
sudo apt-get update

# Instalar dependencias del sistema
echo "📦 Instalando dependencias..."
sudo apt-get install -y python3 python3-pip python3-venv python3-dev mysql-server libmysqlclient-dev git nodejs npm

# Instalar PM2 globalmente
echo "📦 Instalando PM2..."
sudo npm install -g pm2

# Crear directorio de aplicación si no existe
if [ ! -d "$APP_DIR" ]; then
    echo "📁 Clonando repositorio..."
    git clone $REPO_URL $APP_DIR
else
    echo "📁 Actualizando repositorio..."
    cd $APP_DIR
    git pull origin main
fi

cd $APP_DIR

# Crear entorno virtual
echo "🐍 Configurando entorno virtual Python..."
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias Python
echo "📦 Instalando dependencias Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Configurar MySQL
echo "🗄️  Configurando base de datos MySQL..."

# Asegurarse de que MySQL esté corriendo
sudo systemctl start mysql
sudo systemctl enable mysql

# Crear usuario y base de datos
sudo mysql <<EOF
-- Crear base de datos si no existe
CREATE DATABASE IF NOT EXISTS $DB_NAME;

-- Crear usuario si no existe y dar permisos
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

echo "✅ Base de datos configurada"

# Crear archivo .env si no existe
if [ ! -f ".env" ]; then
    echo "⚙️  Creando archivo .env..."
    cat > .env <<EOF
PORT=5010
FLASK_ENV=production
DATABASE_URL=mysql+pymysql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=False
EOF
    echo "✅ Archivo .env creado"
else
    echo "⚙️  Archivo .env ya existe, saltando..."
fi

# Crear directorio de logs
mkdir -p logs

# Inicializar base de datos (crear tablas)
echo "🗄️  Inicializando tablas de base de datos..."
python3 <<PYTHON
from app import app, db
with app.app_context():
    db.create_all()
    print("✅ Tablas creadas correctamente")
PYTHON

# Detener PM2 si está corriendo
echo "🔄 Deteniendo aplicación anterior..."
pm2 stop inventario-tintas 2>/dev/null || true
pm2 delete inventario-tintas 2>/dev/null || true

# Iniciar con PM2
echo "🚀 Iniciando aplicación con PM2..."
pm2 start ecosystem.config.js

# Guardar configuración PM2
pm2 save

# Configurar PM2 para inicio automático
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u root --hp /root

echo ""
echo "✅ ¡Deploy completado exitosamente!"
echo ""
echo "📊 Información del servicio:"
echo "   • URL: http://192.168.5.59:5010"
echo "   • Base de datos: $DB_NAME"
echo "   • Usuario DB: $DB_USER"
echo ""
echo "🔧 Comandos útiles:"
echo "   • Ver logs: pm2 logs inventario-tintas"
echo "   • Estado: pm2 status"
echo "   • Reiniciar: pm2 restart inventario-tintas"
echo "   • Detener: pm2 stop inventario-tintas"
echo ""
echo "🔗 Endpoints disponibles:"
echo "   • GET  http://192.168.5.59:5010/"
echo "   • GET  http://192.168.5.59:5010/health"
echo "   • GET  http://192.168.5.59:5010/api/productos"
echo "   • POST http://192.168.5.59:5010/api/productos"
echo ""
