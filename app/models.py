"""
Modelos de la base de datos
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager


# =============================================================================
# USUARIOS Y AUTENTICACIÓN
# =============================================================================

class Usuario(UserMixin, db.Model):
    """Usuarios del sistema"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    nombre_completo = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150))
    
    # Roles: 'admin', 'oficina', 'almacen', 'consulta'
    rol = db.Column(db.String(20), nullable=False, default='consulta')
    activo = db.Column(db.Boolean, default=True)
    
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime)
    
    # Relaciones
    entradas = db.relationship('Entrada', backref='usuario', lazy='dynamic')
    salidas = db.relationship('Salida', backref='usuario', lazy='dynamic')
    solicitudes_creadas = db.relationship('SolicitudCompra', 
                                          foreign_keys='SolicitudCompra.creado_por_id',
                                          backref='creador', lazy='dynamic')
    solicitudes_aprobadas = db.relationship('SolicitudCompra',
                                            foreign_keys='SolicitudCompra.aprobado_por_id',
                                            backref='aprobador', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def puede_aprobar(self):
        """Solo admin y oficina pueden aprobar compras"""
        return self.rol in ['admin', 'oficina']
    
    def puede_editar_productos(self):
        """Admin y oficina pueden editar productos"""
        return self.rol in ['admin', 'oficina']
    
    def puede_registrar_movimientos(self):
        """Admin, oficina y almacén pueden registrar movimientos"""
        return self.rol in ['admin', 'oficina', 'almacen']
    
    def __repr__(self):
        return f'<Usuario {self.username}>'


# =============================================================================
# PRODUCTOS / TINTAS
# =============================================================================

class Categoria(db.Model):
    """Categorías de productos (Tipo Pintura / Serie)"""
    __tablename__ = 'categorias'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    descripcion = db.Column(db.String(255))
    activo = db.Column(db.Boolean, default=True)
    
    productos = db.relationship('Producto', backref='categoria', lazy='dynamic')
    
    def __repr__(self):
        return f'<Categoria {self.nombre}>'


class ZonaStock(db.Model):
    """Ubicaciones de almacenamiento"""
    __tablename__ = 'zonas_stock'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    descripcion = db.Column(db.String(255))
    
    productos = db.relationship('Producto', backref='zona', lazy='dynamic')
    
    def __repr__(self):
        return f'<ZonaStock {self.nombre}>'


class Producto(db.Model):
    """Productos (Tintas/Pinturas)"""
    __tablename__ = 'productos'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo_ean = db.Column(db.String(50), unique=True, nullable=False, index=True)
    codigo_proveedor = db.Column(db.String(50), index=True)
    
    nombre = db.Column(db.String(150), nullable=False)  # Tipo Pintura / Serie
    color = db.Column(db.String(100))
    
    # Stock
    peso_unidad = db.Column(db.Numeric(10, 3))  # kg por bote
    stock_actual = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=0)
    
    # Precios
    precio_compra = db.Column(db.Numeric(10, 2), default=0)
    dto_1 = db.Column(db.Numeric(5, 2), default=0)
    dto_2 = db.Column(db.Numeric(5, 2), default=0)
    
    # Relaciones
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'))
    zona_id = db.Column(db.Integer, db.ForeignKey('zonas_stock.id'))
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'))
    
    # Estado
    activo = db.Column(db.Boolean, default=True)
    descatalogado = db.Column(db.Boolean, default=False)
    
    # Fechas
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_ultima_entrada = db.Column(db.DateTime)
    fecha_ultima_salida = db.Column(db.DateTime)
    
    # Relaciones inversas
    entradas = db.relationship('Entrada', backref='producto', lazy='dynamic')
    salidas = db.relationship('Salida', backref='producto', lazy='dynamic')
    lineas_solicitud = db.relationship('LineaSolicitud', backref='producto', lazy='dynamic')
    
    @property
    def stock_bajo(self):
        """Retorna True si el stock está por debajo del mínimo"""
        return self.stock_actual <= self.stock_minimo
    
    @property
    def valor_inventario(self):
        """Valor total del stock de este producto"""
        return float(self.stock_actual) * float(self.precio_compra or 0)
    
    def __repr__(self):
        return f'<Producto {self.codigo_ean} - {self.nombre}>'


# =============================================================================
# PROVEEDORES
# =============================================================================

class Proveedor(db.Model):
    """Proveedores de tintas"""
    __tablename__ = 'proveedores'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    nif = db.Column(db.String(20), unique=True)
    
    # Contacto
    direccion = db.Column(db.String(255))
    codigo_postal = db.Column(db.String(10))
    municipio = db.Column(db.String(100))
    provincia = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(150))
    web = db.Column(db.String(255))
    
    # Persona de contacto
    contacto_nombre = db.Column(db.String(150))
    contacto_telefono = db.Column(db.String(20))
    contacto_email = db.Column(db.String(150))
    
    notas = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    productos = db.relationship('Producto', backref='proveedor', lazy='dynamic')
    entradas = db.relationship('Entrada', backref='proveedor', lazy='dynamic')
    solicitudes = db.relationship('SolicitudCompra', backref='proveedor', lazy='dynamic')
    
    def __repr__(self):
        return f'<Proveedor {self.nombre}>'


# =============================================================================
# MOVIMIENTOS DE INVENTARIO
# =============================================================================

class Entrada(db.Model):
    """Entradas de inventario (compras)"""
    __tablename__ = 'entradas'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_registro = db.Column(db.Integer, unique=True, index=True)
    
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Producto
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    
    # Documentación
    albaran = db.Column(db.String(50))
    factura = db.Column(db.String(50))
    
    # Precios
    precio_unitario = db.Column(db.Numeric(10, 2))
    dto_1 = db.Column(db.Numeric(5, 2), default=0)
    dto_2 = db.Column(db.Numeric(5, 2), default=0)
    
    # Relaciones
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    solicitud_id = db.Column(db.Integer, db.ForeignKey('solicitudes_compra.id'))
    
    notas = db.Column(db.Text)
    
    @property
    def precio_total(self):
        """Calcula precio total con descuentos"""
        precio = float(self.precio_unitario or 0) * self.cantidad
        if self.dto_1:
            precio -= precio * float(self.dto_1) / 100
        if self.dto_2:
            precio -= precio * float(self.dto_2) / 100
        return round(precio, 2)
    
    def __repr__(self):
        return f'<Entrada {self.numero_registro}>'


class Salida(db.Model):
    """Salidas de inventario (consumos)"""
    __tablename__ = 'salidas'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_registro = db.Column(db.Integer, unique=True, index=True)
    
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Producto
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    
    # Destino/Uso
    destino = db.Column(db.String(150))  # Departamento, proyecto, etc.
    
    # Usuario que registra
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    
    notas = db.Column(db.Text)
    
    @property
    def valor(self):
        """Valor de la salida basado en precio del producto"""
        return float(self.producto.precio_compra or 0) * self.cantidad
    
    def __repr__(self):
        return f'<Salida {self.numero_registro}>'


# =============================================================================
# GESTIÓN DE COMPRAS (WORKFLOW)
# =============================================================================

class SolicitudCompra(db.Model):
    """Solicitudes de compra con workflow de aprobación"""
    __tablename__ = 'solicitudes_compra'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    
    # Estados: pendiente, aprobada, rechazada, pedida, en_transito, recibida, cancelada
    estado = db.Column(db.String(20), nullable=False, default='pendiente', index=True)
    
    # Prioridad: normal, alta, urgente
    prioridad = db.Column(db.String(20), default='normal')
    
    # Proveedor sugerido
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'))
    
    # Creación (Almacén)
    creado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    motivo = db.Column(db.Text)  # Por qué se solicita
    
    # Aprobación (Oficina)
    aprobado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_aprobacion = db.Column(db.DateTime)
    notas_aprobacion = db.Column(db.Text)
    
    # Pedido al proveedor
    fecha_pedido = db.Column(db.DateTime)
    numero_pedido_proveedor = db.Column(db.String(50))
    
    # Seguimiento
    fecha_envio_proveedor = db.Column(db.DateTime)
    numero_seguimiento = db.Column(db.String(100))
    fecha_entrega_estimada = db.Column(db.DateTime)
    
    # Recepción
    fecha_recepcion = db.Column(db.DateTime)
    recibido_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    notas_recepcion = db.Column(db.Text)
    
    # Líneas de productos
    lineas = db.relationship('LineaSolicitud', backref='solicitud', 
                             lazy='dynamic', cascade='all, delete-orphan')
    
    # Entradas generadas
    entradas = db.relationship('Entrada', backref='solicitud', lazy='dynamic')
    
    # Historial de cambios
    historial = db.relationship('HistorialSolicitud', backref='solicitud',
                                lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def total_estimado(self):
        """Total estimado de la solicitud"""
        total = 0
        for linea in self.lineas:
            total += linea.subtotal
        return round(total, 2)
    
    @property
    def estado_color(self):
        """Color Bootstrap para el estado"""
        colores = {
            'pendiente': 'warning',
            'aprobada': 'info',
            'rechazada': 'danger',
            'pedida': 'primary',
            'en_transito': 'secondary',
            'recibida': 'success',
            'cancelada': 'dark'
        }
        return colores.get(self.estado, 'secondary')
    
    @staticmethod
    def generar_numero():
        """Genera número de solicitud único"""
        from datetime import datetime
        ultimo = SolicitudCompra.query.order_by(
            SolicitudCompra.id.desc()
        ).first()
        num = (ultimo.id + 1) if ultimo else 1
        return f"SOL-{datetime.now().strftime('%Y%m')}-{num:04d}"
    
    def puede_aprobar(self):
        return self.estado == 'pendiente'
    
    def puede_pedir(self):
        return self.estado == 'aprobada'
    
    def puede_marcar_enviado(self):
        return self.estado == 'pedida'
    
    def puede_recibir(self):
        return self.estado in ['pedida', 'en_transito']
    
    def __repr__(self):
        return f'<SolicitudCompra {self.numero}>'


class LineaSolicitud(db.Model):
    """Líneas de productos en una solicitud de compra"""
    __tablename__ = 'lineas_solicitud'
    
    id = db.Column(db.Integer, primary_key=True)
    
    solicitud_id = db.Column(db.Integer, db.ForeignKey('solicitudes_compra.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    
    cantidad_solicitada = db.Column(db.Integer, nullable=False)
    cantidad_aprobada = db.Column(db.Integer)
    cantidad_recibida = db.Column(db.Integer)
    
    precio_estimado = db.Column(db.Numeric(10, 2))
    precio_real = db.Column(db.Numeric(10, 2))
    
    notas = db.Column(db.String(255))
    
    @property
    def subtotal(self):
        """Subtotal de la línea"""
        cant = self.cantidad_aprobada or self.cantidad_solicitada
        precio = float(self.precio_real or self.precio_estimado or 0)
        return cant * precio
    
    def __repr__(self):
        return f'<LineaSolicitud {self.id}>'


class HistorialSolicitud(db.Model):
    """Historial de cambios en solicitudes de compra"""
    __tablename__ = 'historial_solicitudes'
    
    id = db.Column(db.Integer, primary_key=True)
    solicitud_id = db.Column(db.Integer, db.ForeignKey('solicitudes_compra.id'), nullable=False)
    
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    
    estado_anterior = db.Column(db.String(20))
    estado_nuevo = db.Column(db.String(20))
    
    accion = db.Column(db.String(100))  # Descripción de la acción
    notas = db.Column(db.Text)
    
    usuario = db.relationship('Usuario')
    
    def __repr__(self):
        return f'<HistorialSolicitud {self.id}>'


# =============================================================================
# ALERTAS Y NOTIFICACIONES
# =============================================================================

class Alerta(db.Model):
    """Alertas del sistema (stock bajo, etc.)"""
    __tablename__ = 'alertas'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Tipos: stock_bajo, solicitud_pendiente, pedido_retrasado
    tipo = db.Column(db.String(50), nullable=False)
    mensaje = db.Column(db.String(255), nullable=False)
    
    # Referencia al objeto relacionado
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'))
    solicitud_id = db.Column(db.Integer, db.ForeignKey('solicitudes_compra.id'))
    
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    leida = db.Column(db.Boolean, default=False)
    fecha_lectura = db.Column(db.DateTime)
    
    producto = db.relationship('Producto')
    solicitud = db.relationship('SolicitudCompra')
    
    def __repr__(self):
        return f'<Alerta {self.tipo}>'
