"""
Rutas principales y dashboard
"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import Producto, Entrada, Salida, SolicitudCompra, Proveedor
from app import db
from sqlalchemy import func
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Página principal - redirige al dashboard o login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal con resumen del sistema"""
    
    # Estadísticas generales
    stats = {
        'total_productos': Producto.query.filter_by(activo=True).count(),
        'total_proveedores': Proveedor.query.filter_by(activo=True).count(),
        'productos_stock_bajo': Producto.query.filter(
            Producto.stock_actual <= Producto.stock_minimo,
            Producto.activo == True
        ).count(),
    }
    
    # Solicitudes por estado
    solicitudes_stats = db.session.query(
        SolicitudCompra.estado,
        func.count(SolicitudCompra.id)
    ).group_by(SolicitudCompra.estado).all()
    stats['solicitudes'] = dict(solicitudes_stats)
    
    # Movimientos del mes
    inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    stats['entradas_mes'] = Entrada.query.filter(
        Entrada.fecha >= inicio_mes
    ).count()
    stats['salidas_mes'] = Salida.query.filter(
        Salida.fecha >= inicio_mes
    ).count()
    
    # Valor total del inventario
    valor_inventario = db.session.query(
        func.sum(Producto.stock_actual * Producto.precio_compra)
    ).filter(Producto.activo == True).scalar() or 0
    stats['valor_inventario'] = round(float(valor_inventario), 2)
    
    # Productos con stock bajo (para la tabla de alertas)
    productos_stock_bajo = Producto.query.filter(
        Producto.stock_actual <= Producto.stock_minimo,
        Producto.activo == True
    ).order_by(Producto.stock_actual).limit(10).all()
    
    # Solicitudes pendientes de aprobar (lista para mostrar en dashboard)
    lista_solicitudes_pendientes = SolicitudCompra.query.filter_by(
        estado='pendiente'
    ).order_by(SolicitudCompra.fecha_creacion.desc()).limit(5).all()
    
    # Solicitudes en curso (pedidas o en tránsito)
    solicitudes_en_curso = SolicitudCompra.query.filter(
        SolicitudCompra.estado.in_(['pedida', 'en_transito'])
    ).order_by(SolicitudCompra.fecha_pedido.desc()).limit(5).all()
    
    # Últimos movimientos
    ultimas_entradas = Entrada.query.order_by(
        Entrada.fecha.desc()
    ).limit(5).all()
    ultimas_salidas = Salida.query.order_by(
        Salida.fecha.desc()
    ).limit(5).all()
    
    return render_template('dashboard.html',
                           stats=stats,
                           productos_stock_bajo=productos_stock_bajo,
                           lista_solicitudes_pendientes=lista_solicitudes_pendientes,
                           solicitudes_en_curso=solicitudes_en_curso,
                           ultimas_entradas=ultimas_entradas,
                           ultimas_salidas=ultimas_salidas)
