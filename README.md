# Recuperación de Inventarios Excel

Proyecto para gestión y recuperación de inventarios Excel - MKTO CATAL IMPORTACIONES

## Descripción
Sistema de control y gestión del inventario de tintas del taller. Este proyecto contiene scripts de Python para recuperar datos de archivos Excel (.xlsm) protegidos con contraseña de macros/licencia.

## Archivos

### Originales (protegidos)
- `INVENTARIO TINTAS PUBLINDAL.xlsm` - Inventario de tintas (19 hojas)
- `INVENTARIO PLASTICO-CARTON.xlsm` - Inventario de plástico/cartón (13 hojas)

### Recuperados (sin protección)
- `INVENTARIO TINTAS PUBLINDAL_RECUPERADO.xlsx` - Datos extraídos sin macros
- `INVENTARIO PLASTICO-CARTON_RECUPERADO.xlsx` - Datos extraídos sin macros

## Scripts

- `extraer_datos.py` - Script para extraer un archivo individual
- `extraer_todos.py` - Script para extraer todos los archivos .xlsm

## Uso

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

## Notas
- Los archivos recuperados contienen solo los datos (valores), no el formato visual
- Las macros VBA fueron eliminadas para evitar la solicitud de licencia

## Autor
Gonzalo Pérez (gperezmakito-hub)
