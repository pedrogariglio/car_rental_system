# Car Rental System

Sistema de escritorio para la gestión de alquiler de vehículos. Trabajo práctico
integrador de Programación en Python.

## Estado del proyecto

**Fase 5 completada**: núcleo funcional del MVP, incluyendo vehículos, clientes,
reservas, disponibilidad, inicio de alquileres, devoluciones y cálculo del
importe final, con 82 pruebas automatizadas en verde. La interfaz gráfica,
reportes y API externa todavía no están implementados.

## Alcance

- Administración de vehículos y clientes.
- Reservas, disponibilidad y cancelaciones.
- Inicio de alquileres y registro de devoluciones.
- Cálculo de importes según la política de facturación acordada.
- Historial, reportes y exportación a archivos de texto.
- Integración con una API externa (finalidad pendiente de definición).

Fuera del alcance: portal de clientes, pagos en línea, contabilidad completa,
facturación fiscal y múltiples sucursales.

## Tecnologías

- Python 3.12+
- MySQL 8+
- PyMySQL
- CustomTkinter
- pytest

## Instalación

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Completar `.env` con las credenciales locales de MySQL. El archivo `.env` no se
versiona.

## Base de datos

Crear la base de desarrollo y aplicar el esquema:

```bash
mysql -u usuario -p -e "CREATE DATABASE IF NOT EXISTS car_rental_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u usuario -p car_rental_system < sql/schema.sql
```

La base de pruebas se define con `DB_TEST_NAME`. Las pruebas de integración la
crean automáticamente si el usuario de MySQL tiene permisos; en caso contrario se
omiten.

## Pruebas

```bash
source venv/bin/activate
python -m pytest -q
```

Para ejecutar solo las pruebas que no requieren MySQL:

```bash
python -m pytest -q -m "not integracion"
```

## Ejecución

La aplicación todavía no es ejecutable: `main.py` se incorporará en una fase
posterior.

## Estructura

```
car_rental_system/
├── main.py                 # (pendiente) punto de entrada
├── config.py               # lectura de configuración y .env
├── db.py                   # conexión MySQL y transacciones
├── modelos/                # entidades del dominio
├── repositorios/           # acceso a datos
├── servicios/              # reglas de negocio
├── interfaz/               # GUI CustomTkinter
├── utilidades/             # fechas, validaciones, exportación
├── api/                    # integración con API externa
├── sql/                    # esquema y datos de prueba
├── docs/                   # requisitos y decisiones
└── tests/                  # pruebas con pytest
```

## Documentación

- [Requisitos](docs/requisitos.md)
- [Modelo de datos](docs/modelo_datos.md)
- [Política de facturación y disponibilidad](docs/politica_facturacion.md)
- [Casos de prueba](docs/casos_prueba.md)
- [Decisiones de diseño](docs/decisiones.md)
- [Plan de implementación](docs/plan_implementacion.md)
