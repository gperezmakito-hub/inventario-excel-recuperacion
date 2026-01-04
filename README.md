# Inventario Tintas - Sistema de Gestión de Inventario

Sistema web para gestión de inventario de tintas y pinturas, desarrollado en Flask con MySQL.

## 🚀 Características

- **Gestión de Productos**: Catálogo completo con categorías, proveedores y zonas de stock
- **Control de Stock**: Entradas y salidas con trazabilidad completa
- **Alertas Automáticas**: Notificación cuando el stock baja del mínimo
- **Flujo de Compras**: Solicitud → Aprobación → Pedido → Recepción
- **Reportes**: Inventario, movimientos, valoración con exportación CSV
- **Multi-usuario**: Roles de admin, oficina, almacén y consulta

## 📋 Requisitos

- Python 3.10+
- MySQL 8.0+ o MariaDB 10.5+
- pip

## 🔧 Instalación

1. **Clonar el repositorio** (si aplica)

2. **Crear entorno virtual e instalar dependencias**:
   ```bash
   # Windows
   setup.bat
   
   # Linux/Mac
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configurar base de datos MySQL**:
   ```sql
   CREATE DATABASE inventario_tintas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'inventario'@'localhost' IDENTIFIED BY 'tu_password';
   GRANT ALL PRIVILEGES ON inventario_tintas.* TO 'inventario'@'localhost';
   FLUSH PRIVILEGES;
   ```

4. **Configurar variables de entorno**:
   ```bash
   cp .env.example .env
   # Editar .env con tus credenciales
   ```

5. **Migrar datos desde Excel** (opcional):
   ```bash
   python scripts/migrar_excel.py
   ```

6. **Ejecutar la aplicación**:
   ```bash
   python run.py
   ```

7. **Abrir en el navegador**: http://localhost:5000

## 👥 Usuarios por defecto

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| admin | admin123 | Administrador |
| almacen | almacen123 | Almacén |
| oficina | oficina123 | Oficina |

## 📁 Estructura del Proyecto

```
inventario-tintas/
├── app/
│   ├── __init__.py          # Factory de la aplicación
│   ├── models.py             # Modelos SQLAlchemy
│   ├── routes/               # Blueprints
│   │   ├── main.py           # Dashboard
│   │   ├── auth.py           # Autenticación
│   │   ├── productos.py      # CRUD productos
│   │   ├── movimientos.py    # Entradas/Salidas
│   │   ├── proveedores.py    # CRUD proveedores
│   │   ├── compras.py        # Flujo de compras
│   │   └── reportes.py       # Informes
│   └── templates/            # Plantillas Jinja2
├── scripts/
│   └── migrar_excel.py       # Importador desde Excel
├── config.py                 # Configuración
├── requirements.txt          # Dependencias
└── run.py                    # Punto de entrada
```

## 🔄 Flujo de Compras

1. **Alerta**: Sistema detecta stock bajo mínimo
2. **Solicitud**: Almacén crea solicitud de compra
3. **Aprobación**: Oficina revisa y aprueba/rechaza
4. **Pedido**: Se registra pedido al proveedor
5. **Envío**: Se marca como enviado/en tránsito
6. **Recepción**: Almacén recibe y actualiza stock

## 📊 Roles y Permisos

| Acción | Admin | Oficina | Almacén | Consulta |
|--------|-------|---------|---------|----------|
| Ver dashboard | ✅ | ✅ | ✅ | ✅ |
| Editar productos | ✅ | ✅ | ❌ | ❌ |
| Crear solicitudes | ✅ | ✅ | ✅ | ❌ |
| Aprobar compras | ✅ | ✅ | ❌ | ❌ |
| Ver reportes | ✅ | ✅ | ✅ | ✅ |

## 🛠️ Desarrollo

```bash
# Activar entorno virtual
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Ejecutar en modo debug
python run.py
```

## 📄 Licencia

Uso interno - Todos los derechos reservados
