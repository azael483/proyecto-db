import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'constructoradb483'  # Cambia esto por una clave segura

def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Azael483",
        database="constructoradb"
    )

# Decorador para requerir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión primero', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorador para verificar permisos
def rol_requerido(*roles_permitidos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'rol' not in session or session['rol'] not in roles_permitidos:
                flash('No tienes permisos para esta acción', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ===================== LOGIN =====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Usuarios WHERE username = %s AND password = %s", (username, password))
        usuario = cursor.fetchone()
        cursor.close()
        conexion.close()
        
        if usuario:
            session['usuario_id'] = usuario['id_usuario']
            session['username'] = usuario['username']
            session['rol'] = usuario['rol']
            session['nombre_completo'] = usuario['nombre_completo']
            flash(f'Bienvenido {usuario["nombre_completo"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('login'))

# ===================== PÁGINA PRINCIPAL =====================
@app.route('/')
@login_required
def index():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.id_proyecto, p.nombre, p.ubicacion, e.estado
        FROM Proyectos p
        JOIN Estados e ON p.id_estado = e.id_estado
        ORDER BY p.nombre
    """)
    proyectos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template('index.html', proyectos=proyectos)

# ===================== DETALLE DEL PROYECTO =====================
@app.route('/proyecto/<int:id>')
@login_required
def proyecto_detalle(id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    
    # Datos generales del proyecto
    cursor.execute("""
        SELECT p.*, c.nombre as cliente_nombre, c.apellido as cliente_apellido, e.estado
        FROM Proyectos p
        JOIN Clientes c ON p.id_cliente = c.id_cliente
        JOIN Estados e ON p.id_estado = e.id_estado
        WHERE p.id_proyecto = %s
    """, (id,))
    proyecto = cursor.fetchone()
    
    # Presupuesto usando el procedimiento almacenado
    presupuesto = None
    cursor.callproc("PresupuestoProyecto", [id])
    for result in cursor.stored_results():
        presupuesto = result.fetchone()
    
    # Si no hay presupuesto, crear uno por defecto
    if presupuesto is None:
        presupuesto = (proyecto['nombre'], proyecto['costo_estimado'], 0, 0, 0)
    
    # Encargados del proyecto
    cursor.execute("""
        SELECT e.nombre, e.apellido, e.puesto, pe.rol
        FROM Proyectos_Empleados pe
        JOIN Empleados e ON pe.id_empleado = e.id_empleado
        WHERE pe.id_proyecto = %s
    """, (id,))
    encargados = cursor.fetchall()
    
    cursor.close()
    conexion.close()
    
    return render_template('proyecto_detalle.html', 
                         proyecto=proyecto, 
                         presupuesto=presupuesto,
                         encargados=encargados)

# ===================== TRABAJADORES DEL PROYECTO =====================
@app.route('/proyecto/<int:id>/trabajadores')
@login_required
def proyecto_trabajadores(id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    
    # Info del proyecto
    cursor.execute("SELECT nombre FROM Proyectos WHERE id_proyecto = %s", (id,))
    proyecto = cursor.fetchone()
    
    # Trabajadores del proyecto
    cursor.execute("""
        SELECT e.id_empleado, e.nombre, e.apellido, e.puesto, e.salario, pe.rol
        FROM Proyectos_Empleados pe
        JOIN Empleados e ON pe.id_empleado = e.id_empleado
        WHERE pe.id_proyecto = %s
    """, (id,))
    trabajadores = cursor.fetchall()
    
    # Calcular totales
    total_trabajadores = len(trabajadores)
    total_salarios = sum(t['salario'] for t in trabajadores)
    
    cursor.close()
    conexion.close()
    
    return render_template('proyecto_trabajadores.html',
                         proyecto=proyecto,
                         trabajadores=trabajadores,
                         total_trabajadores=total_trabajadores,
                         total_salarios=total_salarios,
                         id_proyecto=id)

# ===================== MATERIALES DEL PROYECTO =====================
@app.route('/proyecto/<int:id>/materiales')
@login_required
def proyecto_materiales(id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    
    # Info del proyecto
    cursor.execute("SELECT nombre FROM Proyectos WHERE id_proyecto = %s", (id,))
    proyecto = cursor.fetchone()
    
    # Materiales del proyecto
    cursor.execute("""
        SELECT m.nombre as material, m.unidad, pm.cantidad,
               m.costo_unitario, (pm.cantidad * m.costo_unitario) as costo_total,
               e.nombre as empleado_nombre, e.apellido as empleado_apellido
        FROM Proyectos_Materiales pm
        JOIN Materiales m ON pm.id_material = m.id_material
        LEFT JOIN Empleados e ON pm.id_empleado_responsable = e.id_empleado
        WHERE pm.id_proyecto = %s
    """, (id,))
    materiales = cursor.fetchall()
    
    # Total de materiales
    total_costo = sum(m['costo_total'] for m in materiales)
    
    cursor.close()
    conexion.close()
    
    return render_template('proyecto_materiales.html',
                         proyecto=proyecto,
                         materiales=materiales,
                         total_costo=total_costo,
                         id_proyecto=id)

# ===================== EDITAR PROYECTO (Admin) =====================
@app.route('/proyecto/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@rol_requerido('Admin')
def editar_proyecto(id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        ubicacion = request.form['ubicacion']
        id_estado = request.form['id_estado']
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']
        costo_estimado = request.form['costo_estimado']
        
        cursor.execute("""
            UPDATE Proyectos 
            SET nombre=%s, ubicacion=%s, id_estado=%s, fecha_inicio=%s, fecha_fin=%s, costo_estimado=%s
            WHERE id_proyecto=%s
        """, (nombre, ubicacion, id_estado, fecha_inicio, fecha_fin, costo_estimado, id))
        conexion.commit()
        cursor.close()
        conexion.close()
        
        flash('Proyecto actualizado correctamente', 'success')
        return redirect(url_for('proyecto_detalle', id=id))
    
    # Obtener datos del proyecto
    cursor.execute("""
        SELECT p.*, e.estado 
        FROM Proyectos p
        JOIN Estados e ON p.id_estado = e.id_estado
        WHERE p.id_proyecto = %s
    """, (id,))
    proyecto = cursor.fetchone()
    
    # Obtener todos los estados disponibles
    cursor.execute("SELECT id_estado, estado FROM Estados")
    estados = cursor.fetchall()
    
    cursor.close()
    conexion.close()
    
    return render_template('editar_proyecto.html', proyecto=proyecto, estados=estados)

# ===================== AGREGAR TRABAJADOR (Admin/Supervisor) =====================
@app.route('/proyecto/<int:id>/agregar_trabajador', methods=['GET', 'POST'])
@login_required
@rol_requerido('Admin', 'Supervisor')
def agregar_trabajador(id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    
    if request.method == 'POST':
        id_empleado = request.form['id_empleado']
        rol = request.form['rol']
        
        try:
            cursor.execute("""
                INSERT INTO Proyectos_Empleados (id_proyecto, id_empleado, rol)
                VALUES (%s, %s, %s)
            """, (id, id_empleado, rol))
            conexion.commit()
            flash('Trabajador agregado al proyecto', 'success')
        except:
            flash('Error: El trabajador ya está en el proyecto', 'danger')
        
        cursor.close()
        conexion.close()
        return redirect(url_for('proyecto_trabajadores', id=id))
    
    # Obtener empleados disponibles
    cursor.execute("SELECT id_empleado, nombre, apellido, puesto FROM Empleados")
    empleados = cursor.fetchall()
    cursor.close()
    conexion.close()
    
    return render_template('agregar_trabajador.html', empleados=empleados, id_proyecto=id)

# ===================== AGREGAR MATERIAL (Admin/Supervisor) =====================
@app.route('/proyecto/<int:id>/agregar_material', methods=['GET', 'POST'])
@login_required
@rol_requerido('Admin', 'Supervisor')
def agregar_material(id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    
    if request.method == 'POST':
        id_material = request.form['id_material']
        cantidad = request.form['cantidad']
        id_empleado_responsable = request.form['id_empleado_responsable']
        
        try:
            cursor.execute("""
                INSERT INTO Proyectos_Materiales (id_proyecto, id_material, cantidad, id_empleado_responsable)
                VALUES (%s, %s, %s, %s)
            """, (id, id_material, cantidad, id_empleado_responsable))
            conexion.commit()
            flash('Material agregado al proyecto', 'success')
        except:
            flash('Error: El material ya existe en el proyecto', 'danger')
        
        cursor.close()
        conexion.close()
        return redirect(url_for('proyecto_materiales', id=id))
    
    # Obtener materiales y empleados
    cursor.execute("SELECT id_material, nombre, unidad, costo_unitario FROM Materiales")
    materiales = cursor.fetchall()
    
    cursor.execute("SELECT id_empleado, nombre, apellido FROM Empleados")
    empleados = cursor.fetchall()
    
    cursor.close()
    conexion.close()
    
    return render_template('agregar_material.html', 
                         materiales=materiales, 
                         empleados=empleados,
                         id_proyecto=id)

if __name__ == "__main__":
    app.run(debug=True)