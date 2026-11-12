# Plan de implementación

Trabajo incremental. Cada fase debe revisarse y verificarse antes de avanzar.

## Fase 0 — Preparación (completada)

**Alcance:** repositorio propio, estructura de directorios, dependencias,
`.env.example`, `.gitignore` y documentación inicial.

**Entregables:**

- Repositorio Git local con rama `main`.
- `requirements.txt` con PyMySQL, python-dotenv, CustomTkinter y pytest.
- Documentos de requisitos, modelo de datos, facturación, casos de prueba,
  decisiones y plan.
- Carpetas de capas creadas (aún sin lógica).

**Verificación:** estructura y archivos revisados. No se ejecutaron pruebas
porque todavía no existe código funcional.

## Fase 1 — Dominio y facturación (completada)

**Depende de:** Fase 0.

**Alcance:** modelos de dominio, estados, validaciones puras y cálculo de
importes en `servicios/facturacion.py`. Sin MySQL ni GUI.

**Entregables:**

- Modelos `Vehiculo`, `Cliente`, `Reserva` y `Alquiler`.
- Estados y clasificación de devoluciones del dominio.
- Validaciones reutilizables y excepción `ErrorValidacion`.
- Cálculo puro de bloques, importe estimado y facturación de devoluciones.
- Pruebas F-01 a F-14 y validaciones básicas de los modelos.

**Verificación:** `venv/bin/python -m pytest -q` → **35 passed**. No se usa
`float` para importes y `servicios/facturacion.py` no importa `db` ni `interfaz`.

## Fase 2 — Conexión y esquema MySQL (completada)

**Depende de:** Fase 0.

**Alcance:** `config.py`, `db.py` con PyMySQL, `sql/schema.sql`, transacciones y
base de prueba.

**Entregables:**

- Lectura de configuración desde `.env` y validación de variables.
- Clase `BaseDatos` con consultas parametrizadas, commit, rollback y context
  manager de transacción.
- Esquema MySQL con claves foráneas, restricciones `CHECK`, índice de
  disponibilidad y `UNIQUE (reserva_id)`.
- Pruebas de configuración y pruebas de integración de conexión, esquema, commit
  y rollback.

**Verificación:** ejecución contra MySQL 8.4 → **43 passed** (39 unitarias y 4 de
integración). El esquema se creó en `car_rental_system_test` y el rollback se
comprobó con una inserción descartada.

## Fase 3 — Repositorios y CRUD de vehículos y clientes (completada)

**Depende de:** Fases 1 y 2.

**Alcance:** repositorios parametrizados y servicios de alta, consulta,
modificación y baja lógica.

**Entregables:**

- Repositorios de vehículos y clientes con SQL parametrizado.
- Servicios con validaciones, transacciones, detección de duplicados y baja
  lógica.
- Traducción de violaciones `UNIQUE` a `ErrorDuplicado` y luego a
  `ErrorValidacion` en los servicios.
- Pruebas de integración de CRUD, duplicados, inexistentes y campos no
  permitidos.

**Verificación:** ejecución contra MySQL 8.4 → **54 passed** (39 unitarias y 15 de
integración). Se comprobaron alta, consulta, modificación, baja/reactivación y
rechazo de patentes y documentos duplicados.

## Fase 4 — Reservas y disponibilidad

**Depende de:** Fase 3.

**Alcance:** alta, consulta, modificación y cancelación de reservas; cálculo del
importe estimado; control transaccional de solapamientos.

**Aceptación:** casos D-01 a D-10 y V-01, V-04, V-09 en verde; cancelación libera
el intervalo.

## Fase 5 — Alquileres y devoluciones

**Depende de:** Fase 4.

**Alcance:** inicio de alquiler desde reserva, cierre con devolución, cálculo y
persistencia del desglose económico.

**Aceptación:** casos V-05 a V-08 y V-10 en verde; como máximo un alquiler por
reserva; cierre transaccional coherente.

## Fase 6 — Historial, reportes y exportación

**Depende de:** Fase 5.

**Alcance:** consultas de historial, reportes y exportación a archivos de texto.

**Aceptación:** filtros por cliente, vehículo y fechas; archivo exportado
verificable; montos formateados con `Decimal`.

## Fase 7 — Interfaz gráfica

**Depende de:** Fases 3 a 6.

**Alcance:** ventanas y formularios CustomTkinter conectados a los servicios.

**Aceptación:** flujos completos de vehículos, clientes, reservas, alquileres,
devoluciones y reportes; sin lógica de negocio en la UI.

## Fase 8 — API externa

**Depende de:** Fase 7 y definición de la finalidad de la API.

**Alcance:** cliente HTTP con manejo de timeout y errores, sin secretos en el
código.

**Aceptación:** integración documentada, degradación controlada ante fallos y
credenciales en `.env`.

## Fase 9 — Cierre

**Depende de:** todas las anteriores.

**Alcance:** repaso de validaciones, datos de demostración, documentación final y
ejecución completa de la suite.

**Aceptación:** suite completa en verde, README actualizado y alcance verificado
contra `docs/requisitos.md`.

## Decisiones pendientes antes de avanzar

1. Finalidad y proveedor de la API externa (Fase 8).
2. Ventana temporal para cancelar reservas confirmadas.
3. Edición de vehículos/clientes con alquiler en curso.
4. Comportamiento ante retiro real distinto del previsto.
