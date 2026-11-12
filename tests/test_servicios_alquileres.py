"""Pruebas de integración de inicio y cierre de alquileres."""

from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from modelos.estados import (
    EstadoAlquiler,
    EstadoReserva,
    EstadoVehiculo,
)
from servicios.servicio_alquileres import ServicioAlquileres
from servicios.servicio_clientes import ServicioClientes
from servicios.servicio_reservas import ServicioReservas
from servicios.servicio_vehiculos import ServicioVehiculos
from utilidades.excepciones import ErrorNoEncontrado, ErrorValidacion

pytestmark = pytest.mark.integracion

INICIO = datetime(2026, 12, 10, 10, 0)
TARIFA = Decimal("10000.00")


@pytest.fixture
def entorno(base_datos_prueba):
    servicio_vehiculos = ServicioVehiculos(base_datos_prueba)
    servicio_clientes = ServicioClientes(base_datos_prueba)
    servicio_reservas = ServicioReservas(base_datos_prueba)
    servicio_alquileres = ServicioAlquileres(base_datos_prueba)

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

    datos = SimpleNamespace(
        base_datos=base_datos_prueba,
        servicio_vehiculos=servicio_vehiculos,
        servicio_reservas=servicio_reservas,
        servicio_alquileres=servicio_alquileres,
        cliente=cliente,
        vehiculo=vehiculo,
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
        base_datos_prueba.ejecutar(
            "DELETE FROM vehiculos WHERE id = %s",
            (vehiculo.id,),
        )
        base_datos_prueba.ejecutar(
            "DELETE FROM clientes WHERE id = %s",
            (cliente.id,),
        )


def _reservar(
    entorno,
    retiro=INICIO,
    devolucion=None,
    vehiculo=None,
):
    if devolucion is None:
        devolucion = retiro + timedelta(hours=48)
    return entorno.servicio_reservas.crear(
        entorno.cliente.id,
        (vehiculo or entorno.vehiculo).id,
        retiro,
        devolucion,
    )


def test_v10_cierre_puntual_completa_y_libera(entorno) -> None:
    reserva = _reservar(entorno)
    alquiler = entorno.servicio_alquileres.iniciar(reserva.id, INICIO)

    assert alquiler.id is not None
    assert alquiler.estado is EstadoAlquiler.EN_CURSO
    assert (
        entorno.servicio_vehiculos.obtener(entorno.vehiculo.id).estado
        is EstadoVehiculo.ALQUILADO
    )

    cerrado = entorno.servicio_alquileres.cerrar(
        alquiler.id, INICIO + timedelta(hours=48)
    )

    assert cerrado.estado is EstadoAlquiler.FINALIZADO
    assert cerrado.importe_base == Decimal("20000.00")
    assert cerrado.recargo_demora == Decimal("0.00")
    assert cerrado.importe_final == Decimal("20000.00")
    assert (
        entorno.servicio_reservas.obtener(reserva.id).estado
        is EstadoReserva.COMPLETADA
    )
    assert (
        entorno.servicio_vehiculos.obtener(entorno.vehiculo.id).estado
        is EstadoVehiculo.DISPONIBLE
    )

    persistido = entorno.servicio_alquileres.obtener(alquiler.id)
    assert persistido.importe_final == Decimal("20000.00")
    assert (
        entorno.servicio_reservas.consultar_disponibilidad(
            entorno.vehiculo.id,
            INICIO + timedelta(hours=72),
            INICIO + timedelta(hours=96),
        )
        is True
    )


def test_devolucion_anticipada_recalcula_importe_base(entorno) -> None:
    reserva = _reservar(entorno)
    alquiler = entorno.servicio_alquileres.iniciar(reserva.id, INICIO)

    cerrado = entorno.servicio_alquileres.cerrar(
        alquiler.id, INICIO + timedelta(hours=20)
    )

    assert cerrado.importe_base == Decimal("10000.00")
    assert cerrado.recargo_demora == Decimal("0.00")
    assert cerrado.importe_final == Decimal("10000.00")


def test_devolucion_tardia_aplica_recargo(entorno) -> None:
    reserva = _reservar(entorno)
    alquiler = entorno.servicio_alquileres.iniciar(reserva.id, INICIO)

    cerrado = entorno.servicio_alquileres.cerrar(
        alquiler.id, INICIO + timedelta(hours=50)
    )

    assert cerrado.importe_base == Decimal("20000.00")
    assert cerrado.recargo_demora == Decimal("833.33")
    assert cerrado.importe_final == Decimal("20833.33")


def test_cierre_usa_tarifa_acordada_aunque_cambie_el_vehiculo(
    entorno,
) -> None:
    reserva = _reservar(entorno)
    alquiler = entorno.servicio_alquileres.iniciar(reserva.id, INICIO)

    entorno.servicio_vehiculos.modificar(
        entorno.vehiculo.id,
        tarifa_diaria=Decimal("12000.00"),
    )

    cerrado = entorno.servicio_alquileres.cerrar(
        alquiler.id, INICIO + timedelta(hours=48)
    )

    assert cerrado.importe_final == Decimal("20000.00")


def test_v05_no_inicia_reserva_cancelada(entorno) -> None:
    reserva = _reservar(entorno)
    entorno.servicio_reservas.cancelar(reserva.id)

    with pytest.raises(ErrorValidacion):
        entorno.servicio_alquileres.iniciar(reserva.id, INICIO)


def test_v06_no_permite_segundo_alquiler(entorno) -> None:
    reserva = _reservar(entorno)
    entorno.servicio_alquileres.iniciar(reserva.id, INICIO)

    with pytest.raises(ErrorValidacion):
        entorno.servicio_alquileres.iniciar(reserva.id, INICIO)


def test_v07_no_inicia_con_otro_alquiler_en_curso(entorno) -> None:
    primera = _reservar(
        entorno,
        INICIO,
        INICIO + timedelta(hours=24),
    )
    segunda = _reservar(
        entorno,
        INICIO + timedelta(hours=72),
        INICIO + timedelta(hours=96),
    )
    entorno.servicio_alquileres.iniciar(primera.id, INICIO)

    with pytest.raises(ErrorValidacion):
        entorno.servicio_alquileres.iniciar(
            segunda.id, INICIO + timedelta(hours=72)
        )


def test_no_cierra_dos_veces(entorno) -> None:
    reserva = _reservar(entorno)
    alquiler = entorno.servicio_alquileres.iniciar(reserva.id, INICIO)
    entorno.servicio_alquileres.cerrar(
        alquiler.id, INICIO + timedelta(hours=48)
    )

    with pytest.raises(ErrorValidacion):
        entorno.servicio_alquileres.cerrar(
            alquiler.id, INICIO + timedelta(hours=49)
        )


def test_no_cierra_alquiler_inexistente(entorno) -> None:
    with pytest.raises(ErrorNoEncontrado):
        entorno.servicio_alquileres.cerrar(
            2_000_000_000, INICIO + timedelta(hours=1)
        )


def test_cierre_invalido_mantiene_alquiler_en_curso(entorno) -> None:
    reserva = _reservar(entorno)
    alquiler = entorno.servicio_alquileres.iniciar(reserva.id, INICIO)

    with pytest.raises(ErrorValidacion):
        entorno.servicio_alquileres.cerrar(alquiler.id, INICIO)

    persistido = entorno.servicio_alquileres.obtener(alquiler.id)
    assert persistido.estado is EstadoAlquiler.EN_CURSO
    assert persistido.importe_base is None
    assert persistido.importe_final is None


def test_no_inicia_con_vehiculo_en_mantenimiento(entorno) -> None:
    reserva = _reservar(entorno)
    entorno.servicio_vehiculos.cambiar_estado(
        entorno.vehiculo.id, EstadoVehiculo.MANTENIMIENTO
    )

    with pytest.raises(ErrorValidacion):
        entorno.servicio_alquileres.iniciar(reserva.id, INICIO)
