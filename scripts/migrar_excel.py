#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de migración de datos Excel a SQLite
Importa productos, proveedores y movimientos del inventario Excel
"""

import os
import sys
from datetime import datetime
from decimal import Decimal

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from openpyxl import load_workbook

from app import create_app, db
from app.models import (
    Usuario, Categoria, ZonaStock, Producto, 
    Proveedor, Entrada, Salida
)

# Ruta al archivo Excel
EXCEL_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'inventario-excel-recuperacion',
    'INVENTARIO TINTAS PUBLINDAL_RECUPERADO.xlsx'
)


def limpiar_valor(valor):
    """Limpia un valor de celda"""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    if isinstance(valor, str):
        valor = valor.strip()
        return valor if valor else None
    return valor


def crear_usuarios():
    """Crea usuarios por defecto"""
    print("\n👤 Creando usuarios...")
    
    usuarios = [
        {'username': 'admin', 'password': 'admin123', 'nombre': 'Administrador', 
         'email': 'admin@publindal.com', 'rol': 'admin'},
        {'username': 'almacen', 'password': 'almacen123', 'nombre': 'Usuario Almacén', 
         'email': 'almacen@publindal.com', 'rol': 'almacen'},
        {'username': 'oficina', 'password': 'oficina123', 'nombre': 'Usuario Oficina', 
         'email': 'oficina@publindal.com', 'rol': 'oficina'},
    ]
    
    for u in usuarios:
        existente = Usuario.query.filter_by(username=u['username']).first()
        if not existente:
            usuario = Usuario(
                username=u['username'],
                nombre_completo=u['nombre'],
                email=u['email'],
                rol=u['rol'],
                activo=True
            )
            usuario.set_password(u['password'])
            db.session.add(usuario)
            print(f"   ✓ Usuario: {u['username']}")
        else:
            print(f"   Usuario {u['username']} ya existe")
    
    db.session.commit()


def crear_categorias():
    """Crea las categorías de productos"""
    print("\n📂 Creando categorías...")
    
    categorias = [
        ('TINTA SOLVENTE', 'Tintas base solvente'),
        ('TINTA UV', 'Tintas curado UV'),
        ('TINTA LATEX', 'Tintas látex'),
        ('TINTA SUBLIMACION', 'Tintas sublimación'),
        ('BARNIZ', 'Barnices y lacas'),
        ('LIMPIADOR', 'Limpiadores y disolventes'),
        ('DILUYENTE', 'Diluyentes y aditivos'),
        ('TAMPOGRAFÍA', 'Tintas para tampografía'),
        ('SERIGRAFÍA', 'Tintas para serigrafía'),
        ('OTROS', 'Otros productos'),
    ]
    
    categorias_map = {}
    for nombre, descripcion in categorias:
        existente = Categoria.query.filter_by(nombre=nombre).first()
        if not existente:
            cat = Categoria(nombre=nombre, descripcion=descripcion, activo=True)
            db.session.add(cat)
            db.session.flush()
            categorias_map[nombre] = cat.id
        else:
            categorias_map[nombre] = existente.id
    
    db.session.commit()
    print(f"   Total: {len(categorias)} categorías")
    return categorias_map


def crear_zonas_stock():
    """Crea las zonas de almacenamiento"""
    print("\n📍 Creando zonas de stock...")
    
    zonas = [
        ('ALTILLO', 'Zona del altillo'),
        ('POLIGONO', 'Almacén del polígono'),
        ('LABORATORIO', 'Zona de laboratorio'),
        ('PRINCIPAL', 'Almacén principal'),
    ]
    
    zonas_map = {}
    for nombre, descripcion in zonas:
        existente = ZonaStock.query.filter_by(nombre=nombre).first()
        if not existente:
            zona = ZonaStock(nombre=nombre, descripcion=descripcion)
            db.session.add(zona)
            db.session.flush()
            zonas_map[nombre.upper()] = zona.id
        else:
            zonas_map[nombre.upper()] = existente.id
    
    db.session.commit()
    print(f"   Total: {len(zonas)} zonas")
    return zonas_map


def importar_proveedores(excel_file):
    """Importa proveedores desde la hoja PROVEEDORES"""
    print("\n📦 Importando proveedores...")
    
    try:
        df = pd.read_excel(excel_file, 'PROVEEDORES', header=0)
    except Exception as e:
        print(f"   ⚠️  Error leyendo hoja PROVEEDORES: {e}")
        return {}
    
    proveedores_map = {}
    contador = 0
    
    for idx, row in df.iterrows():
        nombre = limpiar_valor(row.get('Unnamed: 0') or row.iloc[0] if len(row) > 0 else None)
        
        if not nombre or nombre == 'Empresa':
            continue
        
        # Saltar filas vacías o de encabezado
        if str(nombre).upper() in ('NAN', 'EMPRESA', 'PROVEEDOR'):
            continue
        
        # Verificar si ya existe
        existente = Proveedor.query.filter_by(nombre=nombre).first()
        if existente:
            proveedores_map[nombre] = existente.id
            proveedores_map[nombre.upper()] = existente.id
            continue
        
        # Extraer datos del proveedor
        nif = limpiar_valor(row.iloc[1]) if len(row) > 1 else None
        direccion = limpiar_valor(row.iloc[2]) if len(row) > 2 else None
        cp = limpiar_valor(row.iloc[3]) if len(row) > 3 else None
        municipio = limpiar_valor(row.iloc[4]) if len(row) > 4 else None
        provincia = limpiar_valor(row.iloc[5]) if len(row) > 5 else None
        telefono = limpiar_valor(row.iloc[6]) if len(row) > 6 else None
        web = limpiar_valor(row.iloc[7]) if len(row) > 7 else None
        email = limpiar_valor(row.iloc[10]) if len(row) > 10 else None
        contacto = limpiar_valor(row.iloc[13]) if len(row) > 13 else None
        movil = limpiar_valor(row.iloc[14]) if len(row) > 14 else None
        
        proveedor = Proveedor(
            nombre=str(nombre)[:150],
            nif=str(nif)[:20] if nif else None,
            direccion=str(direccion)[:200] if direccion else None,
            codigo_postal=str(cp)[:10] if cp else None,
            municipio=str(municipio)[:100] if municipio else None,
            provincia=str(provincia)[:100] if provincia else None,
            telefono=str(telefono)[:20] if telefono else None,
            web=str(web)[:200] if web else None,
            email=str(email)[:100] if email else None,
            contacto_nombre=str(contacto)[:100] if contacto else None,
            contacto_telefono=str(movil)[:20] if movil else None,
            activo=True
        )
        db.session.add(proveedor)
        db.session.flush()
        proveedores_map[nombre] = proveedor.id
        proveedores_map[nombre.upper()] = proveedor.id
        contador += 1
        print(f"   ✓ Proveedor: {nombre}")
    
    db.session.commit()
    print(f"   Total: {contador} proveedores importados")
    return proveedores_map


def detectar_categoria(nombre, serie, seccion):
    """Detecta la categoría basándose en el nombre, serie o sección del producto"""
    texto = f"{nombre or ''} {serie or ''} {seccion or ''}".upper()
    
    if 'DILUYENTE' in texto or 'ADITIVO' in texto or 'RETARDANTE' in texto:
        return 'DILUYENTE'
    if 'LIMPIA' in texto or 'WASH' in texto or 'CLEAN' in texto:
        return 'LIMPIADOR'
    if 'BARNIZ' in texto or 'LACA' in texto or 'VARNISH' in texto:
        return 'BARNIZ'
    if 'SUBLIM' in texto:
        return 'TINTA SUBLIMACION'
    if 'UV' in texto:
        return 'TINTA UV'
    if 'LATEX' in texto:
        return 'TINTA LATEX'
    if 'SOLVENT' in texto or 'SOLVENTE' in texto:
        return 'TINTA SOLVENTE'
    if 'TAMPOGRAFÍA' in texto or 'TAMPO' in texto or 'TP-' in texto:
        return 'TAMPOGRAFÍA'
    if 'SERIGRAFÍA' in texto or 'SERIMID' in texto or 'SERI' in texto:
        return 'SERIGRAFÍA'
    
    return 'OTROS'


def importar_productos(excel_file, proveedores_map, categorias_map, zonas_map):
    """Importa productos desde la hoja BASE DATOS"""
    print("\n🎨 Importando productos desde BASE DATOS...")
    
    try:
        # La hoja BASE DATOS tiene encabezados en la fila 12 (índice 11)
        df = pd.read_excel(excel_file, 'BASE DATOS', header=11)
    except Exception as e:
        print(f"   ⚠️  Error leyendo hoja BASE DATOS: {e}")
        return {}
    
    print(f"   Columnas encontradas: {list(df.columns)}")
    print(f"   Total filas: {len(df)}")
    
    productos_map = {}
    contador = 0
    errores = 0
    
    for idx, row in df.iterrows():
        try:
            # Extraer código EAN
            codigo_ean = limpiar_valor(row.get('Código EAN'))
            if not codigo_ean:
                continue
            
            # Convertir a string
            codigo_ean = str(codigo_ean).strip()
            
            # Saltar filas de encabezado o instrucciones
            if codigo_ean.upper() in ('CÓDIGO EAN', 'EAN', 'NAN') or len(codigo_ean) < 5:
                continue
            
            # Verificar si ya existe
            existente = Producto.query.filter_by(codigo_ean=codigo_ean).first()
            if existente:
                productos_map[codigo_ean] = existente.id
                continue
            
            # Extraer datos del producto
            codigo_proveedor = limpiar_valor(row.get('Cod. Provee.'))
            proveedor_nombre = limpiar_valor(row.get('Proveedor'))
            zona_stock = limpiar_valor(row.get('Zona Stock'))
            pintura = limpiar_valor(row.get('Pintura'))
            tipo_serie = limpiar_valor(row.get('Tipo Pintura / Serie'))
            color = limpiar_valor(row.get('Color'))
            kg_bote = limpiar_valor(row.get('kg. Bote'))
            nro_botes = limpiar_valor(row.get('Nº Botes'))
            cant_min = limpiar_valor(row.get('Cant. Min.'))
            precio = limpiar_valor(row.get('Precio'))
            dto1 = limpiar_valor(row.get('Dto.1'))
            dto2 = limpiar_valor(row.get('Dto.2'))
            seccion = limpiar_valor(row.get('SECCIÓN'))
            
            # Construir nombre del producto
            nombre = tipo_serie or pintura or f"Producto {codigo_ean}"
            
            # Convertir valores numéricos
            try:
                kg_bote = float(kg_bote) if kg_bote else None
            except (ValueError, TypeError):
                kg_bote = None
            
            try:
                stock = int(float(nro_botes)) if nro_botes else 0
            except (ValueError, TypeError):
                stock = 0
            
            try:
                stock_min = int(float(cant_min)) if cant_min and str(cant_min).upper() != 'NO' else 0
            except (ValueError, TypeError):
                stock_min = 0
            
            try:
                precio_compra = float(precio) if precio else 0.0
            except (ValueError, TypeError):
                precio_compra = 0.0
            
            try:
                descuento1 = float(dto1) if dto1 else 0.0
            except (ValueError, TypeError):
                descuento1 = 0.0
            
            try:
                descuento2 = float(dto2) if dto2 else 0.0
            except (ValueError, TypeError):
                descuento2 = 0.0
            
            # Buscar proveedor
            proveedor_id = None
            if proveedor_nombre:
                proveedor_id = proveedores_map.get(proveedor_nombre) or proveedores_map.get(proveedor_nombre.upper())
            
            # Buscar zona
            zona_id = None
            if zona_stock:
                zona_id = zonas_map.get(str(zona_stock).upper())
            
            # Detectar categoría
            categoria_nombre = detectar_categoria(nombre, tipo_serie, seccion)
            categoria_id = categorias_map.get(categoria_nombre, categorias_map.get('OTROS'))
            
            # Crear producto
            producto = Producto(
                codigo_ean=codigo_ean,
                codigo_proveedor=str(codigo_proveedor)[:50] if codigo_proveedor else None,
                nombre=str(nombre)[:150],
                color=str(color)[:100] if color else None,
                peso_unidad=kg_bote,
                stock_actual=stock,
                stock_minimo=stock_min,
                precio_compra=precio_compra,
                dto_1=descuento1,
                dto_2=descuento2,
                categoria_id=categoria_id,
                zona_id=zona_id,
                proveedor_id=proveedor_id,
                activo=True
            )
            
            db.session.add(producto)
            db.session.flush()
            productos_map[codigo_ean] = producto.id
            contador += 1
            
            if contador % 100 == 0:
                print(f"   ... {contador} productos procesados")
                
        except Exception as e:
            errores += 1
            if errores <= 5:
                print(f"   ⚠️  Error en fila {idx}: {e}")
    
    db.session.commit()
    print(f"   ✓ Total: {contador} productos importados ({errores} errores)")
    return productos_map


def importar_entradas(excel_file, productos_map):
    """Importa movimientos de entrada"""
    print("\n📥 Importando entradas...")
    
    # Por ahora no importamos entradas históricas, 
    # ya que el stock actual ya está en los productos
    print("   ℹ️  Stock actual importado directamente en productos")
    print("   ✓ Total: 0 entradas (stock ya incluido en productos)")


def importar_salidas(excel_file, productos_map):
    """Importa movimientos de salida"""
    print("\n📤 Importando salidas...")
    
    # Por ahora no importamos salidas históricas
    print("   ℹ️  Historial de salidas no importado")
    print("   ✓ Total: 0 salidas")


def main():
    """Función principal de migración"""
    print("=" * 60)
    print("🔄 MIGRACIÓN DE DATOS EXCEL A SQLITE")
    print("=" * 60)
    
    if not os.path.exists(EXCEL_FILE):
        print(f"\n❌ Error: No se encuentra el archivo Excel")
        print(f"   Ruta: {EXCEL_FILE}")
        return
    
    print(f"\n📄 Archivo: {EXCEL_FILE}")
    
    # Crear aplicación Flask
    app = create_app()
    
    with app.app_context():
        # Crear tablas
        print("\n🗄️  Creando tablas de base de datos...")
        db.create_all()
        
        # Ejecutar migración
        crear_usuarios()
        categorias_map = crear_categorias()
        zonas_map = crear_zonas_stock()
        proveedores_map = importar_proveedores(EXCEL_FILE)
        productos_map = importar_productos(EXCEL_FILE, proveedores_map, categorias_map, zonas_map)
        importar_entradas(EXCEL_FILE, productos_map)
        importar_salidas(EXCEL_FILE, productos_map)
        
        print("\n" + "=" * 60)
        print("✅ MIGRACIÓN COMPLETADA")
        print("=" * 60)
        
        print("\nUsuarios creados:")
        print("  - admin / admin123 (Administrador)")
        print("  - almacen / almacen123 (Almacén)")
        print("  - oficina / oficina123 (Oficina)")
        
        # Resumen
        total_productos = Producto.query.count()
        total_proveedores = Proveedor.query.count()
        total_categorias = Categoria.query.count()
        
        print(f"\nResumen de datos:")
        print(f"  - {total_productos} productos")
        print(f"  - {total_proveedores} proveedores")
        print(f"  - {total_categorias} categorías")
        
        print("\nAhora puedes ejecutar la aplicación con: python run.py")


if __name__ == '__main__':
    main()
