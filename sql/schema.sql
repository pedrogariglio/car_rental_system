CREATE TABLE IF NOT EXISTS vehiculos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patente VARCHAR(10) NOT NULL,
    marca VARCHAR(50) NOT NULL,
    modelo VARCHAR(50) NOT NULL,
    anio INT NOT NULL,
    categoria VARCHAR(30) NOT NULL,
    tarifa_diaria DECIMAL(10,2) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'disponible',
    CONSTRAINT uq_vehiculos_patente UNIQUE (patente),
    CONSTRAINT chk_vehiculos_anio CHECK (anio >= 1900),
    CONSTRAINT chk_vehiculos_tarifa CHECK (tarifa_diaria > 0),
    CONSTRAINT chk_vehiculos_estado CHECK (
        estado IN ('disponible', 'alquilado', 'mantenimiento', 'baja')
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    documento VARCHAR(20) NOT NULL,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    telefono VARCHAR(30) NULL,
    correo_electronico VARCHAR(100) NULL,
    activo TINYINT(1) NOT NULL DEFAULT 1,
    CONSTRAINT uq_clientes_documento UNIQUE (documento),
    CONSTRAINT chk_clientes_activo CHECK (activo IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS reservas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    vehiculo_id INT NOT NULL,
    fecha_hora_retiro_prevista DATETIME NOT NULL,
    fecha_hora_devolucion_prevista DATETIME NOT NULL,
    tarifa_diaria_acordada DECIMAL(10,2) NOT NULL,
    importe_estimado DECIMAL(10,2) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'confirmada',
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_reservas_cliente FOREIGN KEY (cliente_id)
        REFERENCES clientes(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_reservas_vehiculo FOREIGN KEY (vehiculo_id)
        REFERENCES vehiculos(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_reservas_fechas CHECK (
        fecha_hora_devolucion_prevista > fecha_hora_retiro_prevista
    ),
    CONSTRAINT chk_reservas_tarifa CHECK (tarifa_diaria_acordada > 0),
    CONSTRAINT chk_reservas_importe CHECK (importe_estimado >= 0),
    CONSTRAINT chk_reservas_estado CHECK (
        estado IN ('confirmada', 'cancelada', 'completada')
    ),
    INDEX idx_reservas_disponibilidad (
        vehiculo_id,
        fecha_hora_retiro_prevista,
        fecha_hora_devolucion_prevista
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS alquileres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reserva_id INT NOT NULL,
    fecha_hora_retiro_real DATETIME NOT NULL,
    fecha_hora_devolucion_real DATETIME NULL,
    importe_base DECIMAL(10,2) NULL,
    recargo_demora DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    importe_final DECIMAL(10,2) NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'en_curso',
    CONSTRAINT uq_alquileres_reserva UNIQUE (reserva_id),
    CONSTRAINT fk_alquileres_reserva FOREIGN KEY (reserva_id)
        REFERENCES reservas(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_alquileres_fechas CHECK (
        fecha_hora_devolucion_real IS NULL
        OR fecha_hora_devolucion_real > fecha_hora_retiro_real
    ),
    CONSTRAINT chk_alquileres_importes CHECK (
        (importe_base IS NULL OR importe_base >= 0)
        AND (importe_final IS NULL OR importe_final >= 0)
        AND recargo_demora >= 0
    ),
    CONSTRAINT chk_alquileres_estado CHECK (
        estado IN ('en_curso', 'finalizado')
    ),
    CONSTRAINT chk_alquileres_cierre CHECK (
        (
            estado = 'en_curso'
            AND fecha_hora_devolucion_real IS NULL
            AND importe_base IS NULL
            AND importe_final IS NULL
            AND recargo_demora = 0
        )
        OR
        (
            estado = 'finalizado'
            AND fecha_hora_devolucion_real IS NOT NULL
            AND importe_base IS NOT NULL
            AND importe_final IS NOT NULL
            AND importe_final = importe_base + recargo_demora
        )
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
