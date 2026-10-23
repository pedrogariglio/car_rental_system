# Modelo de datos

Documento normativo del esquema. El archivo `sql/schema.sql` se implementará en la
Fase 2 y deberá coincidir con esta definición.

## 1. Entidades y relaciones

- `vehiculos` 1 — N `reservas`
- `clientes` 1 — N `reservas`
- `reservas` 1 — 0..1 `alquileres`

## 2. Tablas

### `vehiculos`

| Columna | Tipo | Restricciones |
|---------|------|---------------|
| `id` | `INT` | PK, AUTO_INCREMENT |
| `patente` | `VARCHAR(10)` | NOT NULL, UNIQUE |
| `marca` | `VARCHAR(50)` | NOT NULL |
| `modelo` | `VARCHAR(50)` | NOT NULL |
| `anio` | `INT` | NOT NULL |
| `categoria` | `VARCHAR(30)` | NOT NULL |
| `tarifa_diaria` | `DECIMAL(10,2)` | NOT NULL, > 0 |
| `estado` | `VARCHAR(20)` | NOT NULL, DEFAULT `'disponible'` |

Estados admitidos: `disponible`, `alquilado`, `mantenimiento`, `baja`.

### `clientes`

| Columna | Tipo | Restricciones |
|---------|------|---------------|
| `id` | `INT` | PK, AUTO_INCREMENT |
| `documento` | `VARCHAR(20)` | NOT NULL, UNIQUE |
| `nombre` | `VARCHAR(50)` | NOT NULL |
| `apellido` | `VARCHAR(50)` | NOT NULL |
| `telefono` | `VARCHAR(30)` | NULL |
| `correo_electronico` | `VARCHAR(100)` | NULL |
| `activo` | `TINYINT(1)` | NOT NULL, DEFAULT 1 |

La baja de clientes es lógica (`activo = 0`) para preservar el historial.

### `reservas`

| Columna | Tipo | Restricciones |
|---------|------|---------------|
| `id` | `INT` | PK, AUTO_INCREMENT |
| `cliente_id` | `INT` | NOT NULL, FK `clientes(id)` |
| `vehiculo_id` | `INT` | NOT NULL, FK `vehiculos(id)` |
| `fecha_hora_retiro_prevista` | `DATETIME` | NOT NULL |
| `fecha_hora_devolucion_prevista` | `DATETIME` | NOT NULL |
| `tarifa_diaria_acordada` | `DECIMAL(10,2)` | NOT NULL, > 0 |
| `importe_estimado` | `DECIMAL(10,2)` | NOT NULL, >= 0 |
| `estado` | `VARCHAR(20)` | NOT NULL, DEFAULT `'confirmada'` |
| `fecha_creacion` | `DATETIME` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` |

Estados admitidos: `confirmada`, `cancelada`, `completada`.

Restricciones:

- `fecha_hora_devolucion_prevista > fecha_hora_retiro_prevista`.
- Índice `(vehiculo_id, fecha_hora_retiro_prevista, fecha_hora_devolucion_prevista)`
  para las consultas de disponibilidad.

### `alquileres`

| Columna | Tipo | Restricciones |
|---------|------|---------------|
| `id` | `INT` | PK, AUTO_INCREMENT |
| `reserva_id` | `INT` | NOT NULL, UNIQUE, FK `reservas(id)` |
| `fecha_hora_retiro_real` | `DATETIME` | NOT NULL |
| `fecha_hora_devolucion_real` | `DATETIME` | NULL hasta el cierre |
| `importe_base` | `DECIMAL(10,2)` | NULL hasta el cierre |
| `recargo_demora` | `DECIMAL(10,2)` | NOT NULL, DEFAULT 0 |
| `importe_final` | `DECIMAL(10,2)` | NULL hasta el cierre |
| `estado` | `VARCHAR(20)` | NOT NULL, DEFAULT `'en_curso'` |

Estados admitidos: `en_curso`, `finalizado`.

Restricciones:

- `UNIQUE (reserva_id)` garantiza como máximo un alquiler por reserva.
- Al cerrar: `fecha_hora_devolucion_real >= fecha_hora_retiro_real`.
- Al cerrar: `importe_final = importe_base + recargo_demora`.

## 3. Invariantes de negocio

1. Una reserva `confirmada` bloquea su intervalo previsto.
2. Una reserva `cancelada` o `completada` no bloquea disponibilidad.
3. Un alquiler `en_curso` bloquea el vehículo desde su retiro real y sin fecha de
   fin conocida.
4. Un alquiler `finalizado` es histórico y no bloquea por sí mismo.
5. Las reservas se solapan si `nuevo_retiro < existente_devolucion` **y**
   `nuevo_devolucion > existente_retiro`. Los extremos que coinciden no se
   consideran solapamiento.
6. Un vehículo en estado `baja` o `mantenimiento` no puede reservarse ni
   alquilarse.
7. La tarifa usada para facturar es siempre `reservas.tarifa_diaria_acordada`.

## 4. Estrategia de concurrencia

MySQL no ofrece exclusion constraints. La prevención de solapamientos se
implementará en la capa de servicios mediante:

- Validación dentro de una transacción.
- `SELECT ... FOR UPDATE` sobre las reservas y alquileres del vehículo.
- Índice compuesto para las consultas de intervalo.

Limitación documentada: escrituras realizadas fuera de la aplicación no quedan
protegidas por esta validación.
