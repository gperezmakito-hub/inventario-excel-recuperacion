"""
Rutas de gestión de compras con workflow de aprobación
"""
import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import (
    SolicitudCompra, LineaSolicitud, HistorialSolicitud,
    Producto, Proveedor, Entrada
)
from app import db
from datetime import datetime
from functools import wraps

compras_bp = Blueprint('compras', __name__)


def registrar_historial(solicitud, estado_anterior, estado_nuevo, accion, notas=None):
    """Registra un cambio en el historial de la solicitud"""
    historial = HistorialSolicitud(
        solicitud_id=solicitud.id,
        usuario_id=current_user.id,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        accion=accion,
        notas=notas
    )
    db.session.add(historial)


def requiere_permiso_aprobar(f):
    """Decorador para verificar permiso de aprobación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.puede_aprobar():
            flash('No tienes permiso para aprobar solicitudes.', 'danger')
            return redirect(url_for('compras.listar'))
        return f(*args, **kwargs)
    return decorated_function


# =============================================================================
# LISTADOS
# =============================================================================

@compras_bp.route('/')
@login_required
def listar():
    """Listado de solicitudes de compra"""
    page = request.args.get('page', 1, type=int)
    estado = request.args.get('estado', '')
    prioridad = request.args.get('prioridad', '')
    
    query = SolicitudCompra.query
    
    if estado:
        query = query.filter_by(estado=estado)
    if prioridad:
        query = query.filter_by(prioridad=prioridad)
    
    solicitudes = query.order_by(
        SolicitudCompra.fecha_creacion.desc()
    ).paginate(page=page, per_page=25, error_out=False)
    
    # Contadores por estado
    contadores = {}
    for est in ['pendiente', 'aprobada', 'pedida', 'en_transito', 'recibida']:
        contadores[est] = SolicitudCompra.query.filter_by(estado=est).count()
    
    return render_template('compras/listar.html',
                           solicitudes=solicitudes,
                           contadores=contadores,
                           estado_filtro=estado)


@compras_bp.route('/pendientes')
@login_required
def pendientes():
    """Solicitudes pendientes de aprobación"""
    solicitudes = SolicitudCompra.query.filter_by(
        estado='pendiente'
    ).order_by(
        SolicitudCompra.prioridad.desc(),
        SolicitudCompra.fecha_creacion
    ).all()
    
    return render_template('compras/pendientes.html', solicitudes=solicitudes)


@compras_bp.route('/en-curso')
@login_required
def en_curso():
    """Solicitudes en curso (aprobadas, pedidas, en tránsito)"""
    solicitudes = SolicitudCompra.query.filter(
        SolicitudCompra.estado.in_(['aprobada', 'pedida', 'en_transito'])
    ).order_by(
        SolicitudCompra.fecha_pedido.desc()
    ).all()
    
    return render_template('compras/en_curso.html', solicitudes=solicitudes)


# =============================================================================
# CREAR SOLICITUD (ALMACÉN)
# =============================================================================

@compras_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    """Crear nueva solicitud de compra"""
    if request.method == 'POST':
        # Crear solicitud
        solicitud = SolicitudCompra(
            numero=SolicitudCompra.generar_numero(),
            estado='pendiente',
            prioridad=request.form.get('prioridad', 'normal'),
            proveedor_id=request.form.get('proveedor_id', type=int) or None,
            creado_por_id=current_user.id,
            motivo=request.form.get('motivo', '').strip() or None
        )
        
        db.session.add(solicitud)
        db.session.flush()  # Para obtener el ID
        
        # Agregar líneas de productos
        producto_ids = request.form.getlist('producto_id[]')
        cantidades = request.form.getlist('cantidad[]')
        precios = request.form.getlist('precio[]')
        
        if not producto_ids:
            flash('Debes agregar al menos un producto a la solicitud.', 'warning')
            return redirect(url_for('compras.nueva'))
        
        for i, producto_id in enumerate(producto_ids):
            if producto_id and cantidades[i]:
                producto = Producto.query.get(int(producto_id))
                if producto:
                    # Usar el precio del formulario si está disponible, sino el del producto
                    precio = float(precios[i]) if i < len(precios) and precios[i] else producto.precio_compra
                    
                    linea = LineaSolicitud(
                        solicitud_id=solicitud.id,
                        producto_id=int(producto_id),
                        cantidad_solicitada=int(cantidades[i]),
                        precio_estimado=precio
                    )
                    db.session.add(linea)
        
        # Registrar en historial
        registrar_historial(solicitud, None, 'pendiente', 'Solicitud creada')
        
        db.session.commit()
        
        flash(f'Solicitud {solicitud.numero} creada correctamente. Pendiente de aprobación.', 'success')
        return redirect(url_for('compras.ver', id=solicitud.id))
    
    # Productos con stock bajo para sugerir
    productos_stock_bajo = Producto.query.filter(
        Producto.stock_actual <= Producto.stock_minimo,
        Producto.stock_minimo > 0,
        Producto.activo == True
    ).order_by(Producto.nombre).all()
    
    proveedores = Proveedor.query.filter_by(activo=True).order_by(Proveedor.nombre).all()
    
    return render_template('compras/form_nueva.html',
                           productos_stock_bajo=productos_stock_bajo,
                           proveedores=proveedores)


@compras_bp.route('/rapida/<int:producto_id>', methods=['GET', 'POST'])
@login_required
def solicitud_rapida(producto_id):
    """Crear solicitud rápida desde un producto con stock bajo"""
    producto = Producto.query.get_or_404(producto_id)
    
    if request.method == 'POST':
        cantidad = request.form.get('cantidad', 0, type=int)
        if cantidad <= 0:
            flash('La cantidad debe ser mayor que 0.', 'warning')
            return redirect(url_for('compras.solicitud_rapida', producto_id=producto_id))
        
        # Crear solicitud
        solicitud = SolicitudCompra(
            numero=SolicitudCompra.generar_numero(),
            estado='pendiente',
            prioridad=request.form.get('prioridad', 'normal'),
            proveedor_id=producto.proveedor_id,
            creado_por_id=current_user.id,
            motivo=f"Stock bajo: {producto.stock_actual}/{producto.stock_minimo}"
        )
        
        db.session.add(solicitud)
        db.session.flush()
        
        # Agregar línea
        linea = LineaSolicitud(
            solicitud_id=solicitud.id,
            producto_id=producto.id,
            cantidad_solicitada=cantidad,
            precio_estimado=producto.precio_compra
        )
        db.session.add(linea)
        
        registrar_historial(solicitud, None, 'pendiente', 
                           f'Solicitud rápida para {producto.nombre}')
        
        db.session.commit()
        
        flash(f'Solicitud {solicitud.numero} creada para "{producto.nombre}".', 'success')
        return redirect(url_for('compras.ver', id=solicitud.id))
    
    # Sugerir cantidad: reponer hasta 2x el mínimo
    cantidad_sugerida = max(1, (producto.stock_minimo * 2) - producto.stock_actual)
    
    return render_template('compras/form_rapida.html',
                           producto=producto,
                           cantidad_sugerida=cantidad_sugerida)


@compras_bp.route('/nueva-desde-stock', methods=['POST'])
@login_required
def nueva_desde_stock():
    """Crear solicitud de compra desde selección múltiple en stock bajo"""
    try:
        productos_json = request.form.get('productos_json', '[]')
        productos_data = json.loads(productos_json)
        
        if not productos_data:
            flash('No se han seleccionado productos.', 'warning')
            return redirect(url_for('productos.stock_bajo'))
        
        # Obtener primer producto para determinar proveedor
        primer_producto = Producto.query.get(productos_data[0]['producto_id'])
        if not primer_producto:
            flash('Error: Producto no encontrado.', 'danger')
            return redirect(url_for('productos.stock_bajo'))
        
        # Crear solicitud
        solicitud = SolicitudCompra(
            numero=SolicitudCompra.generar_numero(),
            estado='pendiente',
            prioridad='normal',
            proveedor_id=primer_producto.proveedor_id,
            creado_por_id=current_user.id,
            motivo=request.form.get('observaciones', '').strip() or 'Reposición stock bajo'
        )
        
        db.session.add(solicitud)
        db.session.flush()
        
        # Agregar líneas de productos
        productos_agregados = 0
        for item in productos_data:
            producto = Producto.query.get(item['producto_id'])
            if producto:
                # Verificar que todos sean del mismo proveedor
                if producto.proveedor_id != primer_producto.proveedor_id:
                    db.session.rollback()
                    flash('Error: Todos los productos deben ser del mismo proveedor.', 'danger')
                    return redirect(url_for('productos.stock_bajo'))
                
                linea = LineaSolicitud(
                    solicitud_id=solicitud.id,
                    producto_id=producto.id,
                    cantidad_solicitada=item['cantidad'],
                    precio_estimado=producto.precio_compra
                )
                db.session.add(linea)
                productos_agregados += 1
        
        if productos_agregados == 0:
            db.session.rollback()
            flash('No se pudo agregar ningún producto a la solicitud.', 'warning')
            return redirect(url_for('productos.stock_bajo'))
        
        # Registrar en historial
        registrar_historial(solicitud, None, 'pendiente', 
                           f'Solicitud creada desde stock bajo con {productos_agregados} productos')
        
        db.session.commit()
        
        flash(f'Solicitud {solicitud.numero} creada con {productos_agregados} productos.', 'success')
        return redirect(url_for('compras.ver', id=solicitud.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear la solicitud: {str(e)}', 'danger')
        return redirect(url_for('productos.stock_bajo'))


# =============================================================================
# VER SOLICITUD
# =============================================================================

@compras_bp.route('/<int:id>')
@login_required
def ver(id):
    """Ver detalle de una solicitud"""
    solicitud = SolicitudCompra.query.get_or_404(id)
    lineas = solicitud.lineas.all()
    historial = solicitud.historial.order_by(HistorialSolicitud.fecha.desc()).all()
    
    return render_template('compras/ver.html',
                           solicitud=solicitud,
                           lineas=lineas,
                           historial=historial)


# =============================================================================
# APROBAR / RECHAZAR (OFICINA)
# =============================================================================

@compras_bp.route('/<int:id>/aprobar', methods=['GET', 'POST'])
@login_required
@requiere_permiso_aprobar
def aprobar(id):
    """Aprobar solicitud de compra"""
    solicitud = SolicitudCompra.query.get_or_404(id)
    
    if not solicitud.puede_aprobar():
        flash('Esta solicitud no puede ser aprobada.', 'warning')
        return redirect(url_for('compras.ver', id=id))
    
    if request.method == 'POST':
        estado_anterior = solicitud.estado
        
        # Actualizar cantidades aprobadas y precios
        for linea in solicitud.lineas:
            cantidad_aprobada = request.form.get(f'cantidad_{linea.id}', type=int)
            precio_actualizado = request.form.get(f'precio_{linea.id}', type=float)
            
            linea.cantidad_aprobada = cantidad_aprobada
            
            # Actualizar precio estimado si se modificó
            if precio_actualizado is not None:
                linea.precio_estimado = precio_actualizado
        
        solicitud.estado = 'aprobada'
        solicitud.aprobado_por_id = current_user.id
        solicitud.fecha_aprobacion = datetime.now()
        solicitud.notas_aprobacion = request.form.get('notas', '').strip() or None
        
        # Actualizar proveedor si se cambió
        proveedor_id = request.form.get('proveedor_id', type=int)
        if proveedor_id:
            solicitud.proveedor_id = proveedor_id
        
        registrar_historial(solicitud, estado_anterior, 'aprobada',
                           f'Aprobada por {current_user.nombre_completo}',
                           solicitud.notas_aprobacion)
        
        db.session.commit()
        
        flash(f'Solicitud {solicitud.numero} aprobada correctamente.', 'success')
        return redirect(url_for('compras.ver', id=id))
    
    lineas = solicitud.lineas.all()
    proveedores = Proveedor.query.filter_by(activo=True).order_by(Proveedor.nombre).all()
    
    return render_template('compras/form_aprobar.html',
                           solicitud=solicitud,
                           lineas=lineas,
                           proveedores=proveedores)


@compras_bp.route('/<int:id>/rechazar', methods=['POST'])
@login_required
@requiere_permiso_aprobar
def rechazar(id):
    """Rechazar solicitud de compra"""
    solicitud = SolicitudCompra.query.get_or_404(id)
    
    if not solicitud.puede_aprobar():
        flash('Esta solicitud no puede ser rechazada.', 'warning')
        return redirect(url_for('compras.ver', id=id))
    
    estado_anterior = solicitud.estado
    solicitud.estado = 'rechazada'
    solicitud.aprobado_por_id = current_user.id
    solicitud.fecha_aprobacion = datetime.now()
    solicitud.notas_aprobacion = request.form.get('motivo_rechazo', '').strip()
    
    registrar_historial(solicitud, estado_anterior, 'rechazada',
                       f'Rechazada por {current_user.nombre_completo}',
                       solicitud.notas_aprobacion)
    
    db.session.commit()
    
    flash(f'Solicitud {solicitud.numero} rechazada.', 'info')
    return redirect(url_for('compras.ver', id=id))


# =============================================================================
# PEDIR AL PROVEEDOR (OFICINA)
# =============================================================================

@compras_bp.route('/<int:id>/pedir', methods=['GET', 'POST'])
@login_required
@requiere_permiso_aprobar
def pedir(id):
    """Registrar pedido al proveedor"""
    solicitud = SolicitudCompra.query.get_or_404(id)
    
    if not solicitud.puede_pedir():
        flash('Esta solicitud no puede ser pedida al proveedor.', 'warning')
        return redirect(url_for('compras.ver', id=id))
    
    if request.method == 'POST':
        estado_anterior = solicitud.estado
        
        # Actualizar precios si se modificaron
        for linea in solicitud.lineas:
            precio_final = request.form.get(f'precio_{linea.id}', type=float)
            if precio_final is not None:
                linea.precio_real = precio_final
        
        solicitud.estado = 'pedida'
        solicitud.fecha_pedido = datetime.now()
        solicitud.numero_pedido_proveedor = request.form.get('numero_pedido', '').strip() or None
        
        # Fecha estimada de entrega
        fecha_entrega = request.form.get('fecha_entrega_estimada')
        if fecha_entrega:
            solicitud.fecha_entrega_estimada = datetime.strptime(fecha_entrega, '%Y-%m-%d')
        
        registrar_historial(solicitud, estado_anterior, 'pedida',
                           f'Pedido realizado al proveedor',
                           f'Nº Pedido: {solicitud.numero_pedido_proveedor}')
        
        db.session.commit()
        
        flash(f'Pedido registrado para solicitud {solicitud.numero}.', 'success')
        return redirect(url_for('compras.ver', id=id))
    
    return render_template('compras/form_pedir.html', 
                         solicitud=solicitud,
                         now=datetime.now())


# =============================================================================
# SEGUIMIENTO (ENVÍO)
# =============================================================================

@compras_bp.route('/<int:id>/marcar-enviado', methods=['POST'])
@login_required
def marcar_enviado(id):
    """Marcar pedido como enviado por el proveedor"""
    solicitud = SolicitudCompra.query.get_or_404(id)
    
    if not solicitud.puede_marcar_enviado():
        flash('Esta solicitud no puede marcarse como enviada.', 'warning')
        return redirect(url_for('compras.ver', id=id))
    
    estado_anterior = solicitud.estado
    
    solicitud.estado = 'en_transito'
    solicitud.fecha_envio_proveedor = datetime.now()
    solicitud.numero_seguimiento = request.form.get('numero_seguimiento', '').strip() or None
    
    # Actualizar fecha estimada si se proporciona
    fecha_entrega = request.form.get('fecha_entrega_estimada')
    if fecha_entrega:
        solicitud.fecha_entrega_estimada = datetime.strptime(fecha_entrega, '%Y-%m-%d')
    
    registrar_historial(solicitud, estado_anterior, 'en_transito',
                       'Pedido enviado por el proveedor',
                       f'Seguimiento: {solicitud.numero_seguimiento}')
    
    db.session.commit()
    
    flash(f'Solicitud {solicitud.numero} marcada como en tránsito.', 'success')
    return redirect(url_for('compras.ver', id=id))


# =============================================================================
# RECEPCIÓN (ALMACÉN)
# =============================================================================

@compras_bp.route('/<int:id>/recibir', methods=['GET', 'POST'])
@login_required
def recibir(id):
    """Registrar recepción del pedido"""
    solicitud = SolicitudCompra.query.get_or_404(id)
    
    if not solicitud.puede_recibir():
        flash('Esta solicitud no puede ser recibida.', 'warning')
        return redirect(url_for('compras.ver', id=id))
    
    lineas = solicitud.lineas.all()
    
    if request.method == 'POST':
        estado_anterior = solicitud.estado
        
        # Procesar cada línea
        for linea in lineas:
            cantidad_recibida = request.form.get(f'cantidad_{linea.id}', 0, type=int)
            precio_real = request.form.get(f'precio_{linea.id}', type=float)
            
            linea.cantidad_recibida = cantidad_recibida
            if precio_real:
                linea.precio_real = precio_real
            
            # Crear entrada de inventario si se recibió algo
            if cantidad_recibida > 0:
                # Generar número de registro
                ultimo = Entrada.query.order_by(Entrada.numero_registro.desc()).first()
                numero_registro = (ultimo.numero_registro + 1) if ultimo else 1
                
                entrada = Entrada(
                    numero_registro=numero_registro,
                    fecha=datetime.now(),
                    producto_id=linea.producto_id,
                    cantidad=cantidad_recibida,
                    albaran=request.form.get('albaran', '').strip() or None,
                    factura=request.form.get('factura', '').strip() or None,
                    precio_unitario=linea.precio_real or linea.precio_estimado,
                    proveedor_id=solicitud.proveedor_id,
                    usuario_id=current_user.id,
                    solicitud_id=solicitud.id
                )
                db.session.add(entrada)
                
                # Actualizar stock del producto
                producto = linea.producto
                producto.stock_actual += cantidad_recibida
                producto.fecha_ultima_entrada = datetime.now()
                
                # Actualizar precio si cambió
                if linea.precio_real and linea.precio_real != producto.precio_compra:
                    producto.precio_compra = linea.precio_real
        
        solicitud.estado = 'recibida'
        solicitud.fecha_recepcion = datetime.now()
        solicitud.recibido_por_id = current_user.id
        solicitud.notas_recepcion = request.form.get('notas', '').strip() or None
        
        registrar_historial(solicitud, estado_anterior, 'recibida',
                           f'Recibido por {current_user.nombre_completo}',
                           solicitud.notas_recepcion)
        
        db.session.commit()
        
        flash(f'Recepción de solicitud {solicitud.numero} completada. Stock actualizado.', 'success')
        return redirect(url_for('compras.ver', id=id))
    
    return render_template('compras/form_recibir.html',
                           solicitud=solicitud,
                           lineas=lineas)


# =============================================================================
# CANCELAR
# =============================================================================

@compras_bp.route('/<int:id>/cancelar', methods=['POST'])
@login_required
def cancelar(id):
    """Cancelar solicitud"""
    solicitud = SolicitudCompra.query.get_or_404(id)
    
    if solicitud.estado in ['recibida', 'cancelada']:
        flash('Esta solicitud no puede ser cancelada.', 'warning')
        return redirect(url_for('compras.ver', id=id))
    
    # Solo admin o el creador pueden cancelar
    if not (current_user.rol == 'admin' or solicitud.creado_por_id == current_user.id):
        flash('No tienes permiso para cancelar esta solicitud.', 'danger')
        return redirect(url_for('compras.ver', id=id))
    
    estado_anterior = solicitud.estado
    solicitud.estado = 'cancelada'
    
    registrar_historial(solicitud, estado_anterior, 'cancelada',
                       f'Cancelada por {current_user.nombre_completo}',
                       request.form.get('motivo', '').strip())
    
    db.session.commit()
    
    flash(f'Solicitud {solicitud.numero} cancelada.', 'info')
    return redirect(url_for('compras.ver', id=id))


# =============================================================================
# API
# =============================================================================

@compras_bp.route('/api/productos-stock-bajo')
@login_required
def api_productos_stock_bajo():
    """API: Productos con stock bajo"""
    productos = Producto.query.filter(
        Producto.stock_actual <= Producto.stock_minimo,
        Producto.stock_minimo > 0,
        Producto.activo == True
    ).all()
    
    return jsonify([{
        'id': p.id,
        'codigo_ean': p.codigo_ean,
        'nombre': p.nombre,
        'color': p.color,
        'stock_actual': p.stock_actual,
        'stock_minimo': p.stock_minimo,
        'precio_compra': float(p.precio_compra) if p.precio_compra else 0,
        'proveedor': p.proveedor.nombre if p.proveedor else None
    } for p in productos])
