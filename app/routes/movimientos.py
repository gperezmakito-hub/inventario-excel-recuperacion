"""
Rutas de movimientos de inventario (entradas y salidas)
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Producto, Entrada, Salida, Proveedor
from app import db
from datetime import datetime
from functools import wraps

movimientos_bp = Blueprint('movimientos', __name__)


def requiere_permiso_movimientos(f):
    """Decorador para verificar permiso de movimientos"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.puede_registrar_movimientos():
            flash('No tienes permiso para registrar movimientos.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# =============================================================================
# ENTRADAS
# =============================================================================

@movimientos_bp.route('/entradas')
@login_required
def listar_entradas():
    """Listado de entradas"""
    page = request.args.get('page', 1, type=int)
    
    # Filtros
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    proveedor_id = request.args.get('proveedor', type=int)
    buscar = request.args.get('buscar', '').strip()
    
    query = Entrada.query
    
    if fecha_desde:
        query = query.filter(Entrada.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d'))
    if fecha_hasta:
        query = query.filter(Entrada.fecha <= datetime.strptime(fecha_hasta + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
    if proveedor_id:
        query = query.filter_by(proveedor_id=proveedor_id)
    if buscar:
        query = query.join(Producto).filter(
            db.or_(
                Producto.codigo_ean.ilike(f'%{buscar}%'),
                Producto.nombre.ilike(f'%{buscar}%'),
                Entrada.albaran.ilike(f'%{buscar}%'),
                Entrada.factura.ilike(f'%{buscar}%')
            )
        )
    
    entradas = query.order_by(Entrada.fecha.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    
    proveedores = Proveedor.query.filter_by(activo=True).order_by(Proveedor.nombre).all()
    
    return render_template('movimientos/entradas_listar.html',
                           entradas=entradas,
                           proveedores=proveedores)


@movimientos_bp.route('/entradas/nueva', methods=['GET', 'POST'])
@login_required
@requiere_permiso_movimientos
def nueva_entrada():
    """Registrar nueva entrada"""
    if request.method == 'POST':
        producto_id = request.form.get('producto_id', type=int)
        producto = Producto.query.get_or_404(producto_id)
        
        cantidad = request.form.get('cantidad', 0, type=int)
        if cantidad <= 0:
            flash('La cantidad debe ser mayor que 0.', 'warning')
            return redirect(url_for('movimientos.nueva_entrada'))
        
        # Generar número de registro
        ultimo = Entrada.query.order_by(Entrada.numero_registro.desc()).first()
        numero_registro = (ultimo.numero_registro + 1) if ultimo else 1
        
        entrada = Entrada(
            numero_registro=numero_registro,
            fecha=datetime.now(),
            producto_id=producto_id,
            cantidad=cantidad,
            albaran=request.form.get('albaran', '').strip() or None,
            factura=request.form.get('factura', '').strip() or None,
            precio_unitario=request.form.get('precio_unitario', type=float) or producto.precio_compra,
            dto_1=request.form.get('dto_1', 0, type=float),
            dto_2=request.form.get('dto_2', 0, type=float),
            proveedor_id=request.form.get('proveedor_id', type=int) or producto.proveedor_id,
            usuario_id=current_user.id,
            notas=request.form.get('notas', '').strip() or None
        )
        
        # Actualizar stock del producto
        producto.stock_actual += cantidad
        producto.fecha_ultima_entrada = datetime.now()
        
        # Actualizar precio si se proporciona uno nuevo
        if request.form.get('actualizar_precio'):
            producto.precio_compra = entrada.precio_unitario
        
        db.session.add(entrada)
        db.session.commit()
        
        flash(f'Entrada registrada. Stock actual de "{producto.nombre}": {producto.stock_actual}', 'success')
        return redirect(url_for('movimientos.listar_entradas'))
    
    proveedores = Proveedor.query.filter_by(activo=True).order_by(Proveedor.nombre).all()
    producto_id = request.args.get('producto_id', type=int)
    producto = Producto.query.get(producto_id) if producto_id else None
    
    return render_template('movimientos/entrada_form.html',
                           proveedores=proveedores,
                           producto_preseleccionado=producto)


@movimientos_bp.route('/entradas/<int:id>')
@login_required
def ver_entrada(id):
    """Ver detalle de una entrada"""
    entrada = Entrada.query.get_or_404(id)
    return render_template('movimientos/entrada_ver.html', entrada=entrada)


# =============================================================================
# SALIDAS
# =============================================================================

@movimientos_bp.route('/salidas')
@login_required
def listar_salidas():
    """Listado de salidas"""
    page = request.args.get('page', 1, type=int)
    
    # Filtros
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    buscar = request.args.get('buscar', '').strip()
    
    query = Salida.query
    
    if fecha_desde:
        query = query.filter(Salida.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d'))
    if fecha_hasta:
        query = query.filter(Salida.fecha <= datetime.strptime(fecha_hasta + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
    if buscar:
        query = query.join(Producto).filter(
            db.or_(
                Producto.codigo_ean.ilike(f'%{buscar}%'),
                Producto.nombre.ilike(f'%{buscar}%'),
                Salida.destino.ilike(f'%{buscar}%')
            )
        )
    
    salidas = query.order_by(Salida.fecha.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    
    return render_template('movimientos/salidas_listar.html', salidas=salidas)


@movimientos_bp.route('/salidas/nueva', methods=['GET', 'POST'])
@login_required
@requiere_permiso_movimientos
def nueva_salida():
    """Registrar nueva salida"""
    if request.method == 'POST':
        producto_id = request.form.get('producto_id', type=int)
        producto = Producto.query.get_or_404(producto_id)
        
        cantidad = request.form.get('cantidad', 0, type=int)
        if cantidad <= 0:
            flash('La cantidad debe ser mayor que 0.', 'warning')
            return redirect(url_for('movimientos.nueva_salida'))
        
        if cantidad > producto.stock_actual:
            flash(f'Stock insuficiente. Stock actual: {producto.stock_actual}', 'danger')
            return redirect(url_for('movimientos.nueva_salida'))
        
        # Generar número de registro
        ultimo = Salida.query.order_by(Salida.numero_registro.desc()).first()
        numero_registro = (ultimo.numero_registro + 1) if ultimo else 1
        
        salida = Salida(
            numero_registro=numero_registro,
            fecha=datetime.now(),
            producto_id=producto_id,
            cantidad=cantidad,
            destino=request.form.get('destino', '').strip() or None,
            usuario_id=current_user.id,
            notas=request.form.get('notas', '').strip() or None
        )
        
        # Actualizar stock del producto
        producto.stock_actual -= cantidad
        producto.fecha_ultima_salida = datetime.now()
        
        db.session.add(salida)
        db.session.commit()
        
        # Verificar si el stock quedó bajo el mínimo
        if producto.stock_bajo:
            flash(f'⚠️ ALERTA: El stock de "{producto.nombre}" está por debajo del mínimo ({producto.stock_actual}/{producto.stock_minimo})', 'warning')
        
        flash(f'Salida registrada. Stock actual de "{producto.nombre}": {producto.stock_actual}', 'success')
        return redirect(url_for('movimientos.listar_salidas'))
    
    producto_id = request.args.get('producto_id', type=int)
    producto = Producto.query.get(producto_id) if producto_id else None
    
    return render_template('movimientos/salida_form.html',
                           producto_preseleccionado=producto)


@movimientos_bp.route('/salidas/<int:id>')
@login_required
def ver_salida(id):
    """Ver detalle de una salida"""
    salida = Salida.query.get_or_404(id)
    return render_template('movimientos/salida_ver.html', salida=salida)
