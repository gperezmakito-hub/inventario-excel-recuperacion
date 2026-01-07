"""
Script para actualizar los proveedores de productos desde el Excel original.
Lee la columna 'Proveedor' de la hoja 'BASE DATOS' y actualiza la relación en la BD.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from app import create_app, db
from app.models import Producto, Proveedor

# Ruta al Excel
EXCEL_PATH = r'C:\Users\gonza\OneDrive\Documents\MAKITO\inventario-excel-recuperacion\INVENTARIO TINTAS PUBLINDAL_RECUPERADO.xlsx'

def actualizar_proveedores():
    app = create_app()
    
    with app.app_context():
        # Leer Excel con proveedores
        print("Leyendo Excel...")
        df = pd.read_excel(EXCEL_PATH, sheet_name='BASE DATOS', header=11)
        
        # Limpiar datos
        df = df.dropna(subset=['Código EAN'])
        df['Código EAN'] = df['Código EAN'].astype(str).str.strip()
        df['Proveedor'] = df['Proveedor'].fillna('').astype(str).str.strip()
        
        # Obtener proveedores únicos del Excel
        proveedores_excel = df['Proveedor'].unique()
        proveedores_excel = [p for p in proveedores_excel if p and p != 'nan']
        
        print(f"\nProveedores en Excel: {len(proveedores_excel)}")
        
        # Crear/actualizar proveedores en BD
        mapa_proveedores = {}  # nombre_excel -> id_bd
        
        for nombre_excel in proveedores_excel:
            # Buscar proveedor existente (por nombre exacto o similar)
            proveedor = Proveedor.query.filter(
                db.or_(
                    Proveedor.nombre == nombre_excel,
                    Proveedor.nombre.ilike(f'%{nombre_excel}%')
                )
            ).first()
            
            if not proveedor:
                # Crear nuevo proveedor
                proveedor = Proveedor(
                    nombre=nombre_excel,
                    activo=True
                )
                db.session.add(proveedor)
                db.session.flush()  # Para obtener el ID
                print(f"  + Nuevo proveedor: {nombre_excel}")
            else:
                print(f"  ✓ Proveedor existente: {nombre_excel} -> {proveedor.nombre}")
            
            mapa_proveedores[nombre_excel] = proveedor.id
        
        db.session.commit()
        print(f"\nTotal proveedores en BD: {Proveedor.query.count()}")
        
        # Actualizar productos con su proveedor
        print("\nActualizando productos...")
        actualizados = 0
        no_encontrados = 0
        
        for _, row in df.iterrows():
            codigo_ean = str(row['Código EAN']).strip()
            nombre_proveedor = str(row['Proveedor']).strip()
            
            if not nombre_proveedor or nombre_proveedor == 'nan':
                continue
            
            # Buscar producto por código EAN
            producto = Producto.query.filter_by(codigo_ean=codigo_ean).first()
            
            if producto:
                proveedor_id = mapa_proveedores.get(nombre_proveedor)
                if proveedor_id:
                    producto.proveedor_id = proveedor_id
                    actualizados += 1
            else:
                no_encontrados += 1
        
        db.session.commit()
        
        # Estadísticas finales
        print(f"\n=== RESUMEN ===")
        print(f"Productos actualizados: {actualizados}")
        print(f"Productos no encontrados en BD: {no_encontrados}")
        
        # Verificar resultado
        con_proveedor = Producto.query.filter(Producto.proveedor_id.isnot(None)).count()
        sin_proveedor = Producto.query.filter(Producto.proveedor_id.is_(None)).count()
        
        print(f"\nEstado final de productos:")
        print(f"  Con proveedor: {con_proveedor}")
        print(f"  Sin proveedor: {sin_proveedor}")

if __name__ == '__main__':
    actualizar_proveedores()
