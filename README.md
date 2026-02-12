# Recuperación de Inventarios Excel

Proyecto para gestión y recuperación de inventarios Excel - MKTO CATAL IMPORTACIONES

## 🚀 API REST para Gestión de Inventario

Esta aplicación proporciona una API REST completa para gestionar el inventario de tintas, con base de datos PostgreSQL y despliegue en servidor con PM2.

## 📋 Características

- ✅ API REST completa (CRUD de productos y movimientos)
- ✅ Base de datos MySQL
- ✅ Gestión de stock en tiempo real
- ✅ Control de movimientos (entrada/salida/ajuste)
- ✅ Estadísticas de inventario
- ✅ Deploy automatizado con PM2
- ✅ Extracción de datos desde archivos Excel protegidos

## 🛠️ Tecnologías

- **Backend:** Python 3, Flask
- **Base de datos:** MySQL
- **Servidor:** Gunicorn + PM2
- **ORM:** SQLAlchemy

## 📁 Archivos del Proyecto

### Scripts de Extracción
- `extraer_datos.py` - Script para extraer un archivo individual
- `extraer_todos.py` - Script para extraer todos los archivos .xlsm

### Archivos Excel
- `INVENTARIO TINTAS PUBLINDAL.xlsm` - Inventario de tintas (19 hojas)
- `INVENTARIO PLASTICO-CARTON.xlsm` - Inventario de plástico/cartón (13 hojas)

## 🚀 Deploy en Servidor (192.168.5.59)

### Opción 1: Deploy Automático (Recomendado)

```bash
# Conectar al servidor
ssh root@192.168.5.59

# Descargar y ejecutar script de deploy
curl -o deploy.sh https://raw.githubusercontent.com/gperezmakito-hub/inventario-excel-recuperacion/main/deploy.sh
chmod +x deploy.sh
bash deploy.sh
```

El script automáticamente:
1. ✅ Instala todas las dependencias (Python, MySQL, Node.js, PM2)
2. ✅ Clona el repositorio
3. ✅ Crea la base de datos MySQL
4. ✅ Configura el entorno virtual Python
5. ✅ Crea las tablas de la base de datos
6. ✅ Inicia la aplicación con PM2 en el puerto 5010

### Opción 2: Deploy Manual

Ver sección completa en la documentación detallada.

## 🔧 Gestión del Servicio

```bash
# Ver estado
pm2 status

# Ver logs en tiempo real
pm2 logs inventario-tintas

# Reiniciar
pm2 restart inventario-tintas

# Actualizar desde GitHub
cd /root/inventario-excel-recuperacion
git pull origin main
pm2 restart inventario-tintas
```

## 📡 Endpoints de la API

### General
- `GET /` - Información de la API
- `GET /health` - Estado del servidor

### Productos
- `GET /api/productos` - Listar todos los productos
- `POST /api/productos` - Crear producto
- `PUT /api/productos/<id>` - Actualizar producto
- `DELETE /api/productos/<id>` - Desactivar producto

### Movimientos
- `GET /api/movimientos` - Listar movimientos
- `POST /api/movimientos` - Registrar movimiento (entrada/salida/ajuste)

### Estadísticas
- `GET /api/estadisticas` - Estadísticas generales del inventario

## 📝 Uso de Scripts de Extracción

```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno (Windows)
.venv\Scripts\activate

# Instalar dependencias
pip install openpyxl

# Ejecutar extracción
python extraer_todos.py
```

## 🗄️ Estructura de la Base de Datos

### Tabla: productos
- Código, nombre, categoría, unidad
- Stock actual, stock mínimo, precio unitario
- Ubicación, observaciones, estado activo

### Tabla: movimientos
- Tipo: entrada, salida o ajuste
- Cantidad, motivo, usuario, fecha
- Relación con producto

## 👨‍💻 Autor

Gonzalo Pérez ([gperezmakito-hub](https://github.com/gperezmakito-hub))  
MKTO CATAL IMPORTACIONES, S.L

---

**Servidor de producción:** http://192.168.5.59:5010
