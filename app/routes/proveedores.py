"""
Rutas de gestión de proveedores
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Proveedor, Producto
from app import db
from functools import wraps

proveedores_bp = Blueprint('proveedores', __name__)


def requiere_permiso_edicion(f):
    """Decorador para verificar permiso de edición"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.puede_editar_productos():
            flash('No tienes permiso para realizar esta acción.', 'danger')
            return redirect(url_for('proveedores.listar'))
        return f(*args, **kwargs)
    return decorated_function


@proveedores_bp.route('/')
@login_required
def listar():
    """Listado de proveedores"""
    page = request.args.get('page', 1, type=int)
    buscar = request.args.get('buscar', '').strip()
    solo_activos = request.args.get('solo_activos', True, type=bool)
    
    query = Proveedor.query
    
    if solo_activos:
        query = query.filter_by(activo=True)
    
    if buscar:
        query = query.filter(
            db.or_(
                Proveedor.nombre.ilike(f'%{buscar}%'),
                Proveedor.nif.ilike(f'%{buscar}%'),
                Proveedor.municipio.ilike(f'%{buscar}%')
            )
        )
    
    proveedores = query.order_by(Proveedor.nombre).paginate(
        page=page, per_page=25, error_out=False
    )
    
    return render_template('proveedores/listar.html', proveedores=proveedores)


@proveedores_bp.route('/<int:id>')
@login_required
def ver(id):
    """Ver detalle de un proveedor"""
    proveedor = Proveedor.query.get_or_404(id)
    
    # Productos de este proveedor
    productos = proveedor.productos.filter_by(activo=True).order_by(Producto.nombre).all()
    
    return render_template('proveedores/ver.html',
                           proveedor=proveedor,
                           productos=productos)


@proveedores_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@requiere_permiso_edicion
def nuevo():
    """Crear nuevo proveedor"""
    if request.method == 'POST':
        nif = request.form.get('nif', '').strip()
        if nif and Proveedor.query.filter_by(nif=nif).first():
            flash('Ya existe un proveedor con ese NIF.', 'danger')
            return redirect(url_for('proveedores.nuevo'))
        
        proveedor = Proveedor(
            nombre=request.form.get('nombre', '').strip(),
            nif=nif or None,
            direccion=request.form.get('direccion', '').strip() or None,
            codigo_postal=request.form.get('codigo_postal', '').strip() or None,
            municipio=request.form.get('municipio', '').strip() or None,
            provincia=request.form.get('provincia', '').strip() or None,
            telefono=request.form.get('telefono', '').strip() or None,
            email=request.form.get('email', '').strip() or None,
            web=request.form.get('web', '').strip() or None,
            contacto_nombre=request.form.get('contacto_nombre', '').strip() or None,
            contacto_telefono=request.form.get('contacto_telefono', '').strip() or None,
            contacto_email=request.form.get('contacto_email', '').strip() or None,
            notas=request.form.get('notas', '').strip() or None
        )
        
        db.session.add(proveedor)
        db.session.commit()
        
        flash(f'Proveedor "{proveedor.nombre}" creado correctamente.', 'success')
        return redirect(url_for('proveedores.ver', id=proveedor.id))
    
    return render_template('proveedores/form.html', proveedor=None)


@proveedores_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@requiere_permiso_edicion
def editar(id):
    """Editar proveedor existente"""
    proveedor = Proveedor.query.get_or_404(id)
    
    if request.method == 'POST':
        nif = request.form.get('nif', '').strip()
        existente = Proveedor.query.filter_by(nif=nif).first()
        if nif and existente and existente.id != proveedor.id:
            flash('Ya existe otro proveedor con ese NIF.', 'danger')
            return redirect(url_for('proveedores.editar', id=id))
        
        proveedor.nombre = request.form.get('nombre', '').strip()
        proveedor.nif = nif or None
        proveedor.direccion = request.form.get('direccion', '').strip() or None
        proveedor.codigo_postal = request.form.get('codigo_postal', '').strip() or None
        proveedor.municipio = request.form.get('municipio', '').strip() or None
        proveedor.provincia = request.form.get('provincia', '').strip() or None
        proveedor.telefono = request.form.get('telefono', '').strip() or None
        proveedor.email = request.form.get('email', '').strip() or None
        proveedor.web = request.form.get('web', '').strip() or None
        proveedor.contacto_nombre = request.form.get('contacto_nombre', '').strip() or None
        proveedor.contacto_telefono = request.form.get('contacto_telefono', '').strip() or None
        proveedor.contacto_email = request.form.get('contacto_email', '').strip() or None
        proveedor.notas = request.form.get('notas', '').strip() or None
        proveedor.activo = 'activo' in request.form
        
        db.session.commit()
        
        flash('Proveedor actualizado correctamente.', 'success')
        return redirect(url_for('proveedores.ver', id=proveedor.id))
    
    return render_template('proveedores/form.html', proveedor=proveedor)


@proveedores_bp.route('/api/buscar')
@login_required
def api_buscar():
    """API para búsqueda de proveedores"""
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    
    proveedores = Proveedor.query.filter(
        Proveedor.activo == True,
        db.or_(
            Proveedor.nombre.ilike(f'%{q}%'),
            Proveedor.nif.ilike(f'%{q}%')
        )
    ).limit(10).all()
    
    return jsonify([{
        'id': p.id,
        'nombre': p.nombre,
        'nif': p.nif,
        'telefono': p.telefono
    } for p in proveedores])
