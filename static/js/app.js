const API_URL = 'http://192.168.5.59:5010/api';

class InventarioApp {
    constructor() {
        this.productos = [];
        this.movimientos = [];
        this.estadisticas = {};
        this.currentTab = 'productos';
        this.init();
    }

    init() {
        this.setupTabs();
        this.setupModals();
        this.loadData();
    }

    setupTabs() {
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            });
        });
    }

    setupModals() {
        // Cerrar modales al hacer clic fuera
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });
    }

    switchTab(tabName) {
        // Actualizar tabs activos
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Mostrar contenido
        document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
        document.getElementById(`${tabName}-tab`).style.display = 'block';

        this.currentTab = tabName;
    }

    async loadData() {
        try {
            await Promise.all([
                this.loadProductos(),
                this.loadMovimientos(),
                this.loadEstadisticas()
            ]);
        } catch (error) {
            this.showError('Error al cargar datos: ' + error.message);
        }
    }

    async loadProductos() {
        try {
            const response = await fetch(`${API_URL}/productos`);
            if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);
            this.productos = await response.json();
            this.renderProductos();
        } catch (error) {
            this.showError('Error al cargar productos: ' + error.message);
        }
    }

    async loadMovimientos() {
        try {
            const response = await fetch(`${API_URL}/movimientos`);
            if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);
            this.movimientos = await response.json();
            this.renderMovimientos();
        } catch (error) {
            this.showError('Error al cargar movimientos: ' + error.message);
        }
    }

    async loadEstadisticas() {
        try {
            const response = await fetch(`${API_URL}/estadisticas`);
            if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);
            this.estadisticas = await response.json();
            this.renderEstadisticas();
        } catch (error) {
            this.showError('Error al cargar estadísticas: ' + error.message);
        }
    }

    renderEstadisticas() {
        const stats = this.estadisticas;
        document.getElementById('total-productos').textContent = stats.total_productos || 0;
        document.getElementById('productos-bajos').textContent = stats.productos_bajo_stock || 0;
        document.getElementById('valor-total').textContent = `€${(stats.valor_total || 0).toFixed(2)}`;
    }

    renderProductos() {
        const tbody = document.getElementById('productos-tbody');
        if (this.productos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:40px;">No hay productos registrados</td></tr>';
            return;
        }

        tbody.innerHTML = this.productos.map(p => `
            <tr>
                <td>${p.codigo}</td>
                <td>${p.nombre}</td>
                <td>${p.categoria || '-'}</td>
                <td class="${p.stock_actual <= p.stock_minimo ? 'stock-low' : 'stock-ok'}">
                    ${p.stock_actual} ${p.unidad || 'uds'}
                </td>
                <td>${p.stock_minimo}</td>
                <td>€${(p.precio_unitario || 0).toFixed(2)}</td>
                <td>${p.ubicacion || '-'}</td>
                <td>
                    <span class="badge ${p.activo ? 'badge-success' : 'badge-danger'}">
                        ${p.activo ? 'Activo' : 'Inactivo'}
                    </span>
                </td>
            </tr>
        `).join('');
    }

    renderMovimientos() {
        const tbody = document.getElementById('movimientos-tbody');
        if (this.movimientos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:40px;">No hay movimientos registrados</td></tr>';
            return;
        }

        tbody.innerHTML = this.movimientos.slice(0, 50).map(m => {
            const producto = this.productos.find(p => p.id === m.producto_id);
            return `
                <tr>
                    <td>${new Date(m.fecha).toLocaleString('es-ES')}</td>
                    <td>${producto ? producto.nombre : 'Producto #' + m.producto_id}</td>
                    <td>
                        <span class="badge ${m.tipo === 'entrada' ? 'badge-success' : 'badge-warning'}">
                            ${m.tipo.toUpperCase()}
                        </span>
                    </td>
                    <td>${m.cantidad}</td>
                    <td>${m.motivo || '-'}</td>
                    <td>${m.usuario || '-'}</td>
                </tr>
            `;
        }).join('');
    }

    showError(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-error';
        alertDiv.innerHTML = `<strong>Error:</strong> ${message}`;
        
        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        setTimeout(() => alertDiv.remove(), 5000);
    }

    showSuccess(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success';
        alertDiv.innerHTML = `<strong>Éxito:</strong> ${message}`;
        
        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        setTimeout(() => alertDiv.remove(), 3000);
    }

    openModal(modalId) {
        document.getElementById(modalId).classList.add('active');
    }

    closeModal(modalId) {
        document.getElementById(modalId).classList.remove('active');
    }

    async addProducto(formData) {
        try {
            const response = await fetch(`${API_URL}/productos`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Error al crear producto');
            }

            this.showSuccess('Producto creado correctamente');
            this.closeModal('modal-nuevo-producto');
            await this.loadData();
        } catch (error) {
            this.showError(error.message);
        }
    }

    async addMovimiento(formData) {
        try {
            const response = await fetch(`${API_URL}/movimientos`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Error al registrar movimiento');
            }

            this.showSuccess('Movimiento registrado correctamente');
            this.closeModal('modal-nuevo-movimiento');
            await this.loadData();
        } catch (error) {
            this.showError(error.message);
        }
    }
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.app = new InventarioApp();
});
