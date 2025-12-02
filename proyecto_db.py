import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui_12345'  # Cambia esto por una clave segura

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
    try:
        cursor.callproc("PresupuestoProyecto", [id])
        for result in cursor.stored_results():
            presupuesto = result.fetchone()
    except:
        pass
    
    # Si no hay presupuesto del procedimiento, calcularlo manualmente
    if presupuesto is None:
        # Obtener costo de materiales
        cursor.execute("""
            SELECT COALESCE(SUM(pm.cantidad * m.costo_unitario), 0) as costo_materiales
            FROM Proyectos_Materiales pm
            JOIN Materiales m ON pm.id_material = m.id_material
            WHERE pm.id_proyecto = %s
        """, (id,))
        costo_materiales = cursor.fetchone()['costo_materiales']
        
        # Obtener costo de empleados
        cursor.execute("""
            SELECT COALESCE(SUM(e.salario), 0) as costo_empleados
            FROM Proyectos_Empleados pe
            JOIN Empleados e ON pe.id_empleado = e.id_empleado
            WHERE pe.id_proyecto = %s
        """, (id,))
        costo_empleados = cursor.fetchone()['costo_empleados']
        
        presupuesto_total = costo_materiales + costo_empleados
        presupuesto = (proyecto['nombre'], proyecto['costo_estimado'], costo_materiales, costo_empleados, presupuesto_total)
    
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
        SELECT pm.id_registro, m.id_material, m.nombre as material, m.unidad, pm.cantidad,
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
            # Verificar si ya existe este material con el mismo encargado
            cursor.execute("""
                SELECT cantidad, id_registro 
                FROM Proyectos_Materiales 
                WHERE id_proyecto=%s AND id_material=%s AND id_empleado_responsable=%s
            """, (id, id_material, id_empleado_responsable))
            
            material_existente = cursor.fetchone()
            
            if material_existente:
                # Si existe con el mismo encargado, sumar la cantidad
                cantidad_existente = float(material_existente['cantidad'])
                cantidad_nueva = float(cantidad)
                nueva_cantidad = cantidad_existente + cantidad_nueva
                
                cursor.execute("""
                    UPDATE Proyectos_Materiales 
                    SET cantidad = %s
                    WHERE id_registro = %s
                """, (nueva_cantidad, material_existente['id_registro']))
                conexion.commit()
                flash(f'Cantidad actualizada: {cantidad_existente} + {cantidad_nueva} = {nueva_cantidad}', 'success')
            else:
                # Si no existe o tiene diferente encargado, crear nuevo registro
                cursor.execute("""
                    INSERT INTO Proyectos_Materiales (id_proyecto, id_material, cantidad, id_empleado_responsable)
                    VALUES (%s, %s, %s, %s)
                """, (id, id_material, cantidad, id_empleado_responsable))
                conexion.commit()
                flash('Material agregado al proyecto', 'success')
                
        except Exception as e:
            flash(f'Error al agregar material: {str(e)}', 'danger')
        
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

# ===================== CREAR NUEVO EMPLEADO (Admin/Supervisor) =====================
@app.route('/empleados/nuevo', methods=['GET', 'POST'])
@login_required
@rol_requerido('Admin', 'Supervisor')
def nuevo_empleado():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        puesto = request.form['puesto']
        salario = request.form['salario']
        id_departamento = request.form['id_departamento']
        
        cursor.execute("""
            INSERT INTO Empleados (nombre, apellido, puesto, salario, id_departamento)
            VALUES (%s, %s, %s, %s, %s)
        """, (nombre, apellido, puesto, salario, id_departamento))
        conexion.commit()
        
        # Obtener el ID del empleado recién creado
        nuevo_id = cursor.lastrowid
        
        flash(f'Empleado {nombre} {apellido} creado exitosamente', 'success')
        
        # Si viene desde un proyecto, redirigir al agregar trabajador
        redirect_to_project = request.form.get('redirect_to_project')
        if redirect_to_project:
            cursor.close()
            conexion.close()
            # Redirigir a agregar el empleado al proyecto
            return redirect(url_for('agregar_trabajador', id=redirect_to_project, nuevo_empleado=nuevo_id))
        
        cursor.close()
        conexion.close()
        return redirect(url_for('lista_empleados'))
    
    # Obtener departamentos
    cursor.execute("SELECT id_departamento, nombre FROM Departamentos")
    departamentos = cursor.fetchall()
    cursor.close()
    conexion.close()
    
    return render_template('nuevo_empleado.html', departamentos=departamentos)

# ===================== CREAR NUEVO MATERIAL (Admin/Supervisor) =====================
@app.route('/materiales/nuevo', methods=['GET', 'POST'])
@login_required
@rol_requerido('Admin', 'Supervisor')
def nuevo_material():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        unidad = request.form['unidad']
        costo_unitario = request.form['costo_unitario']
        
        cursor.execute("""
            INSERT INTO Materiales (nombre, unidad, costo_unitario)
            VALUES (%s, %s, %s)
        """, (nombre, unidad, costo_unitario))
        conexion.commit()
        
        # Obtener el ID del material recién creado
        nuevo_id = cursor.lastrowid
        
        flash(f'Material {nombre} creado exitosamente', 'success')
        
        # Si viene desde un proyecto, redirigir al agregar material
        redirect_to_project = request.form.get('redirect_to_project')
        if redirect_to_project:
            cursor.close()
            conexion.close()
            return redirect(url_for('agregar_material', id=redirect_to_project, nuevo_material=nuevo_id))
        
        cursor.close()
        conexion.close()
        return redirect(url_for('lista_materiales'))
    
    cursor.close()
    conexion.close()
    return render_template('nuevo_material.html')

# ===================== LISTA DE EMPLEADOS =====================
@app.route('/empleados')
@login_required
def lista_empleados():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT e.*, d.nombre as departamento_nombre
        FROM Empleados e
        LEFT JOIN Departamentos d ON e.id_departamento = d.id_departamento
        ORDER BY e.nombre
    """)
    empleados = cursor.fetchall()
    cursor.close()
    conexion.close()
    
    return render_template('lista_empleados.html', empleados=empleados)

# ===================== LISTA DE MATERIALES =====================
@app.route('/materiales')
@login_required
def lista_materiales():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM Materiales ORDER BY nombre")
    materiales = cursor.fetchall()
    cursor.close()
    conexion.close()
    
    return render_template('lista_materiales.html', materiales=materiales)

# ===================== EDITAR EMPLEADO (Admin/Supervisor) =====================
@app.route('/empleados/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@rol_requerido('Admin', 'Supervisor')
def editar_empleado(id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        puesto = request.form['puesto']
        salario = request.form['salario']
        id_departamento = request.form['id_departamento']
        
        cursor.execute("""
            UPDATE Empleados 
            SET nombre=%s, apellido=%s, puesto=%s, salario=%s, id_departamento=%s
            WHERE id_empleado=%s
        """, (nombre, apellido, puesto, salario, id_departamento, id))
        conexion.commit()
        
        flash('Empleado actualizado correctamente', 'success')
        cursor.close()
        conexion.close()
        return redirect(url_for('lista_empleados'))
    
    cursor.execute("SELECT * FROM Empleados WHERE id_empleado = %s", (id,))
    empleado = cursor.fetchone()
    
    cursor.execute("SELECT id_departamento, nombre FROM Departamentos")
    departamentos = cursor.fetchall()
    
    cursor.close()
    conexion.close()
    return render_template('editar_empleado.html', empleado=empleado, departamentos=departamentos)

# ===================== EDITAR MATERIAL (Admin/Supervisor) =====================
@app.route('/materiales/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@rol_requerido('Admin', 'Supervisor')
def editar_material(id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        unidad = request.form['unidad']
        costo_unitario = request.form['costo_unitario']
        
        cursor.execute("""
            UPDATE Materiales 
            SET nombre=%s, unidad=%s, costo_unitario=%s
            WHERE id_material=%s
        """, (nombre, unidad, costo_unitario, id))
        conexion.commit()
        
        flash('Material actualizado correctamente', 'success')
        cursor.close()
        conexion.close()
        return redirect(url_for('lista_materiales'))
    
    cursor.execute("SELECT * FROM Materiales WHERE id_material = %s", (id,))
    material = cursor.fetchone()
    cursor.close()
    conexion.close()
    
    return render_template('editar_material.html', material=material)

# ===================== ELIMINAR TRABAJADOR DEL PROYECTO (Admin/Supervisor) =====================
@app.route('/proyecto/<int:id_proyecto>/trabajador/<int:id_empleado>/eliminar', methods=['POST'])
@login_required
@rol_requerido('Admin', 'Supervisor')
def eliminar_trabajador_proyecto(id_proyecto, id_empleado):
    conexion = conectar()
    cursor = conexion.cursor()
    
    cursor.execute("""
        DELETE FROM Proyectos_Empleados 
        WHERE id_proyecto=%s AND id_empleado=%s
    """, (id_proyecto, id_empleado))
    conexion.commit()
    cursor.close()
    conexion.close()
    
    flash('Trabajador eliminado del proyecto', 'success')
    return redirect(url_for('proyecto_trabajadores', id=id_proyecto))

# ===================== ELIMINAR MATERIAL DEL PROYECTO (Admin/Supervisor) =====================
@app.route('/proyecto/<int:id_proyecto>/material/<int:id_registro>/eliminar', methods=['POST'])
@login_required
@rol_requerido('Admin', 'Supervisor')
def eliminar_material_proyecto(id_proyecto, id_registro):
    conexion = conectar()
    cursor = conexion.cursor()
    
    cursor.execute("""
        DELETE FROM Proyectos_Materiales 
        WHERE id_registro=%s
    """, (id_registro,))
    conexion.commit()
    cursor.close()
    conexion.close()
    
    flash('Material eliminado del proyecto', 'success')
    return redirect(url_for('proyecto_materiales', id=id_proyecto))

if __name__ == "__main__":
    app.run(debug=True)