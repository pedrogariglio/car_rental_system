"""Pruebas de integración de reservas y disponibilidad."""

from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from modelos.estados import EstadoAlquiler, EstadoReserva, EstadoVehiculo
from servicios.servicio_clientes import ServicioClientes
from servicios.servicio_reservas import ServicioReservas
from servicios.servicio_vehiculos import ServicioVehiculos
from utilidades.excepciones import ErrorValidacion

pytestmark = pytest.mark.integracion

INICIO = datetime(2026, 12, 10, 10, 0)
TARIFA = Decimal("10000.00")


@pytest.fixture
def entorno(base_datos_prueba):
    servicio_vehiculos = ServicioVehiculos(base_datos_prueba)
    servicio_clientes = ServicioClientes(base_datos_prueba)
    servicio_reservas = ServicioReservas(base_datos_prueba)

    cliente = servicio_clientes.registrar(
        f"T{uuid4().hex[:10]}",
        "Ana",
        "Pérez",
    )
    vehiculo = servicio_vehiculos.registrar(
        f"T{uuid4().hex[:6].upper()}",
        "Toyota",
        "Corolla",
        2024,
        "sedan",
        TARIFA,
    )
    vehiculos_creados = [vehiculo]

    def nuevo_vehiculo():
        nuevo = servicio_vehiculos.registrar(
            f"T{uuid4().hex[:6].upper()}",
            "Ford",
            "Focus",
            2023,
            "sedan",
            TARIFA,
        )
        vehiculos_creados.append(nuevo)
        return nuevo

    datos = SimpleNamespace(
        base_datos=base_datos_prueba,
        servicio_vehiculos=servicio_vehiculos,
        servicio_reservas=servicio_reservas,
        cliente=cliente,
        vehiculo=vehiculo,
        nuevo_vehiculo=nuevo_vehiculo,
    )

    yield datos

    with base_datos_prueba.transaccion():
        base_datos_prueba.ejecutar(
            """
            DELETE FROM alquileres
            WHERE reserva_id IN (
                SELECT id FROM reservas WHERE cliente_id = %s
            )
            """,
            (cliente.id,),
        )
        base_datos_prueba.ejecutar(
            "DELETE FROM reservas WHERE cliente_id = %s",
            (cliente.id,),
        )
        for creado in vehiculos_creados:
            base_datos_prueba.ejecutar(
                "DELETE FROM vehiculos WHERE id = %s",
                (creado.id,),
            )
        base_datos_prueba.ejecutar(
            "DELETE FROM clientes WHERE id = %s",
            (cliente.id,),
        )


def _reservar(entorno, retiro=INICIO, devolucion=None, vehiculo=None):
    if devolucion is None:
        devolucion = retiro + timedelta(hours=24)
    return entorno.servicio_reservas.crear(
        entorno.cliente.id,
        (vehiculo or entorno.vehiculo).id,
        retiro,
        devolucion,
    )


def _completar_reserva(entorno, reserva) -> None:
    with entorno.base_datos.transaccion():
        entorno.base_datos.ejecutar(
            "UPDATE reservas SET estado = %s WHERE id = %s",
            (EstadoReserva.COMPLETADA.value, reserva.id),
        )


def _crear_alquiler_en_curso(entorno, reserva, retiro_real) -> None:
    with entorno.base_datos.transaccion():
        entorno.base_datos.ejecutar(
            """
            INSERT INTO alquileres (
                reserva_id, fecha_hora_retiro_real, estado
            )
            VALUES (%s, %s, %s)
            """,
            (
                reserva.id,
                retiro_real,
                EstadoAlquiler.EN_CURSO.value,
            ),
        )


def _crear_alquiler_finalizado(
    entorno, reserva, retiro_real, devolucion_real
) -> None:
    with entorno.base_datos.transaccion():
        entorno.base_datos.ejecutar(
            """
            INSERT INTO alquileres (
                reserva_id,
                fecha_hora_retiro_real,
                fecha_hora_devolucion_real,
                importe_base,
                recargo_demora,
                importe_final,
                estado
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                reserva.id,
                retiro_real,
                devolucion_real,
                Decimal("10000.00"),
                Decimal("0.00"),
                Decimal("10000.00"),
                EstadoAlquiler.FINALIZADO.value,
            ),
        )


def test_d01_rechaza_solapamiento_con_reserva_confirmada(entorno) -> None:
    _reservar(entorno, INICIO, INICIO + timedelta(hours=48))

    assert (
        entorno.servicio_reservas.consultar_disponibilidad(
            entorno.vehiculo.id,
            INICIO + timedelta(hours=24),
            INICIO + timedelta(hours=72),
        )
        is False
    )
    with pytest.raises(ErrorValidacion):
        _reservar(
            entorno,
            INICIO + timedelta(hours=24),
            INICIO + timedelta(hours=72),
        )


def test_d02_permite_extremos_contiguos(entorno) -> None:
    _reservar(entorno, INICIO, INICIO + timedelta(hours=24))

    assert (
        entorno.servicio_reservas.consultar_disponibilidad(
            entorno.vehiculo.id,
            INICIO + timedelta(hours=24),
            INICIO + timedelta(hours=48),
        )
        is True
    )
    nueva = _reservar(
        entorno,
        INICIO + timedelta(hours=24),
        INICIO + timedelta(hours=48),
    )
    assert nueva.id is not None


def test_d03_d09_cancelacion_libera_intervalo(entorno) -> None:
    reserva = _reservar(entorno, INICIO, INICIO + timedelta(hours=24))
    entorno.servicio_reservas.cancelar(reserva.id)

    assert (
        entorno.servicio_reservas.consultar_disponibilidad(
            entorno.vehiculo.id,
            INICIO,
            INICIO + timedelta(hours=24),
        )
        is True
    )
    nueva = _reservar(entorno, INICIO, INICIO + timedelta(hours=24))
    assert nueva.id is not None


def test_d04_reserva_completada_no_bloquea(entorno) -> None:
    reserva = _reservar(entorno, INICIO, INICIO + timedelta(hours=24))
    _completar_reserva(entorno, reserva)

    assert (
        entorno.servicio_reservas.consultar_disponibilidad(
            entorno.vehiculo.id,
            INICIO,
            INICIO + timedelta(hours=24),
        )
        is True
    )


def test_d05_alquiler_en_curso_bloquea(entorno) -> None:
    reserva = _reservar(
        entorno,
        INICIO - timedelta(hours=48),
        INICIO - timedelta(hours=24),
    )
    _crear_alquiler_en_curso(entorno, reserva, INICIO - timedelta(hours=1))

    assert (
        entorno.servicio_reservas.consultar_disponibilidad(
            entorno.vehiculo.id,
            INICIO,
            INICIO + timedelta(hours=24),
        )
        is False
    )
    with pytest.raises(ErrorValidacion):
        _reservar(entorno, INICIO, INICIO + timedelta(hours=24))


def test_d06_alquiler_finalizado_no_bloquea(entorno) -> None:
    reserva = _reservar(
        entorno,
        INICIO - timedelta(hours=48),
        INICIO - timedelta(hours=24),
    )
    _completar_reserva(entorno, reserva)
    _crear_alquiler_finalizado(
        entorno,
        reserva,
        INICIO - timedelta(hours=48),
        INICIO - timedelta(hours=24),
    )

    assert (
        entorno.servicio_reservas.consultar_disponibilidad(
            entorno.vehiculo.id,
            INICIO - timedelta(hours=24),
            INICIO,
        )
        is True
    )


def test_d07_otro_vehiculo_permite_misma_franja(entorno) -> None:
    _reservar(entorno, INICIO, INICIO + timedelta(hours=24))
    otro = entorno.nuevo_vehiculo()

    assert (
        entorno.servicio_reservas.consultar_disponibilidad(
            otro.id,
            INICIO,
            INICIO + timedelta(hours=24),
        )
        is True
    )


def test_d08_mismo_vehiculo_sin_solape(entorno) -> None:
    _reservar(entorno, INICIO, INICIO + timedelta(hours=24))

    assert (
        entorno.servicio_reservas.consultar_disponibilidad(
            entorno.vehiculo.id,
            INICIO + timedelta(hours=72),
            INICIO + timedelta(hours=96),
        )
        is True
    )


def test_d10_permite_nueva_reserva_que_termina_al_iniciar_la_existente(
    entorno,
) -> None:
    _reservar(entorno, INICIO, INICIO + timedelta(hours=24))

    nueva = _reservar(
        entorno,
        INICIO - timedelta(hours=24),
        INICIO,
    )
    assert nueva.id is not None


def test_v01_rechaza_rango_invalido(entorno) -> None:
    with pytest.raises(ErrorValidacion):
        _reservar(entorno, INICIO, INICIO)


@pytest.mark.parametrize(
    "estado", [EstadoVehiculo.BAJA, EstadoVehiculo.MANTENIMIENTO]
)
def test_v04_rechaza_vehiculo_no_operativo(entorno, estado) -> None:
    entorno.servicio_vehiculos.cambiar_estado(entorno.vehiculo.id, estado)

    with pytest.raises(ErrorValidacion):
        _reservar(entorno, INICIO, INICIO + timedelta(hours=24))


def test_v08_no_cancela_reserva_con_alquiler(entorno) -> None:
    reserva = _reservar(entorno, INICIO, INICIO + timedelta(hours=24))
    _crear_alquiler_en_curso(entorno, reserva, INICIO)

    with pytest.raises(ErrorValidacion):
        entorno.servicio_reservas.cancelar(reserva.id)


def test_v09_rollback_no_deja_reserva_parcial(entorno) -> None:
    _reservar(entorno, INICIO, INICIO + timedelta(hours=48))
    antes = len(
        entorno.servicio_reservas.listar(cliente_id=entorno.cliente.id)
    )

    with pytest.raises(ErrorValidacion):
        _reservar(
            entorno,
            INICIO + timedelta(hours=24),
            INICIO + timedelta(hours=72),
        )

    despues = len(
        entorno.servicio_reservas.listar(cliente_id=entorno.cliente.id)
    )
    assert despues == antes


def test_modificar_recalcula_importe_estimado(entorno) -> None:
    reserva = _reservar(entorno, INICIO, INICIO + timedelta(hours=24))

    modificada = entorno.servicio_reservas.modificar(
        reserva.id,
        fecha_hora_devolucion_prevista=INICIO + timedelta(hours=48),
    )

    assert modificada.importe_estimado == Decimal("20000.00")


def test_modificar_rechaza_solapamiento(entorno) -> None:
    _reservar(entorno, INICIO, INICIO + timedelta(hours=24))
    segunda = _reservar(
        entorno,
        INICIO + timedelta(hours=48),
        INICIO + timedelta(hours=72),
    )

    with pytest.raises(ErrorValidacion):
        entorno.servicio_reservas.modificar(
            segunda.id,
            fecha_hora_retiro_prevista=INICIO + timedelta(hours=12),
            fecha_hora_devolucion_prevista=INICIO + timedelta(hours=36),
        )


def test_no_se_puede_cancelar_dos_veces(entorno) -> None:
    reserva = _reservar(entorno, INICIO, INICIO + timedelta(hours=24))
    entorno.servicio_reservas.cancelar(reserva.id)

    with pytest.raises(ErrorValidacion):
        entorno.servicio_reservas.cancelar(reserva.id)
