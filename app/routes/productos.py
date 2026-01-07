"""
Rutas de gestión de productos
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Producto, Categoria, ZonaStock, Proveedor
from app import db
from functools import wraps

productos_bp = Blueprint('productos', __name__)


def requiere_permiso_edicion(f):
    """Decorador para verificar permiso de edición"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.puede_editar_productos():
            flash('No tienes permiso para realizar esta acción.', 'danger')
            return redirect(url_for('productos.listar'))
        return f(*args, **kwargs)
    return decorated_function


@productos_bp.route('/')
@login_required
def listar():
    """Listado de productos con filtros"""
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    # Filtros
    buscar = request.args.get('buscar', '').strip()
    categoria_id = request.args.get('categoria', type=int)
    proveedor_id = request.args.get('proveedor', type=int)
    stock_bajo = request.args.get('stock_bajo', False, type=bool)
    solo_activos = request.args.get('solo_activos', True, type=bool)
    
    # Query base
    query = Producto.query
    
    if solo_activos:
        query = query.filter_by(activo=True)
    
    if buscar:
        query = query.filter(
            db.or_(
                Producto.codigo_ean.ilike(f'%{buscar}%'),
                Producto.nombre.ilike(f'%{buscar}%'),
                Producto.color.ilike(f'%{buscar}%'),
                Producto.codigo_proveedor.ilike(f'%{buscar}%')
            )
        )
    
    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)
    
    if proveedor_id:
        query = query.filter_by(proveedor_id=proveedor_id)
    
    if stock_bajo:
        query = query.filter(Producto.stock_actual <= Producto.stock_minimo)
    
    # Ordenar y paginar
    productos = query.order_by(Producto.nombre).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Datos para filtros
    categorias = Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
    proveedores = Proveedor.query.filter_by(activo=True).order_by(Proveedor.nombre).all()
    
    return render_template('productos/listar.html',
                           productos=productos,
                           categorias=categorias,
                           proveedores=proveedores,
                           filtros={
                               'buscar': buscar,
                               'categoria_id': categoria_id,
                               'proveedor_id': proveedor_id,
                               'stock_bajo': stock_bajo,
                               'solo_activos': solo_activos
                           })


@productos_bp.route('/<int:id>')
@login_required
def ver(id):
    """Ver detalle de un producto"""
    producto = Producto.query.get_or_404(id)
    
    # Últimos movimientos
    ultimas_entradas = producto.entradas.order_by(
        db.desc('fecha')
    ).limit(10).all()
    ultimas_salidas = producto.salidas.order_by(
        db.desc('fecha')
    ).limit(10).all()
    
    return render_template('productos/ver.html',
                           producto=producto,
                           ultimas_entradas=ultimas_entradas,
                           ultimas_salidas=ultimas_salidas)


@productos_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@requiere_permiso_edicion
def nuevo():
    """Crear nuevo producto"""
    if request.method == 'POST':
        # Validar código EAN único
        codigo_ean = request.form.get('codigo_ean', '').strip()
        if Producto.query.filter_by(codigo_ean=codigo_ean).first():
            flash('Ya existe un producto con ese código EAN.', 'danger')
            return redirect(url_for('productos.nuevo'))
        
        producto = Producto(
            codigo_ean=codigo_ean,
            codigo_proveedor=request.form.get('codigo_proveedor', '').strip() or None,
            nombre=request.form.get('nombre', '').strip(),
            color=request.form.get('color', '').strip() or None,
            peso_unidad=request.form.get('peso_unidad', type=float) or None,
            stock_actual=request.form.get('stock_actual', 0, type=int),
            stock_minimo=request.form.get('stock_minimo', 0, type=int),
            precio_compra=request.form.get('precio_compra', 0, type=float),
            dto_1=request.form.get('dto_1', 0, type=float),
            dto_2=request.form.get('dto_2', 0, type=float),
            categoria_id=request.form.get('categoria_id', type=int) or None,
            zona_id=request.form.get('zona_id', type=int) or None,
            proveedor_id=request.form.get('proveedor_id', type=int) or None
        )
        
        db.session.add(producto)
        db.session.commit()
        
        flash(f'Producto "{producto.nombre}" creado correctamente.', 'success')
        return redirect(url_for('productos.ver', id=producto.id))
    
    categorias = Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
    zonas = ZonaStock.query.order_by(ZonaStock.nombre).all()
    proveedores = Proveedor.query.filter_by(activo=True).order_by(Proveedor.nombre).all()
    
    return render_template('productos/form.html',
                           producto=None,
                           categorias=categorias,
                           zonas=zonas,
                           proveedores=proveedores)


@productos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@requiere_permiso_edicion
def editar(id):
    """Editar producto existente"""
    producto = Producto.query.get_or_404(id)
    
    if request.method == 'POST':
        # Validar código EAN único (excepto el actual)
        codigo_ean = request.form.get('codigo_ean', '').strip()
        existente = Producto.query.filter_by(codigo_ean=codigo_ean).first()
        if existente and existente.id != producto.id:
            flash('Ya existe otro producto con ese código EAN.', 'danger')
            return redirect(url_for('productos.editar', id=id))
        
        producto.codigo_ean = codigo_ean
        producto.codigo_proveedor = request.form.get('codigo_proveedor', '').strip() or None
        producto.nombre = request.form.get('nombre', '').strip()
        producto.color = request.form.get('color', '').strip() or None
        producto.peso_unidad = request.form.get('peso_unidad', type=float) or None
        producto.stock_minimo = request.form.get('stock_minimo', 0, type=int)
        producto.precio_compra = request.form.get('precio_compra', 0, type=float)
        producto.dto_1 = request.form.get('dto_1', 0, type=float)
        producto.dto_2 = request.form.get('dto_2', 0, type=float)
        producto.categoria_id = request.form.get('categoria_id', type=int) or None
        producto.zona_id = request.form.get('zona_id', type=int) or None
        producto.proveedor_id = request.form.get('proveedor_id', type=int) or None
        producto.activo = 'activo' in request.form
        producto.descatalogado = 'descatalogado' in request.form
        
        db.session.commit()
        
        flash('Producto actualizado correctamente.', 'success')
        return redirect(url_for('productos.ver', id=producto.id))
    
    categorias = Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
    zonas = ZonaStock.query.order_by(ZonaStock.nombre).all()
    proveedores = Proveedor.query.filter_by(activo=True).order_by(Proveedor.nombre).all()
    
    return render_template('productos/form.html',
                           producto=producto,
                           categorias=categorias,
                           zonas=zonas,
                           proveedores=proveedores)


@productos_bp.route('/stock-bajo')
@login_required
def stock_bajo():
    """Listado de productos con stock bajo"""
    proveedor_id = request.args.get('proveedor_id', type=int)
    
    query = Producto.query.filter(
        Producto.stock_actual <= Producto.stock_minimo,
        Producto.activo == True
    )
    
    # Filtrar por proveedor si se especifica
    if proveedor_id:
        query = query.filter_by(proveedor_id=proveedor_id)
    
    productos = query.order_by(Producto.stock_actual).all()
    
    # Obtener proveedores con productos en stock bajo y contar
    proveedores_query = db.session.query(
        Proveedor,
        db.func.count(Producto.id).label('productos_stock_bajo')
    ).join(
        Producto, Producto.proveedor_id == Proveedor.id
    ).filter(
        Producto.stock_actual <= Producto.stock_minimo,
        Producto.activo == True,
        Proveedor.activo == True
    ).group_by(Proveedor.id).order_by(Proveedor.nombre).all()
    
    # Crear lista de proveedores con el conteo
    proveedores = []
    for prov, count in proveedores_query:
        prov.productos_stock_bajo = count
        proveedores.append(prov)
    
    return render_template('productos/stock_bajo.html', 
                         productos=productos,
                         proveedores=proveedores,
                         proveedor_id=proveedor_id)


@productos_bp.route('/api/buscar')
@login_required
def api_buscar():
    """API para búsqueda de productos (autocompletado)"""
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    
    productos = Producto.query.filter(
        Producto.activo == True,
        db.or_(
            Producto.codigo_ean.ilike(f'%{q}%'),
            Producto.nombre.ilike(f'%{q}%'),
            Producto.color.ilike(f'%{q}%')
        )
    ).limit(10).all()
    
    return jsonify([{
        'id': p.id,
        'codigo_ean': p.codigo_ean,
        'nombre': p.nombre,
        'color': p.color,
        'stock_actual': p.stock_actual,
        'stock_minimo': p.stock_minimo,
        'precio_compra': float(p.precio_compra) if p.precio_compra else 0
    } for p in productos])
