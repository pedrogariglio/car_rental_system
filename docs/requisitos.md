# Requisitos del sistema

## 1. Objetivo

Construir una aplicación de escritorio para administrar el alquiler de vehículos,
aplicando programación estructurada y orientada a objetos, separación de
responsabilidades, manejo de excepciones, persistencia en MySQL e interfaz
gráfica con CustomTkinter.

## 2. Alcance funcional

| ID | Requisito |
|----|-----------|
| RF-01 | Registrar, consultar, modificar y administrar vehículos. |
| RF-02 | Registrar, consultar y modificar clientes. |
| RF-03 | Crear, consultar, modificar y cancelar reservas. |
| RF-04 | Consultar la disponibilidad de un vehículo para un período. |
| RF-05 | Iniciar alquileres asociados a una reserva. |
| RF-06 | Registrar devoluciones y calcular los importes. |
| RF-07 | Consultar el historial de clientes, reservas y alquileres. |
| RF-08 | Generar reportes y exportar información a archivos de texto. |
| RF-09 | Integrar al menos una API externa. |

## 3. Fuera de alcance

- Portal para clientes.
- Pagos en línea.
- Contabilidad completa.
- Facturación fiscal.
- Gestión de múltiples sucursales.

## 4. Reglas generales

- Todos los alquileres deben estar vinculados a una reserva, incluso los
  iniciados presencialmente. En ese caso se crea la reserva y el alquiler en la
  misma operación transaccional.
- Una reserva puede originar como máximo un alquiler.
- Un cliente puede tener muchas reservas.
- Un vehículo puede tener muchas reservas a lo largo del tiempo.
- La tarifa diaria acordada en la reserva queda congelada y no cambia si se
  modifica la tarifa vigente del vehículo.
- Las reservas superpuestas para un mismo vehículo deben rechazarse.
- Los importes se representan con `Decimal` en Python y `DECIMAL(10,2)` en MySQL.
  No se utiliza `float` para valores monetarios.

## 5. Nomenclatura

Entidades, tablas, atributos, clases, variables de dominio y funciones de negocio
se nombran en español. Los nombres de bibliotecas, módulos de terceros y APIs se
mantienen en su denominación original.

## 6. Requisitos no funcionales

- Código legible y documentado, apto para explicación académica.
- Separación entre modelos, repositorios, servicios, interfaz y configuración.
- La lógica de facturación debe poder probarse sin MySQL ni interfaz gráfica.
- Validación de fechas, importes, estados y disponibilidad.
- Uso de transacciones en operaciones que actualizan varios registros.
- Suite de pruebas automatizadas con pytest.
- Sin dependencias innecesarias ni patrones arquitectónicos injustificados.
