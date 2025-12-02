DROP DATABASE IF EXISTS ConstructoraDB;
CREATE DATABASE ConstructoraDB;
USE ConstructoraDB;
-- AGREGAR A TU BASE DE DATOS EXISTENTE

-- TABLA USUARIOS PARA LOGIN
CREATE TABLE Usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    rol ENUM('Admin', 'Supervisor', 'Consulta') NOT NULL,
    nombre_completo VARCHAR(100) NOT NULL
);


-- TABLA DEPARTAMENTOS
CREATE TABLE Departamentos (
    id_departamento INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL
);

-- TABLA EMPLEADOS
CREATE TABLE Empleados (
    id_empleado INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    puesto VARCHAR(50),
    salario DECIMAL(10,2),
    id_departamento INT,
    FOREIGN KEY (id_departamento) REFERENCES Departamentos(id_departamento)
);

-- TABLA CLIENTES
CREATE TABLE Clientes (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    telefono VARCHAR(15),
    email VARCHAR(50)
);

-- TABLA etados del proyecto
CREATE TABLE Estados (
    id_estado INT AUTO_INCREMENT PRIMARY KEY,
    estado VARCHAR(50) NOT NULL
);
-- TABLA PROYECTOS
CREATE TABLE Proyectos (
    id_proyecto INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    ubicacion VARCHAR(100),
    fecha_inicio DATE,
    fecha_fin DATE,
    costo_estimado DECIMAL(12,2),
    id_cliente INT,
    FOREIGN KEY (id_cliente) REFERENCES Clientes(id_cliente),
    id_estado INT,
    FOREIGN KEY (id_estado) REFERENCES Estados(id_estado)
);

-- TABLA INTERMEDIA: PROYECTOS Y EMPLEADOS
CREATE TABLE Proyectos_Empleados (
    id_proyecto INT,
    id_empleado INT,
    rol VARCHAR(50), 
    PRIMARY KEY (id_proyecto, id_empleado),
    FOREIGN KEY (id_proyecto) REFERENCES Proyectos(id_proyecto),
    FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
);

-- TABLA MATERIALES
CREATE TABLE Materiales (
    id_material INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    unidad VARCHAR(20), 
    costo_unitario DECIMAL(10,2)
);

-- TABLA INTERMEDIA: PROYECTOS Y MATERIALES
CREATE TABLE Proyectos_Materiales (
    id_proyecto INT,
    id_material INT,
    cantidad DECIMAL(10,2),
    id_empleado_responsable INT NULL,
    PRIMARY KEY (id_proyecto, id_material),
    FOREIGN KEY (id_empleado_responsable) REFERENCES Empleados(id_empleado)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    FOREIGN KEY (id_proyecto) REFERENCES Proyectos(id_proyecto),
    FOREIGN KEY (id_material) REFERENCES Materiales(id_material)
);

-- USUARIOS
INSERT INTO Usuarios (username, password, rol, nombre_completo) VALUES
('admin', 'admin123', 'Admin', 'Administrador del Sistema'),
('supervisor', 'super123', 'Supervisor', 'Juan Supervisor'),
('consulta', 'consulta123', 'Consulta', 'María Consultora');

-- Departamentos
INSERT INTO Departamentos (nombre) VALUES
('Ingeniería'),
('Administración'),
('Construcción'),
('Diseño'),
('Supervisión');

-- Empleados
INSERT INTO Empleados (nombre, apellido, puesto, salario, id_departamento) VALUES
('Juan', 'Pérez', 'Ingeniero Civil', 30000, 1),
('María', 'García', 'Arquitecta', 28000, 4),
('Carlos', 'López', 'Contador', 20000, 2),
('Ana', 'Martínez', 'Albañil', 12000, 3),
('José', 'Ramírez', 'Supervisor de Obra', 25000, 5),
('Elena', 'Flores', 'Diseñadora de Interiores', 23000, 4),
('Miguel', 'Santos', 'Electricista', 15000, 3),
('Laura', 'Torres', 'Administradora', 21000, 2);

-- Clientes
INSERT INTO Clientes (nombre, apellido, telefono, email) VALUES
('Luis', 'Hernández', '5544332211', 'luis@mail.com'),
('Sofía', 'Ramírez', '5533445566', 'sofia@mail.com'),
('Daniel', 'Mendoza', '5522113344', 'daniel@mail.com'),
('Lucía', 'Pérez', '5588776655', 'lucia@mail.com');

INSERT INTO Estados (estado) VALUES
('Completado'),
('En construccion'),
('Pausado'),
('Cancelado');

-- Proyectos
INSERT INTO Proyectos (nombre, ubicacion, fecha_inicio, fecha_fin, costo_estimado, id_cliente, id_estado) VALUES
('Residencial Las Palmas', 'Monterrey', '2025-01-15', '2025-09-30', 15000000, 1, 2),
('Edificio Torre Azul', 'Guadalajara', '2025-03-01', '2026-02-28', 35000000, 2, 2),
('Casa Moderna Riviera', 'Cancún', '2025-04-10', '2025-12-20', 9000000, 3, 3),
('Plaza Comercial Sol', 'Ciudad de México', '2025-02-01', '2026-03-15', 28000000, 4, 3);

-- Relación Proyectos ↔ Empleados
INSERT INTO Proyectos_Empleados (id_proyecto, id_empleado, rol) VALUES
(1, 1, 'Ingeniero Residente'),
(1, 4, 'Albañil'),
(1, 5, 'Supervisor'),
(2, 2, 'Arquitecta Jefe'),
(2, 3, 'Contador'),
(2, 7, 'Electricista'),
(3, 1, 'Ingeniero Civil'),
(3, 6, 'Diseñadora'),
(4, 8, 'Administradora'),
(4, 5, 'Supervisor');

-- Materiales
INSERT INTO Materiales (nombre, unidad, costo_unitario) VALUES
('Grava', 'm3', 700.00),
('Varilla de acero 3/8"', 'pieza', 120.00),
('Bloque de concreto', 'pieza', 9.50),
('Madera para cimbra', 'm3', 2500.00),
('Yeso', 'saco', 150.00),
('Pintura blanca', 'litro', 80.00),
('Tubería PVC 2”', 'metro', 45.00),
('Cemento', 'tonelada', 2500.00),
('Arena', 'm3', 500.00),
('Acero', 'tonelada', 12000.00),
('Ladrillo', 'pieza', 5.00),
('Vidrio templado', 'm2', 850.00),
('Cable eléctrico', 'metro', 25.00),
('Azulejo', 'm2', 300.00);

-- Materiales usados en cada proyecto
INSERT INTO Proyectos_Materiales (id_proyecto, id_material, cantidad, id_empleado_responsable) VALUES
(1, 5, 400, 1),
(1, 6, 200, 4),
(1, 9, 25, 5),
(1, 10, 10, 4),
(2, 7, 300, 2),
(2, 8, 500, 3),
(2, 11, 400, 7),
(2, 1, 250, 2),
(3, 5, 200, 1),
(3, 13, 600, 2),
(3, 14, 100, 4),
(4, 10, 80, 3),
(4, 12, 150, 5),
(4, 8, 700, 8);

-- =====================================================
-- CONSULTA: DETALLE DE PROYECTOS (Actualizada)
-- =====================================================
SELECT 
    p.nombre AS Proyecto,                          
    c.nombre AS Nombre_Cliente,                      
    c.apellido AS Apellido_Cliente,                  
    m.nombre AS Material,                          
    pm.cantidad AS Cantidad_Usada,        
    (pm.cantidad * m.costo_unitario) AS Costo_Material_Total,  
    e.nombre AS Empleado_Responsable,                          
    e.apellido AS Apellido_Responsable,               
    e.puesto AS Puesto_Responsable,                             
    p.costo_estimado AS Presupuesto_Proyecto       
FROM Proyectos p
JOIN Clientes c ON p.id_cliente = c.id_cliente
JOIN Proyectos_Materiales pm ON p.id_proyecto = pm.id_proyecto
JOIN Materiales m ON pm.id_material = m.id_material
JOIN Empleados e ON pm.id_empleado_responsable = e.id_empleado
ORDER BY p.nombre, m.nombre;

-- =====================================================
-- CONSULTA: DETALLE DE EMPLEADOS
-- =====================================================
SELECT 
    Empleados.nombre AS Empleado,
    Empleados.puesto,
    Empleados.salario,
    Proyectos.nombre AS Proyecto
FROM Empleados
JOIN Proyectos_Empleados ON Empleados.id_empleado = Proyectos_Empleados.id_empleado
JOIN Proyectos ON Proyectos_Empleados.id_proyecto = Proyectos.id_proyecto;

-- =====================================================
-- procedimiento: checar los presupuestos 
-- =====================================================
DELIMITER $$

CREATE PROCEDURE PresupuestoProyecto(IN proyecto_id INT)
BEGIN
    SELECT Proyectos.nombre AS Proyecto,
           Proyectos.costo_estimado AS Presupuesto_Original,
           SUM(Proyectos_Materiales.cantidad * Materiales.costo_unitario) AS Costo_Materiales,
           SUM(Empleados.salario) AS Costo_Empleados,
           (SUM(Proyectos_Materiales.cantidad * Materiales.costo_unitario) + SUM(Empleados.salario)) AS Presupuesto_Total
    FROM Proyectos
    JOIN Proyectos_Materiales ON Proyectos.id_proyecto = Proyectos_Materiales.id_proyecto
    JOIN Materiales ON Proyectos_Materiales.id_material = Materiales.id_material
    JOIN Proyectos_Empleados ON Proyectos.id_proyecto = Proyectos_Empleados.id_proyecto
    JOIN Empleados ON Proyectos_Empleados.id_empleado = Empleados.id_empleado
    WHERE Proyectos.id_proyecto = proyecto_id
    GROUP BY Proyectos.id_proyecto;
END $$

DELIMITER ;

-- =====================================================
-- procedimiento: ver los costos totales de los materiales  
-- =====================================================

DELIMITER $$

CREATE PROCEDURE MaterialesProyecto(IN proyecto_id INT)
BEGIN
    SELECT 
        Materiales.nombre AS Material,                    
        Materiales.unidad AS Unidad,                      
        Proyectos_Materiales.cantidad AS Cantidad,       
        (Proyectos_Materiales.cantidad * Materiales.costo_unitario) AS Costo_Total  
    FROM Proyectos_Materiales
    JOIN Materiales ON Proyectos_Materiales.id_material = Materiales.id_material
    WHERE Proyectos_Materiales.id_proyecto = proyecto_id;
END $$

DELIMITER ;

-- =====================================================
-- Transacción: presupuesto no puede ser menor al costo actual
-- =====================================================

DELIMITER $$

CREATE PROCEDURE ActualizarPresupuesto(
    IN p_proyecto INT,
    IN p_nuevo_presupuesto DECIMAL(12,2)
)
BEGIN
    DECLARE costo_actual DECIMAL(12,2);

    START TRANSACTION;

    -- Costo actual de materiales
    SELECT SUM(pm.cantidad * m.costo_unitario)
    INTO costo_actual
    FROM Proyectos_Materiales pm
    JOIN Materiales m ON pm.id_material = m.id_material
    WHERE pm.id_proyecto = p_proyecto;

    -- Validación
    IF p_nuevo_presupuesto < costo_actual THEN
        -- Si el presupuesto es insuficiente, cancelar todo
        ROLLBACK;
    ELSE
        -- Actualizar presupuesto del proyecto
        UPDATE Proyectos 
        SET costo_estimado = p_nuevo_presupuesto
        WHERE id_proyecto = p_proyecto;

        COMMIT;
    END IF;

END $$

DELIMITER ;

-- =====================================================
-- Transacción: Registrar un cliente nuevo y crear su proyecto
-- =====================================================
DELIMITER $$

CREATE PROCEDURE RegistrarClienteProyecto(
    IN p_nombre_cliente VARCHAR(50),
    IN p_apellido_cliente VARCHAR(50),
    IN p_telefono VARCHAR(15),
    IN p_email VARCHAR(50),
    IN p_nombre_proyecto VARCHAR(100),
    IN p_ubicacion VARCHAR(100),
    IN p_fecha_inicio DATE,
    IN p_fecha_fin DATE,
    IN p_costo_estimado DECIMAL(12,2),
    IN p_estado INT
)
BEGIN
    DECLARE nuevo_cliente_id INT;

    START TRANSACTION;

    -- Insertar cliente
    INSERT INTO Clientes (nombre, apellido, telefono, email)
    VALUES (p_nombre_cliente, p_apellido_cliente, p_telefono, p_email);

    -- Guardar ID del nuevo cliente
    SET nuevo_cliente_id = LAST_INSERT_ID();

    -- Insertar proyecto asociado
    INSERT INTO Proyectos (nombre, ubicacion, fecha_inicio, fecha_fin, costo_estimado, id_cliente, id_estado)
    VALUES (p_nombre_proyecto, p_ubicacion, p_fecha_inicio, p_fecha_fin, p_costo_estimado, nuevo_cliente_id, p_estado);

    COMMIT;
END $$

DELIMITER ;
