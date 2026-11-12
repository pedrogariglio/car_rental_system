# Decisiones de diseño

Registro liviano de decisiones (ADR). Fecha de registro: 2026-10-22.

## ADR-001 — Repositorio propio

**Contexto:** el proyecto vive dentro de `ADETEC_2026`, que contiene otros
trabajos académicos.

**Decisión:** `car_rental_system/` es un repositorio Git independiente, con rama
`main`. El repositorio se inicializó localmente; la creación del remoto en GitHub
queda pendiente.

**Consecuencias:** historial aislado del resto de los ejercicios. El repositorio
padre no debe versionar el contenido de este directorio.

## ADR-002 — Interfaz con CustomTkinter

**Contexto:** se evaluó Tkinter/ttk y CustomTkinter.

**Decisión:** usar CustomTkinter por su apariencia moderna y widgets listos para
una interfaz de escritorio actual.

**Consecuencias:** se agrega una dependencia externa (`customtkinter`). La lógica
de negocio no dependerá de la GUI para poder probarse de forma aislada.

## ADR-003 — Pruebas con pytest

**Decisión:** usar pytest como marco de pruebas.

**Consecuencias:** dependencia de desarrollo. Las pruebas de facturación y
validaciones puras no requieren MySQL ni la interfaz.

## ADR-004 — Acceso a MySQL con PyMySQL

**Decisión:** usar PyMySQL, según lo definido en la especificación del proyecto.
No se reutiliza `mysql-connector-python` del proyecto `mundial/`.

**Consecuencias:** SQL parametrizado y manejo explícito de transacciones en la
capa de acceso a datos.

## ADR-005 — Carpetas planas por capa

**Contexto:** se evaluó un paquete bajo `src/` frente a módulos en carpetas
directas.

**Decisión:** usar carpetas planas (`modelos/`, `repositorios/`, `servicios/`,
`interfaz/`, `utilidades/`, `api/`).

**Consecuencias:** imports simples y estructura explicable académicamente, sin
complejidad de empaquetado.

## ADR-006 — Baja lógica

**Decisión:** vehículos y clientes no se eliminan físicamente. Los vehículos usan
`estado` (incluye `baja`) y los clientes usan `activo`.

**Consecuencias:** se conserva el historial de reservas y alquileres. Las
consultas operativas deben filtrar registros dados de baja.

## ADR-007 — Base de datos de pruebas separada

**Decisión:** las pruebas de integración usan `DB_TEST_NAME`, distinta de la base
de desarrollo `DB_NAME`.

**Consecuencias:** evita contaminar datos reales. El esquema de prueba se crea y
limpia desde la suite o mediante script.

## ADR-008 — Redondeo monetario

**Decisión:** usar `Decimal` con `ROUND_HALF_UP`, redondeando una sola vez el
importe final a dos decimales. El recargo persistido se deriva como
`importe_final - importe_base`.

**Consecuencias:** se mantiene la invariante
`importe_final = importe_base + recargo_demora` y no se usa `float`.

## ADR-009 — Sin buffer entre alquileres

**Decisión:** no se agrega buffer automático. Un alquiler puede terminar
exactamente cuando comienza el siguiente, si no hay solapamiento estricto.

**Consecuencias:** la regla de disponibilidad usa desigualdades estrictas.

## ADR-010 — Nomenclatura de dominio en español

**Decisión:** entidades, tablas, atributos, clases y funciones de negocio en
español. Bibliotecas, módulos de terceros y APIs conservan su nombre original.

**Consecuencias:** coherencia con la consigna y con el modelo de datos.

## ADR-011 — GUI mínima de una sola ventana con pestañas

**Contexto:** el MVP necesita una interfaz demostrable sin ampliar demasiado el
alcance ni duplicar lógica de negocio.

**Decisión:** usar una única ventana con cuatro pestañas (Vehículos, Clientes,
Reservas, Alquileres). Las vistas solo llaman a los servicios y no contienen
reglas de negocio.

**Consecuencias:** navegación simple y menos código de infraestructura. Los
reportes y la API externa quedan fuera de esta versión y se agregarán después.
