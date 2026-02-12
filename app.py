from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Inicializar Flask
app = Flask(__name__)
CORS(app)

# Configuración
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost/inventario_tintas')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Inicializar base de datos
db = SQLAlchemy(app)

# Modelos
class Producto(db.Model):
    __tablename__ = 'productos'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(100))
    unidad = db.Column(db.String(20))
    stock_actual = db.Column(db.Float, default=0)
    stock_minimo = db.Column(db.Float, default=0)
    precio_unitario = db.Column(db.Float, default=0)
    ubicacion = db.Column(db.String(100))
    observaciones = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'categoria': self.categoria,
            'unidad': self.unidad,
            'stock_actual': self.stock_actual,
            'stock_minimo': self.stock_minimo,
            'precio_unitario': self.precio_unitario,
            'ubicacion': self.ubicacion,
            'observaciones': self.observaciones,
            'activo': self.activo,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Movimiento(db.Model):
    __tablename__ = 'movimientos'
    
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'entrada', 'salida', 'ajuste'
    cantidad = db.Column(db.Float, nullable=False)
    motivo = db.Column(db.String(200))
    usuario = db.Column(db.String(100))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    
    producto = db.relationship('Producto', backref='movimientos')
    
    def to_dict(self):
        return {
            'id': self.id,
            'producto_id': self.producto_id,
            'tipo': self.tipo,
            'cantidad': self.cantidad,
            'motivo': self.motivo,
            'usuario': self.usuario,
            'fecha': self.fecha.isoformat()
        }

# Rutas
@app.route('/')
def index():
    return jsonify({
        'message': 'API Inventario Tintas - MKTO CATAL IMPORTACIONES',
        'version': '1.0.0',
        'endpoints': {
            'productos': '/api/productos',
            'movimientos': '/api/movimientos',
            'health': '/health'
        }
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()})

# CRUD Productos
@app.route('/api/productos', methods=['GET'])
def get_productos():
    try:
        categoria = request.args.get('categoria')
        activo = request.args.get('activo', 'true').lower() == 'true'
        
        query = Producto.query
        if categoria:
            query = query.filter_by(categoria=categoria)
        query = query.filter_by(activo=activo)
        
        productos = query.all()
        return jsonify([p.to_dict() for p in productos])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/productos/<int:id>', methods=['GET'])
def get_producto(id):
    try:
        producto = Producto.query.get_or_404(id)
        return jsonify(producto.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/productos', methods=['POST'])
def create_producto():
    try:
        data = request.get_json()
        
        producto = Producto(
            codigo=data['codigo'],
            nombre=data['nombre'],
            categoria=data.get('categoria'),
            unidad=data.get('unidad'),
            stock_actual=data.get('stock_actual', 0),
            stock_minimo=data.get('stock_minimo', 0),
            precio_unitario=data.get('precio_unitario', 0),
            ubicacion=data.get('ubicacion'),
            observaciones=data.get('observaciones')
        )
        
        db.session.add(producto)
        db.session.commit()
        
        return jsonify(producto.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/productos/<int:id>', methods=['PUT'])
def update_producto(id):
    try:
        producto = Producto.query.get_or_404(id)
        data = request.get_json()
        
        for key, value in data.items():
            if hasattr(producto, key):
                setattr(producto, key, value)
        
        producto.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(producto.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/productos/<int:id>', methods=['DELETE'])
def delete_producto(id):
    try:
        producto = Producto.query.get_or_404(id)
        producto.activo = False
        db.session.commit()
        
        return jsonify({'message': 'Producto desactivado correctamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# CRUD Movimientos
@app.route('/api/movimientos', methods=['GET'])
def get_movimientos():
    try:
        producto_id = request.args.get('producto_id')
        tipo = request.args.get('tipo')
        
        query = Movimiento.query
        if producto_id:
            query = query.filter_by(producto_id=producto_id)
        if tipo:
            query = query.filter_by(tipo=tipo)
        
        movimientos = query.order_by(Movimiento.fecha.desc()).all()
        return jsonify([m.to_dict() for m in movimientos])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/movimientos', methods=['POST'])
def create_movimiento():
    try:
        data = request.get_json()
        
        producto = Producto.query.get_or_404(data['producto_id'])
        
        movimiento = Movimiento(
            producto_id=data['producto_id'],
            tipo=data['tipo'],
            cantidad=data['cantidad'],
            motivo=data.get('motivo'),
            usuario=data.get('usuario')
        )
        
        # Actualizar stock
        if data['tipo'] == 'entrada':
            producto.stock_actual += data['cantidad']
        elif data['tipo'] == 'salida':
            producto.stock_actual -= data['cantidad']
        elif data['tipo'] == 'ajuste':
            producto.stock_actual = data['cantidad']
        
        db.session.add(movimiento)
        db.session.commit()
        
        return jsonify(movimiento.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Estadísticas
@app.route('/api/estadisticas', methods=['GET'])
def get_estadisticas():
    try:
        total_productos = Producto.query.filter_by(activo=True).count()
        productos_bajo_stock = Producto.query.filter(
            Producto.stock_actual <= Producto.stock_minimo,
            Producto.activo == True
        ).count()
        
        valor_total = db.session.query(
            db.func.sum(Producto.stock_actual * Producto.precio_unitario)
        ).filter_by(activo=True).scalar() or 0
        
        return jsonify({
            'total_productos': total_productos,
            'productos_bajo_stock': productos_bajo_stock,
            'valor_total_inventario': round(valor_total, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Inicializar base de datos
@app.route('/api/init-db', methods=['POST'])
def init_db():
    try:
        db.create_all()
        return jsonify({'message': 'Base de datos inicializada correctamente'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5010))
    app.run(host='0.0.0.0', port=port, debug=False)
