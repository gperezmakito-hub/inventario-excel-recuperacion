"""
Rutas de autenticación
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import Usuario
from app import db
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Inicio de sesión"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('Por favor, introduce usuario y contraseña.', 'warning')
            return render_template('auth/login.html')
        
        usuario = Usuario.query.filter_by(username=username).first()
        
        if usuario is None or not usuario.check_password(password):
            flash('Usuario o contraseña incorrectos.', 'danger')
            return render_template('auth/login.html')
        
        if not usuario.activo:
            flash('Tu cuenta está desactivada. Contacta con el administrador.', 'warning')
            return render_template('auth/login.html')
        
        # Login exitoso
        login_user(usuario, remember=remember)
        usuario.ultimo_acceso = datetime.utcnow()
        db.session.commit()
        
        flash(f'¡Bienvenido/a, {usuario.nombre_completo}!', 'success')
        
        # Redirigir a la página solicitada o al dashboard
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/perfil')
@login_required
def perfil():
    """Ver perfil del usuario"""
    return render_template('auth/perfil.html')


@auth_bp.route('/cambiar-password', methods=['GET', 'POST'])
@login_required
def cambiar_password():
    """Cambiar contraseña"""
    if request.method == 'POST':
        password_actual = request.form.get('password_actual', '')
        password_nuevo = request.form.get('password_nuevo', '')
        password_confirmar = request.form.get('password_confirmar', '')
        
        if not current_user.check_password(password_actual):
            flash('La contraseña actual es incorrecta.', 'danger')
            return render_template('auth/cambiar_password.html')
        
        if password_nuevo != password_confirmar:
            flash('Las contraseñas nuevas no coinciden.', 'warning')
            return render_template('auth/cambiar_password.html')
        
        if len(password_nuevo) < 4:
            flash('La contraseña debe tener al menos 4 caracteres.', 'warning')
            return render_template('auth/cambiar_password.html')
        
        current_user.set_password(password_nuevo)
        db.session.commit()
        
        flash('Contraseña cambiada correctamente.', 'success')
        return redirect(url_for('auth.perfil'))
    
    return render_template('auth/cambiar_password.html')
