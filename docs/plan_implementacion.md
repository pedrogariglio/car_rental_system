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

## Fase 1 — Dominio y facturación

**Depende de:** Fase 0.

**Alcance:** modelos de dominio, estados, validaciones puras y cálculo de
importes en `servicios/facturacion.py`. Sin MySQL ni GUI.

**Aceptación:** casos F-01 a F-14 en verde; sin `float`; la lógica de facturación
se importa sin acceso a base de datos.

## Fase 2 — Conexión y esquema MySQL

**Depende de:** Fase 0.

**Alcance:** `config.py`, `db.py` con PyMySQL, `sql/schema.sql`, transacciones y
base de prueba.

**Aceptación:** esquema creado en `DB_TEST_NAME`; conexión y rollback
verificados; credenciales leídas desde `.env`.

## Fase 3 — Repositorios y CRUD de vehículos y clientes

**Depende de:** Fases 1 y 2.

**Alcance:** repositorios parametrizados y servicios de alta, consulta,
modificación y baja lógica.

**Aceptación:** CRUD funcional, validaciones V-02 y V-03, sin concatenación de SQL
con datos de usuario.

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
