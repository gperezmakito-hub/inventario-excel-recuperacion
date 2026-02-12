"""
Rutas de reportes y estadísticas
"""
from flask import Blueprint, render_template, request, Response
from flask_login import login_required
from app.models import Producto, Entrada, Salida, SolicitudCompra, Proveedor
from app import db
from sqlalchemy import func
from datetime import datetime, timedelta
import csv
import io

reportes_bp = Blueprint('reportes', __name__)


@reportes_bp.route('/')
@login_required
def index():
    """Índice de reportes disponibles"""
    return render_template('reportes/index.html')


@reportes_bp.route('/inventario')
@login_required
def inventario():
    """Reporte de inventario actual"""
    # Filtros
    categoria_id = request.args.get('categoria', type=int)
    proveedor_id = request.args.get('proveedor', type=int)
    solo_stock_bajo = request.args.get('stock_bajo', False, type=bool)
    
    query = Producto.query.filter_by(activo=True)
    
    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)
    if proveedor_id:
        query = query.filter_by(proveedor_id=proveedor_id)
    if solo_stock_bajo:
        query = query.filter(
            Producto.stock_actual <= Producto.stock_minimo,
            Producto.stock_minimo > 0
        )
    
    productos = query.order_by(Producto.nombre).all()
    
    # Calcular totales
    total_unidades = sum(p.stock_actual for p in productos)
    total_valor = sum(p.valor_inventario for p in productos)
    productos_bajo_minimo = sum(1 for p in productos if p.stock_bajo)
    
    return render_template('reportes/inventario.html',
                           productos=productos,
                           total_unidades=total_unidades,
                           total_valor=total_valor,
                           productos_bajo_minimo=productos_bajo_minimo)


@reportes_bp.route('/movimientos')
@login_required
def movimientos():
    """Reporte de movimientos"""
    # Fechas por defecto: último mes
    fecha_hasta = datetime.now()
    fecha_desde = fecha_hasta - timedelta(days=30)
    
    if request.args.get('fecha_desde'):
        fecha_desde = datetime.strptime(request.args.get('fecha_desde'), '%Y-%m-%d')
    if request.args.get('fecha_hasta'):
        fecha_hasta = datetime.strptime(request.args.get('fecha_hasta'), '%Y-%m-%d')
    
    # Entradas del período
    entradas = Entrada.query.filter(
        Entrada.fecha >= fecha_desde,
        Entrada.fecha <= fecha_hasta
    ).all()
    
    # Salidas del período
    salidas = Salida.query.filter(
        Salida.fecha >= fecha_desde,
        Salida.fecha <= fecha_hasta
    ).all()
    
    # Totales
    total_entradas = sum(e.cantidad for e in entradas)
    total_salidas = sum(s.cantidad for s in salidas)
    valor_entradas = sum(e.precio_total for e in entradas)
    valor_salidas = sum(s.valor for s in salidas)
    
    return render_template('reportes/movimientos.html',
                           entradas=entradas,
                           salidas=salidas,
                           fecha_desde=fecha_desde,
                           fecha_hasta=fecha_hasta,
                           total_entradas=total_entradas,
                           total_salidas=total_salidas,
                           valor_entradas=valor_entradas,
                           valor_salidas=valor_salidas)


@reportes_bp.route('/compras')
@login_required
def compras():
    """Reporte de solicitudes de compra"""
    # Fechas por defecto: último trimestre
    fecha_hasta = datetime.now()
    fecha_desde = fecha_hasta - timedelta(days=90)
    
    if request.args.get('fecha_desde'):
        fecha_desde = datetime.strptime(request.args.get('fecha_desde'), '%Y-%m-%d')
    if request.args.get('fecha_hasta'):
        fecha_hasta = datetime.strptime(request.args.get('fecha_hasta'), '%Y-%m-%d')
    
    solicitudes = SolicitudCompra.query.filter(
        SolicitudCompra.fecha_creacion >= fecha_desde,
        SolicitudCompra.fecha_creacion <= fecha_hasta
    ).order_by(SolicitudCompra.fecha_creacion.desc()).all()
    
    # Estadísticas por estado
    por_estado = db.session.query(
        SolicitudCompra.estado,
        func.count(SolicitudCompra.id)
    ).filter(
        SolicitudCompra.fecha_creacion >= fecha_desde,
        SolicitudCompra.fecha_creacion <= fecha_hasta
    ).group_by(SolicitudCompra.estado).all()
    
    # Tiempo promedio de aprobación
    tiempos = []
    for s in solicitudes:
        if s.fecha_aprobacion and s.fecha_creacion:
            delta = s.fecha_aprobacion - s.fecha_creacion
            tiempos.append(delta.total_seconds() / 3600)  # En horas
    
    tiempo_promedio_aprobacion = sum(tiempos) / len(tiempos) if tiempos else 0
    
    return render_template('reportes/compras.html',
                           solicitudes=solicitudes,
                           fecha_desde=fecha_desde,
                           fecha_hasta=fecha_hasta,
                           por_estado=dict(por_estado),
                           tiempo_promedio_aprobacion=round(tiempo_promedio_aprobacion, 1))


@reportes_bp.route('/valoracion')
@login_required
def valoracion():
    """Valoración del inventario"""
    # Agrupado por proveedor
    por_proveedor = db.session.query(
        Proveedor.nombre,
        func.count(Producto.id),
        func.sum(Producto.stock_actual),
        func.sum(Producto.stock_actual * Producto.precio_compra)
    ).join(Producto).filter(
        Producto.activo == True
    ).group_by(Proveedor.id).all()
    
    # Total general
    total = db.session.query(
        func.sum(Producto.stock_actual * Producto.precio_compra)
    ).filter(Producto.activo == True).scalar() or 0
    
    return render_template('reportes/valoracion.html',
                           por_proveedor=por_proveedor,
                           total_valoracion=float(total))


# =============================================================================
# EXPORTACIONES CSV
# =============================================================================

@reportes_bp.route('/exportar/inventario')
@login_required
def exportar_inventario():
    """Exportar inventario a CSV"""
    productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre).all()
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Cabecera
    writer.writerow([
        'Código EAN', 'Nombre', 'Color', 'Stock Actual', 'Stock Mínimo',
        'Precio Compra', 'Valor Inventario', 'Proveedor', 'Categoría'
    ])
    
    # Datos
    for p in productos:
        writer.writerow([
            p.codigo_ean,
            p.nombre,
            p.color or '',
            p.stock_actual,
            p.stock_minimo,
            float(p.precio_compra) if p.precio_compra else 0,
            p.valor_inventario,
            p.proveedor.nombre if p.proveedor else '',
            p.categoria.nombre if p.categoria else ''
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=inventario_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )


@reportes_bp.route('/exportar/movimientos')
@login_required
def exportar_movimientos():
    """Exportar movimientos a CSV"""
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    if not fecha_desde or not fecha_hasta:
        fecha_hasta = datetime.now()
        fecha_desde = fecha_hasta - timedelta(days=30)
    else:
        fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
        fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d')
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Cabecera
    writer.writerow([
        'Tipo', 'Fecha', 'Nº Registro', 'Código EAN', 'Producto',
        'Cantidad', 'Precio Unit.', 'Total', 'Proveedor/Destino', 'Usuario'
    ])
    
    # Entradas
    entradas = Entrada.query.filter(
        Entrada.fecha >= fecha_desde,
        Entrada.fecha <= fecha_hasta
    ).all()
    
    for e in entradas:
        writer.writerow([
            'ENTRADA',
            e.fecha.strftime('%Y-%m-%d %H:%M'),
            e.numero_registro,
            e.producto.codigo_ean,
            e.producto.nombre,
            e.cantidad,
            float(e.precio_unitario) if e.precio_unitario else 0,
            e.precio_total,
            e.proveedor.nombre if e.proveedor else '',
            e.usuario.nombre_completo if e.usuario else ''
        ])
    
    # Salidas
    salidas = Salida.query.filter(
        Salida.fecha >= fecha_desde,
        Salida.fecha <= fecha_hasta
    ).all()
    
    for s in salidas:
        writer.writerow([
            'SALIDA',
            s.fecha.strftime('%Y-%m-%d %H:%M'),
            s.numero_registro,
            s.producto.codigo_ean,
            s.producto.nombre,
            s.cantidad,
            float(s.producto.precio_compra) if s.producto.precio_compra else 0,
            s.valor,
            s.destino or '',
            s.usuario.nombre_completo if s.usuario else ''
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=movimientos_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )
